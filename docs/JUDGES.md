# For judges: where to find the evidence for each criterion

Every claim below points at a file or a command you can run in under a minute.
Nothing here needs keys or network unless it says **connected**.

| Criterion (weight) | What LastCopy does | Check it |
|---|---|---|
| **Impact (30)** | Decides, per field tablet, whether a reset would destroy the only copy of survey data. ODK is used by 2M+ people sending 250M+ submissions a year in 194 countries (WHO polio and cholera surveillance among them). The output is an action a coordinator can take tonight: reset, recover a named file, or hold. | [`output_examples/live_clearance_sheet.md`](../output_examples/live_clearance_sheet.md), a printable sheet with actions and sign-off lines · README §1 sources |
| **Technical execution (20)** | A Meterless World Model plans every step from graph state. Four cross-source SQL joins run on Zetaris, a deterministic verifier compares original bytes, and a code wipe gate issues hashed certificates. Bounded run (12 steps, 2 critique rounds, 10 model calls, 300 s), schema-bound model calls with a labelled fallback. **303 tests.** Blind benchmark: `python -m scripts.blind_eval` (500/500 fleets and 1,980/1,980 tablets decided correctly across seeds 1-500, 0 tablets wrongly cleared). | `python run.py` (about 4 s) · `python -m pytest -q` · `npm run conformance:world-model` (8/8) |
| **Innovation (15)** | Agents investigate, code proves. The Reviewer can send hypotheses back. Raw bytes can overturn the Investigator, and that is logged as `decision_changed`. A model can never make a tablet look safe, and an Adversary must fail to break every clearance before it stands. Every certificate can be re-verified by a third party from the original archives. | `python -m scripts.verify_certificate output_examples/live_connected_fleet.json --archive fixtures/fleet/tablet-02.zip --archive fixtures/fleet/server-payload.zip` |
| **Demo (15)** | Live site with an interactive replay of five real runs, including the 27 Oct connected run. | <https://lastcopy-five.vercel.app/demo> → "Live · 27 Oct" tab; step through the plan |
| **Product & UX (10)** | One answer per tablet in plain language, a hero that shows the real decision, an interactive gate calculator, a clearance sheet for print. | <https://lastcopy-five.vercel.app> |
| **Sponsor tech (10)** | **Zetaris:** every Scout and evidence query in connected mode (7 in the live run). **Meterless World Model:** selects every next action. **Meterless Nightshift → NVIDIA Nemotron:** all 7 judgement calls in the live run, including the Adversary ranking five objections against the cleared tablet, model identity recorded per call, 0 fallbacks. | [`logs/trace-live-connected-fleet.jsonl`](../logs/trace-live-connected-fleet.jsonl) (each `model_request` line names `nvidia/nemotron-3.5-lightning-30b-a3b`) · `sponsor_status` in [`live_connected_fleet.json`](../output_examples/live_connected_fleet.json) |

## Guideline checklist

| Requirement | Where |
|---|---|
| Public repo + README | this repository, [`README.md`](../README.md) |
| `run.py` entry point | `python run.py`, `--all`, `--serve` (POST `/investigate`) |
| `input_examples/` / `output_examples/` | four bundled questions; outputs include decisions, certificates, SQL text, hypotheses and the full trace |
| `logs/` JSONL with agent_name, action, input/output summary, target_agent, model, confidence, retry_count, status | `logs/trace-*.jsonl` (four sample runs plus the live connected run) |
| `SAMPLE_MODE` | Sample is the default; Connected needs `SAMPLE_MODE=false` and `--connected --nemotron` |
| Docker | `docker compose build && docker compose up -d` |
| Bounded runs and failure handling | README §6 |
| Pre-existing components declared | README §8 |

## Honest limits

- The live run used the bundled synthetic five-tablet fixture, not field data from a real survey team.
- Sample mode replaces the five model roles with a written offline policy. Every trace line says so.
- A certificate proves which bytes were compared, not that the answers are true, and covers only the supplied exports.
- Tested against ODK Central v2026.3.1 and Collect v2026.3.5. No Kobo or encrypted-form claim.
