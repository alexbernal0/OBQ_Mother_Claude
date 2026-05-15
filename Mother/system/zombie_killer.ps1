# zombie_killer.ps1 - Mother v5 Zombie Killer
param([switch]$Install, [switch]$Uninstall, [switch]$Status)

$TaskName = "MotherZombieKiller"
$LogFile  = Join-Path $env:USERPROFILE ".mother\zombie_killer.log"
$ScriptPath = $MyInvocation.MyCommand.Path

if ($Install) {
    New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -EA SilentlyContinue } catch {}
    $arg = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $ScriptPath + '"'
    $action   = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
    $trigger  = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
    $prin     = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $prin -Description "Mother v5 zombie killer every 5 min" | Out-Null
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Installed and started: $TaskName"
    Write-Host "Log: $LogFile"
    exit 0
}

if ($Uninstall) {
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -EA Stop; Write-Host "Removed: $TaskName" }
    catch { Write-Host "Not found: $TaskName" }
    exit 0
}

if ($Status) {
    try {
        $t = Get-ScheduledTask -TaskName $TaskName -EA Stop
        $i = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "State: $($t.State) | Last: $($i.LastRunTime) | Result: $($i.LastTaskResult) | Next: $($i.NextRunTime)"
        if (Test-Path $LogFile) { Get-Content $LogFile -Tail 5 }
    } catch { Write-Host "Not registered. Run with -Install." }
    exit 0
}

# Default: run cleanup
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null
$candidates = @(Get-Process python,pythonw -EA SilentlyContinue | Where-Object { $_.WorkingSet64 -lt 15MB })
if ($candidates.Count -eq 0) { exit 0 }

$cpu1 = @{}
foreach ($p in $candidates) { $cpu1[$p.Id] = $p.CPU }
Start-Sleep -Seconds 2

$killed = 0
foreach ($p in $candidates) {
    try {
        $cur = Get-Process -Id $p.Id -EA Stop
        if (($cur.CPU - $cpu1[$p.Id]) -lt 0.1) {
            Stop-Process -Id $p.Id -Force -EA Stop
            $mb = [math]::Round($p.WorkingSet64/1MB)
            $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') KILLED PID=$($p.Id) mem=${mb}MB"
            Add-Content $LogFile $line -EA SilentlyContinue
            $killed++
        }
    } catch {}
}

$cli = Get-Process opencode-cli -EA SilentlyContinue
if ($cli -and [math]::Round($cli.WorkingSet64/1MB) -gt 600) {
    $warn = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') WARNING opencode-cli=$([math]::Round($cli.WorkingSet64/1MB))MB"
    Add-Content $LogFile $warn -EA SilentlyContinue
}

if ($killed -gt 0) {
    Add-Content $LogFile "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Done: killed $killed zombies" -EA SilentlyContinue
}