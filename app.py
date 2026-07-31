##app
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dir_temporal = os.path.join(BASE_DIR, "tmp_uploads")
os.makedirs(dir_temporal, exist_ok=True)

os.environ["TMPDIR"] = dir_temporal
os.environ["TEMP"] = dir_temporal
os.environ["TMP"] = dir_temporal

tempfile.tempdir = dir_temporal

from flask import Flask, render_template, request, send_file, session, flash, redirect, url_for

import pandas as pd
import io
import os
import math 
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import time
from helpers import formatear_tiempo
import numpy as np
import unicodedata
import sqlite3
from data_manager import obtener_detalle_facturacion
import urllib.parse
from flask import send_from_directory
from negociaciones_repository import inicializar_bd
from repository_manager import guardar_negociacion
import tempfile
from pathlib import Path
from archivo_service import guardar_archivo, obtener_hojas_excel, obtener_nombre_archivo


import data_manager

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# === CORREGIDO: Apuntar a la nueva base de datos SQLite y no al Excel viejo ===
RUTA_DB = os.path.join(BASE_DIR, "data", "herramienta_negociacion.db")

# Almacén temporal de negociaciones
cache_negociaciones = {}

app = Flask(__name__)
app.secret_key = "TuClaveSuperSecreta"

import tempfile

# Definir una carpeta temporal dentro de tu propio proyecto
dir_temporal = os.path.join(os.path.dirname(__file__), 'tmp_uploads')

@app.route("/")
def inicio():
     return render_template("index.html")

@app.route("/detalle/<string:cum>")
def detalle(cum):
    
    # Decodifica de forma segura caracteres o guiones provenientes de la URL
    cum_limpio = urllib.parse.unquote(cum)
    datos = obtener_detalle_facturacion(cum_limpio)

    if not datos:
        return "Medicamento no encontrado en el sistema de facturación", 404

    # Evalúa si la petición fue hecha con Fetch API (AJAX)
    es_modal = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    return render_template(
        "detalle.html",
        medicamento=datos["cabecera"],
        detalle=datos["detalle"],
        es_modal=es_modal
    )

# ==============================================================================
# VARIABLE GLOBAL EN RAM PARA ALTA VELOCIDAD
# ==============================================================================
LISTA_REGIONALES_ESTATICA = ["NACIONAL", "CENTRO ORIENTE", "BUCARAMANGA", "BOGOTA", "MEDELLIN", "BARRANQUILLA", "CALI"]

