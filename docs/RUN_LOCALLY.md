# Open LastCopy on this PC

The **repo root** means the LastCopy project folder. PowerShell is the terminal
that runs commands in that folder; it is not the repo.

Use **Windows Terminal → PowerShell** (or the PowerShell terminal panel in
Codex). You do not need Administrator mode. Keep two tabs open.

In the first PowerShell tab, paste:

```powershell
Set-Location -LiteralPath 'C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy'
$env:SAMPLE_MODE='true'
$env:LASTCOPY_DATA_DIR='private/local-workspace'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

This is the private local API. Leave the tab running.

In the second PowerShell tab, paste:

```powershell
Set-Location -LiteralPath 'C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy'
npm run build
npm run start
```

This is the production UI. Leave this tab running too. Open
[LastCopy on this PC](http://127.0.0.1:3000/).

If those services are already running, just open the link. An “address already
in use” message means another process already owns that port; do not repeatedly
launch copies. Stop the relevant LastCopy terminal with **Ctrl+C** before
restarting it. Neither command deploys to Vercel or changes GitHub visibility.

Sample mode uses synthetic files with the actual comparator. It makes no
provider calls. Recovery in this mode compares a separate authored readback
fixture and does not upload data. Use the README's connected instructions only
when the configured synthetic test services are available.

The existing Vercel preview does not automatically show local changes. This
redesign is kept local until deployment is explicitly authorized.
