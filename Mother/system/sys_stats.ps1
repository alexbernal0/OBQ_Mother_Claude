$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match 'NVIDIA|RTX|GTX' } | Select-Object -First 1
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }

Write-Host "RAM_TOTAL_GB=" ([math]::Round($os.TotalVisibleMemorySize/1MB,1))
Write-Host "RAM_FREE_GB=" ([math]::Round($os.FreePhysicalMemory/1MB,1))
Write-Host "CPU_NAME=" $cpu.Name.Trim()
Write-Host "CPU_CORES=" $cpu.NumberOfCores
Write-Host "CPU_THREADS=" $cpu.NumberOfLogicalProcessors
Write-Host "GPU_NAME=" $gpu.Name
Write-Host "GPU_VRAM_GB=" ([math]::Round($gpu.AdapterRAM/1GB,0))
Write-Host "SVCHOST_COUNT=" (Get-Process svchost -EA SilentlyContinue).Count
foreach ($d in $drives) {
    $used = [math]::Round($d.Used/1GB,1)
    $total = [math]::Round(($d.Used+$d.Free)/1GB,1)
    $pct = [math]::Round($d.Used/($d.Used+$d.Free)*100,0)
    Write-Host ("DRIVE_" + $d.Name + "=" + $used + "/" + $total + "GB_" + $pct + "pct")
}
