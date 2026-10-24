# Requested Vercel hosting

## Stage 7 deployment preparation — no new deployment

The working product is the local production UI plus private persistent API.
Use the README's Windows commands or the Sample-only Docker Compose setup.
Do not publish port 8000, tunnel the workstation, copy `.env` into an image or
configure browser-visible secrets. Docker binds only host loopback; its evidence
volume is private and must be retained across restarts.

The existing Vercel preview remains a frontend-only preview. Its allowlisted
proxy deliberately returns unavailable in the Vercel environment; it cannot
execute the local verifier/investigator/recovery. Stage 7 does not deploy or
push a branch that might trigger the connected automatic Vercel deployment.

For an owner-approved future frontend update, review its install/build settings
below, immutable commit, asset/licenses and noindex policy first. Do not remove
noindex merely to inflate a private-preview SEO score. A public canonical origin
can be set only after the actual chosen public hostname is known.

Hosting the full product needs a separate authenticated service with durable
private object storage/SQLite replacement or reviewed single-instance storage,
job ownership, retention/backups, provider network access, TLS and per-user
authorization. Test recovery against an explicitly configured synthetic project
before granting any further target scope. Do not move durable attempt state into
stateless functions or imply that frontend deployment proves integration health.

The original hosting receipt below is historical; no new hosted acceptance is
claimed by this stage.

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

Actual deployment: **READY**, https://lastcopy-five.vercel.app/ . The linked
private repository's Git push built the tested application commit
`dfbc15b2ac21dae389306c706a509ba5750179df`. Hosted health returned 200; hosted
inventory returned the intentional 503 and the UI explained the unavailable
private backend. Full receipt is in VERIFICATION.md and HANDOFF.md.
