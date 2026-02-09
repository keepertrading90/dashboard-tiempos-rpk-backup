import pandas as pd
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
from datetime import datetime

app = FastAPI()

# Habilitar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRIPT_DIR = Path(__file__).parent.resolve()
EXCEL_FILE = SCRIPT_DIR / "ANALISIS_MENSUAL_TIEMPOS_V2.xlsx"

# Cache de datos para mejor rendimiento
_data_cache = None
_cache_time = None

def load_data():
    """Carga y cachea los datos del Excel"""
    global _data_cache, _cache_time
    
    # Recargar si el cache tiene más de 60 segundos
    if _data_cache is None or _cache_time is None or (datetime.now() - _cache_time).seconds > 60:
        if not EXCEL_FILE.exists():
            print(f"[ERROR] No existe el archivo {EXCEL_FILE}")
            return None, None, None
        
        try:
            df_centros = pd.read_excel(EXCEL_FILE, sheet_name='Datos_Centros')
            df_rankings = pd.read_excel(EXCEL_FILE, sheet_name='Rankings')
            
            # Intentar cargar la nueva hoja, si no existe usar un DF vacío
            try:
                df_ca = pd.read_excel(EXCEL_FILE, sheet_name='Datos_Centro_Articulo')
            except:
                print("[WARN] Hoja 'Datos_Centro_Articulo' no encontrada. Usando datos vacíos.")
                df_ca = pd.DataFrame(columns=['Fecha', 'Centro', 'Articulo', 'Horas'])
            
            # Limpiar NaN
            df_centros = df_centros.fillna(0)
            df_rankings = df_rankings.fillna(0)
            df_ca = df_ca.fillna(0)
            
            # Normalizar fechas a formato YYYY-MM-DD
            df_centros['Fecha'] = pd.to_datetime(df_centros['Fecha']).dt.strftime('%Y-%m-%d')
            df_rankings['Fecha'] = pd.to_datetime(df_rankings['Fecha']).dt.strftime('%Y-%m-%d')
            if not df_ca.empty:
                df_ca['Fecha'] = pd.to_datetime(df_ca['Fecha']).dt.strftime('%Y-%m-%d')
            
            # Excluir centros que empiezan por 9 (ej: 910, 911, 912, etc.)
            df_centros = df_centros[~df_centros['Centro'].astype(str).str.startswith('9')]
            df_rankings = df_rankings[~df_rankings['Centro'].astype(str).str.startswith('9')]
            if not df_ca.empty:
                df_ca = df_ca[~df_ca['Centro'].astype(str).str.startswith('9')]
            
            _data_cache = (df_centros, df_rankings, df_ca)
            _cache_time = datetime.now()
        except Exception as e:
            print(f"[ERROR] Cargando Excel: {e}")
            if _data_cache is not None:
                return _data_cache # Devolver cache antiguo si el nuevo falla
            return None, None, None
    
    return _data_cache


