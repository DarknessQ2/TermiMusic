import os
import json

BASE_DIR = os.path.expanduser("~/.config/termimusic")
PLAYLIST_DIR = os.path.join(BASE_DIR, "playlists")
DOWNLOAD_DIR = os.path.expanduser("~/Music/TermiMusic_Downloads")
SOCKET = "/tmp/termimusic-socket"
CAVA_CONF_PATH = "/tmp/termimusic_cava"

# Crea carpetas maestras si no existen
for d in [PLAYLIST_DIR, DOWNLOAD_DIR]:
    os.makedirs(d, exist_ok=True)

# =====================================================================
# 💾 CLASE DE ESTADO GLOBAL
# =====================================================================
class Estado:
    # Variables Persistentes (Se guardan en estado_config.json)
    modo_dinamico = True
    modo_loop = "off"
    color_cava = "197"

    # Variables Volátiles (Estado en tiempo real del programa)
    msj_error = ""
    error_time = 0
    dl_active = False
    dl_current = 0
    dl_total = 0
    dl_name = ""

    ARCHIVO_CONFIG = os.path.join(BASE_DIR, "estado_config.json")

    @classmethod
    def guardar(cls):
        try:
            datos = {
                "modo_dinamico": cls.modo_dinamico,
                "modo_loop": cls.modo_loop,
                "color_cava": cls.color_cava
            }
            with open(cls.ARCHIVO_CONFIG, "w") as f:
                json.dump(datos, f, indent=4)
        except: pass

    @classmethod
    def cargar(cls):
        try:
            if os.path.exists(cls.ARCHIVO_CONFIG):
                with open(cls.ARCHIVO_CONFIG, "r") as f:
                    datos = json.load(f)
                    cls.modo_dinamico = datos.get("modo_dinamico", True)
                    cls.modo_loop = datos.get("modo_loop", "off")
                    cls.color_cava = datos.get("color_cava", "197")
        except: pass

# Inicializar carga al importar config
Estado.cargar()
