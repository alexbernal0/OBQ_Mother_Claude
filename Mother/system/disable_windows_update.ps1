#Requires -RunAsAdministrator

Write-Host "Disabling Windows Update auto-restart and auto-install..." -ForegroundColor Green

# ── Prevent ALL auto-restarts ─────────────────────────────────────────────────
$auPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
if (-not (Test-Path $auPath)) { New-Item -Path $auPath -Force | Out-Null }
Set-ItemProperty -Path $auPath -Name "NoAutoRebootWithLoggedOnUsers" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $auPath -Name "AlwaysAutoRebootAtScheduledTime" -Value 0 -Type DWord -Force
Set-ItemProperty -Path $auPath -Name "AUPowerManagement" -Value 0 -Type DWord -Force
Write-Host "  Auto-restart: DISABLED" -ForegroundColor Yellow

# ── Stop Windows Update from auto-downloading and installing ──────────────────
Set-ItemProperty -Path $auPath -Name "NoAutoUpdate" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $auPath -Name "AUOptions" -Value 1 -Type DWord -Force
# AUOptions: 1=notify only, 2=auto-download+notify, 3=auto-download+schedule, 4=auto
Write-Host "  Auto-download/install: DISABLED (notify only)" -ForegroundColor Yellow

# ── Windows Update service — set to Manual (not Disabled — keeps security patches available when YOU choose) ──
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Set-Service wuauserv -StartupType Manual -ErrorAction SilentlyContinue
Write-Host "  Windows Update service: MANUAL (won't run in background)" -ForegroundColor Yellow

# ── Update Orchestrator — this is what triggers the overnight restarts ────────
Stop-Service UsoSvc -Force -ErrorAction SilentlyContinue
Set-Service UsoSvc -StartupType Disabled -ErrorAction SilentlyContinue
Write-Host "  Update Orchestrator (UsoSvc): DISABLED" -ForegroundColor Yellow

# ── Windows Update Medic Service — this re-enables wuauserv if you disable it ──
# Requires registry hack since it self-heals
$medicPath = "HKLM:\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc"
if (Test-Path $medicPath) {
    Set-ItemProperty -Path $medicPath -Name "Start" -Value 4 -Type DWord -Force
    Write-Host "  WaaSMedicSvc (update self-healer): DISABLED" -ForegroundColor Yellow
} else {
    Write-Host "  WaaSMedicSvc: not found (OK)" -ForegroundColor Gray
}

# ── Scheduled tasks that trigger overnight updates ────────────────────────────
$tasks = @(
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="Reboot"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="Reboot_AC"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="Schedule Scan"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="UpdateAssistant"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="USO_UxBroker"},
    @{Path="\Microsoft\Windows\WindowsUpdate\"; Name="Scheduled Start"}
)
foreach ($t in $tasks) {
    Disable-ScheduledTask -TaskPath $t.Path -TaskName $t.Name -ErrorAction SilentlyContinue | Out-Null
    Write-Host ("  Task disabled: " + $t.Name) -ForegroundColor Yellow
}

# ── Verify ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== VERIFICATION ===" -ForegroundColor Green
$noAutoUpdate = (Get-ItemProperty $auPath -ErrorAction SilentlyContinue).NoAutoUpdate
$noReboot     = (Get-ItemProperty $auPath -ErrorAction SilentlyContinue).NoAutoRebootWithLoggedOnUsers
$wuSvc        = (Get-Service wuauserv -ErrorAction SilentlyContinue).StartType
$usoSvc       = (Get-Service UsoSvc -ErrorAction SilentlyContinue).StartType
Write-Host ("  NoAutoUpdate:              " + $noAutoUpdate + " (1=disabled)")
Write-Host ("  NoAutoRebootWithLoggedOn:  " + $noReboot + " (1=disabled)")
Write-Host ("  wuauserv startup:          " + $wuSvc + " (Manual=won't auto-run)")
Write-Host ("  UsoSvc startup:            " + $usoSvc + " (Disabled)")
Write-Host ""
Write-Host "DONE. Windows will no longer auto-update or restart." -ForegroundColor Green
Write-Host "To manually check for updates: Settings > Windows Update > Check for updates" -ForegroundColor Cyan
Read-Host "Press Enter to close"