# ==============================================================================
# VISTA OPERATIVA DE CONSULTA DE REFERENCIA (CORREGIDA SINTAXIS)
# ==============================================================================
@app.route("/referencia", methods=["GET", "POST"])
def referencia():
    resultados = []
    detalle = None
    medicamento = None
    filtro = ""

    pagina = int(request.args.get("pagina", 1))
    registros_por_pagina = 15
    total_paginas = 1
    total_registros = 0

    titulo_principal = "Valor Referencia"
    acto_administrativo = "NA"
    valor_normativo = "NA"

    # 1. CAPTURA Y PROCESAMIENTO DE FILTROS (Unificado como 'tipo_filtro')
    if request.method == "POST":
        tipo_filtro = request.form.get("tipo_filtro", "CUM")
        if tipo_filtro == "REGIONAL":
            filtro = request.form.get("regional", "")
        else:
            filtro = request.form.get("filtro", "")
    else:
        tipo_filtro = request.args.get("tipo_filtro", "CUM")
        if tipo_filtro == "REGIONAL":
            filtro = request.args.get("regional", request.args.get("filtro", ""))
        else:
            filtro = request.args.get("filtro", "").strip()

    # 2. EJECUCIÓN DE BÚSQUEDA VECTORIZADA
    if filtro:
        resultados_completos = data_manager.buscar_medicamentos(filtro, tipo_filtro)
        total_registros = len(resultados_completos)
        total_paginas = max(1, math.ceil(total_registros / registros_por_pagina))

        inicio = (pagina - 1) * registros_por_pagina
        fin = inicio + registros_por_pagina
        resultados = resultados_completos[inicio:fin]

    # 3. EXTRAER RESUMEN DE DETALLES DE CUM SELECCIONADO
    codigo_seleccionado = request.args.get("codigo", "").strip()
    if codigo_seleccionado:
        detalle = data_manager.obtener_resumen(codigo_seleccionado)
        
        if detalle:
            for campo in ["VALOR REFERENCIA", "VALOR MAXIMO", "VALOR MINIMO", "VALOR PROMEDIO"]:
                valor = detalle.get(campo)
                if pd.notna(valor):
                    detalle[campo] = "$ {:,.0f}".format(float(valor)).replace(",", ".")

            titulo_principal = "Valor Referencia"
            acto_administrativo = "NA"
            valor_normativo = "NA"

            precio_regulacion = detalle.get("PRECIO REGULACION")
            nota_tecnica = detalle.get("NOTA TECNICA")

            # Casos normativos de visualización empresarial
            if pd.notna(precio_regulacion):
                titulo_principal = "Valor Regulación"
                acto_administrativo = detalle.get("FUENTE", "NA")
                valor_normativo = precio_regulacion
                if pd.notna(valor_normativo):
                    valor_normativo = "$ {:,.0f}".format(float(valor_normativo)).replace(",", ".")

            elif pd.notna(nota_tecnica):
                acto_administrativo = detalle.get("FUENTE", "NA")
                valor_normativo = nota_tecnica
                if pd.notna(valor_normativo):
                    valor_normativo = "$ {:,.0f}".format(float(valor_normativo)).replace(",", ".")

            medicamento = detalle
            filtro = filtro.strip()

    if filtro == "":
        resultados = []
        detalle = None
        medicamento = None
        total_registros = 0
        total_paginas = 1

    # 4. RETORNO LIMPIO HACIA JINJA2 (Corregidos 'tipo_filtro' y comas huérfanas)
    return render_template(
        "referencia/referencia.html",
        resultados=resultados,
        detalle=detalle,
        medicamento=medicamento,
        filtro=filtro,
        tipo_filtro=tipo_filtro,  # Enlaza perfecto con tu HTML y JavaScript
        titulo_principal=titulo_principal,
        acto_administrativo=acto_administrativo,
        valor_normativo=valor_normativo,
        regionales=LISTA_REGIONALES_ESTATICA,  # Cache RAM instantánea
        pagina=pagina,
        total_paginas=total_paginas,
        total_registros=total_registros
    )

def encontrar_encabezado(ruta, hoja):
    
    def limpiar(valor):
        valor = str(valor)
        valor = unicodedata.normalize("NFKD", valor) # Corregido NFKK a NFKD
        return valor.encode("ascii", "ignore").decode("utf-8").upper().strip()

    # OPTIMIZACIÓN: Leer únicamente las primeras 20 filas usando calamine
    df_preview = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=20, engine="calamine")
    
    fila_encontrada = None
    for i, fila in df_preview.iterrows():
        valores = [limpiar(x) for x in fila.tolist()]
        tiene_codigo = any("CODIGO" in x or "CUM" in x for x in valores)
        tiene_descripcion = any("DESCRIP" in x for x in valores)
        tiene_valor = any("VALOR" in x or "PRECIO" in x for x in valores)
        
        if tiene_codigo and tiene_descripcion and tiene_valor:
            fila_encontrada = i
            break
            
    if fila_encontrada is None:
        return None, None
        
    # Cargar los datos reales usando el motor optimizado
    datos = pd.read_excel(ruta, sheet_name=hoja, header=fila_encontrada, engine="calamine")
    return datos, fila_encontrada + 1

def normalizar_codigo(valor):

    if pd.isna(valor):
        return ""

    valor = str(valor).strip()

    if valor.endswith(".0"):
        valor = valor[:-2]

    return valor

