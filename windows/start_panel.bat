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
rem Works even if "pip install -e ." was never run: src is put on the path, and missing packages are installed once.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
.venv\Scripts\python.exe -c "import fastapi, uvicorn, yaml, pydantic" 2>nul || .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-panel.txt
.venv\Scripts\python.exe -c "import support" 2>nul || .venv\Scripts\python.exe -m pip install -e . --no-deps --quiet
.venv\Scripts\python.exe -m support.panel %*
pause
