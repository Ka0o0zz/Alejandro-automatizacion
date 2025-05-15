@echo off
REM Activar el entorno virtual y ejecutar el script de extracción

cd /d "%~dp0"
call env\Scripts\activate.bat
python python/core.py
pause
