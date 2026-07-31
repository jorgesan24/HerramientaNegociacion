import os
import sqlite3
from pathlib import Path
import pandas as pd
import math

BASE_DIR = Path(__file__).parent
RUTA_DB = BASE_DIR / "data" / "herramienta_negociacion.db"

# ==============================================================
# 1. BUSCADOR COMPLEMENTARIO DE MEDICAMENTOS (SQLite)
# ==============================================================
def buscar_medicamentos(filtro, tipo_filtro):
    mapa_filtros = {
        "CUM": "CÓDIGO",
        "P. ACTIVO": "[P. ACTIVO]",
        "GRUPO TERAPEUTICO": "[GRUPO TERAPEUTICO]",
        "NIT": "NIT",
        "REGIONAL": "REGIONAL"
    }
    
    columna_sql = mapa_filtros.get(tipo_filtro, "CÓDIGO")
    
    # 1. EVITAR ROW_FACTORY GLOBAL: Conexión limpia y directa por tuplas en C
    conn = sqlite3.connect(RUTA_DB)
    cursor = conn.cursor()
    
    # Consulta plana agrupada veloz
    query = f"""
    SELECT CÓDIGO, [DESCRIPCIÓN], [P. ACTIVO], [GRUPO TERAPEUTICO], NIT, REGIONAL, FUENTE, VALOR
    FROM referencia
    WHERE {columna_sql} LIKE ?
    GROUP BY CÓDIGO
    ORDER BY [DESCRIPCIÓN] ASC
    LIMIT 200 -- LIMITANTE CLAVE: Evita colapsar la RAM si el filtro es muy genérico
    """
    cursor.execute(query, (f"%{filtro}%",))
    
    # 2. MAPEO VECTORIZADO RÁPIDO (Mucho más eficiente que dict(row) en millones de filas)
    columnas = [col[0] for col in cursor.description]
    resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    
    conn.close()
    return resultados

# ==============================================================
# 2. OBTENER DETALLE O RESUMEN PARA CARGAS DINÁMICAS
# ==============================================================
def obtener_resumen(codigo):
    if not codigo:
        return None
        
    codigo_str = str(codigo).strip()
    
    conn = sqlite3.connect(RUTA_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Intento 1: Buscar con el código completo tal cual viene (ej: '20023450-1')
    cursor.execute("SELECT * FROM referencia WHERE CÓDIGO = ? LIMIT 1", (codigo_str,))
    fila = cursor.fetchone()
    
    # Intento 2: Si no se encuentra y contiene un guion, busca por el prefijo base (ej: '20023450')
    if not fila and "-" in codigo_str:
        codigo_base = codigo_str.split("-")[0]
        cursor.execute("SELECT * FROM referencia WHERE CÓDIGO = ? LIMIT 1", (codigo_base,))
        fila = cursor.fetchone()
        
    conn.close()
    
    return dict(fila) if fila else None

# ==============================================================
# 3. DETALLE DE FACTURACIÓN
# ==============================================================
def obtener_detalle_facturacion(codigo):
    cabecera = obtener_resumen(codigo)

    agrupador = str(cabecera.get("AGRUPADOR", "")).strip()
    expediente = str(cabecera.get("EXPEDIENTE", "")).strip()

    conn = sqlite3.connect(RUTA_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if agrupador.upper() == "PENDIENTE" or not agrupador:
        cursor.execute("""
            SELECT
                NIT, OPERADOR, REGIONAL, CÓDIGO, EXPEDIENTE, 
                AGRUPADOR, DESCRIPCIÓN, CANTIDAD, VALOR, TOTAL, AÑO
            FROM referencia
            WHERE EXPEDIENTE = ? AND EXPEDIENTE IS NOT NULL AND EXPEDIENTE != ''
            ORDER BY AÑO DESC, OPERADOR
        """, (expediente,))
    else:
        cursor.execute("""
            SELECT
                NIT, OPERADOR, REGIONAL, CÓDIGO, EXPEDIENTE, 
                AGRUPADOR, DESCRIPCIÓN, CANTIDAD, VALOR, TOTAL, AÑO
            FROM referencia
            WHERE AGRUPADOR = ?
            ORDER BY AÑO DESC, OPERADOR
        """, (agrupador,))

    detalle = [dict(fila) for fila in cursor.fetchall()]
    conn.close()

    return {
        "cabecera": cabecera,
        "detalle": detalle
    }

# ==============================================================================
# 4. EXPORTADORES (Limpiado el duplicado que tenías al final)
# ==============================================================================
def generar_excel_negociacion(datos, encabezado, ruta_salida):
    from excel_exporter import generar_excel_negociacion as generar
    return generar(datos, encabezado, ruta_salida)