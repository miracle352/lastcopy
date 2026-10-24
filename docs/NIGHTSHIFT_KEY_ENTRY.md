# Private key entry when Nightshift Setup does not open

Observed 2026-10-24 on the installed Nightshift 1.2.3: NVIDIA Add Key in the
first-run wizard left the screen unchanged; Skip setup then left the content
area blank. The desktop window and daemon were responding. The exact frontend
exception is not established; this is not evidence of an invalid NVIDIA key.

The actual native bridge references `/admin/keys`. Credential-free validation
returned `provider required`. A clearly non-secret unsupported probe provider
confirmed the POST shape `{provider, value}`; it was immediately cleared with an
empty value, and configured-provider names returned to their original empty set.
No existing provider was changed by those probes. No direct NVIDIA inference
endpoint is used by LastCopy's helper.

`scripts/configure_nvidia_nightshift.mjs` opens a human-operated console prompt:

- Input is hidden and must come from a real interactive console, never CLI args.
- The runtime version/model-directory identity is checked before transmitting.
- A pre-existing NVIDIA entry is preserved by default. Explicit --replace re-entry
  replaces only that entry after the human submits a new value.
- Only the observed local Nightshift key API receives the value. The key is not
  printed, returned in receipts, or written into LastCopy configuration/files.
- The private receipt is `private/smoke/nightshift-nvidia-key-entry.json`; it
  records storage status, not the key. Stored does not mean authenticated or
  inference-verified. Actual model inventory and inference must follow.
- Closing the entry console or Ctrl+C before submission cancels entry.

Run from an ordinary interactive PowerShell in the repository root:

```powershell
$env:LOCALAPPDATA=Join-Path $env:USERPROFILE 'AppData\Local'
node scripts/configure_nvidia_nightshift.mjs
```

The key must never be pasted into Codex/chat, passed on a command line, or added
to a screenshot. Code-owned tests use non-secret dummy input and fake transports:

```powershell
node --test tests/nightshift-key-entry.test.mjs
```

Six tests passed: reject malformed or duplicated input before any request; preserve an
existing NVIDIA entry by default; support explicit NVIDIA-only re-entry; reject a different runtime; and send the observed request
while omitting the key from returned receipts. The Windows interactive launch
was issued successfully. Storage/authentication was subsequently verified through real Nightshift cloud
responses; retain the actual receipts rather than inferring success from storage.


Historical initial checks: the private entry reported stored and Nightshift advertised NVIDIA
cloud routes. Actual chat attempts returned HTTP 502 `provider_error` / `fetch failed`;
authentication is not yet proved. The user reported a possible double paste. A
fresh re-entry prompt now rejects a second `nvapi-` prefix and keeps the closing
prompt hidden as well. No existing key was retrieved to inspect or compare.


Resolved 2026-10-24: the guarded single-copy re-entry was stored, then a real
Nightshift request returned LASTCOPY_OK from its NVIDIA Nemotron route. Strict
action JSON also passed with reasoning_effort=none. Both full connected cases
passed; see verification/stage3-live-export.json and stage3-live-conflict.json.
The original entry was not retrieved, so duplication is possible but unproven.
The temporary error-code-only diagnostic preload was removed and its temporary
files cleaned up. No vendor runtime files or TLS safeguards were modified.
