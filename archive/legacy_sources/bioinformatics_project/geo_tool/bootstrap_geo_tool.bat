@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%"

set "PYTHON_BIN=%PYTHON_BIN%"
if not defined PYTHON_BIN set "PYTHON_BIN=py -3"

call :run_python %PYTHON_BIN% --version
if errorlevel 1 (
  call :run_python python --version
  if errorlevel 1 (
    echo [ERROR] No usable Python interpreter was found.
    echo [ERROR] Install Python 3.10+ or set PYTHON_BIN before running this script.
    exit /b 1
  )
  set "PYTHON_BIN=python"
)

echo == 1^) Check Python ==
call :run_python %PYTHON_BIN% --version
if errorlevel 1 exit /b 1

echo == 2^) Create virtual environment ==
call :run_python %PYTHON_BIN% -m venv .venv
if errorlevel 1 (
  echo [ERROR] Failed to create .venv in "%REPO_ROOT%".
  exit /b 1
)

set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo [ERROR] Virtual environment Python was not found at "%VENV_PYTHON%".
  exit /b 1
)

echo == 3^) Upgrade pip ==
call "%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip/setuptools/wheel.
  exit /b 1
)

echo == 4^) Install layered GUI requirements ==
call "%VENV_PYTHON%" -m pip install -r "%REPO_ROOT%\geo_tool\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Failed to install geo_tool/requirements.txt.
  exit /b 1
)

echo == 5^) Check core dependencies ==
call "%VENV_PYTHON%" -c "import GEOparse, PySide6, pandas, numpy; print('GEOparse:', GEOparse.__version__); print('PySide6:', PySide6.__version__); print('pandas:', pandas.__version__); print('numpy:', numpy.__version__)"
if errorlevel 1 (
  echo [ERROR] Core dependency check failed.
  exit /b 1
)

echo == 6^) Done ==
echo Suggested checks:
echo   "%VENV_PYTHON%" geo_tool\run_geo_tool.py --check
echo Launch GUI:
echo   "%VENV_PYTHON%" geo_tool\run_geo_tool.py
echo Windows wrapper:
echo   geo_tool\run_geo_tool.bat --check
exit /b 0

:run_python
%*
exit /b %errorlevel%
