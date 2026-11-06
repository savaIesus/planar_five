@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0" || goto :folder_error

if not exist "requirements.txt" goto :folder_error
if not exist "main.py" goto :folder_error

if exist ".venv\Scripts\python.exe" goto :check_venv

echo Looking for Python 3.12 or newer...
set "PYTHON_COMMAND="
py -3.12 -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PYTHON_COMMAND=py -3.12"
if defined PYTHON_COMMAND goto :create_venv
py -3 -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PYTHON_COMMAND=py -3"
if defined PYTHON_COMMAND goto :create_venv
python -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PYTHON_COMMAND=python"
if not defined PYTHON_COMMAND goto :python_error

:create_venv
echo Creating virtual environment in .venv...
%PYTHON_COMMAND% -m venv ".venv"
if errorlevel 1 goto :venv_error

:check_venv
".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3, 12))"
if errorlevel 1 goto :venv_error

echo Installing dependencies. This may take several minutes...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto :install_error

set "PLANAR_ROOT=%CD%"
echo Creating desktop shortcuts...
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $desktop = [Environment]::GetFolderPath('DesktopDirectory'); if (-not $desktop -or -not (Test-Path -LiteralPath $desktop -PathType Container)) { throw 'Desktop folder not found' }; $shell = New-Object -ComObject WScript.Shell; foreach ($entry in @(@('Planar Five.lnk', 'run_app.bat'), @('Planar Five Training.lnk', 'run_training.bat'))) { $link = $shell.CreateShortcut((Join-Path $desktop $entry[0])); $link.TargetPath = Join-Path $env:PLANAR_ROOT $entry[1]; $link.WorkingDirectory = $env:PLANAR_ROOT; $link.Save() }"
if errorlevel 1 goto :shortcut_error

echo.
echo Setup complete. Use the Planar Five shortcuts on your desktop.
echo Do not run the main application and training at the same time.
pause
exit /b 0

:folder_error
echo ERROR: Keep setup.bat in the project folder next to main.py and requirements.txt.
goto :failure
:python_error
echo ERROR: Python 3.12 or newer was not found. Install Python 3.12 and run setup again.
goto :failure
:venv_error
echo ERROR: Could not create or use .venv. If it is broken or uses an older Python,
echo remove the .venv folder manually and run setup again.
goto :failure
:install_error
echo ERROR: Dependency installation failed. Check the messages above and Internet access,
echo then run setup again.
goto :failure
:shortcut_error
echo ERROR: Could not create desktop shortcuts. Check PowerShell and desktop permissions.
echo You can run run_app.bat and run_training.bat from the project folder instead.
:failure
pause
exit /b 1
