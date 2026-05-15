# Mother v5 Code Intel Watcher - Windows Task Scheduler auto-start
#
# Registers the watcher daemon to start at user logon.
# Run as: powershell -ExecutionPolicy Bypass -File code_intel_autostart.ps1
#
# Manage:
#   --install    Register and start (default)
#   --uninstall  Remove the task
#   --status     Show task state

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$TaskName = "MotherCodeIntelWatcher"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WatcherScript = Join-Path $ScriptDir "code_intel_watcher.py"
$PythonW = "pythonw.exe"

# Default to install if no flag given
if (-not $Install -and -not $Uninstall -and -not $Status) {
    $Install = $true
}

if ($Status) {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "Task: $TaskName"
        Write-Host "  State: $($task.State)"
        Write-Host "  Last Run: $($info.LastRunTime)"
        Write-Host "  Last Result: $($info.LastTaskResult)"
        Write-Host "  Next Run: $($info.NextRunTime)"
    } catch {
        Write-Host "Task not registered: $TaskName" -ForegroundColor Yellow
    }
    exit 0
}

if ($Uninstall) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "Removed task: $TaskName" -ForegroundColor Green
    } catch {
        Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
    }
    exit 0
}

if ($Install) {
    if (-not (Test-Path $WatcherScript)) {
        Write-Host "Watcher script not found: $WatcherScript" -ForegroundColor Red
        exit 1
    }

    # Remove existing
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    } catch {}

    # Build action - pythonw runs without console window
    $action = New-ScheduledTaskAction `
        -Execute $PythonW `
        -Argument "`"$WatcherScript`"" `
        -WorkingDirectory $ScriptDir

    # Trigger on user logon
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

    # Settings: restart on failure, no time limit, run only when logged in
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0)

    # Run as current user
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Mother v5 Code Intel - keeps code indexes live across all registered projects" `
        | Out-Null

    Write-Host "Registered task: $TaskName" -ForegroundColor Green
    Write-Host "Will auto-start on next logon."
    Write-Host ""
    Write-Host "Start now? Run:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName $TaskName"
    exit 0
}
