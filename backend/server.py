import pandas as pd
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
from datetime import datetime
import os

app = FastAPI(title="RPK Time Analysis Dashboard API")

# Habilitar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR
EXCEL_FILE = DATA_DIR / "ANALISIS_MENSUAL_TIEMPOS_V2.xlsx"
STATIC_DIR = BASE_DIR / "frontend"

# Cache de datos para mejor rendimiento
_data_cache = None
_cache_time = None

def load_data():
    """Carga y cachea los datos del Excel con estándar de seguridad industrial"""
    global _data_cache, _cache_time
    
    # Recargar si el cache no existe o han pasado más de 60 segundos
    if _data_cache is None or _cache_time is None or (datetime.now() - _cache_time).seconds > 60:
        if not EXCEL_FILE.exists():
            # Intentar buscar en el directorio actual por si acaso
            alternative_path = Path(__file__).parent / "ANALISIS_MENSUAL_TIEMPOS_V2.xlsx"
            if alternative_path.exists():
                file_to_load = alternative_path
            else:
                print(f"[ERROR] No existe el archivo {EXCEL_FILE}")
                return None, None, None
        else:
            file_to_load = EXCEL_FILE
        
        try:
            # Lectura optimizada: solo hojas necesarias
            df_centros = pd.read_excel(file_to_load, sheet_name='Datos_Centros')
            df_rankings = pd.read_excel(file_to_load, sheet_name='Rankings')
            
            # Intentar cargar la nueva hoja de desglose
            try:
                df_ca = pd.read_excel(file_to_load, sheet_name='Datos_Centro_Articulo')
            except Exception:
                df_ca = pd.DataFrame(columns=['Fecha', 'Centro', 'Articulo', 'Horas'])
            
            # Limpieza y normalización
            df_centros = df_centros.fillna(0)
            df_rankings = df_rankings.fillna(0)
            df_ca = df_ca.fillna(0)
            
            # Normalizar fechas a formato YYYY-MM-DD
            for df in [df_centros, df_rankings, df_ca]:
                if not df.empty and 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')
            
            # Regla de Negocio: Excluir centros auxiliares (empiezan por 9)
            def filter_aux(df):
                if df.empty or 'Centro' not in df.columns: return df
                return df[~df['Centro'].astype(str).str.startswith('9')]

            df_centros = filter_aux(df_centros)
            df_rankings = filter_aux(df_rankings)
            df_ca = filter_aux(df_ca)
            
            _data_cache = (df_centros, df_rankings, df_ca)
            _cache_time = datetime.now()
        except Exception as e:
            print(f"[ERROR] Fallo crítico cargando base de datos: {e}")
            if _data_cache is not None:
                return _data_cache
            return None, None, None
    
    return _data_cache

@app.get("/api/status")
def get_status():
    """Endpoint de salud del sistema"""
    data = load_data()
    return {
        "status": "online" if data[0] is not None else "degraded",
        "last_cache": _cache_time.strftime("%Y-%m-%d %H:%M:%S") if _cache_time else None,
        "database": str(EXCEL_FILE.name)
    }

@app.get("/api/centros")
def get_centros():
    """Lista maestra de centros con carga acumulada"""
    data = load_data()
    if data[0] is None: return JSONResponse({"error": "DB_NOT_FOUND"}, status_code=500)
    
    df_centros, _, _ = data
    centros_carga = df_centros.groupby('Centro')['Carga_Dia'].sum().sort_values(ascending=False)
    centros_list = [{"id": str(c), "carga_total": round(v, 2)} for c, v in centros_carga.items()]
    
    return {"centros": centros_list}

@app.get("/api/fechas")
def get_fechas():
    """Rango temporal de datos disponibles"""
    data = load_data()
    if data[0] is None: return JSONResponse({"error": "DB_NOT_FOUND"}, status_code=500)
    
    df_centros, _, _ = data
    fechas = sorted(df_centros['Fecha'].unique())
    
    return {
        "fecha_min": fechas[0] if fechas else None,
        "fecha_max": fechas[-1] if fechas else None,
        "fechas": fechas
    }

