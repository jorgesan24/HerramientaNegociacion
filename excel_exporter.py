import os
from pathlib import Path
from openpyxl import load_workbook
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RUTA_PLANTILLA = BASE_DIR / "data" / "plantilla_negociacion.xlsx"

MAPEO_EXPORTACION = {
    1: "CODIGO",
    2: "DESCRIPCION",
    3: "VALOR OFERTADO",
    4: "REGULACION",
    5: "NT",
    6: "REFERENCIA",
    7: "PM",
    8: "VALOR OBJETIVO",
    9: "VALIDACION",
    10: "ESTADO REGISTRO",  # antes INVIMA
    11: "DUPLICADO",
    12: "ORIGEN",           # antes ORIGEN OBJETIVO
    13: "DESVIACION"
}

CAMPOS_ENCABEZADO = {
    # Datos proveedor
    "C8": "identificacion_representante",
    "F8": "nombre_representante",
    "C9": "nit",
    "F9": "proveedor",
    "C10": "ciudad",
    "F10": "sucursal",
    "L10": "codigo_sucursal",
    # Datos contrato
    "J2": "fecha_inicio",
    "E5": "plan_otro",
    "I5": "forma_contratacion"
}

TIPO_ATENCION = {
    "AMBULATORIA": "D3",
    "DOMICILIARIA": "F3",
    "HOSPITALIZACIÓN": "I3",
    "HOSPITALIZACION": "I3",
    "URGENCIAS": "L3"
}

PLAN_CELDAS = {
    "POS CONTRIBUTIVO": "D4",
    "POS SUBSIDIADO": "F4",
    "PLAN EMPRESARIAL": "I4",
    "PLAN PREMIUM": "L4",
}

def marcar_tipo_atencion(ws, encabezado):
    tipos = encabezado.get("tipo_atencion", [])
    if isinstance(tipos, str):
        tipos = [tipos]
    for tipo in tipos:
        tipo = tipo.upper()
        if tipo in TIPO_ATENCION:
            ws[TIPO_ATENCION[tipo]] = "X"

def marcar_plan(ws, encabezado):
    planes = encabezado.get("plan", [])
    if isinstance(planes, str):
        planes = [planes]
    for plan in planes:
        plan = plan.upper()
        if plan in PLAN_CELDAS:
            ws[PLAN_CELDAS[plan]] = "X"
            
    if "OTRO" in [p.upper() for p in planes]:
        ws["D5"] = "X"
        ws["E5"] = encabezado.get("plan_otro", "")

def escribir_encabezado(ws, encabezado):
    for celda, campo in CAMPOS_ENCABEZADO.items():
        ws[celda] = encabezado.get(campo, "")
    marcar_tipo_atencion(ws, encabezado)
    marcar_plan(ws, encabezado)

def escribir_tabla(ws, datos):
    fila_excel = 13
    # CORREGIDO: Desempaquetado correcto de tupla (idx, registro) para evitar ValueError
    for idx, registro in datos.iterrows():
        for columna_excel, columna_df in MAPEO_EXPORTACION.items():
            # CORREGIDO: Sintaxis limpia y uso seguro de .get() sobre la serie de Pandas
            valor = registro.get(columna_df, "")
            ws.cell(row=fila_excel, column=columna_excel, value=valor)
        fila_excel += 1

from openpyxl import load_workbook
import pandas as pd

def generar_excel_negociacion(datos, encabezado, ruta_salida):
    # 1. Asegurar directorios de salida
    carpeta_destino = Path(os.path.dirname(ruta_salida))
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    
    # 2. Cargar la plantilla base solo para modificar las celdas del encabezado
    wb = load_workbook(RUTA_PLANTILLA)
    ws = wb.active
    
    # Escribe los datos fijos del encabezado (Consume poca RAM)
    escribir_encabezado(ws, encabezado)
    
    # Guardamos los encabezados de forma temporal antes de inyectar la tabla masiva
    wb.save(ruta_salida)
    wb.close()
    
    # 3. PROCESAMIENTO OPTIMIZADO (Bajo consumo de RAM): 
    # Mapeamos las columnas del DataFrame de datos exactamente como las necesitas
    columnas_ordenadas = [MAPEO_EXPORTACION[i] for i in sorted(MAPEO_EXPORTACION.keys())]
    df_filtrado = datos[columnas_ordenadas]
    
    # Usamos Pandas con el motor de openpyxl para volcar la tabla en bloque a partir de la fila 13
    with pd.ExcelWriter(ruta_salida, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
        df_filtrado.to_excel(
            writer, 
            sheet_name=writer.sheets[ws.title].title, 
            startrow=12,    # Fila 13 en Excel (indexado en 0)
            startcol=0,     # Columna A
            header=False,   # No sobreescribir con los nombres técnicos de columnas
            index=False     # No agregar una columna de índices numéricos
        )
        
    return ruta_salida

def aplicar_formatos(ws):
    pass

def ajustar_columnas(ws):
    pass

def configurar_impresion(ws):
    pass
