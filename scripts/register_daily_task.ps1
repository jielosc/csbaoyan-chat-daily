param(
    [string]$TaskName = "CSBaoyanDailyReport",
    [string]$Time = "06:30",
    [string]$PythonCommand
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

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Daily -At $runAt
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Task created: $TaskName"
Write-Host "Schedule: daily at $Time"
Write-Host "User: $currentUser"
Write-Host "Script: $pipelineScript"
Write-Host "Note: this task is configured for an interactive logon. If you need it to run while signed out, change it in Task Scheduler and store the password."
