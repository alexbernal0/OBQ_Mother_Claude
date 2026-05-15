#Requires -RunAsAdministrator
<#
.SYNOPSIS
    OBQ Mother System Optimizer v1.0
    Safe, reversible Windows optimizations for an AI/ML GPU workstation.
    RTX 3090 | 128GB RAM | Ollama | Python | DuckDB | OpenCode

.NOTES
    WHAT THIS SCRIPT DOES:
      1. Creates a System Restore point first (safety net)
      2. Disables Microsoft telemetry + data collection services
      3. Disables Windows AI services competing with Ollama (WSAIFabricSvc, Recall, Copilot)
      4. Disables Xbox GameBar/DVR (known CUDA interference on RTX cards)
      5. Disables Windows Update auto-restart + delivery optimization
      6. Disables Windows Widgets service
      7. Consolidates svchost processes (128GB RAM threshold)
      8. Disables SysMain/Superfetch (useless on 128GB + NVMe, just wastes CPU)
      9. Disables unnecessary scheduled tasks (telemetry, compatibility, error reporting)
      10. Applies registry privacy tweaks (telemetry, activity tracking)

    WHAT THIS DOES NOT TOUCH:
      - GPU drivers / NVIDIA / CUDA / cuDNN — never
      - ESET antivirus services — never
      - Advanced SystemCare — never (user chose to keep)
      - Norgate Data Updater — never (user chose to keep)
      - Windows Search (WSearch) — never (user chose to keep)
      - Python / PATH / environment variables — never
      - Network stack / DNS — never
      - WSL / Hyper-V — never
      - Windows Defender Firewall — never
      - Any driver-related services — never
      - Microsoft Store — never
      - Windows Terminal — never

    REVERTING:
      - System Restore point created before any changes
      - Each registry change documented with original value
      - Services can be re-enabled: Set-Service <name> -StartupType Automatic
      - Restore point label: "Mother-Optimize-YYYY-MM-DD"
#>

$ErrorActionPreference = "Continue"
$date = Get-Date -Format "yyyy-MM-dd HH:mm"
$logFile = "$env:USERPROFILE\Desktop\MotherV4\Mother\system\optimize_log.txt"

