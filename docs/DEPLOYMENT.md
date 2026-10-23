# Requested Vercel hosting

The direct user request authorizes creating this new private GitHub repository
and hosting the Stage 1 skeleton on Vercel. The packet's default no-deploy clause
continues to apply to unrelated deployments, public repository changes and entry
submission. No secrets, private field data or evidence API are deployed.

Project: `lastcopy`, repository `miracle352/lastcopy`, branch `main`, web workspace
root `web`. Node 24, Next.js 16.4.3. Install from the parent workspace lock with
`npm ci --prefix ..`, build `npm run build`, default `.next` output in `web`.
The source remains private. A Vercel URL does not change repository visibility.

Stage 1 Vercel functionality: explanatory skeleton and `/api/health` showing
`evidence_backend: not_deployed`. `/api/inventory` returns 503 in the hosted
environment. The UI explains that inventory requires the local private API.
No provider credentials or API URL are needed on Vercel for this stage.

Full evidence processing and durable local private files must not be silently
moved to stateless functions. A future deployment plan needs explicit storage,
data access and trust boundaries. No tunnel or public workstation API is created.

Actual deployment result and checked URL are recorded in VERIFICATION.md and
HANDOFF.md. Until those records say READY, this file is configuration guidance.
