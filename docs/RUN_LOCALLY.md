# Open LastCopy on this PC

The **repo root** means the LastCopy project folder. PowerShell is the terminal
that runs commands in that folder; it is not the repo.

Use **Windows Terminal → PowerShell** (or the PowerShell terminal panel in
Codex). You do not need Administrator mode. Keep two tabs open.

In the first PowerShell tab, paste:

```powershell
Set-Location -LiteralPath 'C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy'
$env:SAMPLE_MODE='false'
$env:LASTCOPY_DATA_DIR='private/application'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

This is the private local API using the existing server-side connection settings.
Leave the tab running. The configured local Central and Zetaris Docker containers
and Nightshift must be running for connected investigation. This does not provision
AWS or create another paid cloud service.

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

Open **Check my records**. The connection card reads the actual local Central
project/form. Add a supported device export, review the expected-device list,
confirm the scope and choose **Check my records** to capture and compare. This
PC's configured read scope is now **Water Point Condition Check**, project 3.
It is empty and awaiting actual collection. The demonstrated synthetic pilot is
separate in project 4, and existing recovery writes remain restricted to project 2.
No field campaign has been checked without its own exports.

After uploading device exports and reviewing the roster, choose **Use these
exports for automatic checks**. The automatic checker accepts those registered
inputs and watches the configured private inbox for later sealed exports. Its
actual state, pause/start controls, latest report and remaining attempt budget
are visible in the app. It runs only while the API is running. See
[CONTINUOUS_CHECKS.md](CONTINUOUS_CHECKS.md) for the device-export producer,
Collect configuration, supported limits and the distinction from phone streaming.

The landing examples compare synthetic files automatically with the actual
comparator and no provider calls. **Try example records** opens the explicit
offline sample workflow. Its recovery compares an authored readback fixture;
it does not upload. For an entirely offline API instead, set SAMPLE_MODE to
'true' and LASTCOPY_DATA_DIR to 'private/offline-examples' before starting the
first terminal. The UI will honestly show its Sample-only configuration.

The existing Vercel preview does not automatically show local changes or reach
this PC's loopback API. This update stays local until deployment is authorized.
