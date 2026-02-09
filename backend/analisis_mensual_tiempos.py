# -*- coding: utf-8 -*-
"""
ANALISIS MENSUAL DE TIEMPO MEDIO DE ESPERA
===========================================
Calcula el promedio mensual del "Tiempo Ejecucion Disponible" (TEjec_Disp)
agrupado por Centro y por Artículo.
FILTRO: Se omiten centros de más de 4 dígitos.
"""
import pandas as pd
from pathlib import Path
import re
import sys
import io

# Configurar salida UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuración - Rutas relativas al script
SCRIPT_DIR = Path(__file__).parent.resolve()
# PANEL\_PROYECTOS\DASHBOARD_TIEMPOS -> _PROYECTOS -> PANEL -> PLAN PRODUCCION
BASE_PATH = SCRIPT_DIR.parent.parent.parent
CARPETA_DATOS = BASE_PATH / "List Avance Obra-Centro y Operacion"
OUTPUT_FILE = SCRIPT_DIR / "ANALISIS_MENSUAL_TIEMPOS_V2.xlsx"

# Columnas a cargar
COLUMNAS_REQUERIDAS = ['Centro', 'Artículo', 'TEjec_Disp', 'C. Terminada', 'C.Terminada FAn', 'O.F']

# Mapeo alternativo de columnas
COLUMNAS_ALTERNATIVAS = {
    'Artículo': ['Articulo', 'ARTICULO', 'Artículo'],
    'TEjec_Disp': ['TEjec_Disp', 'Tiempo Ejecucion Disponible', 'T.Ejec Disp'],
    'C. Terminada': ['C. Terminada', 'C.Terminada', 'Cantidad Terminada'],
    'C.Terminada FAn': ['C.Terminada FAn', 'C. Terminada Ant', 'Cantidad Terminada Ant'],
    'O.F': ['O.F', 'OF', 'Orden Fabricacion']
}


def extraer_fecha_nombre(nombre_archivo):
    """Extrae la fecha del nombre del archivo (formato YYYY-MM-DD)"""
    patron = r'\((\d{4}-\d{2}-\d{2})'
    match = re.search(patron, nombre_archivo)
    if match:
        try:
            return pd.to_datetime(match.group(1))
        except:
            return None
    return None


def encontrar_columna(df, nombre_estandar, alternativas):
    """Busca la columna con el nombre estándar o sus alternativas"""
    if nombre_estandar in df.columns:
        return nombre_estandar
    for alt in alternativas.get(nombre_estandar, []):
        if alt in df.columns:
            return alt
    return None


def limpiar_tiempo_disponible(valor):
    """Limpia y convierte el valor de Tiempo Ejecución Disponible a float"""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    valor_str = str(valor).strip()
    valor_str = valor_str.replace(',', '.').replace(' ', '')
    valor_str = re.sub(r'[^\d.\-]', '', valor_str)
    try:
        return float(valor_str) if valor_str else None
    except ValueError:
        return None


def cargar_y_procesar_archivos():
    """Carga todos los archivos Excel y los procesa (solo el último archivo de cada día)"""
    archivos = list(CARPETA_DATOS.glob("*.xlsx"))
    print(f"[INFO] Encontrados {len(archivos)} archivos en la carpeta")
    
    archivos_por_fecha = {}
    for archivo in archivos:
        fecha = extraer_fecha_nombre(archivo.name)
        if fecha is not None:
            fecha_str = fecha.strftime('%Y-%m-%d')
            if fecha_str not in archivos_por_fecha or archivo.name > archivos_por_fecha[fecha_str].name:
                archivos_por_fecha[fecha_str] = archivo
    
    archivos_filtrados = list(archivos_por_fecha.values())
    print(f"[INFO] Usando {len(archivos_filtrados)} archivos (1 por día)")
    
    dfs = []
    errores = 0
    
    for archivo in sorted(archivos_filtrados):
        fecha = extraer_fecha_nombre(archivo.name)
        if fecha is None:
            continue
        
        try:
            df = pd.read_excel(archivo)
            columnas_mapeadas = {}
            for col_std in COLUMNAS_REQUERIDAS:
                col_real = encontrar_columna(df, col_std, COLUMNAS_ALTERNATIVAS)
                if col_real:
                    columnas_mapeadas[col_real] = col_std
            
            cols_existentes = [col for col in columnas_mapeadas.keys() if col in df.columns]
            if not cols_existentes:
                continue
            
            df = df[cols_existentes].copy()
            df = df.rename(columns=columnas_mapeadas)
            
            # FILTRO: Centros con 5 o más dígitos se omiten
            if 'Centro' in df.columns:
                df['Centro'] = df['Centro'].astype(str).str.strip()
                df = df[df['Centro'].str.len() <= 4]
            
            if df.empty:
                continue

            df['Fecha_Reporte'] = fecha
            df['Mes_Año'] = fecha.strftime('%Y-%m')
            
            if 'TEjec_Disp' in df.columns:
                df['TEjec_Disp'] = df['TEjec_Disp'].apply(limpiar_tiempo_disponible)
            
            if 'Artículo' in df.columns:
                df['Artículo'] = df['Artículo'].astype(str).str.strip()
            
            dfs.append(df)
            
        except Exception as e:
            errores += 1
            print(f"  [ERROR] {archivo.name}: {str(e)[:60]}")
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()


