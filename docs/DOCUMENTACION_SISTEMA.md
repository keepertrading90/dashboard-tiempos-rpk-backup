# 📊 Documentación Técnica: Dashboard de Análisis de Tiempos (RPK)

## 1. Concepto y Propósito del Proyecto
El **Dashboard de Tiempos** es una plataforma analítica diseñada para el control y optimización del "Tiempo de Ejecución Disponible" (Wait Time/Load) en los centros de trabajo de RPK. Su misión es:
- Cuantificar la carga de trabajo diaria y mensual por centro.
- Identificar cuellos de botella mediante análisis de medias históricas.
- Desglosar la carga de artículos y Órdenes de Fabricación (OF) por recurso.
- Facilitar la toma de decisiones basada en datos reales de avance de obra.

---

## 2. Arquitectura del Sistema
Siguiendo el estándar **RPK AGENTIC SYSTEM v7.0**, el proyecto se estructura en tres capas:

### A. Capa de Ingestión (Motor ETL)
- **Script**: `backend/analisis_mensual_tiempos.py`.
- **Origen**: Reportes Excel en `y:\Supply Chain\PLAN PRODUCCION\List Avance Obra-Centro y Operacion`.
- **Lógica**:
    - Selecciona el último archivo generado por día.
    - Normaliza columnas heterogéneas (mapeo de alias para 'Artículo', 'TEjec_Disp', etc.).
    - Filtra centros de trabajo por longitud de código (excluye centros > 4 dígitos) y centros auxiliares (serie 9000).
    - Agrega datos por Fecha, Centro, Artículo y OF.
- **Resultado**: Archivo consolidado `ANALISIS_MENSUAL_TIEMPOS_V2.xlsx`.

### B. Backend (Servicio API)
- **Motor**: FastAPI sobre Python Portable.
- **EndPoint Principal**: `/api/summary` (KPIs, evolución temporal, rankings).
- **Drill-Down**: `/api/centro/{id}/articulos/mes/{mes}` para ver el detalle de qué artículos están consumiendo el tiempo en un recurso específico.
- **Optimización**: Sistema de caché de datos de 60 segundos para alto rendimiento.

### C. Frontend (UI/UX)
- **Ubicación**: `frontend/ui/`.
- **Tecnología**: JavaScript asíncrono, CSS industrial Red & Dark y Chart.js.
- **Funcionalidades**:
    - Selectores de rango de fechas.
    - Comparativa multi-centro en gráficas de carga.
    - Tablas interactivas con desglose de artículos.

---

## 3. Lógica de Cálculo y KPIs

### KPIs Fundamentales
1. **Carga Diaria**: Suma de `TEjec_Disp` reportada por cada centro en un día específico.
2. **Media Mensual**: Promedio de carga diaria calculado sobre los días laborables/reportados del mes seleccionado.
3. **Porcentaje de Ocupación**: Distribución relativa del tiempo entre las diferentes OFs en un centro determinado.

---

## 4. Recursos Utilizados

### Core Tecnológico
- **Python Runtime**: `Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe`.
- **Framework Web**: FastAPI + Uvicorn.
- **Análisis de Datos**: Library `pandas` con motores `xlsxwriter` y `openpyxl`.

### Componentes Visuales
- **Chart.js**: Renderizado de series temporales y diagramas de barras.
- **Estándar RPK**: Color Primario `#E30613`, fuentes Roboto/Inter, Dark Mode persistente.

---

## 5. Estructura de Archivos
```text
DASHBOARD_TIEMPOS/
├── backend/
│   ├── analisis_mensual_tiempos.py # Motor de procesamiento ETL.
│   └── server.py                  # API de servicio y lógica de negocio.
├── frontend/
│   ├── ui/                        # HTML, JS y CSS de la interfaz.
│   └── assets/                    # Recursos gráficos y logos.
├── scripts/
│   ├── qa_scanner.py              # Validador de calidad de código.
│   └── ops_sync.py                # Sincronización con repositorio RPK.
├── ANALISIS_MENSUAL_TIEMPOS_V2.xlsx # Snapshot de datos procesados.
└── README.md                      # (Este documento)
```

---

## ⚙️ Operación del Sistema

### Actualización de Datos (ETL)
```bash
& "Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe" backend/analisis_mensual_tiempos.py
```

### Arranque del Servidor
```bash
& "Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe" backend/server.py
```
*(Disponible por defecto en puerto 8000)*

---
**Documentación generada bajo el Estándar RPK AGENTIC SYSTEM v7.0**
