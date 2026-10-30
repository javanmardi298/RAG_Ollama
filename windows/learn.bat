@echo off
rem Lessons from the Windows command line:  windows\learn.bat list | start p01_faq_search | check p01_faq_search | hint ...
cd /d "%~dp0\.."
set PYTHONUTF8=1
rem Works even if "pip install -e ." was never run: src is put on the path, and missing packages are installed once.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
.venv\Scripts\python.exe -c "import fastapi, uvicorn, yaml, pydantic" 2>nul || .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-panel.txt
.venv\Scripts\python.exe -c "import support" 2>nul || .venv\Scripts\python.exe -m pip install -e . --no-deps --quiet
.venv\Scripts\python.exe -m learn %*
