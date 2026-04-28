@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%"

set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo [ERROR] Virtual environment Python was not found at "%VENV_PYTHON%".
  echo [ERROR] Run geo_tool\bootstrap_geo_tool.bat first.
  echo [ERROR] Or use the canonical entrypoint directly: py -3 geo_tool\run_geo_tool.py --check
  exit /b 1
)

call "%VENV_PYTHON%" "%REPO_ROOT%\geo_tool\run_geo_tool.py" %*
set "EXIT_CODE=%errorlevel%"
if not "%EXIT_CODE%"=="0" (
  echo [ERROR] geo_tool\run_geo_tool.py exited with code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
