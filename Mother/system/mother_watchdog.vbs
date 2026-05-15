
' M.O.T.H.E.R Watchdog — runs independently, restarts widget if dead
' Place shortcut in Shell:Startup to survive OpenCode close/reopen

Dim pythonw, script, wsh, shell

pythonw = "C:\Users\admin\Desktop\.venv-obq\Scripts\pythonw.exe"
script  = "C:\Users\admin\Desktop\MotherV4\Mother\system\mother_widget.py"
workdir = "C:\Users\admin\Desktop\MotherV4\Mother\system"

Set wsh   = CreateObject("WScript.Shell")
Set shell = CreateObject("Shell.Application")

' Kill any existing pythonw running mother_widget
wsh.Run "taskkill /F /FI ""WINDOWTITLE eq tk""", 0, True
WScript.Sleep 1500

' Launch with Shell.Application — completely detached from any parent
' Shell.Application uses explorer.exe as parent, not the calling process
shell.ShellExecute pythonw, Chr(34) & script & Chr(34), workdir, "open", 0

WScript.Sleep 3000

' Watchdog loop — check every 30s, relaunch if dead
Do While True
    WScript.Sleep 30000
    
    Dim running
    running = False
    
    Dim objWMI, colProcs, proc
    Set objWMI = GetObject("winmgmts:\\.\root\cimv2")
    Set colProcs = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name='pythonw.exe'")
    
    For Each proc In colProcs
        If InStr(LCase(proc.CommandLine), "mother_widget") > 0 Then
            running = True
        End If
    Next
    
    If Not running Then
        shell.ShellExecute pythonw, Chr(34) & script & Chr(34), workdir, "open", 0
    End If
Loop
