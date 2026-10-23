"""Authoritative API/domain schemas. Browser types are generated, never duplicated."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AfterValidator, AwareDatetime, model_validator
import re


def safe_path(value: str) -> str:
    if (not value or "\\" in value or value.startswith("/") or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or any(ord(c) < 32 for c in value)):
        raise ValueError("expected a relative POSIX archive path without traversal")
    return value


Path = Annotated[str, Field(min_length=1, max_length=1024), AfterValidator(safe_path)]
Id = Annotated[str, Field(min_length=1, max_length=512)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
KnownTime = AwareDatetime | Literal["unknown"]
Verdict = Literal["PRESERVED", "MISSING_SUBMISSION", "MISSING_ATTACHMENT", "CONTENT_CONFLICT", "EXPORT_VIEW_ONLY", "UNVERIFIABLE"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Attribution(Contract):
    origin: Literal["coordinator_attestation", "exporter_metadata"]
    reference: Id


class InstanceEntry(Contract):
    xml_path: Path
    completion_status: Literal["complete", "draft", "unknown"]
    completion_provenance: Attribution


class FormDefinition(Contract):
    xml_path: Path


class DeviceManifest(Contract):
    schema_version: Literal[1]
    snapshot_id: Id
    device_id: Id
    captured_at: KnownTime
    collector_version: Id
    device_provenance: Attribution
    instances: list[InstanceEntry] = Field(min_length=1, max_length=500)
    form_definitions: list[FormDefinition] = Field(min_length=1, max_length=100)
    synthetic: bool = False

    @model_validator(mode="after")
    def unique_paths(self):
        paths = [i.xml_path for i in self.instances] + [f.xml_path for f in self.form_definitions]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate manifest XML paths")
        return self


class Destination(Contract):
    connection_id: Id
    project_id: Annotated[int, Field(gt=0)]
    form_id: Id
    environment: Literal["dedicated_synthetic_test"]
    mapping_provenance: Attribution


class RunManifest(Contract):
    schema_version: Literal[1]
    run_id: Id
    mode: Literal["sample", "connected", "replay"]
    source_snapshot_ids: list[Id] = Field(min_length=1)
    expected_device_ids: list[Id] = Field(min_length=1)
    roster_provenance: Attribution
    destination: Destination
    max_steps: int = Field(default=12, ge=1, le=12)
    max_critique_rounds: int = Field(default=2, ge=0, le=2)
    max_seconds: int = Field(default=300, ge=1, le=300)


class SourceSnapshot(Contract):
    schema_version: Literal[1]
    snapshot_id: Id
    kind: Literal["device", "central_raw"]
    archive_sha256: Digest
    captured_at: KnownTime
    synthetic: bool
    scope_complete: bool
    project_id: int | None = None
    form_ids: list[Id] = Field(default_factory=list)
    device_id: Id | None = None
    limitations: list[str] = Field(default_factory=list)
    receipt_ids: list[Id] = Field(default_factory=list)
    receipts: list["EvidenceReceipt"] = Field(default_factory=list)
    versions: list["SubmissionVersion"] = Field(default_factory=list)


class SubmissionVersion(Contract):
    snapshot_id: Id
    form_id: Id
    form_version: Id | None
    logical_submission_id: Id | None
    version_id: Id
    deprecated_id: Id | None
    xml_path: Path
    xml_sha256: Digest
    completion_status: Literal["complete", "draft", "unknown"]
    current: bool | None
    media: list["MediaReference"] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class XmlFact(Contract):
    snapshot_id: Id
    version_id: Id
    expanded_path: str
    occurrence_indices: list[int]
    expanded_name: str
    attributes: dict[str, str]
    text: str | None
    tail: str | None


class MediaReference(Contract):
    version_id: Id
    filename: Path
    xml_path: str
    occurrence_indices: list[int]
    archive_path: Path
    sha256: Digest | None
    readback_receipt_id: Id | None


class EvidenceReceipt(Contract):
    evidence_id: Id
    source_snapshot_id: Id
    source_file: Path | None
    archive_sha256: Digest | None
    captured_at: KnownTime
    query_receipt_id: Id | None
    request_method: Literal["GET", "POST", "LOCAL"]
    outcome: Literal["success", "partial", "failed", "synthetic"]
    http_status: Annotated[int, Field(ge=100, le=599)] | None = None
    request_scope: str
    response_sha256: Digest | None
    comparison: str | None
    form_id: Id | None
    version_id: Id | None
    xml_path: str | None
    repeat_indices: list[int] = Field(default_factory=list)


class Finding(Contract):
    finding_id: Id
    verdict: Verdict
    preservation: Literal["preserved", "not_preserved", "unknown"]
    summary: str
    snapshot_id: Id
    form_id: Id
    logical_submission_id: Id | None
    version_id: Id
    evidence_ids: list[Id] = Field(min_length=1)
    absence_scope: str | None
    original_retained_in_history: bool = False

    @model_validator(mode="after")
    def consistent_preservation(self):
        expected = ("preserved" if self.verdict in ("PRESERVED", "EXPORT_VIEW_ONLY") else
                    "unknown" if self.verdict == "UNVERIFIABLE" else "not_preserved")
        if self.preservation != expected:
            raise ValueError("verdict and preservation disagree")
        return self


class RecoveryPlan(Contract):
    plan_id: Id
    destination: Destination
    logical_submission_id: Id
    version_id: Id
    operation: Literal["create_missing_submission", "restore_missing_media", "manual"]
    source_hashes: dict[Path, Digest]
    evidence_ids: list[Id] = Field(min_length=1)
    preconditions: list[str] = Field(min_length=1)
    state: Literal["draft", "reviewed", "signing", "pending", "confirmed", "rejected", "reverted", "expired", "unverifiable"]
    fresh_readback_receipt_ids: list[Id] = Field(default_factory=list)


class ImportInventory(Contract):
    manifest: DeviceManifest
    archive_sha256: Digest
    files: dict[str, Digest]
    versions: list[SubmissionVersion]
    limitations: list[str]
    mode: Literal["sample", "connected"]
    preservation_checked: Literal[False] = False


class ConfigurationStatus(Contract):
    mode: Literal["sample", "connected"]
    ready: bool
    missing: dict[str, list[str]]
    errors: list[str]


class Health(Contract):
    service: Literal["lastcopy-api"] = "lastcopy-api"
    status: Literal["ok"] = "ok"
    stage: Literal[1] = 1
    mode: Literal["sample", "connected"]
    live_verified: Literal[False] = False
