param([switch]$ShowEmulator)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
if (!(Test-Path -LiteralPath 'private/cloud/device-link.env')) {throw 'Complete the private cloud pairing first.'}
$taskAdb=Join-Path $taskRoot 'private/android/sdk/platform-tools/adb.exe'
$taskEmulator=Join-Path $taskRoot 'private/android/sdk/emulator/emulator.exe'
$taskLog=Join-Path $taskRoot 'private/runtime-logs'
New-Item -ItemType Directory -Path $taskLog -Force | Out-Null
$taskStamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$taskDevice=& $taskAdb -s emulator-5558 get-state 2>$null
if($LASTEXITCODE -ne 0 -or $taskDevice -ne 'device'){
    $env:ANDROID_HOME=Join-Path $taskRoot 'private/android/sdk'
    $env:ANDROID_AVD_HOME=Join-Path $taskRoot 'private/android/avd'
    $taskArgs=@('-avd','LastCopyCollect','-port','5558','-no-audio','-no-boot-anim','-memory','1024','-cores','2')
    if(!$ShowEmulator){$taskArgs+='-no-window'}
    if($ShowEmulator){Start-Process -FilePath $taskEmulator -ArgumentList $taskArgs -WorkingDirectory $taskRoot | Out-Null}
    else{Start-Process -FilePath $taskEmulator -ArgumentList $taskArgs -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-cloud-emulator.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-cloud-emulator-error.log") | Out-Null}
}
$taskDeadline=(Get-Date).AddMinutes(4)
while((& $taskAdb -s emulator-5558 shell getprop sys.boot_completed 2>$null) -ne '1'){
    if((Get-Date) -gt $taskDeadline){throw 'Emulator did not become ready; no connection success claimed.'}
    Start-Sleep -Milliseconds 500
}
if((& $taskAdb -s emulator-5558 shell getprop ro.kernel.qemu).Trim() -ne '1'){throw 'Only the paired AOSP emulator is supported.'}
if((& $taskAdb -s emulator-5558 shell id -u).Trim() -ne '0'){
    & $taskAdb -s emulator-5558 root
    & $taskAdb -s emulator-5558 wait-for-device
}
$taskExisting=Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -like '*-m scripts.cloud_device_link*' -and $_.CommandLine.Contains($taskRoot)}
if(!$taskExisting){
    $taskProcess=Start-Process -FilePath (Join-Path $taskRoot '.venv/Scripts/python.exe') -ArgumentList '-u','-m','scripts.cloud_device_link' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog "$taskStamp-cloud-link.log") -RedirectStandardError (Join-Path $taskLog "$taskStamp-cloud-link-error.log") -PassThru
    $taskProcess.Id | Set-Content -LiteralPath 'private/cloud/device-link.pid'
}
Write-Output 'Desktop link started or already running. Its actual state appears in private/cloud/device-link-status.json and the saved cloud workspace.'
Write-Output 'Keep this PC/emulator awake. Cloud pause prevents new capture/delivery. No recovery is automatic.'
