import os, json, ctypes, threading, time
import config as cfg

# 1. Cargar la librería C++ compilada
lib_path = os.path.join(os.path.dirname(__file__), "motor_media_c.so")
motor_c = ctypes.CDLL(lib_path)

# Definir tipos de datos del puente C++ para evitar desbordes de memoria
motor_c.mpv_query_c.restype = ctypes.c_char_p
motor_c.yt_dlp_descargar_c.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

# --- COMUNICACIÓN MPV (VIA C++) ---
def mpv_query(prop):
    comando_json = json.dumps({"command": ["get_property", prop]})
    # Llamada directa al Socket POSIX en C++ a velocidad de memoria
    respuesta = motor_c.mpv_query_c(cfg.SOCKET.encode('utf-8'), comando_json.encode('utf-8'))

    if respuesta:
        try:
            linea = respuesta.decode('utf-8').split('\n')[0]
            return json.loads(linea).get("data")
        except: return None
    return None

def mpv_command(cmd_list):
    comando_json = json.dumps({"command": cmd_list})
    motor_c.mpv_command_c(cfg.SOCKET.encode('utf-8'), comando_json.encode('utf-8'))

# --- GESTIÓN DE PLAYLISTS ---
def guardar_playlist(nombre, datos):
    try:
        with open(os.path.join(cfg.PLAYLIST_DIR, f"{nombre}.json"), "w") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except: pass

def cargar_playlist(nombre):
    ruta = os.path.join(cfg.PLAYLIST_DIR, f"{nombre}.json")
    if os.path.exists(ruta):
        try:
            with open(ruta, "r") as f: return json.load(f)
        except: return None
    return None

def obtener_toda_la_biblioteca():
    canciones = []
    archivos_soportados = ('.mp3', '.m4a', '.webm', '.ogg', '.flac', '.wav')
    if os.path.exists(cfg.DOWNLOAD_DIR):
        for root, _, files in os.walk(cfg.DOWNLOAD_DIR):
            for f in files:
                if f.lower().endswith(archivos_soportados): canciones.append(os.path.join(root, f))

    if os.path.exists(cfg.PLAYLIST_DIR):
        for f in os.listdir(cfg.PLAYLIST_DIR):
            if f.endswith(".json"):
                datos = cargar_playlist(f.replace(".json", ""))
                if datos:
                    for item in datos:
                        url = item["url"] if isinstance(item, dict) else item
                        if url not in canciones: canciones.append(url)
    return canciones

# --- MOTOR DE DESCARGAS (NATIVO EN C++) ---
def dl_playlist_thread(pl_name, pl_data):
    carpeta = os.path.join(cfg.DOWNLOAD_DIR, pl_name)
    os.makedirs(carpeta, exist_ok=True)
    urls = [item["url"] for item in pl_data if "url" in item]

    if urls:
        cfg.Estado.dl_active = True
        cfg.Estado.dl_total = len(urls)
        cfg.Estado.dl_current = 0
        cfg.Estado.dl_name = pl_name

        for url in urls:
            # Ejecución delegada al motor de C++ (.so)
            motor_c.yt_dlp_descargar_c(carpeta.encode('utf-8'), url.encode('utf-8'))
            cfg.Estado.dl_current += 1

        cfg.Estado.dl_active = False
        cfg.Estado.msj_error = f"✅ Playlist '{pl_name}' 100% Offline"
    else:
        cfg.Estado.msj_error = "❌ Playlist vacía"
    cfg.Estado.error_time = time.time()

def dl_single_thread(link):
    cfg.Estado.dl_active = True
    cfg.Estado.dl_total = 1
    cfg.Estado.dl_current = 0
    cfg.Estado.dl_name = "Pista actual"

    # Ejecución delegada al motor de C++ (.so)
    motor_c.yt_dlp_descargar_c(cfg.DOWNLOAD_DIR.encode('utf-8'), link.encode('utf-8'))

    cfg.Estado.dl_current = 1
    cfg.Estado.dl_active = False
    cfg.Estado.msj_error = "✅ MP3 Guardado con éxito"
    cfg.Estado.error_time = time.time()
