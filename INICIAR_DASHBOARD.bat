@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo        RPK GROUP | DASHBOARD ANALISIS DE TIEMPOS
echo ============================================================
echo.
echo Iniciando servidor en http://localhost:8000...
echo.

set PYTHON_PATH="%~dp0..\..\_SISTEMA\runtime_python\python.exe"

:: 1. Liberar puerto 8000 si esta ocupado
echo [1/3] Limpiando procesos previos...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

:: 2. Actualizar datos desde el Excel (Opcional, si el script existe)
if exist "%~dp0backend\analisis_mensual_tiempos.py" (
    echo [2/3] Procesando datos de Excel...
    %PYTHON_PATH% "%~dp0backend\analisis_mensual_tiempos.py"
) else (
    echo [2/3] Saltando procesamiento de datos (script no encontrado).
)

:: 3. Iniciar el servidor
echo [3/3] Iniciando backend de FastAPI...
START /MIN "RPK_Dashboard_API" %PYTHON_PATH% "%~dp0backend\server.py"

echo.
echo Dashboard desplegado correctamente.
echo Abriendo aplicacion en el navegador...
echo.

:: Abrir navegador
timeout /t 3 >nul
start "" "http://localhost:8000"

echo.
echo Presiona cualquier tecla para cerrar este lanzador.
pause >nul
