@echo off
REM Wrapper to run the PowerShell installer for Chrome and ChromeDriver on Windows

REM Ensure the script runs with administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb runAs"
    exit /b
)

REM Execute the PowerShell installation script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_chrome_windows.ps1"

pause
