"""Bounded immutable ZIP inventory, not a preservation comparator (Stage 2)."""
import hashlib
import io
import json
import stat
import re
import zipfile
from collections import Counter
from defusedxml.ElementTree import iterparse
from .config import Settings
from .models import DeviceManifest, ImportInventory, SubmissionVersion, MediaReference, safe_path


class ImportRejected(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_xml(data: bytes, settings: Settings):
    if len(data) > settings.limit("MAX_XML_BYTES"):
        raise ImportRejected("XML exceeds MAX_XML_BYTES")
    depth = nodes = text = 0
    root = None
    try:
        for event, element in iterparse(io.BytesIO(data), events=("start", "end"), forbid_dtd=True, forbid_entities=True, forbid_external=True):
            if event == "start":
                if root is None:
                    root = element
                depth += 1
                nodes += 1
                if depth > settings.limit("MAX_XML_DEPTH") or nodes > settings.limit("MAX_XML_NODES"):
                    raise ImportRejected("XML exceeds depth/node limits")
            else:
                text += len(element.text or "") + len(element.tail or "")
                if text > settings.limit("MAX_XML_TEXT"):
                    raise ImportRejected("XML exceeds MAX_XML_TEXT")
                depth -= 1
    except ImportRejected:
        raise
    except Exception:
        raise ImportRejected("Invalid XML or forbidden DTD/entity") from None
    if root is None:
        raise ImportRejected("Empty XML")
    return root


def walk(root):
    def visit(node, path, indices):
        yield node, path, indices
        counts = Counter()
        for child in node:
            counts[child.tag] += 1
            yield from visit(child, f"{path}/{child.tag}[{counts[child.tag]}]", indices + [counts[child.tag]])
    return visit(root, f"/{root.tag}[1]", [1])


def read_archive(data: bytes, settings: Settings) -> dict[str, bytes]:
    if len(data) > settings.limit("MAX_UPLOAD_BYTES"):
        raise ImportRejected("Archive exceeds MAX_UPLOAD_BYTES")
    files = {}
    names = set()
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if len(archive.infolist()) > settings.limit("MAX_ZIP_ENTRIES"):
                raise ImportRejected("Archive exceeds MAX_ZIP_ENTRIES")
            for entry in archive.infolist():
                if "\x00" in entry.orig_filename:
                    raise ImportRejected("NUL in archive path")
                name = entry.filename.rstrip("/") if entry.is_dir() else entry.filename
                safe_path(name)
                normalized = name.casefold()
                if normalized in names:
                    raise ImportRejected("Duplicate normalized archive path")
                names.add(normalized)
                if entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ImportRejected("Encrypted entries and symlinks are unsupported")
                total += entry.file_size
                if total > settings.limit("MAX_UNCOMPRESSED_BYTES"):
                    raise ImportRejected("Archive exceeds MAX_UNCOMPRESSED_BYTES")
                if not entry.is_dir():
                    files[name] = archive.read(entry)
    except ImportRejected:
        raise
    except Exception:
        raise ImportRejected("Invalid ZIP or unsafe archive path") from None
    # Parent-file collisions are ambiguous even though nothing is extracted.
    for name in files:
        if any("/".join(name.split("/")[:i]) in files for i in range(1, len(name.split("/")))):
            raise ImportRejected("Archive path has a file as parent")
    return files


def inventory(data: bytes, settings: Settings) -> ImportInventory:
    files = read_archive(data, settings)
    try:
        manifest = DeviceManifest.model_validate_json(files["device-manifest.json"])
    except Exception:
        raise ImportRejected("device-manifest.json is missing or invalid; identity, completion and provenance are required") from None
    definitions = {}
    xforms = "{http://www.w3.org/2002/xforms}"
    for definition in manifest.form_definitions:
        if definition.xml_path not in files:
            raise ImportRejected("Manifest form definition file is missing")
        form = parse_xml(files[definition.xml_path], settings)
        instances = form.findall(f".//{xforms}model/{xforms}instance")
        if not instances or len(instances[0]) != 1:
            raise ImportRejected("XForm requires one primary instance root")
        template = instances[0][0]
        key = (template.attrib.get("id"), template.attrib.get("version"))
        if not key[0] or key in definitions:
            raise ImportRejected("XForm identity is missing or ambiguous")
        binary = {b.attrib.get("nodeset") or b.attrib.get("ref") for b in form.findall(f".//{xforms}bind") if b.attrib.get("type") == "binary"}
        definitions[key] = (template.tag, binary)
    versions = []
    limitations = []
    for item in manifest.instances:
        if item.xml_path not in files:
            raise ImportRejected("Manifest instance XML file is missing")
        root = parse_xml(files[item.xml_path], settings)
        identities = [node.text for node in root.findall("./{*}meta/{*}instanceID") if node.text]
        deprecated = [node.text for node in root.findall("./{*}meta/{*}deprecatedID") if node.text]
        if len(identities) != 1 or len(deprecated) > 1:
            raise ImportRejected("Instance identity is missing or ambiguous")
        version_id = identities[0]
        key = (root.attrib.get("id"), root.attrib.get("version"))
        if not key[0]:
            raise ImportRejected("Instance form identity is missing")
        issues = []
        definition_matches = key in definitions and definitions[key][0] == root.tag
        if not definition_matches:
            issues.append("Missing matching original XForm; media references cannot be fully established")
        if deprecated:
            issues.append("Edit-chain root is unresolved; no automatic recovery")
        if item.completion_status != "complete":
            issues.append("Completion not established; excluded from automatic submission")
        references = []
        for node, path, indices in walk(root):
            # First-release supported binds use absolute unprefixed paths; do not guess complex XPath.
            local_path = re.sub(r"\[\d+\]", "", re.sub(r"\{[^}]*\}", "", path))
            if not definition_matches or local_path not in definitions[key][1] or not node.text:
                continue
            try:
                filename = safe_path(node.text)
                archive_path = safe_path(item.xml_path.rsplit("/", 1)[0] + "/" + filename) if "/" in item.xml_path else filename
            except ValueError:
                raise ImportRejected("Unsafe media reference") from None
            media_data = files.get(archive_path)
            if media_data is None:
                issues.append("Referenced media bytes absent from source archive")
            references.append(MediaReference(version_id=version_id, filename=filename, xml_path=path, occurrence_indices=indices, archive_path=archive_path, sha256=digest(media_data) if media_data is not None else None, readback_receipt_id=None))
        if any(bind and (":" in bind or "[" in bind or not bind.startswith("/")) for bind in definitions.get(key, (None, set()))[1]):
            issues.append("Unsupported media bind XPath; requires explicit mapping")
        versions.append(SubmissionVersion(snapshot_id=manifest.snapshot_id, form_id=key[0], form_version=key[1], logical_submission_id=None if deprecated else version_id, version_id=version_id, deprecated_id=deprecated[0] if deprecated else None, xml_path=item.xml_path, xml_sha256=digest(files[item.xml_path]), completion_status=item.completion_status, current=None, media=references, limitations=issues))
        limitations.extend(issues)
    return ImportInventory(manifest=manifest, archive_sha256=digest(data), files={name: digest(value) for name, value in files.items()}, versions=versions, limitations=sorted(set(limitations)), mode="sample" if settings.sample else "connected")
