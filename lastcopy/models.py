"""Authoritative API/domain schemas. Browser types are generated, never duplicated."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AfterValidator, AwareDatetime, model_validator, JsonValue
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
    scope_complete: bool = False
    scope_provenance: Attribution | None = None

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
    source_snapshot_ids: list[Id] = Field(min_length=1, max_length=9)
    expected_device_ids: list[Id] = Field(min_length=1, max_length=100)
    roster_provenance: Attribution
    destination: Destination
    max_steps: int = Field(default=12, ge=1, le=12)
    max_critique_rounds: int = Field(default=2, ge=0, le=2)
    max_seconds: int = Field(default=300, ge=1, le=300)

    @model_validator(mode="after")
    def unique_scope(self):
        if len(set(self.source_snapshot_ids)) != len(self.source_snapshot_ids) or len(set(self.expected_device_ids)) != len(self.expected_device_ids):
            raise ValueError('Snapshot IDs and expected device IDs must be unique')
        return self


class TabularView(Contract):
    version_id: Id
    archive_path: Path
    receipt_id: Id
    # Narrow wide-CSV diagnostic view: one row per version, explicit expanded paths.
    columns: dict[str, str] = Field(max_length=1000)


class SourceSnapshot(Contract):
    schema_version: Literal[1]
    snapshot_id: Id
    kind: Literal["device", "central_raw"]
    archive_sha256: Digest
    captured_at: KnownTime
    synthetic: bool
    scope_complete: bool
    project_id: int | None = None
    connection_id: Id | None = None
    form_ids: list[Id] = Field(default_factory=list)
    device_id: Id | None = None
    limitations: list[str] = Field(default_factory=list)
    receipt_ids: list[Id] = Field(default_factory=list)
    receipts: list["EvidenceReceipt"] = Field(default_factory=list)
    versions: list["SubmissionVersion"] = Field(default_factory=list)
    listing_receipt_id: Id | None = None
    history_complete: bool = False
    attachment_listing_receipt_ids: dict[str, str] = Field(default_factory=dict)
    tabular_views: list[TabularView] = Field(default_factory=list, max_length=100)


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
    attachment_filename: Path | None = None


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
    code: str = 'UNSPECIFIED'
    media_filenames: list[str] = Field(default_factory=list)
    recovery_eligible: bool = False
    next_action: Literal['none', 'review_create', 'review_media', 'export_guidance', 'manual'] = 'manual'
    current_version_id: Id | None = None

    @model_validator(mode="after")
    def consistent_preservation(self):
        expected = ("preserved" if self.verdict in ("PRESERVED", "EXPORT_VIEW_ONLY") else
                    "unknown" if self.verdict == "UNVERIFIABLE" else "not_preserved")
        if self.preservation != expected:
            raise ValueError("verdict and preservation disagree")
        if self.recovery_eligible and self.verdict not in ('MISSING_SUBMISSION', 'MISSING_ATTACHMENT'):
            raise ValueError('Only verified missing items may be recovery candidates')
        return self


class Coverage(Contract):
    complete: bool
    expected_devices: list[Id]
    supplied_devices: list[Id]
    missing_devices: list[Id]
    limitations: list[str]
    checked_versions: int


class ReconciliationReport(Contract):
    schema_version: Literal[1] = 1
    run_id: Id
    mode: Literal['sample', 'connected', 'replay']
    provenance: str
    status: Literal['completed'] = 'completed'
    preservation_outcome: Literal['verified', 'with_gaps', 'unresolved']
    coverage: Coverage
    findings: list[Finding]
    receipts: list[EvidenceReceipt]
    input_hashes: dict[str, Digest]
    provider_calls: Literal[0] = 0
    recovery_executed: Literal[False] = False


class RunRequest(Contract):
    manifest_id: Digest
    device_input_ids: list[Digest] = Field(min_length=1, max_length=8)
    server_input_id: Digest


class RegisteredInput(Contract):
    input_id: Digest
    kind: Literal['device', 'server', 'manifest']
    sha256: Digest


class JobStatus(Contract):
    run_id: Id
    state: Literal['queued', 'running', 'completed', 'cancelled', 'failed', 'interrupted']
    preservation_outcome: Literal['verified', 'with_gaps', 'unresolved'] | None = None
    error: str | None = None
    output_hashes: dict[str, Digest] = Field(default_factory=dict)


class RecoveryEnvironment(Contract):
    base_url: str
    central_version: str
    dedicated_test_project: bool
    project_name: str | None


class RecoveryPlan(Contract):
    schema_version: Literal[1]
    plan_id: Digest
    plan_sha256: Digest
    run_id: Id
    finding_id: Id
    target: Destination
    environment: RecoveryEnvironment
    mode: Literal['sample','connected','replay']
    snapshot_id: Id
    logical_submission_id: Id
    version_id: Id
    form_version: Id | None
    operation: Literal['create_missing_submission','restore_missing_media']
    xml_path: Path
    form_paths: list[Path] = Field(min_length=1,max_length=100)
    media_paths: dict[Path,Path]
    media_filenames: list[Path] = Field(max_length=500)
    source_hashes: dict[Path, Digest]
    source_archive_hashes: dict[Digest,int]
    evidence_ids: list[Id] = Field(min_length=1)
    expected_current_version: Id | None
    before_verdict: Literal['MISSING_SUBMISSION','MISSING_ATTACHMENT']
    preconditions: list[str] = Field(min_length=1,max_length=20)
    limitations: list[str]


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
    stage: Literal[5] = 5
    mode: Literal["sample", "connected"]
    live_verified: Literal[False] = False


class RecoveryStageRequest(Contract):
    run_id: Id
    finding_id: Id


class RecoveryReviewRequest(Contract):
    plan_sha256: Digest
    target: Destination


class RecoveryCaptureRequest(Contract):
    manifest_id: Digest
    device_input_ids: list[Digest] = Field(min_length=1,max_length=8)


class UIPrepareRequest(Contract):
    device_input_ids: list[Digest] = Field(min_length=1,max_length=8)
    expected_device_ids: list[Id] = Field(min_length=1,max_length=100)
    source: Literal['snapshot','connection']
    server_input_id: Digest | None = None
    captured_run_reference: Id | None = None
    confirm_scope: bool


class UIFindingRequest(Contract):
    finding_id: Id


class UISampleCase(Contract):
    id: Literal['media','stranded','export','history','conflict']
    title: str
    description: str


class UISettings(Contract):
    mode: Literal['sample','connected']
    target: Destination | None
    connected_ready: bool
    limits: dict[str,int]
    samples: list[UISampleCase]
    backend_scope: str


class UIDevice(Contract):
    input_id: Digest
    sha256: Digest
    inventory: ImportInventory


class UISnapshotIdentity(Contract):
    snapshot_id: Id
    connection_id: Id | None
    project_id: int | None
    form_ids: list[Id]
    captured_at: KnownTime
    scope_complete: bool
    history_complete: bool
    synthetic: bool


class UIServer(Contract):
    input_id: Digest
    sha256: Digest
    snapshot: UISnapshotIdentity


class UIDraft(Contract):
    run_id: Id
    request: RunRequest
    manifest: RunManifest
    devices: list[ImportInventory]
    provenance: str
    sample_case: str | None
    parent_run_id: Id | None
    captured_run_reference: Id | None


class UIStatus(Contract):
    run_id: Id
    state: Literal['draft','queued','running','completed','cancelled','failed','interrupted']
    preservation_outcome: Literal['verified','with_gaps','unresolved'] | None
    error: str | None
    output_hashes: dict[str,Digest] = Field(default_factory=dict)


class UIRunEvent(Contract):
    sequence: int
    run_id: Id
    event: str
    observed_at: AwareDatetime
    details: dict[str,JsonValue]


class UIAttemptEvent(Contract):
    sequence: int
    plan_id: Digest
    state: str
    at: AwareDatetime
    details: dict[str,JsonValue]


class UIReadback(Contract):
    state: Literal['ready','preserved','blocked']
    checked_at: AwareDatetime
    capture_hashes: list[Digest]
    report: ReconciliationReport
    writes: Literal[0]


class RecoveryDeltaItem(Contract):
    snapshot_id: Id
    version_id: Id
    verdict: Verdict


class RecoveryResult(Contract):
    plan_id: Digest
    state: Literal['not_applied','pending_readback','verified','blocked','with_gaps']
    events_available: bool = False
    error: str | None = None
    target: Destination | None = None
    before: ReconciliationReport | None = None
    after: ReconciliationReport | None = None
    capture_hashes: list[list[Digest]] = Field(default_factory=list)
    write_receipts: list[dict[str,JsonValue]] = Field(default_factory=list)
    source_hashes_verified: bool = False
    disappeared: list[Verdict] = Field(default_factory=list)
    remaining: list[Verdict] = Field(default_factory=list)
    new_conflicts: list[Verdict] = Field(default_factory=list)
    scope: str | None = None
    run_delta: dict[str,list[RecoveryDeltaItem]] = Field(default_factory=dict)


class UIPlanState(Contract):
    plan: RecoveryPlan
    reviewed: bool
    result: RecoveryResult
    events: list[UIAttemptEvent]
    readback: UIReadback | None


class UIRunView(Contract):
    manifest: RunManifest
    request: RunRequest
    status: UIStatus
    report: ReconciliationReport | None
    current_report: ReconciliationReport | None
    events: list[UIRunEvent]
    plans: list[UIPlanState]
    sample_readback_run_id: Id | None
    sample_case: str | None = None
    parent_run_id: Id | None = None
    captured_run_reference: Id | None = None
    provenance: str = 'Deterministic supplied-evidence comparison'
    investigation: 'UIInvestigationStatus | None' = None


class UIRecent(Contract):
    run_id: Id
    mode: Literal['sample','connected','replay']
    status: JobStatus
    captured_run_reference: Id | None


class UIObject(Contract):
    object_id: Digest
    snapshot_id: Id
    path: Path
    sha256: Digest


class UIComparedValue(Contract):
    path: str
    occurrence_indices: list[int]
    source_value: str | None
    server_value: str | None
    current_edit_value: str | None
    source_present: bool
    server_present: bool


class UIFindingEvidence(Contract):
    finding: Finding
    receipts: list[EvidenceReceipt]
    source_files: list[UIObject]
    scope: str
    compared_values: list[UIComparedValue]
    server_xml_available: bool
    current_edit_available: bool
    values_truncated: bool


class UIImportSessionRequest(Contract):
    session_id: Id | None = None
    device_input_ids: list[Digest] = Field(default_factory=list,max_length=8)
    roster: str = Field(default='',max_length=20000)
    source: Literal['snapshot','connection']
    server_input_id: Digest | None = None
    captured_run_reference: str = Field(default='',max_length=512)


class UIImportSession(Contract):
    session_id: Id
    devices: list[UIDevice]
    roster: str
    source: Literal['snapshot','connection']
    server: UIServer | None
    captured_run_reference: str


class UIInvestigationStatus(Contract):
    state: Literal['queued','running','completed','failed','cancelled','interrupted']
    error: str | None
    attempt_id: Id
    events: list[dict[str,JsonValue]]
    result: dict[str,JsonValue] | None
    limits: dict[str,int]
    provenance: str
