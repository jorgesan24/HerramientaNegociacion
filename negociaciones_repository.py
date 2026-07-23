import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "repositorio.db"


def obtener_conexion():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd():

    with obtener_conexion() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS negociaciones (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nit TEXT NOT NULL,
                prestador TEXT NOT NULL,
                ciudad TEXT,

                codigo TEXT NOT NULL,
                descripcion TEXT,

                valor_ofertado REAL,

                fecha_creacion TEXT NOT NULL,
                fecha_actualizacion TEXT NOT NULL

            );
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_negociacion
            ON negociaciones(nit, codigo);
        """)

        conn.commit()


def guardar_negociacion(
    nit,
    prestador,
    ciudad,
    codigo,
    descripcion,
    valor_ofertado,
    fecha
):

    with obtener_conexion() as conn:

        conn.execute("""
            INSERT INTO negociaciones (

                nit,
                prestador,
                ciudad,
                codigo,
                descripcion,
                valor_ofertado,
                fecha_creacion,
                fecha_actualizacion

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(nit, codigo)

            DO UPDATE SET

                prestador = excluded.prestador,
                ciudad = excluded.ciudad,
                descripcion = excluded.descripcion,
                valor_ofertado = excluded.valor_ofertado,
                fecha_actualizacion = excluded.fecha_actualizacion;
        """, (

            nit,
            prestador,
            ciudad,
            codigo,
            descripcion,
            valor_ofertado,
            fecha,
            fecha

        ))

        conn.commit()

def guardar_dataframe_negociacion(
    datos: pd.DataFrame,
    nit,
    prestador,
    ciudad
):

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with obtener_conexion() as conn:

        cursor = conn.cursor()

        for _, fila in datos.iterrows():

            cursor.execute(
                """
                INSERT INTO negociaciones(

                    nit,
                    prestador,
                    ciudad,

                    codigo,
                    descripcion,
                    valor_ofertado,

                    fecha_creacion,
                    fecha_actualizacion

                )

                VALUES(?,?,?,?,?,?,?,?)

                ON CONFLICT(nit,codigo)

                DO UPDATE SET

                    descripcion=excluded.descripcion,
                    valor_ofertado=excluded.valor_ofertado,
                    ciudad=excluded.ciudad,
                    prestador=excluded.prestador,
                    fecha_actualizacion=excluded.fecha_actualizacion

                """,
                (

                    nit,
                    prestador,
                    ciudad,

                    fila["CODIGO"],
                    fila["DESCRIPCION"],
                    fila["VALOR OFERTADO"],

                    fecha,
                    fecha

                )

            )

        conn.commit()