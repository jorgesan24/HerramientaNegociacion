##app
from flask import Flask, render_template, request, send_file, session
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

from services.archivo_service import (
    guardar_archivo,
    obtener_hojas_excel,
    obtener_nombre_archivo
)

import data_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# === CORREGIDO: Apuntar a la nueva base de datos SQLite y no al Excel viejo ===
RUTA_DB = os.path.join(BASE_DIR, "data", "herramienta_negociacion.db")

# Almacén temporal de negociaciones
cache_negociaciones = {}

app = Flask(__name__)
app.secret_key = "TuClaveSuperSecreta"


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

@app.route("/referencia", methods=["GET", "POST"])
def referencia():

    resultados = []
    detalle = None
    medicamento=None
    filtro = ""

    pagina = int(
        request.args.get(
            "pagina",
            1
        )
    )

    registros_por_pagina = 15

    total_paginas = 1
    total_registros = 0

    registros_por_pagina = 15

    titulo_principal = "Valor Referencia"
    acto_administrativo = "NA"
    valor_normativo = "NA"

    if request.method == "POST":

        tipo_filtro = request.form.get(
            "tipo_filtro",
            "CUM"
        )

        if tipo_filtro == "REGIONAL":

            filtro = request.form.get(
                "regional",
                ""
            )

        else:

            filtro = request.form.get(
                "filtro",
                ""
            )

    else:

        tipo_filtro = request.args.get(
            "tipo_filtro",
            "CUM"
        )

        if tipo_filtro == "REGIONAL":

            filtro = request.args.get(
                "regional",
                request.args.get("filtro", "")
            )

        else:

            filtro = request.args.get(
                "filtro",
                ""
            ).strip()

    if filtro:

        resultados_completos = data_manager.buscar_medicamentos(
            filtro,
            tipo_filtro
        )

        total_registros = len(
            resultados_completos
        )

        total_paginas = max(
            1,
            math.ceil(
                total_registros /
                registros_por_pagina
            )
        )

        inicio = (
            pagina - 1
        ) * registros_por_pagina

        fin = inicio + registros_por_pagina

        resultados = resultados_completos[
            inicio:fin
        ]

    codigo_seleccionado = request.args.get(
        "codigo",
        ""
    ).strip()

    if codigo_seleccionado:

        detalle = data_manager.obtener_resumen(
            codigo_seleccionado
        )

        if detalle:

            for campo in [
                "VALOR REFERENCIA",
                "VALOR MAXIMO",
                "VALOR MINIMO",
                "VALOR PROMEDIO"
            ]:

                valor = detalle.get(campo)

                if pd.notna(valor):

                    detalle[campo] = (
                        "$ {:,.0f}"
                        .format(float(valor))
                        .replace(",", ".")
                    )

        titulo_principal = "Valor Referencia"
        acto_administrativo = "NA"
        valor_normativo = "NA"

        precio_regulacion = detalle.get(
            "PRECIO REGULACION"
        )

        nota_tecnica = detalle.get(
            "NOTA TECNICA"
        )

        # Caso 1 y 2
        if pd.notna(precio_regulacion):

            titulo_principal = "Valor Regulación"

            acto_administrativo = detalle.get(
                "FUENTE",
                "NA"
            )

            valor_normativo = precio_regulacion

            if pd.notna(valor_normativo):

                valor_normativo = (
                    "$ {:,.0f}"
                    .format(float(valor_normativo))
                    .replace(",", ".")
                )

        # Caso 3
        elif pd.notna(nota_tecnica):

            acto_administrativo = detalle.get(
                "FUENTE",
                "NA"
            )

            valor_normativo = nota_tecnica

            if pd.notna(valor_normativo):

                valor_normativo = (
                    "$ {:,.0f}"
                    .format(float(valor_normativo))
                    .replace(",", ".")
                )

        # Caso 4
        # Se dejan los valores por defecto

        medicamento = detalle

        filtro = filtro.strip()

    if filtro == "":

        resultados = []
        detalle = None
        medicamento = None

        total_registros = 0
        total_paginas = 1

    return render_template(
        "referencia/referencia.html",
        resultados=resultados,
        detalle=detalle,
        medicamento=medicamento,
        filtro=filtro,
        tipo_filtro=tipo_filtro,
        titulo_principal=titulo_principal,
        acto_administrativo=acto_administrativo,
        valor_normativo=valor_normativo,
        regionales=data_manager.obtener_regionales(),
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

@app.route("/negociacion", methods=["GET", "POST"])
def negociacion():

    hojas = []
    datos = None
    mensaje = ""

    validaciones = []
    archivo_valido = False

    total_registros = 0

    ruta = ""

    hoja_seleccionada = ""

    tiempo_proceso = None
    nombre_archivo = ""
    id_cache = "" 

    kpis = None

    tabla = None

    FILTROS_KPI = {
        "aceptables": {
            "columna": "VALIDACION",
            "valores": ["ACEPTAR"]
        },

        "renegociar": {
            "columna": "VALIDACION",
            "valores": ["RENEGOCIAR"]
        },

        "duplicados": {
            "columna": "DUPLICADO",
            "valores": ["DUPLICADO"]
        },

        "activos": {
            "columna": "ESTADO REGISTRO",
            "valores": [
                "VIGENTE",
                "EN TRAMITE RENOV",
                "DROGA BLANCA",
                "PAÑALES",
                "APME",
                "MVND"
            ]
        },

        "no_activos": {
            "columna": "ESTADO REGISTRO",
            "valores": [
            "VENCIDO", 
            "NEGADO", 
            "TEMP. NO COMERC - VIGENTE", 
            "ABANDONO", 
            "TEMP. NO COMERCIALIZADO - EN TRÁMITE RENOV", 
            "NO EXISTE", 
            "REVOCADO", 
            "COMERCIALIZADO SOLO POR EXPORTACION", 
            "SUSPENDIDO", 
            "NO APLICA REGISTRO",
            "INACTIVO",
            "MUESTRA MEDICA",
            "DESISTIDO",
            "CANCELADO",
            "PERDIDA FUERZA EJEC"
            ]
        }
    }

    if request.method == "POST":

        # ==============================
        # CASO 1:
        # CARGA DEL ARCHIVO
        # ==============================

        # Cargar archivo
        if "archivo" in request.files:
            archivo = request.files["archivo"]

            if archivo.filename != "":
                # 1. VALIDACIÓN EXTRA PARA CELULARES:
                # Comprobar si el archivo está vacío o es un acceso virtual (0 bytes)
                archivo.seek(0, os.SEEK_END)
                tamano_archivo = archivo.tell()
                archivo.seek(0) # Resetear el puntero para poder guardarlo después

                if tamano_archivo == 0:
                    mensaje = "❌ El archivo está vacío o es un acceso directo virtual de la nube. Por favor, descárgalo físicamente en la memoria de tu celular antes de subirlo."
                    # Retornamos de inmediato la vista enviando el mensaje de error
                    return render_template(
                        "inicio/index.html", # Cambia por la ruta exacta de tu template si es diferente
                        hojas=hojas,
                        datos=datos,
                        mensaje=mensaje,
                        validaciones=validaciones,
                        archivo_valido=archivo_valido,
                        total_registros=total_registros,
                        ruta=ruta,
                        hoja_seleccionada=hoja_seleccionada,
                        nombre_archivo=nombre_archivo
                    )

                # Si el archivo es real y tiene contenido, continúa el proceso normal:
                ruta = guardar_archivo(
                    archivo,
                    UPLOAD_FOLDER
                )
                hojas = obtener_hojas_excel(ruta)
                nombre_archivo = obtener_nombre_archivo(ruta)

        # ==============================
        # CASO 2:
        # CARGAR HOJA SELECCIONADA
        # ==============================

        # Procesar hoja
        if "hoja" in request.form:

            try:

                inicio = time.perf_counter()

                ruta = request.form.get("archivo")
                hoja = request.form.get("hoja")

                hojas = obtener_hojas_excel(ruta)
                nombre_archivo = obtener_nombre_archivo(ruta)

                hoja = request.form.get("hoja")
                hoja_seleccionada = hoja

                datos, fila_encabezado = encontrar_encabezado(
                    ruta,
                    hoja
                )

                if datos is not None:
                    datos.columns = [
                        str(col).strip().upper()
                        for col in datos.columns
                    ]

                if datos is not None:

                    datos = datos.dropna(
                        axis=1,
                        how="all"    
                    )

                    datos = datos.loc[
                        :,
                        ~datos.columns.astype(str)
                        .str.contains(
                            "^Unnamed",
                            case=False,
                            na=False
                        )
                    ]

                    columnas = list(datos.columns)

                    if len(columnas) >= 3:

                        datos.rename(
                            columns={
                                columnas[0]: "CODIGO",
                                columnas[1]: "DESCRIPCION",
                                columnas[2]: "VALOR OFERTADO"
                            },
                            inplace=True
                        )

                        # ===========================================
                        # VALIDAR QUE "VALOR OFERTADO" SEA NUMÉRICO
                        # ===========================================

                        valor = pd.to_numeric(
                            datos["VALOR OFERTADO"],
                            errors="coerce"
                        )

                        porcentaje_validos = valor.notna().mean()

                        if porcentaje_validos < 0.80:

                            validaciones.append(
                                "❌ La tercera columna no parece contener el Valor Ofertado."
                            )

                            archivo_valido = False

                            return render_template(
                                "negociacion/negociacion.html",
                                ...
                            )

                        # Eliminar filas completamente vacías
                        datos = datos.dropna(how="all")

                        # Limpiar columnas principales
                        for col in ["CODIGO", "DESCRIPCION"]:

                            datos[col] = (
                                datos[col]
                                .fillna("")
                                .astype(str)
                                .str.strip()
                            )

                        # Eliminar filas donde no exista código ni descripción
                        datos = datos[
                            ~(
                                (datos["CODIGO"] == "")
                                &
                                (datos["DESCRIPCION"] == "")
                            )
                        ]

                        datos.reset_index(drop=True, inplace=True)

                    tabla = datos.to_dict(orient="records")

                validaciones = []

                if datos is None:

                    validaciones.append(
                        "❌ No se encontraron encabezados válidos."
                    )

                    archivo_valido = False

                elif datos.empty:

                    validaciones.append(
                        "❌ La hoja no contiene registros."
                    )

                    archivo_valido = False

                elif datos.shape[1] < 3:

                    validaciones.append(
                        "❌ La hoja debe tener mínimo 3 columnas."
                    )

                    archivo_valido = False

                else:

                    validaciones.append(
                        f"✔ Encabezados encontrados en fila: {fila_encabezado}"
                    )

                    validaciones.append(
                        f"✔ Registros encontrados: {len(datos):,}"
                    )

                    validaciones.append(
                        f"✔ Columnas encontradas: {datos.shape[1]}"
                    )

                    archivo_valido = True

                    total_registros = len(datos)

                    cruces = [
                        (
                            "Regulados",
                            "CUM",
                            "Valor UMD con Intermediacion sin decimales",
                            "REGULACION"
                        ),
                        (
                            "NT",
                            "Codigo",
                            "Valor Referencia UMD",
                            "NT"
                        ),
                        (
                            "PM",
                            "CUM",
                            "VMR UMD 2026",
                            "PM"
                        ),
                        (
                            "Tarifario",
                            "CUM",
                            "VALOR",
                            "REFERENCIA"
                        ),
                        (
                            "INVIMA",
                            "CUM",
                            "Estado Registro",
                            "ESTADO REGISTRO"
                        )
                    ]

                    duplicados = datos.duplicated(
                        subset="CODIGO",
                        keep=False
                    )

                    datos["DUPLICADO"] = ""

                    datos.loc[
                        duplicados,
                        "DUPLICADO"
                    ] = "DUPLICADO"

                    for hoja_ref, campo_cod, campo_valor, nombre in cruces:

                        datos, coincidencias = cruzar_referencia(
                            datos,
                            hoja_ref,
                            campo_cod,
                            campo_valor,
                            nombre
                        )

                        validaciones.append(
                            f"✔ {nombre}: {coincidencias:,}"
                        )

                    datos = construir_valor_objetivo(datos)
                    datos = ordenar_columnas(datos)

                    # ----------------------------------------
                    # FORMATO PARA VISUALIZACIÓN
                    # ----------------------------------------

                    from pandas.api.types import is_numeric_dtype

                    # Monedas
                    for col in ["VALOR OFERTADO", "VALOR OBJETIVO"]:

                        if col in datos.columns:

                            datos[col] = (
                                pd.to_numeric(datos[col], errors="coerce")
                                .map(
                                    lambda x:
                                    ""
                                    if pd.isna(x)
                                    else f"{x:,.0f}".replace(",", ".")
                                )
                            )

                    # Enteros
                    for col in ["REGULACION", "NT", "REFERENCIA", "PM"]:

                        if col in datos.columns:

                            datos[col] = (
                                pd.to_numeric(datos[col], errors="coerce")
                                .map(
                                    lambda x:
                                    ""
                                    if pd.isna(x)
                                    else str(int(x))
                                )
                            )

                    # Desviación
                    if "DESVIACION" in datos.columns:

                        datos["DESVIACION"] = (
                            pd.to_numeric(datos["DESVIACION"], errors="coerce")
                            .map(
                                lambda x:
                                ""
                                if pd.isna(x)
                                else (
                                    f"{x:,.2f}"
                                    .replace(",", "X")
                                    .replace(".", ",")
                                    .replace("X", ".")
                                )
                            )
                        )

                    kpis = {
                        "registros": "--",
                        "duplicados": "--",
                        "aceptables": "--",
                        "renegociar": "--",
                        "activos": "--",
                        "no_activos": "--",
                        "fecha": "--",
                        "cobertura": "--"
                    }

                    def construir_kpis(df):

                        kpis = {}

                        for nombre, config in FILTROS_KPI.items():

                            columna = config["columna"]

                            serie = (
                                df[columna]
                                .fillna("")
                                .astype(str)
                                .str.upper()
                                .str.strip()
                            )

                            kpis[nombre] = int(serie.isin(config["valores"]).sum())

                        # Registros
                        kpis["registros"] = len(df)

                        # Cobertura
                        cubiertos = (
                            df[
                                [
                                    "REGULACION",
                                    "NT",
                                    "PM",
                                    "REFERENCIA"
                                ]
                            ]
                            .notna()
                            .any(axis=1)
                        )

                        kpis["cobertura"] = float(
                            round(cubiertos.mean() * 100, 1)
                        )

                        kpis["fecha"] = datetime.now().strftime("%d/%m/%Y")

                        return kpis
                    
                    kpis = construir_kpis(datos)

                    # -----------------------------------------
                    # Formatear KPIs numéricos
                    # -----------------------------------------

                    for campo in list(kpis.keys()):

                        valor = kpis[campo]

                        if isinstance(valor, (int, float)):

                            if campo == "cobertura":

                                kpis[campo] = (
                                    f"{valor:,.1f}"
                                    .replace(",", "X")
                                    .replace(".", ",")
                                    .replace("X", ".")
                                    + "%"
                                )

                            else:

                                kpis[campo] = (
                                    f"{valor:,.0f}"
                                    .replace(",", ".")
                                )

                    fin = time.perf_counter()

                    tiempo_proceso = round(fin - inicio, 2)

                    id_proceso = str(uuid.uuid4())

                    cache_negociaciones[id_proceso] = {
                        "datos": datos.copy(),
                        "archivo": os.path.basename(ruta),
                        "ruta": ruta,
                        "hoja": hoja
                    }

                    session["id_proceso"] = id_proceso

                    tabla = (
                        datos.to_dict(orient="records")
                        if datos is not None
                        else None
                    )

            except Exception as e:

                import traceback

                traceback.print_exc()

                mensaje = (
                    "El archivo no pudo procesarse porque no cumple con la estructura "
                    "esperada por SANEM."
                )

                archivo_valido = False

                validaciones = [
                    "❌ El archivo es incompatible con SANEM.",
                    "Revise que contenga un Código CUM y un Valor Ofertado válidos."
                ]

                tabla = None
                kpis = None
                total_registros = 0

    estado_panel = "inicio"

    if nombre_archivo:
        estado_panel = "archivo"

    if hoja_seleccionada:
        estado_panel = "hoja"

    if tiempo_proceso is not None:
        tiempo_proceso = formatear_tiempo(tiempo_proceso) 

    colapsar_hojas = True

    datos_exportacion = session.get(
        "datos_exportacion",
        {
            "identificacion_representante": "",
            "nombre_representante": "",
            "nit": "",
            "proveedor": "",
            "ciudad": "",
            "sucursal": "",
            "codigo_sucursal": ""
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
        id_cache=session.get("id_proceso", ""),
        estado_panel=estado_panel,
        kpis=kpis,
        tabla=tabla,
        filtros_kpi=FILTROS_KPI,
        tiempo_proceso = tiempo_proceso,
        datos_exportacion=datos_exportacion
    )

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

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)