def cruzar_referencia(datos, hoja, campo_codigo, campo_valor, nombre_resultado):
    from data_manager import RUTA_DB
    
    conn = sqlite3.connect(RUTA_DB)
    nombre_tabla = hoja.strip().lower().replace(" ", "_")
    
    # SOLUCIÓN: Agregados corchetes [...] alrededor de las variables para proteger los espacios
    query = f"SELECT [{campo_codigo}], [{campo_valor}] FROM {nombre_tabla}"
    
    tabla = pd.read_sql_query(query, conn)
    conn.close()
    
    datos = datos.merge(
        tabla,
        left_on="CODIGO",
        right_on=campo_codigo,
        how="left",
        suffixes=("", "_REF")
    )

    columna_merge = campo_valor

    if columna_merge in datos.columns:

        datos.rename(
            columns={
                columna_merge: nombre_resultado
            },
            inplace=True
        )

    # Si existe una columna duplicada del merge
    if f"{campo_valor}_REF" in datos.columns:

        datos.rename(
            columns={
                f"{campo_valor}_REF": nombre_resultado
            },
            inplace=True
        )

    # Si no hubo conflicto de nombres
    elif campo_valor in datos.columns:

        datos.rename(
            columns={
                campo_valor: nombre_resultado
            },
            inplace=True
        )

    datos.drop(
        columns=[campo_codigo],
        inplace=True,
        errors="ignore"
    )

    coincidencias = (
        datos[nombre_resultado]
        .notna()
        .sum()
    )

    return datos, coincidencias

def cargar_archivo_negociacion():

    archivo = request.files.get("archivo")

    if archivo is None or archivo.filename == "":
        return {
            "ok": False,
            "mensaje": "No se seleccionó ningún archivo."
        }

    try:

        print(guardar_archivo)
        print(guardar_archivo.__module__)
        print(guardar_archivo.__code__.co_filename)

        ruta = guardar_archivo(
            archivo,
            Path(dir_temporal)
        )

        hojas = obtener_hojas_excel(ruta)

        session["ruta_archivo"] = ruta
        session["archivo_nombre"] = archivo.filename
        session["hojas_excel"] = hojas

        return {
            "ok": True,
            "hojas": hojas,
            "archivo": archivo.filename
        }

    except Exception as e:

        app.logger.exception(e)

        return {
            "ok": False,
            "mensaje": str(e)
        }

# ==============================================================================
# VARIABLE GLOBAL O DE CONFIGURACIÓN DE KPIS
# ==============================================================================
FILTROS_KPI = {
    "aceptables": {"columna": "VALIDACION", "valores": ["ACEPTAR"]},
    "renegociar": {"columna": "VALIDACION", "valores": ["RENEGOCIAR"]},
    "duplicados": {"columna": "DUPLICADO", "valores": ["DUPLICADO"]},
    "activos": {
        "columna": "ESTADO REGISTRO",
        "valores": ["VIGENTE", "EN TRAMITE RENOV", "DROGA BLANCA", "PAÑALES", "APME", "MVND"]
    },
    "no_activos": {
        "columna": "ESTADO REGISTRO",
        "valores": [
            "VENCIDO", "NEGADO", "TEMP. NO COMERC - VIGENTE", "ABANDONO", 
            "TEMP. NO COMERCIALIZADO - EN TRÁMITE RENOV", "NO EXISTE", "REVOCADO", 
            "COMERCIALIZADO SOLO POR EXPORTACION", "SUSPENDIDO", "NO APLICA REGISTRO",
            "INACTIVO", "MUESTRA MEDICA", "DESISTIDO", "CANCELADO", "PERDIDA FUERZA EJEC"
        ]
    }
}

