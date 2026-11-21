@echo off
setlocal
cd /d "%~dp0"
title Seoul IA FiveM - Painel Web
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" seoul_web.py
) else (
 py -3 seoul_web.py
)
if errorlevel 1 echo [ERRO] Confira se Python 3.11+ esta instalado.
pause
