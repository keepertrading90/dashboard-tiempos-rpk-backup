@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo        LANZADOR DE DASHBOARD EJECUTIVO RPK
echo ============================================================
echo.
echo Iniciando servidor web en http://localhost:8000...
echo.

:: 1. Liberar puerto 8000 si esta ocupado
echo [1/3] Liberando puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

:: 2. Regenerar datos de analisis
echo [2/3] Actualizando datos de analisis...
"%~dp0..\..\_SISTEMA\runtime_python\python.exe" "%~dp0analisis_mensual_tiempos.py"

:: 3. Iniciar el servidor en segundo plano
echo [3/3] Iniciando servidor...
START /MIN "RPK_Dashboard" "%~dp0..\..\_SISTEMA\runtime_python\python.exe" "%~dp0server.py"

echo.
echo El dashboard ya esta funcionando.
echo Se abrira el navegador en unos segundos...
echo.

:: Abrir navegador con tiempo de espera suficiente
timeout /t 5 >nul
start "" "http://localhost:8000"

echo Proceso completado. Puedes cerrar esta ventana.
timeout /t 3 >nul
