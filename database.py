import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "negociaciones.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_bd():

    conn = get_connection()
    cur = conn.cursor()

    # ==========================================
    # Encabezado de cada negociación
    # ==========================================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS negociaciones (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        consecutivo TEXT UNIQUE,

        fecha TEXT,

        nit TEXT,

        prestador TEXT,

        ciudad TEXT,

        tipo_atencion TEXT,

        plan TEXT,

        usuario TEXT

    )
    """)

    # ==========================================
    # Detalle histórico
    # ==========================================
    cur.execute("""
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

        desviacion REAL,

        FOREIGN KEY (negociacion_id)
            REFERENCES negociaciones(id)

    )
    """)

    # ==========================================
    # Repositorio vigente
    # ==========================================
    cur.execute("""
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

    )
    """)

    conn.commit()
    conn.close()