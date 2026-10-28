@echo off
title Instalador - Compilador Equipo 6
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar_windows.ps1"
echo.
pause
