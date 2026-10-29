@echo off
rem Lessons from the Windows command line:  windows\learn.bat list | start p01_faq_search | check p01_faq_search | hint ...
set PYTHONUTF8=1
if exist "%~dp0..\.venv\Scripts\python.exe" (
  "%~dp0..\.venv\Scripts\python.exe" -m learn %*
) else (
  python -m learn %*
)
