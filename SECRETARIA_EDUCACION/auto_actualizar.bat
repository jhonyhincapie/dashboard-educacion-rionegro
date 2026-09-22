@echo off
REM Ejecuta la revision automatica del dashboard. Pensado para Tarea Programada de Windows.
cd /d "%~dp0"
"C:\Users\jhincapie\AppData\Local\Programs\Python\Python312\python.exe" auto_actualizar.py
