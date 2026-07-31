from datetime import datetime
import sqlite3
from database import get_connection

def guardar_negociacion(encabezado, datos):
    # Genera el consecutivo diario único usando la base de datos
    consecutivo = generar_consecutivo()

    conn = get_connection()
    cur = conn.cursor()

    # ==========================================================================
    # BLINDAJE DE LISTAS PARA SQLITE
    # ==========================================================================
    plan_datos = encabezado.get("plan", "")
    if isinstance(plan_datos, list):
        plan_datos = ", ".join(str(p) for p in plan_datos)

    atencion_datos = encabezado.get("tipo_atencion", "")
    if isinstance(atencion_datos, list):
        atencion_datos = ", ".join(str(a) for a in atencion_datos)

    # ==========================================================================
    # Encabezado 
    # ==========================================================================
    fecha_guardar = encabezado.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nit_guardar = encabezado.get("nit") or encabezado.get("proveedor_nit", "")

    cur.execute(
        """
        INSERT INTO negociaciones
        (
            consecutivo,
            fecha,
            nit,
            prestador,
            ciudad,
            tipo_atencion,
            plan,
            usuario
        )
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            consecutivo,
            fecha_guardar,
            nit_guardar,
            encabezado.get("prestador", ""),
            encabezado.get("ciudad", ""),
            atencion_datos,
            plan_datos,
            encabezado.get("usuario", ""),
        ),
    )

    negociacion_id = cur.lastrowid

    # ==========================================================================
    # BLINDAJE CONTRA DATAFRAMES DE PANDAS
    # ==========================================================================
    if hasattr(datos, "to_dict"):
        registros_procesar = datos.to_dict(orient="records")
    else:
        registros_procesar = datos

    # ==========================================================================
    # OPTIMIZACIÓN 1: INSERCIÓN MASIVA VECTORIZADA (executemany)
    # ==========================================================================
    # Preparamos todas las tuplas de datos en memoria en un solo bloque rápido
    tuplas_detalle = [
        (
            negociacion_id,
            fila.get("CODIGO"),
            fila.get("DESCRIPCION"),
            fila.get("VALOR OFERTADO"),
            fila.get("REGULACION"),
            fila.get("NT"),
            fila.get("REFERENCIA"),
            fila.get("PM"),
            fila.get("VALOR OBJETIVO"),
            fila.get("VALIDACION"),
            fila.get("ESTADO REGISTRO"),
            fila.get("DUPLICADO"),
            fila.get("ORIGEN"),
            fila.get("DESVIACION")
        )
        for fila in registros_procesar if not isinstance(fila, str)
    ]

    # Inyectamos miles de registros al disco en una sola operación atómica
    cur.executemany(
        """
        INSERT INTO negociacion_detalle
        (
            negociacion_id,
            codigo,
            descripcion,
            valor_ofertado,
            regulacion,
            nt,
            referencia,
            pm,
            valor_objetivo,
            validacion,
            estado_registro,
            duplicado,
            origen,
            desviacion
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        tuplas_detalle
    )

    conn.commit()

    # Sincroniza y actualiza el repositorio maestro de forma masiva
    actualizar_repositorio_vigente_masivo(
        cur,
        nit_guardar,
        registros_procesar
    )

    conn.commit()
    conn.close()

    return consecutivo


def actualizar_repositorio_vigente_masivo(cur, nit, registros_procesar):
    """
    OPTIMIZACIÓN 2: Actualización por lotes usando executemany para ON CONFLICT.
    """
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tuplas_vigente = [
        (
            nit,
            fila.get("CODIGO"),
            fila.get("DESCRIPCION"),
            fila.get("VALOR OFERTADO"),
            fila.get("REGULACION"),
            fila.get("NT"),
            fila.get("REFERENCIA"),
            fila.get("PM"),
            fila.get("VALOR OBJETIVO"),
            fila.get("VALIDACION"),
            fila.get("ESTADO REGISTRO"),
            fila.get("DUPLICADO"),
            fila.get("ORIGEN"),
            fila.get("DESVIACION"),
            fecha
        )
        for fila in registros_procesar if not isinstance(fila, str)
    ]

    cur.executemany(
        """
        INSERT INTO repositorio_vigente
        (
            nit,
            codigo,
            descripcion,
            valor_ofertado,
            regulacion,
            nt,
            referencia,
            pm,
            valor_objetivo,
            validacion,
            estado_registro,
            duplicado,
            origen,
            desviacion,
            fecha_actualizacion
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(nit, codigo)
        DO UPDATE SET
            descripcion=excluded.descripcion,
            valor_ofertado=excluded.valor_ofertado,
            regulacion=excluded.regulacion,
            nt=excluded.nt,
            referencia=excluded.referencia,
            pm=excluded.pm,
            valor_objetivo=excluded.valor_objetivo,
            validacion=excluded.validacion,
            estado_registro=excluded.estado_registro,
            duplicado=excluded.duplicado,
            origen=excluded.origen,
            desviacion=excluded.desviacion,
            fecha_actualizacion=excluded.fecha_actualizacion
        """,
        tuplas_vigente
    )


def generar_consecutivo():
    """
    Genera un consecutivo único del tipo: NEG-20260722-000001
    """
    conn = get_connection()
    cursor = conn.cursor()

    fecha_hoy = datetime.now().strftime("%Y%m%d")
    fecha_busqueda = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM negociaciones
            WHERE fecha LIKE ?
        """, (fecha_busqueda + "%",))
        cantidad = cursor.fetchone()[0]

    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS negociaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consecutivo TEXT NOT NULL,
                fecha TEXT,
                nit TEXT,
                prestador TEXT,
                ciudad TEXT,
                tipo_atencion TEXT,
                plan TEXT,
                usuario TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS negociacion_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                negociacion_id INTEGER,
                codigo TEXT,
                descripcion TEXT,
                valor_ofertado REAL,
                regulacion REAL,
                nt REAL,
                referencia REAL,
                pm REAL,
                valor_objetivo REAL,
                validacion TEXT,
                estado_registro TEXT,
                duplicado TEXT,
                origen TEXT,
                desviacion REAL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositorio_vigente (
                nit TEXT,
                codigo TEXT,
                descripcion TEXT,
                valor_ofertado REAL,
                regulacion REAL,
                nt REAL,
                referencia REAL,
                pm REAL,
                valor_objetivo REAL,
                validacion TEXT,
                estado_registro TEXT,
                duplicado TEXT,
                origen TEXT,
                desviacion REAL,
                fecha_actualizacion TEXT,
                PRIMARY KEY (nit, codigo)
            );
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM negociaciones
            WHERE fecha LIKE ?
        """, (fecha_busqueda + "%",))
        cantidad = cursor.fetchone()[0]

    conn.close()
    
    nuevo_consecutivo = cantidad + 1
    return f"NEG-{fecha_hoy}-{nuevo_consecutivo:06d}"