@echo off
setlocal
cd /d "%~dp0"
title Seoul IA FiveM
if not exist ".venv\Scripts\python.exe" (
 echo Execute INSTALAR_SEOUL.bat primeiro.
 pause
 exit /b 1
)
set "PATH=%~dp0.venv\Scripts;%PATH%"
".venv\Scripts\python.exe" app.py
if errorlevel 1 echo [ERRO] O aplicativo encerrou com erro.
pause
