@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0" || goto :error
if not exist ".venv\Scripts\python.exe" goto :missing_venv
echo Stop the main application before using training.
".venv\Scripts\python.exe" -m project.training --open-browser
if errorlevel 1 goto :error
exit /b 0

:missing_venv
echo Virtual environment not found. Run setup.bat from the project folder first.
goto :error
:error
echo Training could not be started or exited with an error.
pause
exit /b 1