@app.route('/negociacion', methods=['GET'], endpoint='negociacion')
def negociacion_get():
    # ==========================================================================
    # CORRECCIÓN DE ORIGEN: SEGURA PARA COMPONENTES INTERNOS
    # ==========================================================================
    origen = request.referrer or ""
    
    # Solo limpiamos si el usuario viene de la raíz exacta del sistema o del index,
    # asegurando que si navega en /referencia, la memoria de negociación no se altere.
    if origen and (origen.endswith('/') or 'index' in origen):
        claves_a_borrar = [
            "hojas_excel", "ruta_archivo", "archivo_nombre", 
            "hoja_seleccionada", "id_proceso", "kpis", "tiempo_proceso"
        ]
        for clave in claves_a_borrar:
            session.pop(clave, None)

    # 1. Recuperar persistencia normal desde la sesión
    hojas = session.get("hojas_excel", [])
    ruta = session.get("ruta_archivo", "")
    nombre_archivo = session.get("archivo_nombre", "")
    hoja_seleccionada = session.get("hoja_seleccionada", "")
    id_proceso = session.get("id_proceso", "")
    tiempo_proceso = session.get("tiempo_proceso", None)
    kpis = session.get("kpis", None)

    # Variables por defecto para el renderizado
    datos = None
    tabla = None
    columnas = []
    total_registros = 0
    archivo_valido = False
    validaciones = session.pop("validaciones_flash", [])
    mensaje = request.args.get("mensaje", "")

    # 2. Si existe el proceso, recuperar de caché
    if id_proceso and id_proceso in cache_negociaciones:
        info_cache = cache_negociaciones[id_proceso]
        datos = info_cache.get("datos")
        ruta = info_cache.get("ruta", ruta)
        hoja_seleccionada = info_cache.get("hoja", hoja_seleccionada)
        
        if datos is not None:
            columnas = datos.columns.tolist()
            tabla = datos.to_dict(orient="records")
            total_registros = len(datos)
            archivo_valido = True

    # 3. Columnas visuales base si no hay datos procesados aún
    if not columnas:
        columnas = [
            "CODIGO", "DESCRIPCION", "VALOR OFERTADO", "REGULACION",
            "NT", "REFERENCIA", "PM", "VALOR OBJETIVO", "VALIDACION",
            "ESTADO REGISTRO", "DUPLICADO", "ORIGEN", "DESVIACION"
        ]

    # 4. Determinar dinámicamente el estado visual del panel de control
    estado_panel = "inicio"
    if nombre_archivo:
        estado_panel = "archivo"
    if hoja_seleccionada:
        estado_panel = "hoja"

    if tiempo_proceso is not None:
        tiempo_proceso = formatear_tiempo(tiempo_proceso)

    # 5. Datos por defecto del formulario de exportación (modal)
    datos_exportacion = session.get(
        "datos_exportacion",
        {
            "identificacion_representante": "", "nombre_representante": "", "nit": "",
            "proveedor": "", "ciudad": "", "sucursal": "", "codigo_sucursal": ""
        }
    )

    return render_template(
        "negociacion/negociacion.html",
        hojas=hojas,
        archivo=ruta,
        total_registros=total_registros,
        mensaje=mensaje,
        validaciones=validaciones,
        archivo_valido=archivo_valido,
        hoja_seleccionada=hoja_seleccionada,
        archivo_nombre=nombre_archivo,
        id_cache=id_proceso,
        estado_panel=estado_panel,
        kpis=kpis,
        columnas=columnas,
        tabla=tabla,
        filtros_kpi=FILTROS_KPI,
        tiempo_proceso=tiempo_proceso,
        datos_exportacion=datos_exportacion
    )

