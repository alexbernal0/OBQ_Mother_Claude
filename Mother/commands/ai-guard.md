---
description: "Re-apply AI/telemetry disables after Windows Update. Run whenever Windows updates and things feel slow again."
argument-hint: ""
allowed-tools: "Bash, Read, Write"
---

# /ai-guard — Mother AI Post-Update Guard

Windows Update frequently re-enables Copilot, Recall, telemetry services, and AI features.
Run this after any Windows Update to re-apply all disables.

## What it re-applies

| Category | Items |
|---|---|
| AI/Recall registry | `DisableAIDataAnalysis`, `TurnOffWindowsCopilot`, `IsCopilotAvailable` |
| GameDVR/GameBar | `GameDVR_Enabled`, `AllowGameDVR` (RTX CUDA conflict) |
| Services | `WSAIFabricSvc`, `DiagTrack`, `SysMain`, `WpnService` → Disabled |
| Copilot packages | Removes `Microsoft.Copilot` AppX if reinstalled |
| Widgets packages | Removes `MicrosoftWindows.Client.WebExperience` if reinstalled |

## Step 1 — Check what Windows Update re-enabled

```powershell
$svcs = @("DiagTrack","WSAIFabricSvc","SysMain","WpnService","XblGameSave")
Write-Host "=== Services that should be DISABLED ==="
foreach ($s in $svcs) {
    $svc = Get-Service $s -ErrorAction SilentlyContinue
    if ($svc) {
        $status = if ($svc.StartType -eq "Disabled") { "OK (Disabled)" } else { "REVERTED → $($svc.StartType)" }
        $color = if ($svc.StartType -eq "Disabled") { "Green" } else { "Red" }
        Write-Host "  $($s.PadRight(20)) $status" -ForegroundColor $color
    }
}
Write-Host ""
$recall = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" -ErrorAction SilentlyContinue).DisableAIDataAnalysis
Write-Host "Recall disabled: $(if ($recall -eq 1) { 'YES OK' } else { 'NO — REVERTED' })"
$copilot = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" -ErrorAction SilentlyContinue).TurnOffWindowsCopilot
Write-Host "Copilot disabled: $(if ($copilot -eq 1) { 'YES OK' } else { 'NO — REVERTED' })"
```

## Step 2 — Re-apply all disables

```powershell
# Re-apply registry
$reg = @(
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI",     "DisableAIDataAnalysis",   1),
    @("HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI",     "DisableAIDataAnalysis",   1),
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",   1),
    @("HKCU:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",   1),
    @("HKCU:\SOFTWARE\Microsoft\Windows\Shell\Copilot",           "IsCopilotAvailable",     0),
    @("HKCU:\System\GameConfigStore",                             "GameDVR_Enabled",         0),
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR",       "AllowGameDVR",            0),
    @("HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry",          0)
)
foreach ($r in $reg) {
    if (-not (Test-Path $r[0])) { New-Item -Path $r[0] -Force | Out-Null }
    Set-ItemProperty -Path $r[0] -Name $r[1] -Value $r[2] -Type DWord -Force -ErrorAction SilentlyContinue
    Write-Host "SET: $($r[1]) = $($r[2])"
}

# Re-disable services
$svcs = @("WSAIFabricSvc","DiagTrack","SysMain","WpnService","XblGameSave","XblAuthManager")
foreach ($s in $svcs) {
    $svc = Get-Service $s -ErrorAction SilentlyContinue
    if ($svc -and $svc.StartType -ne "Disabled") {
        Stop-Service $s -Force -ErrorAction SilentlyContinue
        Set-Service $s -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host "DISABLED: $s"
    }
}

# Remove any reinstalled AI AppX packages
$aiPkgs = @("Microsoft.Copilot","MicrosoftWindows.Client.WebExperience","Microsoft.WidgetsPlatformRuntime","Microsoft.BingSearch")
foreach ($pkg in $aiPkgs) {
    $installed = Get-AppxPackage -Name $pkg -ErrorAction SilentlyContinue
    if ($installed) {
        Remove-AppxPackage -Package $installed.PackageFullName -ErrorAction SilentlyContinue
        Write-Host "REMOVED AppX: $pkg"
    }
}
Write-Host ""
Write-Host "AI Guard complete. All disables re-applied."
```

## When to run
- After any Windows Update (especially feature updates like 24H2, 25H2)
- When OpenCode or Ollama feels sluggish after an update
- When you see Copilot/Recall icons reappear in taskbar
- The `MotherAIGuard` scheduled task also runs this automatically at 3AM daily
