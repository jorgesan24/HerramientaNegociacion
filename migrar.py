import pandas as pd
import sqlite3
import os

# Configuración de rutas
excel_file = "data/referencia_web.xlsx"
db_file = "data/herramienta_negociacion.db"

# Asegurar que la carpeta data existe
os.makedirs("data", exist_ok=True)

print(" Conectando a SQLite...")
conn = sqlite3.connect(db_file)

print(" Cargando archivo de Excel completo (esto puede tardar unos segundos)...")
# Al pasar sheet_name=None, Pandas lee TODAS las pestañas y las guarda en un diccionario
todo_el_excel = pd.read_excel(excel_file, sheet_name=None)

print(f" ¡Éxito! Se encontraron {len(todo_el_excel)} pestañas.")

# Iterar automáticamente sobre cada pestaña y guardarla como una tabla
for nombre_pestana, df in todo_el_excel.items():
    # Limpiamos el nombre de la pestaña (quitamos espacios y pasamos a minúsculas)
    nombre_tabla = nombre_pestana.strip().lower().replace(" ", "_")
    
    print(f" Migrando pestaña '{nombre_pestana}' a la tabla '{nombre_tabla}'...")
    
    # Guardar en SQLite
    df.to_sql(nombre_tabla, conn, if_exists="replace", index=False)

# Cerrar la conexión de forma segura
conn.close()
print("\n Proceso terminado. ¡Tu base de datos SQLite está lista con todas sus pestañas!")