@app.route('/negociacion', methods=['POST'], endpoint='negociacion_procesar')
def negociacion_post():
    content_type = request.content_type or ""
    
    # --------------------------------------------------------------------------
    # CASO 1: CARGA INICIAL DEL ARCHIVO EXCEL (BLINDADO PARA MÓVILES)
    # --------------------------------------------------------------------------
    if content_type.startswith("multipart/form-data") and "archivo" in request.files:
        try:
            archivo = request.files.get("archivo")
            
            if archivo and archivo.filename != "":
                # Validación física para detectar accesos directos de nubes o archivos vacíos
                archivo.seek(0, os.SEEK_END)
                tamano_archivo = archivo.tell()
                archivo.seek(0)

                if tamano_archivo == 0:
                    msg = "❌ El archivo está vacío o es un acceso directo virtual de la nube. Por favor, descárgalo físicamente en tu celular."
                    return redirect(url_for('negociacion', mensaje=msg))

                ruta = guardar_archivo(archivo, UPLOAD_FOLDER)
                hojas = obtener_hojas_excel(ruta)
                nombre_archivo = obtener_nombre_archivo(ruta)

                # Persistir metadatos del archivo en la sesión
                session["ruta_archivo"] = ruta
                session["hojas_excel"] = hojas
                session["archivo_nombre"] = nombre_archivo
                
                # Resetear estados de procesos previos al cargar un nuevo libro
                session["hoja_seleccionada"] = ""
                session["id_proceso"] = ""
                session["kpis"] = None
                session["tiempo_proceso"] = None

            return redirect(url_for('negociacion'))

        except Exception as e:
            # Captura si el sistema operativo del celular corta la transferencia a mitad de camino
            import traceback
            traceback.print_exc()
            msg_error = "❌ Error de sincronización: El archivo de Google Drive no está disponible localmente en el celular."
            return redirect(url_for('negociacion', mensaje=msg_error))

    # --------------------------------------------------------------------------
    # CASO 2: PROCESAMIENTO DE LA HOJA SELECCIONADA (VERSION LIGERA PARA LA NUBE)
    # --------------------------------------------------------------------------
    if "hoja" in request.form:
        inicio_tiempo = time.perf_counter()
        ruta = request.form.get("archivo")
        hoja = request.form.get("hoja")
        
        if not ruta or not os.path.exists(ruta):
            return redirect(url_for('negociacion', mensaje="❌ La ruta del archivo expiró o no se encuentra en el servidor."))

        # Re-obtener datos estructurales de forma rápida
        hojas = obtener_hojas_excel(ruta)
        nombre_archivo = obtener_nombre_archivo(ruta)
        session["hoja_seleccionada"] = hoja

        validaciones = []

        try:
            datos, fila_encabezado = encontrar_encabezado(ruta, hoja)
            
            if datos is None or datos.empty:
                session["validaciones_flash"] = ["❌ No se encontraron registros o encabezados válidos."]
                return redirect(url_for('negociacion'))

            # SOLUCIÓN DE VELOCIDAD 1: Quedarnos estrictamente con las primeras columnas y limpiar en un solo paso
            # En lugar de usar expresiones regulares pesadas que activan el Harakiri, cortamos el DataFrame
            datos = datos.dropna(how="all") # Eliminar filas totalmente vacías de inmediato
            
            # Asegurar que todas las columnas sean texto limpio en mayúsculas
            datos.columns = [str(col).strip().upper() for col in datos.columns]
            columnas = list(datos.columns)

            if len(columnas) < 3:
                session["validaciones_flash"] = ["❌ La hoja debe tener mínimo 3 columnas operativas."]
                return redirect(url_for('negociacion'))

            # SOLUCIÓN DE VELOCIDAD 2: Renombrado directo por posición (Evita indexación lenta)
            datos.rename(
                columns={
                    columnas[0]: "CODIGO",
                    columnas[1]: "DESCRIPCION",
                    columnas[2]: "VALOR OFERTADO"
                },
                inplace=True
            )

            # Validar tipo numérico sin generar bucles
            valor_num = pd.to_numeric(datos["VALOR OFERTADO"], errors="coerce")
            if valor_num.notna().mean() < 0.60: # Bajamos levemente el umbral por compatibilidad móvil
                session["validaciones_flash"] = ["❌ La columna de 'Valor Ofertado' no contiene suficientes números válidos."]
                return redirect(url_for('negociacion'))

            # Sanitización veloz de llaves
            datos["CODIGO"] = datos["CODIGO"].fillna("").astype(str).str.strip()
            datos["DESCRIPCION"] = datos["DESCRIPCION"].fillna("").astype(str).str.strip()
            datos = datos[~((datos["CODIGO"] == "") & (datos["DESCRIPCION"] == ""))]
            datos.reset_index(drop=True, inplace=True)

            validaciones.append(f"✔ Encabezados encontrados en fila: {fila_encabezado}")
            validaciones.append(f"✔ Registros encontrados: {len(datos):,}")

            # --- Fase de Cruces de Información SQL de Referencia ---
            cruces = [
                ("Regulados", "CUM", "Valor UMD con Intermediacion sin decimales", "REGULACION"),
                ("NT", "Codigo", "Valor Referencia UMD", "NT"),
                ("PM", "CUM", "VMR UMD 2026", "PM"),
                ("Tarifario", "CUM", "VALOR", "REFERENCIA"),
                ("INVIMA", "CUM", "Estado Registro", "ESTADO REGISTRO")
            ]

            # Detección interna de registros duplicados internos
            duplicados = datos.duplicated(subset="CODIGO", keep=False)
            datos["DUPLICADO"] = ""
            datos.loc[duplicados, "DUPLICADO"] = "DUPLICADO"

            for hoja_ref, campo_cod, campo_valor, nombre_res in cruces:
                datos, coincidencias = cruzar_referencia(datos, hoja_ref, campo_cod, campo_valor, nombre_res)
                validaciones.append(f"✔ {nombre_res}: {coincidencias:,}")

            # Construcción lógica del valor objetivo comercial
            datos = construir_valor_objetivo(datos)
            datos = ordenar_columnas(datos)

            # --- Formateo Visual de Variables de Salida ---
            for col in ["VALOR OFERTADO", "VALOR OBJETIVO"]:
                if col in datos.columns:
                    datos[col] = pd.to_numeric(datos[col], errors="coerce").map(
                        lambda x: "" if pd.isna(x) else f"{x:,.0f}".replace(",", ".")
                    )

            for col in ["REGULACION", "NT", "REFERENCIA", "PM"]:
                if col in datos.columns:
                    datos[col] = pd.to_numeric(datos[col], errors="coerce").map(
                        lambda x: "" if pd.isna(x) else str(int(x))
                    )

            if "DESVIACION" in datos.columns:
                datos["DESVIACION"] = pd.to_numeric(datos["DESVIACION"], errors="coerce").map(
                    lambda x: "" if pd.isna(x) else (
                        f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    )
                )

            # --- Construcción Dinámica del Diccionario KPI ---
            def construir_kpis(df):
                kpis_locales = {}
                for key_nombre, config in FILTROS_KPI.items():
                    col_busqueda = config["columna"]
                    serie = df[col_busqueda].fillna("").astype(str).str.upper().str.strip()
                    kpis_locales[key_nombre] = int(serie.isin(config["valores"]).sum())

                kpis_locales["registros"] = len(df)
                cubiertos = df[["REGULACION", "NT", "PM", "REFERENCIA"]].notna().any(axis=1)
                kpis_locales["cobertura"] = float(round(cubiertos.mean() * 100, 1))
                kpis_locales["fecha"] = datetime.now().strftime("%d/%m/%Y")
                return kpis_locales

            kpis = construir_kpis(datos)

            # Convertir los números de los KPIs a Strings legibles para el frontend
            for campo in list(kpis.keys()):
                valor_kpi = kpis[campo]
                if isinstance(valor_kpi, (int, float)):
                    if campo == "cobertura":
                        kpis[campo] = f"{valor_kpi:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + "%"
                    else:
                        kpis[campo] = f"{valor_kpi:,.0f}".replace(",", ".")

            session["kpis"] = kpis

            # --- Guardado Seguro de Estado de Ejecución ---
            fin_tiempo = time.perf_counter()
            session["tiempo_proceso"] = round(fin_tiempo - inicio_tiempo, 2)
            
            id_proceso = str(uuid.uuid4())
            cache_negociaciones[id_proceso] = {
                "datos": datos.copy(),
                "archivo": os.path.basename(ruta),
                "ruta": ruta,
                "hoja": hoja
            }
            session["id_proceso"] = id_proceso
            session["validaciones_flash"] = validaciones

        except Exception as e:
            import traceback
            traceback.print_exc()
            session["id_proceso"] = ""
            session["kpis"] = None
            session["tiempo_proceso"] = None
            session["validaciones_flash"] = [
                "❌ El archivo es incompatible con SANEM.",
                "Revise que contenga un Código CUM y un Valor Ofertado válidos."
            ]
            return redirect(url_for('negociacion', mensaje="El archivo no pudo procesarse porque no cumple con la estructura esperada por SANEM."))

        return redirect(url_for('negociacion'))

    return redirect(url_for('negociacion'))


