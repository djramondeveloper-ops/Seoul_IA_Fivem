@echo off
setlocal
cd /d "%~dp0"
title Instalador Seoul IA FiveM
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALAR_SEOUL.ps1"
if errorlevel 1 (
 echo.
 echo [ERRO] Instalacao incompleta. Confira as mensagens acima.
) else (
 echo.
 echo [OK] Instalador finalizado.
)
pause
