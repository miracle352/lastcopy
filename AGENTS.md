# LastCopy persistent project instructions

Read [the complete packet](LASTCOPY_CODEX_PROMPTS.md) before working. Prompt 0
is persistent; the Product Contract in docs/PRODUCT_SPEC.md is authoritative.
Execute only the requested stage. Current stage: 6. Stage 7 requires a new request.

Use deterministic code for identities, ZIP/XML handling, hashes, comparisons,
recovery and verdicts. Models may investigate; they cannot decide preservation.
Preserve original archives. Never infer completion from a saved XML file.
Separate Sample, Replay and Connected; sample execution makes no network calls.
Never fabricate provider success, model identity, field data or recovery.
No AI-generated imagery, image tools, raster art, videos or stock photography.
No marketing polish until Stage 6. No Kobo first-release compatibility claim.
Keep credentials server-side in ignored local config; print variable names only.
Reuse the existing Zetaris AWS instance; do not provision infrastructure or IAM.
Live recovery writes only in the configured dedicated synthetic ODK test project.
Do not overwrite conflicting answers, erase devices, or invent missing bytes.
Keep docs/HANDOFF.md current with actual checks, limitations and next stage.

Direct user authorization for this project: create a NEW PRIVATE GitHub repository
and host the skeleton on Vercel. This overrides the packet's default no-deploy
rule only for these actions. Do not make the repository public or submit the entry.
Keep unrelated parent-workspace projects untouched. Use the new repository.

User clarification 2026-10-23: the existing AWS stack is Quickstart networking,
role and S3 setup; the AWS connection is verified but there is no compute cluster.
User chose local Zetaris installation now and cloud launch later. Install and
verify the official local distribution; do not launch an AWS cluster. Preserve
the earlier packet wording as historical supplied context, not deployment proof.
