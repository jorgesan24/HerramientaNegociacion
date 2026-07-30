import os
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
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

def generar_excel_negociacion(datos, encabezado, ruta_salida):
    # 1. Asegurar directorios de salida
    carpeta_destino = Path(os.path.dirname(ruta_salida))
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    
    # 2. Cargar la plantilla base solo para modificar las celdas del encabezado
    wb = load_workbook(RUTA_PLANTILLA)
    ws = wb.active
    
    # Escribe los datos fijos del encabezado
    escribir_encabezado(ws, encabezado)
    
    # Guardamos los encabezados de forma temporal antes de inyectar la tabla masiva
    wb.save(ruta_salida)
    wb.close()
    
    # 3. PROCESAMIENTO OPTIMIZADO (Bajo consumo de RAM)
    columnas_ordenadas = [MAPEO_EXPORTACION[i] for i in sorted(MAPEO_EXPORTACION.keys())]
    df_filtrado = datos[columnas_ordenadas].copy()
    
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
    
    # 4. APLICACIÓN DE FORMATOS Y ESTILOS DE POST-PROCESAMIENTO
    # Volvemos a abrir el archivo generado para aplicar el diseño de celdas
    wb_final = load_workbook(ruta_salida)
    ws_final = wb_final.active
    
    aplicar_formatos(ws_final)
    ajustar_columnas(ws_final)
    configurar_impresion(ws_final)
    
    wb_final.save(ruta_salida)
    wb_final.close()
        
    return ruta_salida

# ==============================================================================
# FUNCIONES AUXILIARES DE ESTILIZADO DE DATOS (RECIÉN COMPLETADAS)
# ==============================================================================

def aplicar_formatos(ws):
    """
    Recorre las celdas escritas por Pandas a partir de la fila 13 para aplicar
    formatos de moneda, texto para CUM, alineaciones y bordes corporativos.
    """
    fuente_datos = Font(name='Calibri', size=11, bold=False, color='000000')
    
    # Alineaciones estándar
    align_centro = Alignment(horizontal='center', vertical='center')
    align_izquierda = Alignment(horizontal='left', vertical='center')
    align_derecha = Alignment(horizontal='right', vertical='center')
    
    # Bordes finos de color gris claro para delimitar las filas de datos
    borde_cuadrícula = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Iterar sobre las filas de la tabla (Fila 13 en adelante)
    for r_idx in range(13, ws.max_row + 1):
        ws.row_dimensions[r_idx].height = 20  # Altura cómoda de lectura por celda
        
        for col_idx, col_name in MAPEO_EXPORTACION.items():
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.font = fuente_datos
            cell.border = borde_cuadrícula

            # 1. CASO CRÍTICO: Blindaje estricto de Códigos CUM (con guiones), NIT o IDs
            if col_name in ["CODIGO", "CUM", "NIT"]:
                cell.number_format = '@'  # Fuerza a Excel a tratarlo como texto puro. Evita errores de guion
                cell.alignment = align_centro

            # 2. Caso Valores de Dinero / Moneda (Permite que sigan sumando en Excel nativo)
            elif "VALOR" in col_name or "PRECIO" in col_name or "REFERENCIA" in col_name or col_name in ["REGULACION", "NT", "PM"]:
                try:
                    if cell.value is not None and cell.value != "":
                        # Limpiar caracteres basura si vienen formateados como texto antes de convertirlos a número real
                        valor_limpio = str(cell.value).replace('$', '').replace('.', '').replace(',', '').strip()
                        cell.value = float(valor_limpio)
                except ValueError:
                    pass
                
                cell.number_format = '$#,##0'  # Formato moneda sin decimales
                cell.alignment = align_derecha

            # 3. Caso Desviaciones o Porcentajes
            elif "DESVIACION" in col_name or "PORCENTAJE" in col_name:
                try:
                    if cell.value is not None and cell.value != "":
                        valor_limpio = str(cell.value).replace(',', '.').strip()
                        cell.value = float(valor_limpio)
                except ValueError:
                    pass
                
                cell.number_format = '#,##0.00'  # Formato decimal con dos posiciones precisas
                cell.alignment = align_derecha

            # 4. Caso Textos Generales (DESCRIPCION, VALIDACION, ORIGEN)
            else:
                cell.alignment = align_izquierda

def ajustar_columnas(ws):
    """
    Escanea las columnas de la hoja para darles un ancho proporcional dinámico,
    evitando textos cortados o los molestos errores '###' de Excel.
    """
    for col in ws.columns:
        max_len = 0
        
        # CORRECCIÓN: Obtenemos la letra de la columna usando la primera celda de la tupla (col[0])
        col_letter = get_column_letter(col[0].column)
        
        # Analizar el largo de los textos a partir de la fila 12 (Títulos y datos)
        # Esto evita que el ancho del encabezado superior deforme las columnas de abajo
        for cell in col:
            if cell.row >= 12:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
        
        # Asignar el ancho óptimo más un margen de seguridad de 4 caracteres
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

def configurar_impresion(ws):
    """
    Configura la hoja de cálculo para que al imprimirla se ajuste de forma profesional.
    """
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE # Horizontal para tablas anchas
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER         # Tamaño Carta
