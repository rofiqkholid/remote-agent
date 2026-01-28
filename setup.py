import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "requests", "pysher", "mss", "pyautogui", "logging", "threading", "json", "socket", "platform", "uuid", "base64", "winreg", "PIL"],
    "include_files": ["config.json"]
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="AgentMonitoring",
    version="1.0",
    description="Remote Computer Monitoring Agent",
    options={"build_exe": build_exe_options},
    executables=[Executable("agent-python/main.py", base=base, target_name="AgentMonitoring.exe")]
)
