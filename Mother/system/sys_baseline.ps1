$os = Get-CimInstance Win32_OperatingSystem
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$freeGB  = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$usedGB  = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
Write-Host "RAM: $usedGB GB used / $totalGB GB total ($freeGB GB free)"

$svchostCount = (Get-Process svchost -ErrorAction SilentlyContinue).Count
Write-Host "svchost processes: $svchostCount"

$thresh = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control' -Name SvcHostSplitThresholdInKB -ErrorAction SilentlyContinue).SvcHostSplitThresholdInKB
Write-Host "SvcHostSplitThresholdInKB: $thresh"

$plan = powercfg /getactivescheme
Write-Host "Power plan: $plan"

Write-Host ""
Write-Host "--- Top 20 RAM consumers ---"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 |
    ForEach-Object { Write-Host ("{0,-35} {1,6} MB" -f $_.Name, [math]::Round($_.WorkingSet64/1MB)) }

Write-Host ""
Write-Host "--- Services set to Automatic that are running ---"
Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' } |
    Sort-Object DisplayName | ForEach-Object { Write-Host $_.Name.PadRight(40) $_.DisplayName }

Write-Host ""
Write-Host "--- Startup programs ---"
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location |
    ForEach-Object { Write-Host $_.Name.PadRight(40) $_.Command }
