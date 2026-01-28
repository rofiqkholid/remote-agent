@echo off
echo ==========================================
echo   Installing Computer Monitoring Agent
echo ==========================================

REM Install MSI silently (/qn)
echo 1. Installing...
msiexec /i "%~dp0AgentMonitoring-1.0-win64.msi" /qn

echo 2. Installation Complete.

echo 3. Starting Agent...
REM Try Program Files (x64)
if exist "%ProgramFiles%\AgentMonitoring\AgentMonitoring.exe" (
    start "" "%ProgramFiles%\AgentMonitoring\AgentMonitoring.exe"
) else (
    REM Try Program Files (x86) just in case
    if exist "%ProgramFiles(x86)%\AgentMonitoring\AgentMonitoring.exe" (
        start "" "%ProgramFiles(x86)%\AgentMonitoring\AgentMonitoring.exe"
    ) else (
        echo WARNING: Could not find Agent executable to start automatically.
        echo Please start "AgentMonitoring" from the Start Menu manually.
    )
)

echo.
echo SUCCESS! Agent is running. Check the Dashboard.
echo ==========================================
pause