def construir_valor_objetivo(datos):

    if datos is None:
        raise Exception("datos llegó como None")    

    valor_objetivo = []
    origen = []
    desviacion = []
    validacion = []

    for _, fila in datos.iterrows():

        # -----------------------------------------------------------
        # Conversión Numérica Segura (Previene el error TypeError)
        # -----------------------------------------------------------
        # pd.to_numeric con errors='coerce' convierte texto inválido o vacío en NaN (nulo)
        ofertado = pd.to_numeric(fila.get("VALOR OFERTADO"), errors='coerce')
        regulacion = pd.to_numeric(fila.get("REGULACION"), errors='coerce')
        nt = pd.to_numeric(fila.get("NT"), errors='coerce')
        pm = pd.to_numeric(fila.get("PM"), errors='coerce')
        referencia = pd.to_numeric(fila.get("REFERENCIA"), errors='coerce')

        # Si el valor ofertado no es un número válido, no se puede procesar la fila
        if pd.isna(ofertado):
            valor_objetivo.append(None)
            origen.append("VALOR OFERTADO INVÁLIDO")
            desviacion.append(None)
            validacion.append("REVISAR")
            continue

        # -------------------------
        # Determinar valor objetivo
        # -------------------------
        if pd.notna(regulacion):
            if ofertado < regulacion:
                objetivo = ofertado
                origen_obj = "OPCIÓN EPS SANITAS"
            else:
                objetivo = regulacion
                origen_obj = "REGULACIÓN"

        elif pd.notna(nt):
            objetivo = nt
            origen_obj = "NT"

        elif pd.notna(pm):
            objetivo = pm
            origen_obj = "PM"

        elif pd.notna(referencia):
            objetivo = referencia
            origen_obj = "REFERENCIA"

        else:
            objetivo = ofertado
            origen_obj = "OPCIÓN EPS SANITAS"

        # -------------------------
        # Desviación (Validación matemática limpia)
        # -------------------------
        if pd.notna(objetivo) and objetivo > 0:
            des = (ofertado - objetivo) / objetivo
        else:
            des = None

        # -------------------------
        # Validación
        # -------------------------
        if pd.notna(objetivo) and ofertado <= objetivo:
            estado = "ACEPTAR"
        else:
            estado = "RENEGOCIAR"

        valor_objetivo.append(objetivo)
        origen.append(origen_obj)
        desviacion.append(des)
        validacion.append(estado)

    # Inyección final de resultados al DataFrame
    datos["VALOR OBJETIVO"] = valor_objetivo
    datos["ORIGEN"] = origen
    datos["DESVIACION"] = desviacion
    datos["VALIDACION"] = validacion

    return datos