def calcular_analisis(df_unificado):
    """Calcula la Media de Carga Diaria por Centro y por Artículo."""
    
    if 'TEjec_Disp' not in df_unificado.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Análisis por Centro
    df_diario_centro = df_unificado.groupby(['Fecha_Reporte', 'Centro'])['TEjec_Disp'].sum().reset_index()
    df_diario_centro.columns = ['Fecha', 'Centro', 'Carga_Dia']
    df_diario_centro['Fecha'] = pd.to_datetime(df_diario_centro['Fecha']).dt.date
    df_diario_centro['Mes'] = pd.to_datetime(df_diario_centro['Fecha']).dt.strftime('%Y-%m')
    
    df_mensual_centro = df_diario_centro.groupby(['Mes', 'Centro'])['Carga_Dia'].agg(
        Media_Mensual='mean',
        Total_Mes='sum'
    ).reset_index()
    
    media_por_centro = pd.merge(df_diario_centro, df_mensual_centro, on=['Mes', 'Centro'], how='left')
    media_por_centro = media_por_centro[['Fecha', 'Centro', 'Carga_Dia', 'Media_Mensual', 'Total_Mes']]
    
    # Análisis por Artículo
    if 'Artículo' in df_unificado.columns:
        df_diario_articulo = df_unificado.groupby(['Fecha_Reporte', 'Artículo'])['TEjec_Disp'].sum().reset_index()
        df_diario_articulo.columns = ['Fecha', 'Artículo', 'Carga_Dia']
        df_diario_articulo['Fecha'] = pd.to_datetime(df_diario_articulo['Fecha']).dt.date
        df_diario_articulo['Mes'] = pd.to_datetime(df_diario_articulo['Fecha']).dt.strftime('%Y-%m')
        
        df_mensual_articulo = df_diario_articulo.groupby(['Mes', 'Artículo'])['Carga_Dia'].agg(
            Media_Mensual='mean',
            Total_Mes='sum'
        ).reset_index()
        
        media_por_articulo = pd.merge(df_diario_articulo, df_mensual_articulo, on=['Mes', 'Artículo'], how='left')
        media_por_articulo = media_por_articulo[['Fecha', 'Artículo', 'Carga_Dia', 'Media_Mensual', 'Total_Mes']]
        
        # NUEVO: Análisis Centro-Artículo (para desplegables en el ranking)
        group_cols = ['Fecha_Reporte', 'Centro', 'Artículo']
        if 'O.F' in df_unificado.columns:
            group_cols.append('O.F')
            
        df_centro_articulo = df_unificado.groupby(group_cols)['TEjec_Disp'].sum().reset_index()
        
        if 'O.F' in df_unificado.columns:
            df_centro_articulo.columns = ['Fecha', 'Centro', 'Articulo', 'OF', 'Horas']
        else:
            df_centro_articulo.columns = ['Fecha', 'Centro', 'Articulo', 'Horas']
            
        df_centro_articulo['Fecha'] = pd.to_datetime(df_centro_articulo['Fecha']).dt.date
    else:
        media_por_articulo = pd.DataFrame(columns=['Fecha', 'Artículo', 'Carga_Dia', 'Media_Mensual', 'Total_Mes'])
        df_centro_articulo = pd.DataFrame(columns=['Fecha', 'Centro', 'Articulo', 'Horas'])

    return media_por_centro, media_por_articulo, df_centro_articulo


