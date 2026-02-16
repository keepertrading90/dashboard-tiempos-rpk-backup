# 📊 Dashboard de Análisis de Tiempos - Proyecto RPK

Información técnica y operativa sobre la funcionalidad, lógica y recursos del sistema de control de tiempos de ejecución.

## 🚀 Funcionalidad
El proyecto permite el análisis profundo de la carga de trabajo en los centros de RPK mediante:
- **Monitorización de Carga**: Seguimiento de las horas de ejecución disponibles (`TEjec_Disp`).
- **Análisis de Medias**: Comparativa de carga actual frente a medias mensuales para detectar saturación.
- **Drill-down de Artículos**: Desglose detallado de qué artículos y OFs componen la carga de un centro.
- **Visualización Temporal**: Gráficas evolutivas multi-centro.

---

## 🧠 Concepto y Lógica Operativa

### Motor de Datos (`backend/analisis_mensual_tiempos.py`)
- **Limpieza Automática**: Filtra centros auxiliares y normaliza formatos de tiempo del ERP.
- **Agregación diaria**: Consolida múltiples reportes en una única base de datos Excel optimizada (`ANALISIS_MENSUAL_TIEMPOS_V2.xlsx`).
- **Lógica de Ranking**: Calcula dinámicamente el top de centros y artículos más cargados.

### Servicio API (`backend/server.py`)
- **FastAPI**: Proporciona endpoints rápidos para el consumo de datos desde el frontend.
- **Reglas de Negocio**: Implementa filtros de centros específicos y cálculos de medias ponderadas.

---

## 🛠️ Recursos y Tecnologías
- **Entorno**: Python 3.11 Portable (Ruta RPK).
- **Librerías Core**: `pandas`, `fastapi`, `uvicorn`.
- **UI/UX**: HTML5/CSS3/JS con **Chart.js** para visualización de series temporales.
- **Estándar Visual**: Dark Mode corporativo RPK Red (`#E30613`).

---

## 📁 Estructura del Proyecto
- `backend/`: Código de procesamiento y servidor API.
- `frontend/`: Interfaz de usuario y estilos.
- `docs/`: Documentación técnica detallada.
- `scripts/`: Herramientas de auditoría y sincronización.

---

## ⚙️ Guía Rápida de Operación

### Refrescar Datos
```bash
& "Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe" backend/analisis_mensual_tiempos.py
```

### Iniciar Aplicación
```bash
& "Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe" backend/server.py
```

---
**Desarrollado bajo el Estándar RPK AGENTIC SYSTEM v7.0**