@app.get("/api/summary")
def get_summary(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """Core Metrics Dashboard Data"""
    data = load_data()
    if data[0] is None: return JSONResponse({"error": "DB_NOT_FOUND"}, status_code=500)
    
    df_centros, df_rankings, _ = data
    
    # Filtrado por rango
    if fecha_inicio: df_centros = df_centros[df_centros['Fecha'] >= fecha_inicio]
    if fecha_fin: df_centros = df_centros[df_centros['Fecha'] <= fecha_fin]
    
    if df_centros.empty:
        return {"error": "NO_DATA_IN_RANGE", "kpis": {"total_carga": 0, "media_carga": 0, "num_centros": 0}}
    
    # Agregaciones KPI
    total_carga = float(df_centros['Carga_Dia'].sum())
    media_carga = float(df_centros.groupby('Fecha')['Carga_Dia'].sum().mean()) if not df_centros.empty else 0
    num_centros = int(df_centros['Centro'].nunique())
    
    # Evolución Total
    evolucion = df_centros.groupby('Fecha')['Carga_Dia'].sum().sort_index()
    
    # Evolución Top 5 para el gráfico principal
    top_centros = df_centros.groupby('Centro')['Carga_Dia'].sum().nlargest(5).index.tolist()
    evolucion_centros = {}
    for c in top_centros:
        df_c = df_centros[df_centros['Centro'] == c].sort_values('Fecha')
        evolucion_centros[str(c)] = {
            "fechas": df_c['Fecha'].tolist(),
            "cargas": df_c['Carga_Dia'].tolist()
        }
    
    # Rankings (última fecha) - Filtrar solo por Centro para el mini-ranking
    ultima_fecha = df_rankings['Fecha'].max()
    rankings_ultima = df_rankings[
        (df_rankings['Fecha'] == ultima_fecha) & 
        (df_rankings['Tipo'] == 'Centro')
    ].copy()
    
    # Asegurar que el ID del Centro es entero para evitar el .0
    rankings_ultima['Centro'] = rankings_ultima['Centro'].fillna(0).astype(int).astype(str)
    
    rankings_dict = rankings_ultima.to_dict(orient='records')

    return {
        "kpis": {
            "total_carga": round(total_carga, 2),
            "media_carga": round(media_carga, 2),
            "num_centros": num_centros
        },
        "evolucion_total": {
            "fechas": evolucion.index.tolist(),
            "cargas": evolucion.values.tolist()
        },
        "evolucion_centros": evolucion_centros,
        "rankings": rankings_dict,
        "ultima_fecha": ultima_fecha
    }

@app.get("/api/centro/{centro_id}")
def get_centro_detalle(
    centro_id: str,
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """Detalle profundo de evolución por centro(s)"""
    data = load_data()
    if data[0] is None: return JSONResponse({"error": "DB_NOT_FOUND"}, status_code=500)
    
    df_centros, _, _ = data
    centro_ids = [c.strip() for c in centro_id.split(',') if c.strip()]
    
    df_filtrado = df_centros[df_centros['Centro'].astype(str).isin(centro_ids)].copy()
    if df_filtrado.empty: return {"error": "CENTRO_NOT_FOUND"}
    
    if fecha_inicio: df_filtrado = df_filtrado[df_filtrado['Fecha'] >= fecha_inicio]
    if fecha_fin: df_filtrado = df_filtrado[df_filtrado['Fecha'] <= fecha_fin]
    
    todas_fechas = sorted(df_filtrado['Fecha'].unique())
    evoluciones = {}
    
    for cid in centro_ids:
        df_c = df_filtrado[df_filtrado['Centro'].astype(str) == cid]
        if df_c.empty: continue
        
        # Sincronización de ejes temporales
        df_full = pd.DataFrame({'Fecha': todas_fechas})
        df_full = pd.merge(df_full, df_c, on='Fecha', how='left').fillna(0)
        
        evoluciones[cid] = {
            "fechas": df_full['Fecha'].tolist(),
            "cargas": df_full['Carga_Dia'].tolist(),
            "stats": {
                "total": round(float(df_c['Carga_Dia'].sum()), 2),
                "media": round(float(df_c['Carga_Dia'].mean()), 2),
                "max": round(float(df_c['Carga_Dia'].max()), 2),
                "min": round(float(df_c['Carga_Dia'].min()), 2)
            }
        }
    
    return {
        "fechas": todas_fechas,
        "centros": evoluciones,
        "multiple": len(centro_ids) > 1
    }

@app.get("/api/centro/{centro_id}/articulos/mes/{mes}")
def get_centro_breakdown(centro_id: str, mes: str):
    """Drill-down: Desglose de artículos por centro y mes"""
    data = load_data()
    if data[0] is None: return JSONResponse({"error": "DB_NOT_FOUND"}, status_code=500)
    
    _, _, df_ca = data
    if df_ca.empty: return {"articulos": []}
    
    centro_ids = [c.strip() for c in centro_id.split(',') if c.strip()]
    df_f = df_ca[df_ca['Centro'].astype(str).isin(centro_ids)].copy()
    df_f['Mes'] = pd.to_datetime(df_f['Fecha']).dt.strftime('%Y-%m')
    df_f = df_f[df_f['Mes'] == mes]
    
    if df_f.empty: return {"articulos": []}
    
    # Agrupación por Artículo y O.F. (si existe)
    agg_cols = ['Articulo']
    if 'OF' in df_f.columns: agg_cols.append('OF')
    
    df_res = df_f.groupby(agg_cols).agg(
        horas=('Horas', 'sum'),
        dias=('Fecha', 'nunique')
    ).reset_index().sort_values('horas', ascending=False)
    
    total = df_res['horas'].sum()
    df_res['porcentaje'] = (df_res['horas'] / total * 100).round(2) if total > 0 else 0
    
    return {
        "mes": mes,
        "total_horas": round(float(total), 2),
        "articulos": df_res.rename(columns={'Articulo': 'articulo', 'OF': 'of'}).to_dict(orient='records')
    }

# SPA: Servir frontend
# Montamos toda la carpeta frontend bajo /static para simplificar rutas
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_index():
    from fastapi.responses import FileResponse
    # index.html está en frontend/ui/index.html
    return FileResponse(STATIC_DIR / "ui" / "index.html")

if __name__ == "__main__":
    import uvicorn
    # Puerto estándar RPK
    uvicorn.run(app, host="0.0.0.0", port=8000)
