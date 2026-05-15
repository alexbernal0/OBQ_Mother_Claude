@echo off
:: M.O.T.H.E.R Widget Launcher
:: Kills any existing instance, then relaunches silently (no console window)
:: To auto-start: Win+R -> shell:startup -> copy shortcut to this .bat here

:: Kill any old widget instance
taskkill /F /FI "WINDOWTITLE eq M.O.T.H.E.R*" 2>nul
taskkill /F /FI "IMAGENAME eq pythonw.exe" 2>nul
timeout /t 1 /nobreak >nul

:: Launch with pythonw = no console window
start "" /B pythonw "%~dp0mother_widget.py"
echo M.O.T.H.E.R Widget launched.
