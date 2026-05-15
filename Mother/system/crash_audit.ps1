$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== CRASH / UNEXPECTED SHUTDOWN EVENTS ===" -ForegroundColor Red
# Event 41 = kernel power loss (crash/hard power off)
# Event 1001 = BugCheck (BSOD)
# Event 6008 = unexpected shutdown
# Event 6009 = system version at boot
Get-WinEvent -LogName System -MaxEvents 1000 -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -in @(41, 1001, 6008, 6009, 6013) } |
    Select-Object -First 15 |
    ForEach-Object {
        Write-Host ""
        Write-Host ("Time:    " + $_.TimeCreated) -ForegroundColor Yellow
        Write-Host ("EventID: " + $_.Id) -ForegroundColor Cyan
        Write-Host ("Level:   " + $_.LevelDisplayName)
        Write-Host ("Message: " + $_.Message.Substring(0, [Math]::Min(300, $_.Message.Length)))
    }

Write-Host ""
Write-Host "=== MINIDUMP FILES (BSOD evidence) ===" -ForegroundColor Red
$dumps = Get-ChildItem "C:\Windows\Minidump" -Filter "*.dmp" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
if ($dumps) {
    $dumps | Select-Object -First 5 | ForEach-Object {
        Write-Host ($_.LastWriteTime.ToString("yyyy-MM-dd HH:mm") + "  " + $_.Name + "  " + [math]::Round($_.Length/1KB) + "KB")
    }
} else {
    Write-Host "No minidump files found"
}

Write-Host ""
Write-Host "=== LAST 5 SYSTEM BOOTS ===" -ForegroundColor Green
Get-WinEvent -LogName System -MaxEvents 2000 -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -eq 6009 } |
    Select-Object -First 5 |
    ForEach-Object { Write-Host ("Boot: " + $_.TimeCreated + " | " + $_.Message.Substring(0,80)) }

Write-Host ""
Write-Host "=== GPU / HARDWARE ERRORS (last 48hrs) ===" -ForegroundColor Red
$cutoff = (Get-Date).AddHours(-48)
Get-WinEvent -LogName System -MaxEvents 2000 -ErrorAction SilentlyContinue |
    Where-Object { $_.TimeCreated -gt $cutoff -and $_.Level -le 2 } |
    Where-Object { $_.Message -match "GPU|display|video|NVIDIA|nvlddmkm|thermal|temperature|power|driver" } |
    Select-Object -First 10 |
    ForEach-Object {
        Write-Host ($_.TimeCreated.ToString("HH:mm") + " [" + $_.Id + "] " + $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length)))
    }

Write-Host ""
Write-Host "=== APPLICATION ERRORS (last 48hrs) ===" -ForegroundColor Yellow
Get-WinEvent -LogName Application -MaxEvents 1000 -ErrorAction SilentlyContinue |
    Where-Object { $_.TimeCreated -gt $cutoff -and $_.Level -le 2 } |
    Select-Object -First 10 |
    ForEach-Object {
        Write-Host ($_.TimeCreated.ToString("HH:mm") + " [" + $_.Id + "] " + $_.Message.Substring(0, [Math]::Min(150, $_.Message.Length)))
    }
