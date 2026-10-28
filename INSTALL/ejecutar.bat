@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto sin_instalar
set "PATH=C:\msys64\ucrt64\bin;%PATH%;C:\msys64\usr\bin"
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
exit /b
:sin_instalar
echo Primero ejecuta INSTALL\instalar_windows.bat
pause