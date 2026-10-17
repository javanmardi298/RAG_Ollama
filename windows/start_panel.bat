@echo off
rem Starts the control panel at http://127.0.0.1:8765 and opens the browser. Close this window to stop the panel
rem (runs that are already going keep running and report to the panel next time).
cd /d "%~dp0\.."
if not exist .venv\Scripts\python.exe (
  echo The virtual environment is missing. Run first, in PowerShell:  .\windows\setup.ps1
  pause
  exit /b 1
)
set PYTHONUTF8=1
.venv\Scripts\python.exe -m support.panel %*
pause
