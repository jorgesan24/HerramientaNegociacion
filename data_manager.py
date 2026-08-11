import os
import sqlite3
from pathlib import Path
import pandas as pd
import math

BASE_DIR = Path(__file__).parent
RUTA_DB = BASE_DIR / "data" / "herramienta_negociacion.db"

# ==============================================================================
# CONEXIÓN COMPATIBLE CON VERCEL SERVERLESS (MODO SOLO LECTURA SEGURO)
# ==============================================================================
# Truco técnico: En Vercel pasamos la URI de solo lectura para evitar el crash 500
try:
    # Intenta abrir el archivo como una URI de lectura pura (Requerido por Vercel)
    ruta_uri = f"file:{RUTA_DB}?mode=ro"
    _CONN_GLOBAL = sqlite3.connect(ruta_uri, uri=True, check_same_thread=False)
    
    # Optimizaciones de pura lectura en RAM (Quitamos WAL y escrituras de disco)
    _CUR_INIT = _CONN_GLOBAL.cursor()
    _CUR_INIT.execute("PRAGMA cache_size = -20000;")  # 20MB de caché RAM para el buscador
    _CUR_INIT.execute("PRAGMA temp_store = MEMORY;")  # Tablas de ordenamiento directo a la RAM
    _CUR_INIT.close()
    print("SANEM: Conexión persistente de solo lectura inicializada en la nube con éxito.")

except sqlite3.OperationalError:
    # Fallback de respaldo por si lo pruebas localmente en Windows y no reconoce la URI
    _CONN_GLOBAL = sqlite3.connect(RUTA_DB, check_same_thread=False)

# ==============================================================================
# 1. BUSCADOR COMPLEMENTARIO DE MEDICAMENTOS (OPTIMIZADO)
# ==============================================================================
def buscar_medicamentos(filtro, tipo_filtro):
    mapa_filtros = {
        "CUM": "CÓDIGO",
        "P. ACTIVO": "[P. ACTIVO]",
        "GRUPO TERAPEUTICO": "[GRUPO TERAPEUTICO]",
        "NIT": "NIT",
        "REGIONAL": "REGIONAL"
    }
    
    columna_sql = mapa_filtros.get(tipo_filtro, "CÓDIGO")
    cursor = _CONN_GLOBAL.cursor()
    
    # Agregamos MAX() a los campos de texto para forzar a SQLite a traer 
    # el valor más completo disponible en lugar de celdas vacías o nulas.
    query = f"""
    SELECT 
        CÓDIGO, 
        MAX([DESCRIPCIÓN]) AS [DESCRIPCIÓN], 
        MAX([P. ACTIVO]) AS [P. ACTIVO], 
        MAX([GRUPO TERAPEUTICO]) AS [GRUPO TERAPEUTICO], 
        MAX(NIT) AS NIT, 
        MAX(REGIONAL) AS REGIONAL, 
        MAX(FUENTE) AS FUENTE, 
        MAX(VALOR) AS VALOR,
        MAX([DESCRIPCIÓN INVIMA]) AS [DESCRIPCIÓN INVIMA],
        MAX(COBERTURA) AS COBERTURA,
        MAX([ESTADO INVIMA]) AS [ESTADO INVIMA]
    FROM referencia
    WHERE {columna_sql} LIKE ?
    GROUP BY CÓDIGO
    ORDER BY [DESCRIPCIÓN] ASC
    LIMIT 200
    """
    cursor.execute(query, (f"%{filtro}%",))
    
    columnas = [col[0] for col in cursor.description]
    resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    cursor.close()
    
    return resultados

# ==============================================================================
# 2. OBTENER DETALLE O RESUMEN PARA CARGAS DINÁMICAS (CAMPOS EXPLÍCITOS)
# ==============================================================================
def obtener_resumen(codigo):
    if not codigo:
        return None
        
    codigo_str = str(codigo).strip()
    cursor = _CONN_GLOBAL.cursor()
    
    # OPTIMIZACIÓN: Seleccionamos los campos explícitos requeridos por tu app.py y las alertas
    campos = "CÓDIGO, [DESCRIPCIÓN], [VALOR REFERENCIA], [VALOR MAXIMO], [VALOR MINIMO], [VALOR PROMEDIO], [PRECIO REGULACION], [NOTA TECNICA], FUENTE, AGRUPADOR, EXPEDIENTE"
    
    cursor.execute(f"SELECT {campos} FROM referencia WHERE CÓDIGO = ? LIMIT 1", (codigo_str,))
    fila = cursor.fetchone()
    
    if not fila and "-" in codigo_str:
        codigo_base = codigo_str.split("-")[0]
        cursor.execute(f"SELECT {campos} FROM referencia WHERE CÓDIGO = ? LIMIT 1", (codigo_base,))
        fila = cursor.fetchone()
        
    if fila:
        columnas = [col[0] for col in cursor.description]
        resultado = dict(zip(columnas, fila))
    else:
        resultado = None
        
    cursor.close()
    return resultado

# ==============================================================================
# 3. DETALLE DE FACTURACIÓN (OPTIMIZADO EN MEMORIA)
# ==============================================================================
def obtener_detalle_facturacion(codigo):
    cabecera = obtener_resumen(codigo)
    if not cabecera:
        return {"cabecera": None, "detalle": []}

    agrupador = str(cabecera.get("AGRUPADOR", "")).strip()
    expediente = str(cabecera.get("EXPEDIENTE", "")).strip()
    cursor = _CONN_GLOBAL.cursor()

    campos_query = "NIT, OPERADOR, REGIONAL, CÓDIGO, EXPEDIENTE, AGRUPADOR, [DESCRIPCIÓN], CANTIDAD, VALOR, TOTAL, AÑO"

    if agrupador.upper() == "PENDIENTE" or not agrupador:
        cursor.execute(f"""
            SELECT {campos_query}
            FROM referencia
            WHERE EXPEDIENTE = ? AND EXPEDIENTE IS NOT NULL AND EXPEDIENTE != ''
            ORDER BY AÑO DESC, OPERADOR
            LIMIT 500 -- Evita congelar el navegador inyectando demasiadas filas al modal HTML
        """, (expediente,))
    else:
        cursor.execute(f"""
            SELECT {campos_query}
            FROM referencia
            WHERE AGRUPADOR = ?
            ORDER BY AÑO DESC, OPERADOR
            LIMIT 500
        """, (agrupador,))

    columnas = [col[0] for col in cursor.description]
    detalle = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()

    return {
        "cabecera": cabecera,
        "detalle": detalle
    }

# ==============================================================================
# 4. EXPORTADORES
# ==============================================================================
def generar_excel_negociacion(datos, encabezado, ruta_salida):
    from excel_exporter import generar_excel_negociacion as generar
    return generar(datos, encabezado, ruta_salida)