@app.get("/api/centro/{centro_id}/articulos")
def get_centro_articulos(
    centro_id: str,
    fecha: Optional[str] = Query(None)
):
    """Devuelve los artículos de un centro para una fecha específica"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    _, _, df_ca = data
    
    # Si no hay fecha, usar la última disponible
    if not fecha:
        fecha = df_ca['Fecha'].max()
    
    # Filtrar por centro y fecha
    df_filtrado = df_ca[
        (df_ca['Centro'].astype(str) == centro_id) & 
        (df_ca['Fecha'] == fecha)
    ].copy()
    
    if df_filtrado.empty:
        return {"articulos": []}
    
    # Columnas a devolver
    cols = ['Articulo', 'Horas']
    if 'OF' in df_filtrado.columns:
        cols.insert(1, 'OF')
    
    return {
        "centro": centro_id,
        "fecha": fecha,
        "articulos": df_filtrado[cols].to_dict(orient='records')
    }

@app.get("/api/centro/{centro_id}/articulos/mes/{mes}")
def get_centro_articulos_mes(
    centro_id: str,
    mes: str
):
    """Devuelve el desglose de artículos para un centro (o centros) en un mes específico"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    _, _, df_ca = data
    
    if df_ca.empty:
        return {"articulos": []}
        
    # Soporte para múltiples IDs
    centro_ids = [c.strip() for c in centro_id.split(',') if c.strip()]
    
    # Filtrar por centros y mes
    df_filtrado = df_ca[df_ca['Centro'].astype(str).isin(centro_ids)].copy()
    df_filtrado['Mes'] = pd.to_datetime(df_filtrado['Fecha']).dt.strftime('%Y-%m')
    df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
    
    if df_filtrado.empty:
        return {"articulos": []}
    
    # Agrupar por Artículo y O.F.
    group_cols = ['Articulo']
    if 'OF' in df_filtrado.columns:
        group_cols.append('OF')
        
    # Calcular Horas totales y contar días únicos por grupo
    df_mes = df_filtrado.groupby(group_cols).agg(
        Horas=('Horas', 'sum'),
        Dias=('Fecha', 'nunique')
    ).reset_index()
    
    df_mes = df_mes.sort_values('Horas', ascending=False)
    
    total_horas = df_mes['Horas'].sum()
    
    # Calcular porcentaje basado en horas (sigue siendo útil para la barra visual)
    if total_horas > 0:
        df_mes['Porcentaje'] = (df_mes['Horas'] / total_horas * 100).round(2)
    else:
        df_mes['Porcentaje'] = 0
    
    # Renombrar columnas para consistencia con el frontend
    df_mes = df_mes.rename(columns={
        'Articulo': 'articulo',
        'OF': 'of',
        'Horas': 'horas',
        'Dias': 'dias',
        'Porcentaje': 'porcentaje'
    })
    
    return {
        "mes": mes,
        "centros": centro_ids,
        "total_horas": round(float(total_horas), 2),
        "articulos": df_mes.to_dict(orient='records')
    }


@app.get("/api/centros")
def get_centros():
    """Devuelve lista de todos los centros disponibles"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    df_centros, _, _ = data
    
    # Obtener centros únicos ordenados por carga total
    centros_carga = df_centros.groupby('Centro')['Carga_Dia'].sum().sort_values(ascending=False)
    centros_list = [{"id": str(c), "carga_total": round(v, 2)} for c, v in centros_carga.items()]
    
    return {"centros": centros_list}


@app.get("/api/fechas")
def get_fechas():
    """Devuelve rango de fechas disponibles"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    df_centros, _, _ = data
    fechas = sorted(df_centros['Fecha'].unique())
    
    return {
        "fecha_min": fechas[0] if fechas else None,
        "fecha_max": fechas[-1] if fechas else None,
        "fechas": fechas
    }


