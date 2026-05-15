#Requires -RunAsAdministrator
# OBQ Admin Tweaks — run this once as Administrator
# Double-click this file, accept UAC prompt

Write-Host "Applying admin-level optimizations..." -ForegroundColor Green

# Services
$services = @(
    @{Name="WSAIFabricSvc"; Reason="Microsoft AI service competing with Ollama"},
    @{Name="SysMain";       Reason="Superfetch - useless on 128GB RAM"},
    @{Name="WpnService";    Reason="Windows Push Notifications - widgets"},
    @{Name="DiagTrack";     Reason="Microsoft telemetry"},
    @{Name="dmwappushservice"; Reason="WAP telemetry routing"},
    @{Name="WerSvc";        Reason="Windows Error Reporting"}
)

foreach ($svc in $services) {
    try {
        Stop-Service $svc.Name -Force -ErrorAction SilentlyContinue
        Set-Service $svc.Name -StartupType Disabled -ErrorAction Stop
        Write-Host ("DISABLED: " + $svc.Name + " - " + $svc.Reason) -ForegroundColor Yellow
    } catch {
        Write-Host ("FAILED: " + $svc.Name + " - " + $_) -ForegroundColor Red
    }
}

# svchost consolidation - needs HKLM write
try {
    $ram = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1KB
    $ramGB = [math]::Round($ram / 1MB)
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control' `
        -Name 'SvcHostSplitThresholdInKB' -Value ([int]$ram) -Type DWord -Force
    Write-Host ("svchost threshold set to ${ramGB}GB RAM - consolidates after restart") -ForegroundColor Green
} catch {
    Write-Host ("svchost threshold FAILED: $_") -ForegroundColor Red
}

# SysMain prefetch registry
try {
    $prefetchPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters'
    Set-ItemProperty -Path $prefetchPath -Name 'EnableSuperfetch' -Value 0 -Type DWord -Force
    Set-ItemProperty -Path $prefetchPath -Name 'EnablePrefetcher' -Value 0 -Type DWord -Force
    Write-Host "Superfetch prefetch registry disabled" -ForegroundColor Green
} catch {
    Write-Host ("Prefetch registry FAILED: $_") -ForegroundColor Red
}

# Telemetry policy
try {
    New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Force | Out-Null
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' `
        -Name 'AllowTelemetry' -Value 0 -Type DWord -Force
    Write-Host "AllowTelemetry set to 0" -ForegroundColor Green
} catch {
    Write-Host ("Telemetry policy FAILED: $_") -ForegroundColor Red
}

# Delivery Optimization
try {
    New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization' -Force | Out-Null
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization' `
        -Name 'DODownloadMode' -Value 0 -Type DWord -Force
    Write-Host "Delivery Optimization (P2P updates) disabled" -ForegroundColor Green
} catch {
    Write-Host ("Delivery Optimization FAILED: $_") -ForegroundColor Red
}

# Copilot policy
try {
    New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' -Force | Out-Null
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' `
        -Name 'TurnOffWindowsCopilot' -Value 1 -Type DWord -Force
    Write-Host "Windows Copilot disabled via policy" -ForegroundColor Green
} catch {}

# Windows Recall
try {
    New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' -Force | Out-Null
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' `
        -Name 'DisableAIDataAnalysis' -Value 1 -Type DWord -Force
    Write-Host "Windows Recall disabled" -ForegroundColor Green
} catch {}

# Scheduled tasks - telemetry
$tasks = @(
    @{Path="\Microsoft\Windows\Application Experience\"; Name="Microsoft Compatibility Appraiser"},
    @{Path="\Microsoft\Windows\Application Experience\"; Name="ProgramDataUpdater"},
    @{Path="\Microsoft\Windows\Customer Experience Improvement Program\"; Name="Consolidator"},
    @{Path="\Microsoft\Windows\Customer Experience Improvement Program\"; Name="UsbCeip"},
    @{Path="\Microsoft\Windows\Windows Error Reporting\"; Name="QueueReporting"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="Reboot"},
    @{Path="\Microsoft\Windows\UpdateOrchestrator\"; Name="Reboot_AC"}
)
foreach ($task in $tasks) {
    Disable-ScheduledTask -TaskPath $task.Path -TaskName $task.Name -ErrorAction SilentlyContinue | Out-Null
    Write-Host ("Task disabled: " + $task.Name) -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== COMPLETE - RESTART REQUIRED ===" -ForegroundColor Green
Write-Host "After restart: svchost processes will consolidate from ~78 to ~20-30" -ForegroundColor Cyan
Write-Host "WSAIFabricSvc, SysMain, DiagTrack will no longer start" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
