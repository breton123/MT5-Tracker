import psutil, os

def closeTerminal(terminalPath):
    # Normalize the given path for comparison
    normalized_exe_path = os.path.normpath(terminalPath).lower()
    
    for proc in psutil.process_iter(['pid', 'exe']):
        try:
            proc_exe = proc.info['exe']
            if proc_exe and os.path.normpath(proc_exe).lower() == normalized_exe_path:
                proc.terminate()
                proc.wait(timeout=5)  # Wait for the process to terminate
                print(f"Process {proc.pid} terminated.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
       
     
def isTerminalOpen(exe_path):
    for proc in psutil.process_iter(['pid', 'exe']):
        try:
            if proc.info['exe'] and proc.info['exe'].lower() == exe_path.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False