def ordenar_columnas(datos):
    # Orden deseado
    orden = [
        "CODIGO",
        "DESCRIPCION",
        "VALOR OFERTADO",
        "REGULACION",
        "NT",
        "REFERENCIA",
        "PM",
        "VALOR OBJETIVO",
        "VALIDACION",
        "ESTADO REGISTRO",
        "DUPLICADO",
        "ORIGEN",
        "DESVIACION"
    ]

    # Mantener solo las que existan
    orden = [c for c in orden if c in datos.columns]

    # Agregar al final cualquier columna adicional
    restantes = [c for c in datos.columns if c not in orden]

    datos = datos[orden + restantes]

    return datos

@app.route("/exportar")
def exportar():

    filtro = request.args.get(
        "filtro",
        ""
    )

    tipo_filtro = request.args.get(
        "tipo_filtro",
        "CUM"
    )

    if filtro:

        resultados = data_manager.buscar_medicamentos(
            filtro,
            tipo_filtro
        )

    else:

        resultados = []

    df = pd.DataFrame(resultados)

    archivo = io.BytesIO()

    with pd.ExcelWriter(
        archivo,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Referencia"
        )

    archivo.seek(0)

    return send_file(
        archivo,
        as_attachment=True,
        download_name="Referencia.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/exportar_negociacion", methods=["POST"])