@app.get("/api/centro/{centro_id}")
def get_centro_detalle(
    centro_id: str,
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """Devuelve evolución de uno o más centros (separados por coma)"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    df_centros, _, _ = data
    
    # Soporte para múltiples IDs (separados por coma)
    centro_ids = [c.strip() for c in centro_id.split(',') if c.strip()]
    
    # Filtrar por centros
    df_filtrado = df_centros[df_centros['Centro'].astype(str).isin(centro_ids)].copy()
    
    if df_filtrado.empty:
        return {"error": f"Centros {centro_id} no encontrados"}
    
    # Filtrar por fechas
    if fecha_inicio:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] >= fecha_inicio]
    if fecha_fin:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] <= fecha_fin]
    
    df_filtrado = df_filtrado.sort_values(['Fecha', 'Centro'])
    
    # Obtener todas las fechas en el rango para asegurar que todos los centros tengan los mismos puntos en el eje X
    todas_fechas = sorted(df_filtrado['Fecha'].unique())
    
    evoluciones = {}
    for cid in centro_ids:
        df_c = df_filtrado[df_filtrado['Centro'].astype(str) == cid]
        if df_c.empty: continue
        
        # Re-indexar para tener todas las fechas (rellenar con 0 si falta un día)
        df_c_full = pd.DataFrame({'Fecha': todas_fechas})
        df_c_full = pd.merge(df_c_full, df_c, on='Fecha', how='left').fillna(0)
        
        evoluciones[cid] = {
            "fechas": df_c_full['Fecha'].tolist(),
            "cargas": df_c_full['Carga_Dia'].tolist(),
            "stats": {
                "total": round(float(df_c['Carga_Dia'].sum()), 2),
                "media": round(float(df_c['Carga_Dia'].mean()), 2) if not df_c.empty else 0,
                "max": round(float(df_c['Carga_Dia'].max()), 2) if not df_c.empty else 0,
                "min": round(float(df_c['Carga_Dia'].min()), 2) if not df_c.empty else 0
            }
        }
    
    # Si solo hay un centro, mantener compatibilidad con respuesta original (opcional, pero mejor ser explícito)
    # Sin embargo, paraマルチ, devolveremos un objeto con 'fechas' global y 'centros' detallado
    
    stats_globales = {
        "total": round(float(df_filtrado['Carga_Dia'].sum()), 2),
        "media": round(float(df_filtrado.groupby('Fecha')['Carga_Dia'].sum().mean()), 2) if not df_filtrado.empty else 0,
        "max": round(float(df_filtrado.groupby('Fecha')['Carga_Dia'].sum().max()), 2) if not df_filtrado.empty else 0,
        "min": round(float(df_filtrado.groupby('Fecha')['Carga_Dia'].sum().min()), 2) if not df_filtrado.empty else 0
    }

    return {
        "multiple": len(centro_ids) > 1,
        "fechas": todas_fechas,
        "centros": evoluciones,
        "stats_globales": stats_globales,
        # Mantener los campos originales para compatibilidad con carga de un solo centro
        "cargas": evoluciones[centro_ids[0]]["cargas"] if len(centro_ids) == 1 and centro_ids[0] in evoluciones else [],
        "stats": evoluciones[centro_ids[0]]["stats"] if len(centro_ids) == 1 and centro_ids[0] in evoluciones else stats_globales
    }


@app.get("/api/summary")
def get_summary(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """Devuelve resumen general con filtro de fechas opcional"""
    data = load_data()
    if data[0] is None:
        return {"error": "Archivo de datos no encontrado"}
    
    df_centros, df_rankings, _ = data
    
    # Aplicar filtro de fechas
    if fecha_inicio:
        df_centros = df_centros[df_centros['Fecha'] >= fecha_inicio]
        df_rankings = df_rankings[df_rankings['Fecha'] >= fecha_inicio]
    if fecha_fin:
        df_centros = df_centros[df_centros['Fecha'] <= fecha_fin]
        df_rankings = df_rankings[df_rankings['Fecha'] <= fecha_fin]
    
    if df_centros.empty:
        return {"error": "No hay datos para el rango seleccionado"}
    
    # Resumen de KPIs
    total_carga = float(df_centros['Carga_Dia'].sum())
    media_carga = float(df_centros['Carga_Dia'].mean()) if len(df_centros) > 0 else 0.0
    num_centros = int(df_centros['Centro'].nunique())
    
    # Evolución diaria (agrupada por fecha)
    evolucion = df_centros.groupby('Fecha')['Carga_Dia'].sum().reset_index()
    evolucion = evolucion.sort_values('Fecha')
    
    # Evolución por centro (Top 5 con más carga total)
    top_centros_list = df_centros.groupby('Centro')['Carga_Dia'].sum().nlargest(5).index.tolist()
    df_top = df_centros[df_centros['Centro'].isin(top_centros_list)]
    evolucion_centros = {}
    for centro in top_centros_list:
        data_centro = df_top[df_top['Centro'] == centro].sort_values('Fecha')
        evolucion_centros[str(centro)] = {
            "fechas": data_centro['Fecha'].tolist(),
            "cargas": data_centro['Carga_Dia'].tolist()
        }
    
    # Rankings de la última fecha disponible
    ultima_fecha = df_rankings['Fecha'].max()
    rankings_ultima = df_rankings[df_rankings['Fecha'] == ultima_fecha].to_dict(orient='records')

    return {
        "kpis": {
            "total_carga": round(total_carga, 2),
            "media_carga": round(media_carga, 2),
            "num_centros": num_centros
        },
        "evolucion_total": {
            "fechas": evolucion['Fecha'].tolist(),
            "cargas": evolucion['Carga_Dia'].tolist()
        },
        "evolucion_centros": evolucion_centros,
        "rankings": rankings_ultima,
        "ultima_fecha": ultima_fecha
    }


# Servir archivos estáticos del dashboard
app.mount("/", StaticFiles(directory=str(SCRIPT_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
