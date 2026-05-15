Write-Host "=== ALL DISPLAY ADAPTERS ===" -ForegroundColor Green
Get-CimInstance Win32_VideoController | ForEach-Object {
    Write-Host ""
    Write-Host ("Name:        " + $_.Name)
    Write-Host ("Resolution:  " + $_.CurrentHorizontalResolution + " x " + $_.CurrentVerticalResolution)
    Write-Host ("Refresh:     " + $_.CurrentRefreshRate + " Hz")
    Write-Host ("Status:      " + $_.Status)
    Write-Host ("DriverVer:   " + $_.DriverVersion)
    Write-Host ("DriverDate:  " + $_.DriverDate)
}

Write-Host ""
Write-Host "=== MONITOR DETAILS ===" -ForegroundColor Green
Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBasicDisplayParams -ErrorAction SilentlyContinue | ForEach-Object {
    $name = $_.InstanceName
    Write-Host ("Monitor: " + $name)
    Write-Host ("  Max H: " + $_.MaxHorizontalImageSize + "cm  Max V: " + $_.MaxVerticalImageSize + "cm")
}

Write-Host ""
Write-Host "=== CONNECTED MONITORS (from registry) ===" -ForegroundColor Green
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Configuration\*" -ErrorAction SilentlyContinue |
    Select-Object -First 10 | ForEach-Object { Write-Host $_.PSChildName }

Write-Host ""
Write-Host "=== DPI / SCALING PER MONITOR ===" -ForegroundColor Green
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Display {
    [DllImport("user32.dll")] public static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr lprcClip, MonitorEnumProc lpfnEnum, IntPtr dwData);
    public delegate bool MonitorEnumProc(IntPtr hMonitor, IntPtr hdcMonitor, ref RECT lprcMonitor, IntPtr dwData);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetMonitorInfo(IntPtr hMonitor, ref MONITORINFOEX lpmi);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)] public struct MONITORINFOEX {
        public int Size; public RECT Monitor; public RECT WorkArea; public uint Flags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string DeviceName;
    }
}
"@ -ErrorAction SilentlyContinue

# Simple approach - check display config via PowerShell
$displays = Get-CimInstance -ClassName Win32_DesktopMonitor -ErrorAction SilentlyContinue
$displays | ForEach-Object {
    Write-Host ("Monitor: " + $_.Name + " | Status: " + $_.Availability)
}

Write-Host ""
Write-Host "=== RECENT DISPLAY DRIVER EVENTS (last 48hrs) ===" -ForegroundColor Yellow
$cutoff = (Get-Date).AddHours(-48)
Get-WinEvent -LogName System -MaxEvents 2000 -ErrorAction SilentlyContinue |
    Where-Object { $_.TimeCreated -gt $cutoff -and ($_.Message -match "display|monitor|video|resolution|NVIDIA|nvlddmkm" ) } |
    Select-Object -First 10 |
    ForEach-Object { Write-Host ($_.TimeCreated.ToString("yyyy-MM-dd HH:mm") + " [" + $_.Id + "] " + $_.Message.Substring(0,[Math]::Min(150,$_.Message.Length))) }
