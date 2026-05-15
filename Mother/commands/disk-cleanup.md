---
description: "Safe one-command disk cleanup — temp files, WU cache, pip/npm cache, AppData audit. Reports GB recovered."
argument-hint: "[--dry-run]"
allowed-tools: "Bash, Read, Write"
---

# /disk-cleanup — Mother Disk Cleanup

Safe cleanup targeting known junk locations. Never touches project files, models, or user data.

## What gets cleaned

| Target | Path | Safe? |
|---|---|---|
| User Temp | `%TEMP%` | ✅ Always |
| Windows Temp | `C:\Windows\Temp` | ✅ Always |
| WU Download Cache | `C:\Windows\SoftwareDistribution\Download` | ✅ Always |
| IE/Edge Cache | `%LOCALAPPDATA%\Microsoft\Windows\INetCache` | ✅ Always |
| pip cache | `%LOCALAPPDATA%\pip\cache` | ✅ Always |
| npm cache | `%LOCALAPPDATA%\npm-cache` | ✅ Always |
| Claude vm_bundles | `%APPDATA%\Claude\vm_bundles` | ✅ If present (re-downloads on demand) |

## Step 1 — Dry run (show what would be freed)

```powershell
$targets = @(
    "$env:TEMP",
    "C:\Windows\Temp",
    "C:\Windows\SoftwareDistribution\Download",
    "$env:LOCALAPPDATA\Microsoft\Windows\INetCache",
    "$env:LOCALAPPDATA\pip\cache",
    "$env:LOCALAPPDATA\npm-cache",
    "$env:APPDATA\Claude\vm_bundles"
)
$total = 0
foreach ($t in $targets) {
    if (Test-Path $t) {
        $mb = [math]::Round((Get-ChildItem $t -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum -ErrorAction SilentlyContinue).Sum/1MB, 0)
        $total += $mb
        Write-Host ("{0,-55} {1,6} MB" -f $t, $mb)
    }
}
Write-Host ""
Write-Host "Total reclaimable: $total MB ($([math]::Round($total/1024,1)) GB)"
```

## Step 2 — Execute cleanup (if not --dry-run)

```powershell
$targets = @(
    "$env:TEMP",
    "C:\Windows\Temp",
    "C:\Windows\SoftwareDistribution\Download",
    "$env:LOCALAPPDATA\Microsoft\Windows\INetCache",
    "$env:LOCALAPPDATA\pip\cache",
    "$env:LOCALAPPDATA\npm-cache",
    "$env:APPDATA\Claude\vm_bundles"
)
$total = 0
foreach ($t in $targets) {
    if (Test-Path $t) {
        $mb = [math]::Round((Get-ChildItem $t -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum -ErrorAction SilentlyContinue).Sum/1MB, 0)
        Get-ChildItem $t -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        $total += $mb
        Write-Host "CLEANED: $t (~${mb}MB)"
    }
}
Write-Host ""
Write-Host "Done. Total freed: ~$total MB ($([math]::Round($total/1024,1)) GB)"
```

## Step 3 — C drive summary after cleanup

```powershell
$c = Get-PSDrive C
Write-Host "C drive: Used=$([math]::Round($c.Used/1GB,1))GB  Free=$([math]::Round($c.Free/1GB,1))GB"
```

Report findings to user. Never delete anything outside the targets list above.
