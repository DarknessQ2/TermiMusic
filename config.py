import os

BASE_DIR = os.path.expanduser("~/.config/termimusic")
PLAYLIST_DIR = os.path.join(BASE_DIR, "playlists")
DOWNLOAD_DIR = os.path.expanduser("~/Music/TermiMusic_Downloads")
SOCKET = "/tmp/termimusic-socket"
CAVA_CONF_PATH = "/tmp/termimusic_cava"

# Crea carpetas maestras si no existen
for d in [PLAYLIST_DIR, DOWNLOAD_DIR]: os.makedirs(d, exist_ok=True)

# Estado Global Compartido
class Estado:
    msj_error = ""
    error_time = 0
    modo_loop = "off"
    color_cava = "197"
    # Estado de Descargas
    dl_active = False
    dl_current = 0
    dl_total = 0
    dl_name = ""
