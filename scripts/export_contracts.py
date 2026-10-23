"""Run from repository root; npm run contracts follows this export."""
import json
from pathlib import Path
from lastcopy.api import app
from lastcopy import models

def build_openapi():
    schema = app.openapi().copy()
    for name in ("RunManifest", "SourceSnapshot", "SubmissionVersion", "XmlFact", "MediaReference", "EvidenceReceipt", "Finding", "RecoveryPlan", "DeviceManifest"):
        model = getattr(models, name)
        definition = model.model_json_schema(ref_template="#/components/schemas/{model}")
        schema["components"]["schemas"].update(definition.pop("$defs", {}))
        schema["components"]["schemas"][name] = definition
    return schema


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    (root / "contracts").mkdir(exist_ok=True)
    (root / "contracts/openapi.json").write_text(json.dumps(build_openapi(), indent=2) + "\n", encoding="utf-8")
    print("Exported authoritative API and domain contracts")
