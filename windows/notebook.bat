@echo off
rem Opens a lesson as a notebook in JupyterLab:  windows\notebook.bat p01_faq_search
cd /d "%~dp0\.."
set PYTHONUTF8=1
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
.venv\Scripts\python.exe -c "import jupyterlab, ipykernel" 2>nul || .venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.venv\Scripts\python.exe -m learn lab %*
pause
