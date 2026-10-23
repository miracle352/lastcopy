"""Deterministic spec extraction and upstream pin record. No network."""
import json
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
packet = (root / "LASTCOPY_CODEX_PROMPTS.md").read_text(encoding="utf-8")
contract = packet.split("## Product Contract\n", 1)[1].split("\n## Review focus", 1)[0]
(root / "docs/PRODUCT_SPEC.md").write_text("# LastCopy Product Contract\n\nExtracted verbatim from the user-approved [full packet](../LASTCOPY_CODEX_PROMPTS.md).\n\n" + contract, encoding="utf-8")
upstream = root / "third_party/world-model"
files = {path.relative_to(upstream).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(upstream.rglob("*")) if path.is_file() and path.name != "UPSTREAM.json" and "node_modules" not in path.parts}
(upstream / "UPSTREAM.json").write_text(json.dumps({"repository": "https://github.com/Meterless/Meterless", "commit": "1742dec56a66e58eef9dda2d2b865823758ca8cd", "source_directory": "engines/world-model", "license": "Apache-2.0", "renamed": {"AGENTS.md": "SPEC.md"}, "files_sha256": files}, indent=2) + "\n", encoding="utf-8")
zetaris = root / "fixtures/zetaris"
zetaris.mkdir(exist_ok=True)
for name, rows in {
    "device": [("synthetic-001", "a"), ("synthetic-002", "b")],
    "server": [("synthetic-001", "a"), ("synthetic-002", "c"), ("synthetic-unmatched", "d")],
}.items():
    content = "run_id,submission_id,xml_sha256\n" + "".join(f"lastcopy-smoke-001,{identifier},{character * 64}\n" for identifier, character in rows)
    (zetaris / f"{name}.csv").write_text(content, encoding="utf-8")
print("Extracted Product Contract, pinned source hashes, prepared tiny synthetic CSVs")
