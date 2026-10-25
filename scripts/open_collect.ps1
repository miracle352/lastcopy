$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
& (Join-Path $PSScriptRoot 'start_cloud_link.ps1')
$taskAdb=Join-Path $taskRoot 'private/android/sdk/platform-tools/adb.exe'
if((& $taskAdb -s emulator-5558 shell getprop ro.kernel.qemu).Trim() -ne '1'){throw 'Only the explicitly paired emulator may be shown.'}
$taskScrcpy=Join-Path $taskRoot 'private/android/scrcpy/scrcpy-win64-v5.0.1/scrcpy.exe'
if(!(Test-Path -LiteralPath $taskScrcpy)){throw 'Run .venv/Scripts/python.exe -m scripts.setup_collect_window first.'}
$taskExisting=Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -eq 'LastCopy - ODK Collect'}
if(!$taskExisting){
    $env:ADB=$taskAdb
    & $taskAdb -s emulator-5558 shell monkey -p org.odk.collect.android -c android.intent.category.LAUNCHER 1 | Out-Null
    # This visible window is the interactive form-entry control the user needs.
    Start-Process -FilePath $taskScrcpy -ArgumentList '--serial=emulator-5558','--no-audio','--hwdec=disabled','--render-driver=software','--no-clipboard-autosync','--max-size=1024','--max-fps=30','--window-title="LastCopy - ODK Collect"' -WorkingDirectory $taskRoot -RedirectStandardOutput (Join-Path $taskRoot 'private/cloud/collect-window.log') -RedirectStandardError (Join-Path $taskRoot 'private/cloud/collect-window-error.log') | Out-Null
}
Write-Output 'Collect window: Water Point Condition Check. Fill a new form and finish it; Wi-Fi auto-send keeps the original copy and the desktop link checks cloud readback.'
