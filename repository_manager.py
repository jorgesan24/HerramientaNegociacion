from datetime import datetime

from database import get_connection


def guardar_negociacion(encabezado, datos):

    consecutivo = generar_consecutivo()

    conn = get_connection()
    cur = conn.cursor()

    # ==========================================
    # Encabezado
    # ==========================================

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
            encabezado["fecha"],
            encabezado["nit"],
            encabezado["prestador"],
            encabezado["ciudad"],
            encabezado["tipo_atencion"],
            encabezado["plan"],
            encabezado["usuario"],
        ),
    )

    negociacion_id = cur.lastrowid

    # ==========================================
    # Detalle histórico
    # ==========================================

    for fila in datos:

        cur.execute(
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

            VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
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

                fila.get("DESVIACION"),
            ),
        )

    conn.commit()

    actualizar_repositorio_vigente(
        conn,
        encabezado["nit"],
        datos
    )

    conn.commit()
    conn.close()

    return consecutivo

def actualizar_repositorio_vigente(conn, nit, datos):

    cur = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for fila in datos:

        cur.execute(
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

            VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

            ON CONFLICT(nit,codigo)

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

                fecha,
            ),
        )

from datetime import datetime
import sqlite3


def generar_consecutivo():
    """
    Genera un consecutivo del tipo:

    NEG-20260722-000001
    """

    conn = sqlite3.connect("negociaciones.db")
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y%m%d")

    cursor.execute("""
        SELECT COUNT(*)
        FROM negociaciones
        WHERE fecha_proceso LIKE ?
    """, (fecha + "%",))

    cantidad = cursor.fetchone()[0] + 1

    conn.close()

    return f"NEG-{fecha}-{cantidad:06d}"