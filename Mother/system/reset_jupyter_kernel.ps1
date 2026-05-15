# ============================================================
#  OBQ Jupyter Kernel Reset Script
#  Run this BEFORE opening any notebook in VSCode
#  Usage: Right-click → Run with PowerShell
#         or: powershell -File C:\Users\admin\reset_jupyter_kernel.ps1
# ============================================================

$PY = "C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host "=== OBQ Jupyter Kernel Reset ===" -ForegroundColor Cyan
Write-Host ""

# 1. Kill stale ipykernel / jupyter processes
Write-Host "[1/5] Killing stale kernel processes..." -ForegroundColor Yellow
$killed = 0
Get-WmiObject Win32_Process | Where-Object {
    $_.CommandLine -match 'ipykernel_launcher|jupyter-kernel|jupyter-notebook'
} | ForEach-Object {
    Write-Host "  Killed PID=$($_.ProcessId) ($($_.CommandLine.Substring(0,[Math]::Min(60,$_.CommandLine.Length)))...)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    $killed++
}
if ($killed -eq 0) { Write-Host "  None found" -ForegroundColor Green }

# 2. Kill heavy opencode-cli processes (>200MB) — known VSCode kernel competitor
Write-Host "[2/5] Checking opencode-cli memory hogs..." -ForegroundColor Yellow
$oc = Get-Process opencode-cli -ErrorAction SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 200MB }
if ($oc) {
    $oc | ForEach-Object {
        Write-Host "  Killed opencode-cli PID=$($_.Id) MB=$([math]::Round($_.WorkingSet64/1MB))" -ForegroundColor Red
        Stop-Process -Id $_.Id -Force
    }
} else {
    Write-Host "  Clean" -ForegroundColor Green
}

# 3. Clear stale Jupyter runtime files (port conflict source)
Write-Host "[3/5] Clearing stale runtime files..." -ForegroundColor Yellow
$runtimeDirs = @(
    "$env:APPDATA\jupyter\runtime",
    "$env:LOCALAPPDATA\jupyter\runtime"
)
$cleared = 0
foreach ($dir in $runtimeDirs) {
    if (Test-Path $dir) {
        $files = Get-ChildItem $dir -Filter "*.json" -ErrorAction SilentlyContinue
        $files | Remove-Item -Force -ErrorAction SilentlyContinue
        $cleared += ($files | Measure-Object).Count
    }
}
Write-Host "  Cleared $cleared runtime files" -ForegroundColor Green

# 4. Verify ipykernel is healthy
Write-Host "[4/5] Verifying ipykernel..." -ForegroundColor Yellow
$ver = & $PY -c "import ipykernel; print(ipykernel.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ipykernel $ver OK" -ForegroundColor Green
} else {
    Write-Host "  ipykernel MISSING - reinstalling..." -ForegroundColor Red
    & $PY -m pip install ipykernel --quiet
    & $PY -m ipykernel install --user
    Write-Host "  Reinstalled" -ForegroundColor Green
}

# 5. Memory check
Write-Host "[5/5] Memory snapshot..." -ForegroundColor Yellow
$py  = Get-Process python -ErrorAction SilentlyContinue
$pyMB = [math]::Round(($py | Measure-Object WorkingSet64 -Sum).Sum/1MB)
$vc  = Get-Process Code -ErrorAction SilentlyContinue
$vcMB = [math]::Round(($vc | Measure-Object WorkingSet64 -Sum).Sum/1MB)
Write-Host "  Python:  $($py.Count) procs, ${pyMB}MB" -ForegroundColor $(if($pyMB -gt 2000){"Red"}else{"Green"})
Write-Host "  VSCode:  $($vc.Count) procs, ${vcMB}MB" -ForegroundColor $(if($vcMB -gt 3072){"Red"}else{"Green"})

Write-Host ""
Write-Host "=== DONE — Safe to open notebook in VSCode ===" -ForegroundColor Cyan
Write-Host "  Do: Ctrl+Shift+P → Developer: Reload Window" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close"
