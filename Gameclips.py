"""
subir_clips_drive.py

Vigila una carpeta local de clips de juegos y los sube automáticamente
a Google Drive en cuanto detecta que un archivo nuevo ha terminado de grabarse.

Requisitos (instalar con pip):
    pip install watchdog google-api-python-client google-auth-httplib2 google-auth-oauthlib

Antes de ejecutar, necesitas:
    1. Un archivo credentials.json descargado desde Google Cloud Console
       (ver instrucciones al final de este script / en el chat).
    2. Configurar las variables CARPETA_CLIPS y CARPETA_DRIVE_ID más abajo.
"""

import os
import time
import json
import sqlite3
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ----------------------- CONFIGURACIÓN -----------------------

# Carpeta local donde tu software de grabación guarda los clips.
# Ejemplo típico de Nvidia ShadowPlay:
CARPETA_CLIPS = r"C:\Users\TU_USUARIO\Videos\NVIDIA\Highlights"

# ID de la carpeta de Google Drive donde quieres subir los clips.
# Se saca de la URL cuando abres la carpeta en Drive:
# https://drive.google.com/drive/folders/ESTE_ES_EL_ID
CARPETA_DRIVE_ID = "TU_ID_DE_CARPETA_AQUI"

# Extensiones de archivo que se consideran clips válidos
EXTENSIONES_VALIDAS = {".mp4", ".mkv", ".mov"}

# Segundos que debe permanecer estable el tamaño del archivo antes de subirlo
SEGUNDOS_ESTABILIDAD = 5

# Segundos entre comprobaciones de tamaño
INTERVALO_COMPROBACION = 2

# Archivos de configuración de Google (se generan/descargan automáticamente)
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Base de datos local para no subir el mismo clip dos veces
DB_FILE = "clips_subidos.db"

# ----------------------- BASE DE DATOS -----------------------


def iniciar_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subidos (
            ruta TEXT PRIMARY KEY,
            fecha_subida TEXT
        )
        """
    )
    conn.commit()
    return conn


def ya_subido(conn, ruta):
    cur = conn.execute("SELECT 1 FROM subidos WHERE ruta = ?", (ruta,))
    return cur.fetchone() is not None


def marcar_subido(conn, ruta):
    conn.execute(
        "INSERT INTO subidos (ruta, fecha_subida) VALUES (?, datetime('now'))",
        (ruta,),
    )
    conn.commit()


# ----------------------- AUTENTICACIÓN GOOGLE -----------------------


def obtener_servicio_drive():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ----------------------- SUBIDA A DRIVE -----------------------


def esperar_archivo_estable(ruta):
    """Espera hasta que el tamaño del archivo deje de cambiar,
    para evitar subir un clip que aún se está grabando/copiando."""
    tamano_anterior = -1
    while True:
        try:
            tamano_actual = os.path.getsize(ruta)
        except FileNotFoundError:
            return False

        if tamano_actual == tamano_anterior and tamano_actual > 0:
            return True

        tamano_anterior = tamano_actual
        time.sleep(INTERVALO_COMPROBACION)


def subir_archivo(servicio, ruta):
    nombre = os.path.basename(ruta)
    metadata = {"name": nombre, "parents": [CARPETA_DRIVE_ID]}

    # resumable=True: si se corta la conexión a mitad de la subida,
    # la librería reintenta desde donde se quedó en vez de empezar de cero
    media = MediaFileUpload(ruta, resumable=True)

    print(f"Subiendo: {nombre}")
    request = servicio.files().create(body=metadata, media_body=media, fields="id")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%")

    print(f"Subida completa: {nombre} (ID de Drive: {response.get('id')})")


# ----------------------- VIGILANCIA DE LA CARPETA -----------------------


class ManejadorClips(FileSystemEventHandler):
    def __init__(self, servicio, conn):
        self.servicio = servicio
        self.conn = conn

    def on_created(self, event):
        if event.is_directory:
            return

        ruta = event.src_path
        extension = Path(ruta).suffix.lower()

        if extension not in EXTENSIONES_VALIDAS:
            return

        if ya_subido(self.conn, ruta):
            return

        print(f"Nuevo clip detectado: {ruta}")

        if not esperar_archivo_estable(ruta):
            print("El archivo desapareció antes de terminar de escribirse, se ignora.")
            return

        try:
            subir_archivo(self.servicio, ruta)
            marcar_subido(self.conn, ruta)
        except Exception as e:
            print(f"Error subiendo {ruta}: {e}")
            print("No se marca como subido, se reintentará en la próxima ejecución.")


def main():
    if not os.path.isdir(CARPETA_CLIPS):
        print(f"La carpeta {CARPETA_CLIPS} no existe. Revisa CARPETA_CLIPS.")
        return

    conn = iniciar_db()
    servicio = obtener_servicio_drive()

    manejador = ManejadorClips(servicio, conn)
    observer = Observer()
    observer.schedule(manejador, CARPETA_CLIPS, recursive=False)
    observer.start()

    print(f"Vigilando carpeta: {CARPETA_CLIPS}")
    print("Esperando clips nuevos... (Ctrl+C para detener)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nDetenido.")

    observer.join()
    conn.close()


if __name__ == "__main__":
    main()