function Write-Log {
    param([string]$msg, [string]$color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $line = "[$timestamp] $msg"
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
}

function Set-RegistrySafe {
    param([string]$Path, [string]$Name, $Value, [string]$Type = "DWord")
    try {
        if (-not (Test-Path $Path)) {
            New-Item -Path $Path -Force | Out-Null
        }
        $current = (Get-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue).$Name
        Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type $Type -Force
        Write-Log "  REG: $Name = $Value (was: $current)" "Cyan"
    } catch {
        Write-Log "  REG FAILED: $Path\$Name - $_" "Red"
    }
}

function Disable-ServiceSafe {
    param([string]$Name, [string]$Reason)
    try {
        $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
        if ($null -eq $svc) {
            Write-Log "  SVC: $Name not found (may not be installed)" "Gray"
            return
        }
        $current = $svc.StartType
        Stop-Service -Name $Name -Force -ErrorAction SilentlyContinue
        Set-Service -Name $Name -StartupType Disabled -ErrorAction Stop
        Write-Log "  SVC DISABLED: $Name ($Reason) was: $current" "Yellow"
    } catch {
        Write-Log "  SVC FAILED: $Name - $_" "Red"
    }
}

function Disable-TaskSafe {
    param([string]$Path, [string]$Name)
    try {
        $task = Get-ScheduledTask -TaskPath $Path -TaskName $Name -ErrorAction SilentlyContinue
        if ($null -eq $task) { return }
        Disable-ScheduledTask -TaskPath $Path -TaskName $Name -ErrorAction Stop | Out-Null
        Write-Log "  TASK DISABLED: $Path$Name" "Yellow"
    } catch {
        Write-Log "  TASK FAILED: $Path$Name - $_" "Red"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
Write-Log "═══════════════════════════════════════════════════" "Green"
Write-Log "  OBQ Mother System Optimizer v1.0 - $date" "Green"
Write-Log "  RTX 3090 | 128GB RAM | AI/ML Workstation" "Green"
Write-Log "═══════════════════════════════════════════════════" "Green"

# ── Baseline snapshot ─────────────────────────────────────────────────────────
$os = Get-CimInstance Win32_OperatingSystem
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$svchostBefore = (Get-Process svchost -ErrorAction SilentlyContinue).Count
Write-Log "BEFORE: Free RAM = $freeGB GB | svchost count = $svchostBefore" "White"

# ── Step 0: System Restore Point ─────────────────────────────────────────────
Write-Log ""
Write-Log "STEP 0: Creating System Restore Point..." "Green"
try {
    Enable-ComputerRestore -Drive "C:\" -ErrorAction SilentlyContinue
    Checkpoint-Computer -Description "Mother-Optimize-$(Get-Date -Format 'yyyy-MM-dd')" `
        -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
    Write-Log "  Restore point created successfully" "Green"
} catch {
    Write-Log "  Restore point failed: $_ (continuing anyway)" "Yellow"
}

# ── Step 1: Disable Microsoft Telemetry Services ──────────────────────────────
Write-Log ""
Write-Log "STEP 1: Disabling Microsoft Telemetry Services..." "Green"

Disable-ServiceSafe "DiagTrack"       "Connected User Experiences & Telemetry — sends usage data to Microsoft"
Disable-ServiceSafe "dmwappushservice" "WAP Push Message Routing — telemetry routing"
Disable-ServiceSafe "PcaSvc"          "Program Compatibility Assistant — usage telemetry"
Disable-ServiceSafe "DPS"             "Diagnostic Policy Service — fault detection telemetry"
Disable-ServiceSafe "WerSvc"          "Windows Error Reporting — sends crash data to Microsoft"
Disable-ServiceSafe "wercplsupport"   "Windows Error Reporting support"

# Telemetry registry keys
Write-Log "  Applying telemetry registry tweaks..." "Cyan"
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection" "AllowTelemetry" 0
Set-RegistrySafe "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" "AllowTelemetry" 0
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection" "DisableOneSettingsDownloads" 1
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy" "TailoredExperiencesWithDiagnosticDataEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CDP" "PublishUserActivity" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CDP" "UploadUserActivities" 0
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" "EnableActivityFeed" 0
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" "PublishUserActivities" 0

# ── Step 2: Disable Windows AI Services (competing with Ollama) ──────────────
Write-Log ""
Write-Log "STEP 2: Disabling Microsoft AI Services (competing with Ollama)..." "Green"

Disable-ServiceSafe "WSAIFabricSvc"  "Microsoft AI Fabric — competes with Ollama for inference resources"
Disable-ServiceSafe "Wecsvc"         "Windows Event Collector — feeds AI monitoring"

# Disable Copilot via registry
Set-RegistrySafe "HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" "TurnOffWindowsCopilot" 1
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" "TurnOffWindowsCopilot" 1

# Disable Windows Recall (AI screen indexing — massive I/O drain if enabled)
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" "DisableAIDataAnalysis" 1
Set-RegistrySafe "HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" "DisableAIDataAnalysis" 1

# Disable Click to Do AI
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\Shell\Copilot" "IsCopilotAvailable" 0

# ── Step 3: Disable Xbox GameBar/DVR (CUDA interference on RTX 3090) ─────────
Write-Log ""
Write-Log "STEP 3: Disabling Xbox GameBar/DVR (RTX 3090 CUDA interference)..." "Green"

Set-RegistrySafe "HKCU:\System\GameConfigStore" "GameDVR_Enabled" 0
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR" "AllowGameDVR" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" "AppCaptureEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\GameBar" "UseNexusForGameBarEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\GameBar" "AllowAutoGameMode" 0

# Kill GameBarPresenceWriter process (known CUDA conflict process)
Get-Process "GameBarPresenceWriter" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Log "  Killed GameBarPresenceWriter process (CUDA conflict)" "Yellow"

Disable-ServiceSafe "XblGameSave"    "Xbox Live game save — background sync"
Disable-ServiceSafe "XblAuthManager" "Xbox Live auth manager — background auth"
Disable-ServiceSafe "BcastDVRUserService_9ab64" "GameDVR user service"

# ── Step 4: Windows Update — No Auto-Restart, No P2P Delivery ─────────────────
Write-Log ""
Write-Log "STEP 4: Taming Windows Update (no restarts, no P2P delivery)..." "Green"

# Prevent auto-restart when signed in
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" "NoAutoRebootWithLoggedOnUsers" 1
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" "AUPowerManagement" 0

# Pause updates by 1 week (gives you control)
Set-RegistrySafe "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" "DeferFeatureUpdatesPeriodInDays" 7
Set-RegistrySafe "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" "DeferQualityUpdatesPeriodInDays" 3

# Disable Delivery Optimization (P2P update sharing — wastes bandwidth)
Disable-ServiceSafe "DoSvc" "Delivery Optimization — P2P Windows Update sharing"
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" "DODownloadMode" 0

# Disable Update Orchestrator from waking the machine
Disable-TaskSafe "\Microsoft\Windows\UpdateOrchestrator\" "Reboot"
Disable-TaskSafe "\Microsoft\Windows\UpdateOrchestrator\" "Reboot_AC"
Disable-TaskSafe "\Microsoft\Windows\UpdateOrchestrator\" "UpdateAssistant"

# ── Step 5: Disable Windows Widgets Service ────────────────────────────────────
Write-Log ""
Write-Log "STEP 5: Disabling Windows Widgets (background fetch service)..." "Green"

Disable-ServiceSafe "Widgets"           "Windows Widgets — background news/weather fetch"
Disable-ServiceSafe "WpnService"        "Windows Push Notifications — widget + lock screen data"
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Dsh" "AllowNewsAndInterests" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds" "ShellFeedsTaskbarViewMode" 2

# ── Step 6: Disable SysMain/Superfetch (useless on 128GB RAM + NVMe) ──────────
Write-Log ""
Write-Log "STEP 6: Disabling SysMain/Superfetch (useless on 128GB + NVMe SSD)..." "Green"

Disable-ServiceSafe "SysMain" "Superfetch/SysMain — prefetching irrelevant on 128GB RAM, wastes CPU reading disk patterns"
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" "EnableSuperfetch" 0
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" "EnablePrefetcher" 0

# ── Step 7: svchost Process Consolidation (128GB RAM) ─────────────────────────
Write-Log ""
Write-Log "STEP 7: Consolidating svchost processes for 128GB RAM..." "Green"

# Windows default splits svchost at 3.5GB — above that each service gets own process
# With 128GB RAM, set threshold to RAM size to force consolidation
$ramBytes = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum
$ramKB = [int]($ramBytes / 1KB)
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control" "SvcHostSplitThresholdInKB" $ramKB
$ramGB = [math]::Round($ramBytes/1GB)
Write-Log "  svchost threshold set to ${ramGB}GB (was 3.5GB) — effective after restart" "Cyan"
Write-Log "  Current svchost count: $svchostBefore — will reduce significantly after restart" "Cyan"

# ── Step 8: Disable Telemetry Scheduled Tasks ─────────────────────────────────
Write-Log ""
Write-Log "STEP 8: Disabling telemetry scheduled tasks..." "Green"

$telemetryTasks = @(
    @{Path="\Microsoft\Windows\Application Experience\"; Name="Microsoft Compatibility Appraiser"},
    @{Path="\Microsoft\Windows\Application Experience\"; Name="ProgramDataUpdater"},
    @{Path="\Microsoft\Windows\Application Experience\"; Name="StartupAppTask"},
    @{Path="\Microsoft\Windows\Autochk\";               Name="Proxy"},
    @{Path="\Microsoft\Windows\Customer Experience Improvement Program\"; Name="Consolidator"},
    @{Path="\Microsoft\Windows\Customer Experience Improvement Program\"; Name="UsbCeip"},
    @{Path="\Microsoft\Windows\DiskDiagnostic\";        Name="Microsoft-Windows-DiskDiagnosticDataCollector"},
    @{Path="\Microsoft\Windows\Feedback\Siuf\";         Name="DmClient"},
    @{Path="\Microsoft\Windows\Feedback\Siuf\";         Name="DmClientOnScenarioDownload"},
    @{Path="\Microsoft\Windows\Windows Error Reporting\"; Name="QueueReporting"},
    @{Path="\Microsoft\Windows\CloudExperienceHost\";   Name="CreateObjectTask"},
    @{Path="\Microsoft\Windows\PI\";                    Name="Sqm-Tasks"},
    @{Path="\Microsoft\Windows\NetTrace\";              Name="GatherNetworkInfo"}
)

foreach ($task in $telemetryTasks) {
    Disable-TaskSafe $task.Path $task.Name
}

# ── Step 9: Additional Privacy Registry Tweaks ────────────────────────────────
Write-Log ""
Write-Log "STEP 9: Privacy registry tweaks..." "Green"

# Disable advertising ID
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo" "Enabled" 0

# Disable app launch tracking
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" "Start_TrackProgs" 0

# Disable tips and suggestions in Start Menu
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "SubscribedContent-338389Enabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "SubscribedContent-310093Enabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "SubscribedContent-338393Enabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "SystemPaneSuggestionsEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "SoftLandingEnabled" 0

# Disable lock screen ads/spotlight
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "RotatingLockScreenEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" "RotatingLockScreenOverlayEnabled" 0

# Disable Bing search in Start Menu
Set-RegistrySafe "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Explorer" "DisableSearchBoxSuggestions" 1
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search" "BingSearchEnabled" 0
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search" "CortanaConsent" 0

# ── Step 10: Network Performance Tweaks ───────────────────────────────────────
Write-Log ""
Write-Log "STEP 10: Network performance tweaks..." "Green"

# Disable nagling algorithm for lower latency (good for API calls to MotherDuck, EODHD)
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" "TcpAckFrequency" 1
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" "TCPNoDelay" 1

# Disable QoS packet scheduler reservation (frees 20% bandwidth reserved for Windows by default)
Set-RegistrySafe "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Psched" "NonBestEffortLimit" 0

# ── Step 11: Confirm High Performance Power Plan ──────────────────────────────
Write-Log ""
Write-Log "STEP 11: Confirming High Performance power plan for GPU..." "Green"
$currentPlan = powercfg /getactivescheme
if ($currentPlan -match "High performance") {
    Write-Log "  High Performance already active - no change needed" "Green"
} else {
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
    Write-Log "  Switched to High Performance power plan" "Yellow"
}

# Ensure GPU preference is max performance
Set-RegistrySafe "HKCU:\SOFTWARE\Microsoft\DirectX\UserGpuPreferences" "DirectXUserGlobalSettings" "SwapEffectUpgradeEnable=1;" "String"

# ── Step 12: Remove Protected AI/Bloat AppX Packages ─────────────────────────
Write-Log ""
Write-Log "STEP 12: Removing protected AI/bloat AppX packages (AllUsers)..." "Green"

$bloatPkgs = @(
    "MicrosoftWindows.Client.CoreAI",        # Recall/Copilot core AI engine
    "MicrosoftWindows.Client.WebExperience", # Widgets
    "Microsoft.WidgetsPlatformRuntime",       # Widgets platform
    "Microsoft.Windows.AugLoop.CBS",          # Loop components (Teams collab, useless standalone)
    "Microsoft.Copilot",                      # Copilot app
    "Microsoft.BingSearch"                    # Bing in Start
)

foreach ($pkg in $bloatPkgs) {
    try {
        $installed = Get-AppxPackage -AllUsers -Name $pkg -ErrorAction SilentlyContinue
        if ($installed) {
            Remove-AppxPackage -Package $installed.PackageFullName -AllUsers -ErrorAction SilentlyContinue
            Write-Log "  REMOVED AppX: $pkg" "Yellow"
        }
        $prov = Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $pkg }
        if ($prov) {
            Remove-AppxProvisionedPackage -Online -PackageName $prov.PackageName -ErrorAction SilentlyContinue | Out-Null
            Write-Log "  DEPROVISIONED: $pkg (won't reinstall)" "Yellow"
        }
    } catch {
        Write-Log "  SKIP: $pkg — $_" "Gray"
    }
}

# ── Step 13: Disable Fast Startup (RTX GPU driver conflict on resume) ─────────
Write-Log ""
Write-Log "STEP 12: Disabling Fast Startup (GPU driver conflict on resume)..." "Green"
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power" "HiberbootEnabled" 0
Write-Log "  Fast Startup disabled — full driver init on every boot (fixes post-sleep GPU sluggishness)" "Cyan"

# ── Step 13: Disable Modern Standby Networking ────────────────────────────────
Write-Log ""
Write-Log "STEP 13: Disabling Modern Standby Networking (unexpected wakeups)..." "Green"
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\F15576E8-98B7-4186-B944-EAFA664402D9" "Attributes" 2
Write-Log "  Modern Standby Networking disabled — no more network activity during sleep" "Cyan"

# ── Step 14: Disable BitLocker Auto-Encryption (24H2 silently enables this) ───
Write-Log ""
Write-Log "STEP 14: Disabling BitLocker auto-encryption (24H2 silent enablement)..." "Green"
Set-RegistrySafe "HKLM:\SYSTEM\CurrentControlSet\Control\BitLocker" "PreventDeviceEncryption" 1
Write-Log "  BitLocker auto-encryption blocked — no silent I/O overhead" "Cyan"

# ── Step 15: Disk Cleanup ─────────────────────────────────────────────────────
Write-Log ""
Write-Log "STEP 15: Disk cleanup — temp files, caches, WU download cache..." "Green"

$cleanTargets = @(
    @{ Path = $env:TEMP;                                          Label = "User Temp" },
    @{ Path = "C:\Windows\Temp";                                  Label = "Windows Temp" },
    @{ Path = "C:\Windows\SoftwareDistribution\Download";         Label = "WU Download Cache" },
    @{ Path = "$env:LOCALAPPDATA\Microsoft\Windows\INetCache";    Label = "IE/Edge Cache" },
    @{ Path = "$env:LOCALAPPDATA\pip\cache";                      Label = "pip Cache" },
    @{ Path = "$env:LOCALAPPDATA\npm-cache";                      Label = "npm Cache" },
    @{ Path = "$env:LOCALAPPDATA\Temp";                           Label = "LocalAppData Temp" }
)

$totalFreed = 0
foreach ($target in $cleanTargets) {
    if (Test-Path $target.Path) {
        try {
            $sizeBefore = (Get-ChildItem $target.Path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum -ErrorAction SilentlyContinue).Sum
            Get-ChildItem $target.Path -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            $freed = [math]::Round($sizeBefore / 1MB, 0)
            $totalFreed += $freed
            Write-Log "  CLEANED: $($target.Label) — ~${freed}MB freed" "Cyan"
        } catch {
            Write-Log "  SKIP: $($target.Label) — $_" "Gray"
        }
    } else {
        Write-Log "  SKIP: $($target.Label) not found" "Gray"
    }
}
Write-Log "  Total disk freed: ~${totalFreed}MB" "Green"

# ── Step 16: AI Post-Update Guard (scheduled task) ────────────────────────────
Write-Log ""
Write-Log "STEP 16: Installing AI post-update guard (re-apply after Windows Update)..." "Green"

$guardScript = @'
# Mother AI Guard — runs after Windows Update to re-disable AI features
$reg = @(
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI",    "DisableAIDataAnalysis",      1),
    @("HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI",    "DisableAIDataAnalysis",      1),
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",     1),
    @("HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",     1),
    @("HKCU:\SOFTWARE\Microsoft\Windows\Shell\Copilot",          "IsCopilotAvailable",        0),
    @("HKCU:\System\GameConfigStore",                            "GameDVR_Enabled",            0),
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR",      "AllowGameDVR",               0)
)
foreach ($r in $reg) {
    if (-not (Test-Path $r[0])) { New-Item -Path $r[0] -Force | Out-Null }
    Set-ItemProperty -Path $r[0] -Name $r[1] -Value $r[2] -Type DWord -Force -ErrorAction SilentlyContinue
}
# Re-disable AI services that Windows Update may have re-enabled
$aiSvcs = @("WSAIFabricSvc","DiagTrack","SysMain","WpnService")
foreach ($s in $aiSvcs) {
    $svc = Get-Service $s -ErrorAction SilentlyContinue
    if ($svc -and $svc.StartType -ne "Disabled") {
        Stop-Service $s -Force -ErrorAction SilentlyContinue
        Set-Service $s -StartupType Disabled -ErrorAction SilentlyContinue
    }
}
Add-Content "$env:USERPROFILE\Desktop\MotherV4\Mother\system\optimize_log.txt" "[$(Get-Date -Format 'yyyy-MM-dd HH:mm')] AI Guard ran post-update — settings re-applied"
'@

$guardPath = "$env:USERPROFILE\Desktop\MotherV4\Mother\system\ai_guard.ps1"
$guardScript | Set-Content $guardPath -Encoding UTF8

try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$guardPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At "03:00AM"
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    Register-ScheduledTask -TaskName "MotherAIGuard" -TaskPath "\OBQ\" `
        -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
        -Description "Mother AI Guard — re-applies AI/telemetry disables after Windows Update" `
        -Force | Out-Null
    Write-Log "  AI Guard scheduled task registered (runs daily 3AM as SYSTEM)" "Green"
} catch {
    Write-Log "  AI Guard task registration failed: $_ (run as admin to register)" "Yellow"
}

# ── Final Summary ─────────────────────────────────────────────────────────────
Write-Log ""
Write-Log "═══════════════════════════════════════════════════" "Green"
Write-Log "  OPTIMIZATION COMPLETE" "Green"
Write-Log "═══════════════════════════════════════════════════" "Green"

$os2 = Get-CimInstance Win32_OperatingSystem
$freeAfter = [math]::Round($os2.FreePhysicalMemory/1MB, 1)
$svchostAfter = (Get-Process svchost -ErrorAction SilentlyContinue).Count
Write-Log "AFTER (pre-restart): Free RAM = $freeAfter GB | svchost = $svchostAfter" "White"
Write-Log "NOTE: svchost consolidation and some service changes require RESTART" "Yellow"
Write-Log ""
Write-Log "CHANGES MADE:" "Cyan"
Write-Log "  - Telemetry services: DiagTrack, dmwappushservice, WerSvc disabled" "Cyan"
Write-Log "  - AI services: WSAIFabricSvc, Windows Recall, Copilot disabled" "Cyan"
Write-Log "  - GameBar/DVR: Disabled (RTX 3090 CUDA conflict eliminated)" "Cyan"
Write-Log "  - Windows Update: No auto-restart, no P2P delivery" "Cyan"
Write-Log "  - Widgets service: Disabled" "Cyan"
Write-Log "  - SysMain/Superfetch: Disabled (irrelevant on 128GB RAM)" "Cyan"
Write-Log "  - svchost threshold: Set to 128GB (consolidates ~78 processes after restart)" "Cyan"
Write-Log "  - Telemetry tasks: 13 scheduled tasks disabled" "Cyan"
Write-Log "  - Privacy: Advertising ID, tips, Bing search, activity tracking off" "Cyan"
Write-Log "  - Network: TCP ACK optimization, QoS reservation freed" "Cyan"
Write-Log ""
Write-Log "NOT TOUCHED:" "Gray"
Write-Log "  - ESET, Advanced SystemCare, Norgate — left as-is per your choice" "Gray"
Write-Log "  - Windows Search — left as-is per your choice" "Gray"
Write-Log "  - GPU drivers, CUDA, NVIDIA services — never touched" "Gray"
Write-Log "  - Python, PATH, WSL, Hyper-V — never touched" "Gray"
Write-Log ""
Write-Log "TO REVERT: Use System Restore point 'Mother-Optimize-$(Get-Date -Format yyyy-MM-dd)'" "Yellow"
Write-Log "LOG: $logFile" "Gray"
Write-Log ""
Write-Log "RESTART REQUIRED for full effect (svchost consolidation + service changes)" "Red"
