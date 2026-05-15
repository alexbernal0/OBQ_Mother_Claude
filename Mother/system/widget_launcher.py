import subprocess
import sys
import time
import os

PYTHONW = r"C:\Users\admin\Desktop\.venv-obq\Scripts\pythonw.exe"
WIDGET  = r"C:\Users\admin\Desktop\MotherV4\Mother\system\mother_widget.py"
WORKDIR = r"C:\Users\admin\Desktop\MotherV4\Mother\system"

def widget_running():
    import subprocess
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True
    )
    return "mother_widget" in result.stdout.lower() or "pythonw.exe" in result.stdout

def launch():
    subprocess.Popen(
        [PYTHONW, WIDGET],
        cwd=WORKDIR,
        creationflags=0x00000008,  # DETACHED_PROCESS
        close_fds=True
    )

if __name__ == "__main__":
    # Kill any existing widget instance first
    subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq M.O.T.H.E.R*"],
                   capture_output=True)
    time.sleep(1)
    launch()
