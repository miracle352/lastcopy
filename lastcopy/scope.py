"""Deterministic run mapping validation. Never infer destinations from filenames."""
from .models import RunManifest, ImportInventory


def validate_run_import(run: RunManifest, source: ImportInventory) -> list[str]:
    limitations = []
    if source.manifest.snapshot_id not in run.source_snapshot_ids:
        limitations.append("Imported snapshot is outside run scope")
    if source.manifest.device_id not in run.expected_device_ids:
        limitations.append("Imported device is outside the explicit roster")
    if any(version.form_id != run.destination.form_id for version in source.versions):
        limitations.append("Source form does not match explicit destination mapping")
    if run.mode == "sample" and not source.manifest.synthetic:
        limitations.append("Sample runs accept only explicitly synthetic fixture data")
    return limitations
