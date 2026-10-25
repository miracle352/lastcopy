param([switch]$ShowEmulator)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
$taskLog = Join-Path $taskRoot 'private/runtime-logs'
New-Item -ItemType Directory -Path $taskLog -Force | Out-Null
$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'

# Existing pinned local stack only. No build, image pull, volume removal or AWS.
$taskProject = & docker inspect lastcopy-odk-postgres14-1 --format '{{index .Config.Labels "com.docker.compose.project"}}'
if ($LASTEXITCODE -ne 0 -or $taskProject.Trim() -ne 'lastcopy-odk') { throw 'Existing LastCopy Central database is unavailable. Start Docker Desktop; no new database was created.' }
$taskCentral = Join-Path $taskRoot 'private/central'
$taskCompose = @('compose','-p','lastcopy-odk','-f',(Join-Path $taskCentral 'docker-compose.yml'),'-f',(Join-Path $taskCentral 'lastcopy.local.yml'))
$taskNative = Join-Path $taskCentral 'lastcopy.native.yml'
if (Test-Path -LiteralPath $taskNative) { $taskCompose += @('-f',$taskNative) }
& docker @taskCompose up -d --no-deps --no-build --pull never postgres14 mail pyxform enketo_redis_cache enketo_redis_main enketo service nginx
if ($LASTEXITCODE -ne 0) { throw 'Existing Central stack did not start' }

$taskAdb = Join-Path $taskRoot 'private/android/sdk/platform-tools/adb.exe'
$taskEmulator = Join-Path $taskRoot 'private/android/sdk/emulator/emulator.exe'
if (!(Test-Path -LiteralPath $taskAdb) -or !(Test-Path -LiteralPath $taskEmulator)) { throw 'The documented local Android tools are missing' }
$taskDevice = & $taskAdb -s emulator-5558 get-state 2>$null
if ($LASTEXITCODE -ne 0 -or $taskDevice -ne 'device') {
    $env:ANDROID_HOME = Join-Path $taskRoot 'private/android/sdk'
    $env:ANDROID_AVD_HOME = Join-Path $taskRoot 'private/android/avd'
    $taskArgs = @('-avd','LastCopyCollect','-port','5558','-no-audio','-no-boot-anim','-memory','1024','-cores','2')
    if (!$ShowEmulator) { $taskArgs += '-no-window' }
    # Visible only when the caller explicitly requests the interactive window.
    if ($ShowEmulator) {
        Start-Process -FilePath $taskEmulator -ArgumentList $taskArgs -WorkingDirectory $taskRoot -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-emulator.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-emulator-error.log") | Out-Null
    } else {
        Start-Process -FilePath $taskEmulator -ArgumentList $taskArgs -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-emulator.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-emulator-error.log") | Out-Null
    }
}
$taskDeadline = (Get-Date).AddSeconds(240)
do {
    $taskBoot = & $taskAdb -s emulator-5558 shell getprop sys.boot_completed 2>$null
    if ($taskBoot -eq '1') { break }
    if ((Get-Date) -gt $taskDeadline) { throw 'Emulator did not boot within four minutes; no connection success claimed' }
    Start-Sleep -Milliseconds 500
} while ($true)
if ((& $taskAdb -s emulator-5558 shell getprop ro.kernel.qemu).Trim() -ne '1') { throw 'Expected the dedicated AOSP emulator; no physical device will be rooted' }
if ((& $taskAdb -s emulator-5558 shell id -u).Trim() -ne '0') {
    & $taskAdb -s emulator-5558 root
    & $taskAdb -s emulator-5558 wait-for-device
}
& $taskAdb -s emulator-5558 reverse tcp:8384 tcp:8384
if ($LASTEXITCODE -ne 0) { throw 'Paired emulator loopback forwarding failed' }

function Test-LastCopyApi {
    try { return (Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3).service -eq 'lastcopy-api' } catch { return $false }
}
if (!(Test-LastCopyApi)) {
    Start-Process -FilePath (Join-Path $taskRoot '.venv/Scripts/python.exe') -ArgumentList '-m','uvicorn','lastcopy.api:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-api.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-api-error.log") | Out-Null
}
try { $taskWeb = (Invoke-WebRequest -Uri 'http://127.0.0.1:3000/api/health' -TimeoutSec 3).StatusCode -eq 200 } catch { $taskWeb = $false }
if (!$taskWeb) {
    if (!(Test-Path -LiteralPath (Join-Path $taskRoot 'web/.next/BUILD_ID'))) { throw 'Production UI is not built; run npm run build first' }
    Start-Process -FilePath (Get-Command node).Source -ArgumentList 'node_modules/next/dist/bin/next','start','web','--hostname','127.0.0.1','--port','3000' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-ui.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-ui-error.log") | Out-Null
}
$taskDeadline = (Get-Date).AddSeconds(45)
while (!(Test-LastCopyApi)) {
    if ((Get-Date) -gt $taskDeadline) { throw 'API did not become ready. Inspect private/runtime-logs; no success claimed.' }
    Start-Sleep -Milliseconds 500
}
$taskWatch = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ui/watch' -TimeoutSec 10
Write-Output "LastCopy: http://127.0.0.1:3000/app"
Write-Output "Automatic checks: $($taskWatch.state). Device link: $($taskWatch.device_transfer.state)."
Write-Output 'This is a local paired-emulator workflow. Keep this PC and Docker running; no public deployment occurred.'
if ($ShowEmulator -and $taskDevice -eq 'device') { Write-Output 'The emulator was already running; its window mode was preserved to avoid interrupting an open form.' }
