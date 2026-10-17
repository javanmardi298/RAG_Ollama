@echo off
rem Registers this project's MCP server in Claude Desktop (a backup of the old config is kept next to it).
cd /d "%~dp0\.."
set PYTHONUTF8=1
.venv\Scripts\python.exe -m support.panel.claude_desktop install
echo.
echo Now quit Claude Desktop completely (system tray icon - Quit) and open it again.
pause
