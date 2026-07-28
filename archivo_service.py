import os
import pandas as pd
from werkzeug.utils import secure_filename
from pathlib import Path

def guardar_archivo(
    archivo,
    upload_folder: Path
):

    nombre = secure_filename(archivo.filename)

    os.makedirs(upload_folder, exist_ok=True)

    ruta = os.path.join(upload_folder, nombre)

    archivo.save(ruta)

    return str(ruta)

def obtener_hojas_excel(ruta):

    xls = pd.ExcelFile(ruta)

    return xls.sheet_names


def obtener_nombre_archivo(ruta):

    return os.path.basename(ruta)