def exportar_negociacion():

    id_cache = request.form["id_cache"]

    info = cache_negociaciones[id_cache]

    datos = info["datos"]

    nombre_archivo = info["archivo"]

    nombre_salida = (
        os.path.splitext(nombre_archivo)[0]
        + "_Negociado.xlsx"
    )

    # ============================
    # Datos capturados del modal
    # ============================

    encabezado = {

        "fecha_inicio":
            request.form.get("fecha_inicio", ""),
        
        "forma_contratacion":
            request.form.get("forma_contratacion", ""),

        "tipo_atencion":
            request.form.getlist("tipo_atencion"),

        "plan":
            request.form.getlist("plan"),

        "identificacion_representante":
            request.form.get("identificacion_representante", ""),

        "nombre_representante":
            request.form.get("nombre_representante", ""),

        "nit":
            request.form.get("nit", ""),

        "proveedor":
            request.form.get("proveedor", ""),

        "ciudad":
            request.form.get("ciudad", ""),

        "sucursal":
            request.form.get("sucursal", ""),

        "codigo_sucursal":
            request.form.get("codigo_sucursal", ""),

        "plan_otro":
            request.form.get("plan_otro", "")

    }

    # Guardar para la siguiente exportación

    session["datos_exportacion"] = encabezado

    ruta_salida = os.path.join(
        UPLOAD_FOLDER,
        nombre_salida
    )

    consecutivo = guardar_negociacion(
        encabezado,
        datos
    )

    ruta = data_manager.generar_excel_negociacion(
        datos,
        encabezado,
        ruta_salida
    )

    return send_file(
        ruta,
        as_attachment=True,
        download_name=nombre_salida
    )

MENU = [
    {
        "titulo": "Inicio",
        "icono": "🏠",
        "endpoint": "inicio"
    },
    {
        "titulo": "Tabla de Referencia",
        "icono": "📊",
        "endpoint": "referencia"
    },
    {
        "titulo": "Tabla de Negociación",
        "icono": "🤝",
        "endpoint": "negociacion"
    },
    {
        "titulo": "Descargas",
        "icono": "📥",
        "endpoint": "descargas"
    }
]

@app.route("/descargas")
def descargas():
    # Ruta física hacia la carpeta de descargas dentro de static
    carpeta_descargas = os.path.join(app.root_path, 'static', 'descargas')
    
    # Mapeo exacto de los nombres de tus archivos reales en el servidor
    archivos_sistema = {
        "malla_invima": "malla_invima.xlsx",
        "malla_regulacion": "malla_regulacion_consolidado.xlsx",
        "instructivo": "instructivo_herramienta_negociacion_2026.pdf",
        "video_tutorial": "herramienta_negociacion_web.mp4"
    }
    
    fechas = {}
    
    # Función para extraer de forma segura la fecha de última modificación de cada archivo
    def obtener_fecha_archivo(nombre_archivo):
        ruta_completa = os.path.join(carpeta_descargas, nombre_archivo)
        if os.path.exists(ruta_completa):
            timestamp = os.path.getmtime(ruta_completa)
            # Formato corporativo: Día/Mes/Año - Hora:Minutos
            return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y - %I:%M %p')
        return "Pendiente de carga"

    # Calculamos de forma dinámica la fecha para cada elemento
    for clave, nombre_real in archivos_sistema.items():
        fechas[clave] = obtener_fecha_archivo(nombre_real)

    return render_template(
        "descargas/descargas.html", 
        fechas=fechas,
        archivos=archivos_sistema
    )

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static", "img"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )

@app.route("/test_favicon")
def test_favicon():
    ruta = os.path.join(app.root_path, "static", "img", "favicon.ico")
    return {
        "existe": os.path.exists(ruta),
        "ruta": ruta
    }

@app.context_processor
def inject_menu():
    return dict(
        menu=MENU,
        endpoint_actual=request.endpoint
    )

app = app

if __name__ == "__main__":
    # La base de datos ahora se inicializa una sola vez al encender el servidor
    from negociaciones_repository import inicializar_bd
    inicializar_bd()
    
    app.run(debug=True, use_reloader=False)