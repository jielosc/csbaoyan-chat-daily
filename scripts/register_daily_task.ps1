param(
    [string]$TaskName = "CSBaoyanDailyReport",
    [string]$Time = "06:30",
    [string]$PythonCommand,
    [string]$Password,
    [switch]$RunWhenSignedOut
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pipelineScript = (Resolve-Path (Join-Path $PSScriptRoot "daily_pipeline.ps1")).Path
$escapedPipelineScript = $pipelineScript.Replace('"', '\"')

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$escapedPipelineScript`""
if ($PythonCommand) {
    $escapedPythonCommand = $PythonCommand.Replace('"', '\"')
    $arguments += " -PythonCommand `"$escapedPythonCommand`""
}

$runAt = [DateTime]::ParseExact($Time, "HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$workingDirectory = Split-Path -Parent $pipelineScript

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $workingDirectory
$trigger = New-ScheduledTaskTrigger -Daily -At $runAt
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

if ($RunWhenSignedOut) {
    $taskPassword = if ($Password) { $Password } else { $env:CSBAOYAN_TASK_PASSWORD }
    if (-not $taskPassword) {
        throw "RunWhenSignedOut requires a password. Pass -Password or set the CSBAOYAN_TASK_PASSWORD environment variable before registering the task."
    }

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -User $currentUser -Password $taskPassword -RunLevel Limited -Force | Out-Null
}
else {
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
}

Write-Host "Task created: $TaskName"
Write-Host "Schedule: daily at $Time"
Write-Host "User: $currentUser"
Write-Host "Script: $pipelineScript"
if ($RunWhenSignedOut) {
    Write-Host "Logon: runs whether you are signed in or not."
}
else {
    Write-Host "Logon: interactive only."
    Write-Host "Note: if you need it to run while signed out, re-register it with -RunWhenSignedOut and a password."
}