def export_excel(media_por_centro, media_por_articulo, df_centro_articulo):
    """Genera archivo Excel con hojas de datos y rankings."""
    
    with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
        # Hoja Datos_Centros
        media_por_centro.to_excel(writer, sheet_name='Datos_Centros', index=False)
        ws_centros = writer.sheets['Datos_Centros']
        num_rows_c = len(media_por_centro)
        num_cols_c = len(media_por_centro.columns)
        if num_rows_c > 0:
            ws_centros.add_table(0, 0, num_rows_c, num_cols_c - 1, {
                'name': 'TablaCentros',
                'style': 'Table Style Medium 2',
                'columns': [{'header': col} for col in media_por_centro.columns]
            })

        # Hoja Datos_Articulos
        media_por_articulo.to_excel(writer, sheet_name='Datos_Articulos', index=False)
        ws_articulos = writer.sheets['Datos_Articulos']
        num_rows_a = len(media_por_articulo)
        num_cols_a = len(media_por_articulo.columns)
        if num_rows_a > 0:
            ws_articulos.add_table(0, 0, num_rows_a, num_cols_a - 1, {
                'name': 'TablaArticulos',
                'style': 'Table Style Medium 2',
                'columns': [{'header': col} for col in media_por_articulo.columns]
            })
        
        # Hoja Datos_Centro_Articulo
        df_centro_articulo.to_excel(writer, sheet_name='Datos_Centro_Articulo', index=False)
        ws_ca = writer.sheets['Datos_Centro_Articulo']
        num_rows_ca = len(df_centro_articulo)
        num_cols_ca = len(df_centro_articulo.columns)
        if num_rows_ca > 0:
            ws_ca.add_table(0, 0, num_rows_ca, num_cols_ca - 1, {
                'name': 'TablaCentroArticulo',
                'style': 'Table Style Medium 4',
                'columns': [{'header': col} for col in df_centro_articulo.columns]
            })
        
        # Hoja Rankings
        rankings_centros = []
        for fecha in media_por_centro['Fecha'].unique():
            df_fecha = media_por_centro[media_por_centro['Fecha'] == fecha].copy()
            df_fecha = df_fecha.nlargest(15, 'Carga_Dia')
            df_fecha['Ranking'] = range(1, len(df_fecha) + 1)
            df_fecha['Tipo'] = 'Centro'
            df_fecha['Articulo'] = ''
            df_fecha = df_fecha[['Fecha', 'Tipo', 'Ranking', 'Centro', 'Articulo', 'Carga_Dia', 'Media_Mensual', 'Total_Mes']]
            rankings_centros.append(df_fecha)
        
        rankings_articulos = []
        for fecha in media_por_articulo['Fecha'].unique():
            df_fecha = media_por_articulo[media_por_articulo['Fecha'] == fecha].copy()
            df_fecha = df_fecha.nlargest(15, 'Carga_Dia')
            df_fecha['Ranking'] = range(1, len(df_fecha) + 1)
            df_fecha['Tipo'] = 'Artículo'
            df_fecha['Centro'] = ''
            df_fecha = df_fecha.rename(columns={'Artículo': 'Articulo'})
            df_fecha = df_fecha[['Fecha', 'Tipo', 'Ranking', 'Centro', 'Articulo', 'Carga_Dia', 'Media_Mensual', 'Total_Mes']]
            rankings_articulos.append(df_fecha)
        
        if rankings_centros or rankings_articulos:
            df_rankings = pd.concat(rankings_centros + rankings_articulos, ignore_index=True)
            df_rankings = df_rankings.sort_values(['Fecha', 'Tipo', 'Ranking'])
            df_rankings.to_excel(writer, sheet_name='Rankings', index=False)
            ws_rankings = writer.sheets['Rankings']
            num_rows_r = len(df_rankings)
            num_cols_r = len(df_rankings.columns)
            if num_rows_r > 0:
                ws_rankings.add_table(0, 0, num_rows_r, num_cols_r - 1, {
                    'name': 'TablaRankings',
                    'style': 'Table Style Medium 6',
                    'columns': [{'header': col} for col in df_rankings.columns]
                })

def main():
    print("[PASO 1] Cargando datos...")
    df_unificado = cargar_y_procesar_archivos()
    if df_unificado.empty:
        print("[ERROR] No hay datos")
        return
    
    print("[PASO 2] Procesando KPIs...")
    media_por_centro, media_por_articulo, df_centro_articulo = calcular_analisis(df_unificado)
    
    print("[PASO 3] Exportando V2...")
    export_excel(media_por_centro, media_por_articulo, df_centro_articulo)
    print(f"[OK] Generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
