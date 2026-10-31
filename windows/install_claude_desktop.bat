@echo off
rem Registers this project's MCP server in Claude Desktop (a backup of the old config is kept next to it).
cd /d "%~dp0\.."
set PYTHONUTF8=1
rem Works even if "pip install -e ." was never run: src is put on the path, and missing packages are installed once.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
.venv\Scripts\python.exe -c "import fastapi, uvicorn, yaml, pydantic" 2>nul || .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-panel.txt
.venv\Scripts\python.exe -c "import support" 2>nul || .venv\Scripts\python.exe -m pip install -e . --no-deps --quiet
.venv\Scripts\python.exe -m support.panel.claude_desktop install
echo.
echo Now quit Claude Desktop completely (system tray icon - Quit) and open it again.
pause
