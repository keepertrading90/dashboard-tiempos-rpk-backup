@echo off
title RPK Dashboard Debug
chcp 65001 >nul

echo ============================================================
echo   ANALIZANDO ENTORNO RPK...
echo ============================================================

:: Definir rutas absolutas para evitar errores de navegación
set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe"

echo [+] Ruta Raiz: %ROOT_DIR%
echo [+] Buscando Python en: %PYTHON_EXE%

:: 1. Verificar si Python existe
if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encuentra el ejecutable de Python en la ruta de red.
    pause
    exit /b
)

:: 2. Liberar puerto 8000
echo [+] Limpiando puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo [!] Matando proceso PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: 3. Ejecutar procesamiento de datos (Opcional)
if exist "%ROOT_DIR%backend\analisis_mensual_tiempos.py" (
    echo [+] Procesando datos de tiempos...
    "%PYTHON_EXE%" "%ROOT_DIR%backend\analisis_mensual_tiempos.py"
) else (
    echo [!] Aviso: No se encontro script de procesamiento en backend\
)

:: 4. Iniciar Servidor
echo [+] Iniciando servidor FastAPI...
echo [INFO] La ventana se minimizara, pero el servidor seguira corriendo.
start /min "RPK_API" "%PYTHON_EXE%" "%ROOT_DIR%backend\server.py"

:: 5. Abrir navegador
echo [+] Abriendo Dashboard en 3 segundos...
timeout /t 3 >nul
start "" "http://localhost:8000"

echo.
echo ============================================================
echo   TODO LISTO. SI EL NAVEGADOR NO CARGA, REVISA ESTA VENTANA.
echo ============================================================
pause
