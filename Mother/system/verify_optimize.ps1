$svc = @('DiagTrack','WSAIFabricSvc','SysMain','DoSvc','WpnService','XblGameSave','XblAuthManager')
Write-Host "=== Service Status After Optimization ===" -ForegroundColor Green
foreach ($s in $svc) {
    $info = Get-Service $s -ErrorAction SilentlyContinue
    if ($info) {
        $color = if ($info.StartType -eq 'Disabled') { 'Green' } else { 'Yellow' }
        Write-Host ($s.PadRight(30) + $info.Status.ToString().PadRight(12) + $info.StartType) -ForegroundColor $color
    }
}

Write-Host ""
$os = Get-CimInstance Win32_OperatingSystem
$free = [math]::Round($os.FreePhysicalMemory/1MB,1)
Write-Host "Free RAM: $free GB"
Write-Host "svchost count: $((Get-Process svchost -EA SilentlyContinue).Count)"

Write-Host ""
$thresh = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control' -EA SilentlyContinue).SvcHostSplitThresholdInKB
Write-Host "SvcHostSplitThresholdInKB: $thresh (128GB = 134217728)"

$telem = (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -EA SilentlyContinue).AllowTelemetry
Write-Host "AllowTelemetry: $telem (0=disabled)"

$recall = (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' -EA SilentlyContinue).DisableAIDataAnalysis
Write-Host "DisableAIDataAnalysis (Recall): $recall (1=disabled)"

$copilot = (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' -EA SilentlyContinue).TurnOffWindowsCopilot
Write-Host "TurnOffCopilot: $copilot (1=disabled)"

$gamedvr = (Get-ItemProperty 'HKCU:\System\GameConfigStore' -EA SilentlyContinue).GameDVR_Enabled
Write-Host "GameDVR_Enabled: $gamedvr (0=disabled)"

$bingsearch = (Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search' -EA SilentlyContinue).BingSearchEnabled
Write-Host "BingSearchEnabled: $bingsearch (0=disabled)"

$adid = (Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo' -EA SilentlyContinue).Enabled
Write-Host "AdvertisingID: $adid (0=disabled)"
