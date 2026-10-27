# Submit LastCopy: owner checklist (updated 27 Oct 2026)

Platform: <https://hackathon.genai.works/submissions>. Deadline: **27 Oct 23:45 UTC (28 Oct 00:45 WAT)**.
Nothing here has been submitted, and the repository's visibility has not been changed. Both are yours to do.

## 1. Track

**The Agent That Can Explain Why.** Check that no other submission on your account uses it.

## 2. Team name

Pulled from your team settings. It currently shows **python**. Rename the team there if you want LastCopy or your own name.

## 3. Description (paste between the markers; within 150–2000 characters)

<!-- description-start -->
LastCopy answers the question every offline survey team faces before resetting a tablet: is anything on here still the only copy? Field teams using ODK (2M+ people, 250M+ submissions a year, 194 countries) wipe devices between rounds on the strength of a server count. That count cannot see a photo that never uploaded, a record stuck on the device, or a spreadsheet that merely hides answers the server already has.

For each tablet, LastCopy gives one answer: SAFE TO WIPE, RECOVER FIRST or HOLD. It proves the answer byte for byte and explains it in plain language. A Meterless World Model plans the investigation from graph state. A Scout runs four cross-source SQL joins on Zetaris. Nemotron via Meterless Nightshift forms hypotheses, critiques them (the Reviewer can send work back), chooses permitted remedies and writes the explanation. A deterministic verifier compares original bytes and is the only source of verdicts. Raw evidence can overturn a hypothesis, and that change is logged. A code wipe gate (seven criteria) clears a tablet only when the bytes prove it. An Adversary then tries to break every clearance, and code must answer each objection. Each decision gets a SHA-256 certificate that anyone can re-verify against the original archives. No model can make a tablet look safe, and every explanation is checked against the evidence.

On 27 Oct the five-tablet fleet ran live: 7 Zetaris queries, 7 Nemotron calls (Nemotron also played the Adversary), 0 fallbacks, and all decisions correct. A blind benchmark of 500 random fleets got 1,980 of 1,980 tablets right, with 0 wrongly cleared. `python run.py` reproduces the full loop in seconds with no keys. The repo includes four examples, JSONL traces, a printable clearance sheet, 303 tests and Docker. Limits: synthetic fixtures, not yet piloted with a field team.
<!-- description-end -->

## 4. Video (required, 1–4 minutes)

Upload the new narrated film once it is produced: `submission/LastCopy-demo.mp4`. The older `LastCopy-demo-narrated.mp4` shows the previous product and should not be used.

## 5. GitHub solution (required)

<https://github.com/miracle352/lastcopy>: `main` holds the finished product. **Make the repository public** before submitting, then open the link in a signed-out window to confirm judges can see it.

## 6. Pitch deck (optional)

Use the new 9-slide deck (Slides artifact "LastCopy — Open Agent Hackathon deck"). Download it as **PowerPoint or PDF** from its Share › Export menu and upload that file. `LastCopy-submission-deck.pptx` in this folder is the old deck; don't use it.

## 7. Sponsor technology explanation (if the form asks)

- **Zetaris:** the evidence layer. Each connected run registers the device exports, server capture, spreadsheet view and file references as tables. The Scout's four cross-source joins and the evidence fetcher query them. In the live run, all 7 queries were answered by Zetaris.
- **Meterless World Model:** the planner. It holds suspicions, hypothesis revisions, findings, remedies and decisions as a graph and selects every next action from that state (pinned reference, conformance 8/8).
- **Meterless Nightshift → NVIDIA Nemotron:** the only model provider in connected mode. It runs four judgement roles (Investigator, Reviewer, Remediation advisor, Explainer) on `nvidia/nemotron-3.5-lightning-30b-a3b`, and the serving model is recorded on every trace line (`logs/trace-live-connected-fleet.jsonl`).
- **Codex:** the development tool. Cursor was not used.

## 8. Pre-existing components

The vendored Meterless World Model reference (Apache-2.0, `third_party/world-model`), open-source dependencies in `requirements.lock` / `package-lock.json`, and OFL fonts. Everything else was built during the build window.

## Before you press Submit

1. Open <https://lastcopy-five.vercel.app> and `/demo` in a signed-out window. The "Live · 27 Oct" tab should play.
2. Check that the GitHub link works signed out (after making it public).
3. Check that the uploaded video plays with sound.
4. **Save Draft**, review, then **Submit** yourself.

Do not claim a field rollout, piloting with a real team, or Kobo/encrypted-form support.
