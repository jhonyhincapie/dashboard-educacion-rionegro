@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ARCHIVO=%~1"
if not "%ARCHIVO%"=="" goto run

for /f "delims=" %%F in ('dir /b /a-d /o-d "entradas\Presupuesto de egreso*.xls" 2^>nul') do (
    set "ARCHIVO=entradas\%%F"
    goto run
)

echo.
echo   No hay ningun archivo .xls en la carpeta  entradas
echo   Copie alli el Excel de Hacienda y vuelva a hacer doble clic.
echo.
pause
exit /b 1

:run
echo.
echo   Procesando: %ARCHIVO%
echo.
py "extractor_educacion.py" "%ARCHIVO%"
if errorlevel 1 python "extractor_educacion.py" "%ARCHIVO%"
echo.
echo   Listo. Se abre la carpeta de informes.
start "" "%~dp0informes"
pause
