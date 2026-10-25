# Public beta, judge access and cloud AI

## Entry points

- [Try LastCopy](https://lastcopy-five.vercel.app/demo): no account, five real
  offline comparisons, source evidence, a reviewed bundle and a separate
  synthetic readback comparison. No live upload or model call is claimed here.
- [Create an account](https://lastcopy-five.vercel.app/signup): Vercel routes
  private account/file work to the existing HTTPS AWS workspace.
- [Record checks](https://app-18-141-113-136.sslip.io/app).
- [Owner AI setup](https://app-18-141-113-136.sslip.io/integrations).
- [Water Point collection instructions](https://lastcopy-five.vercel.app/collect).

Vercel hosts the public site. The existing $24/month Lightsail server hosts the
UI/API, ODK Central and durable private evidence. No extra server, GPU, domain,
paid email tier or new Zetaris cluster was created. AWS credits are not a promise
of a permanently free service.

## Accounts and email

AWS Cognito Lite in Singapore handles passwords, email verification and reset
codes. The owner confirmed that the real verification email arrived and signup
worked. Separate live controls exercised real Cognito password authentication
and GetUser with two synthetic identities; unverified identities were rejected,
cross-account records were inaccessible, and logout revoked local sessions.
Those controls explicitly suppressed email and cannot prove delivery themselves.
Human password-reset email delivery remains a separate check.

Account identity comes from Cognito's returned immutable `sub`, never a browser
claim or email label. A hashed pseudonymous ID selects a separate SQLite/file
store. New accounts inherit no owner ODK, device, sponsor or recovery credentials.
Passwords/provider tokens are not returned to the browser. LastCopy sessions are
opaque, hashed, persisted, Secure/HttpOnly/SameSite=Strict and expire after eight
hours. Reset through LastCopy revokes its previous account sessions.

Beta bounds: 100 accounts, 100 MiB of registered inputs and 25 saved checks per
account, four active checks across public accounts, plus the existing archive,
XML, request and run limits. Admission uses a cross-process lease. A 5 GiB free
space reserve blocks additional input storage. Existing reports remain readable
when a quota is reached. Authentication/email throttles persist across restarts.
This does not replace independent penetration testing or full abuse monitoring.

**Resend is not configured.** Sending to outside users requires an owned,
verified sending domain; a free `.vercel.app` address does not supply that DNS
control. Cognito's built-in sender avoids a domain purchase for this beta. Its
default quota is 50 emails per day across the AWS account. LastCopy additionally
bounds requests. Neither email delivery nor unlimited free capacity is promised.

References: [Cognito pricing](https://aws.amazon.com/cognito/pricing/),
[default email](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-email.html),
[email quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html),
[Resend domains](https://resend.com/docs/dashboard/domains/introduction).

## Direct NVIDIA versus Nightshift

The owner enters a key on the HTTPS setup page. It stays in a private mode-0600
server file; it is never copied from Nightshift or exported in an environment
archive. The catalogue can reload from the saved key without re-entry. Only
chat candidates are offered; embeddings, parsing, reward and safety-only models
are excluded. Inventory presence is not proof of inference access.

Observed routing control: catalogue-listed 51B and Super requests returned 404;
a documented `stg/nvidia/nemotron-3.5-bolt-e4b` request returned HTTP 200 and
reported actual serving identity `nvidia/nemotron-3.5-bolt-e4b`, with 48
provider-reported tokens in that small connectivity control. The canonical ID
must still exist in the live inventory. The documented route is kept separate
from the returned serving identity; neither is guessed or relabelled.

The fixed two-request test supplies actual synthetic verifier evidence to an
investigator/reviewer and saves sanitized receipts. It cannot alter verifier
results. Failures retain an error receipt with HTTP category and model scope;
no response body, key, sample fallback or manufactured success is logged.
One setup/test runs at a time; ten inference tests/day and thirty catalogue
requests/hour are persisted limits. Thinking is disabled for the supported
Nemotron bounded JSON action path; every returned action is validated again.

The final real hosted test returned HTTP 200 and changed `fetch_raw_xml` to
`export_guidance`, with provider-reported usage of 126 and 528 tokens. JSON and
JSONL receipts identify the actual serving model and evidence hashes. Completed
tests restore automatically as **Replay**, with their captured receipt/time.
Debugging used the current ten-test daily allowance; the UI shows its actual
reset time and disables another test until then. Copy checks remain available.

**This is direct NVIDIA cloud, not Nightshift.** It does not satisfy the
Nightshift/NVIDIA award path. The normal connected investigator still uses the
existing actual Zetaris query and World Model worker; its cloud query deployment
is not configured. The direct-provider smoke is not represented as that entire
acceptance path. Nightshift's verified Windows runtime remains separate; a
supported generic Ubuntu deployment and redistribution rights were not verified.
No proprietary Nightshift runtime was copied to AWS.

Reference: [official Bolt inference/routing API](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-bolt-e4b-infer).

## What remains dependent on a device

The website, Central, saved comparisons and direct cloud AI do not require this
PC to host them. The current Android emulator and native export relay do. When
the PC is off, that device cannot produce new evidence. Collect on a physical
Android device can submit to Central independently, but automatic independent
native backup on a physical phone has not been verified. Browser submission or
server presence alone does not prove preservation of an absent device original.

New public accounts can check private imported exports and scoped server
snapshots. They do not automatically receive an ODK project, device pairing or
Central credentials. Self-service per-account connected collection onboarding,
physical-device backup, and a phone/browser collection workflow remain work.
The existing owner's Water Point project is separate from the synthetic recovery
project. Automatic recovery remains restricted to reviewed synthetic test plans.

## Operations and release limits

Before sensitive field use: owned domain/email capacity, off-host encrypted
backups and restore drills, monitoring/alerts, account/data deletion, retention
controls, support/contact policy, credential rotation, account recovery delivery
verification, and independent security review are still needed. The privacy page
states retention and beta limitations; it is not a completed legal/operations
programme. The previous image advisory and mobile performance limits are not
declared cleared by this update. No fresh field Core Web Vitals are claimed.

Verification receipts: [public-beta evidence](verification/public-beta/).
The source-only deployment archive excludes private files and credentials. Build
failures from UTF-8/type errors were retained; later successful builds supersede
them. Runtime source encoding is now checked before packaging. Existing sealed
stage/cloud receipts are not rewritten. The repository remains private and no
hackathon submission or visibility change was performed.

## Windows terminal and folder

PowerShell is the terminal; the repository root is a folder. Open PowerShell and
run:

```powershell
Set-Location "C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy"
```

For the existing emulator: `./scripts/open_collect.ps1` and
`./scripts/start_cloud_link.ps1`. Hosted users use the HTTPS links above and do
not launch this PC's local API. Local API/CLI setup remains in README and
[RUN_LOCALLY.md](RUN_LOCALLY.md).
