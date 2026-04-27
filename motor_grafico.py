import sys, urllib.request, io, re, threading, os
import config as cfg
try: from PIL import Image
except ImportError: pass

arte_cache = None
ruta_actual = ""
DISCO_ANIM = []

# --- ARTE HD DEL DISCO (Alineado para formar un círculo perfecto) ---
DISCO_DETALLADO = [
    "                    ..........          ",
    "               ...++====-===+*##=...    ",
    "            ...%+==========+*#%%%%%%..  ",
    "         .-%%@%#+======++*#%%@@@@@%%... ",
    "        .. %@@@@%#**++=--==#%@@@@@@@%%%*..",
    "         #%@@@@@@%#*++==+*%%@@@@@@@@@%%%...",
    "        .#@@@@@@@@@%##@@%@@@@@@@@@@@@@@%%#..",
    "       .*%@@@@@@@@@%%#*******%%@@@@@@@@@%%..",
    "       .%@@@@@@@@@#%*=*********#%@@@@@@@@@#.",
    "        -@@@@@@@@@%%*=**-+-**:**##@@@@@@@@@%.",
    "     ..-%@@@@@@@@%%*+*+**:-*****%@@@@@@@@@%.",
    "       .@@@@@@@@@@%%***********%@@@@@@@@@@%.",
    "      ..%@@@@@@@@@@%%********#@@@@@@@@@@@@=.",
    "       ..%@%@@@@@@@@@@@@@@@@@*#%%@@@@@@@@@.",
    "        ..%@@@@@@@@@@@%%#*+*#*+*%%%@@@@@@.",
    "         ..#@@%@@@@@@@@%#+=+##****#%%@@@.",
    "         ...#@@@@@@@@@%%#*+++*##**##%@...",
    "            ..-@@@@@@@%%#*++=+*####%..",
    "              ..:@@%%%%#*+==+**%...",
    "                   .. ......... . ."
]

def cargar_animacion():
    global DISCO_ANIM
    ruta_local = os.path.join(os.path.dirname(__file__), "animacion.txt")
    ruta_config = os.path.join(cfg.BASE_DIR, "animacion.txt")
    ruta = ruta_local if os.path.exists(ruta_local) else ruta_config

    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            frames = f.read().split("===FRAME===")
            DISCO_ANIM = [f.strip("\n") for f in frames if f.strip()]
    if not DISCO_ANIM:
        DISCO_ANIM = ["\nError: animacion.txt vacio o no encontrado.\n"]

def pintar(r, c, texto, color="\033[0m"):
    sys.stdout.write(f"\033[{int(r)};{int(c)}H{color}{texto}\033[0m")

def format_tiempo(s):
    if not s: return "00:00"
    m, s = divmod(int(s), 60)
    return f"{m:02d}:{s:02d}"

def scroll_texto(texto, ancho, paso):
    if len(texto) <= ancho: return f"{texto:<{ancho}}"
    pad = texto + "   •   "
    offset = int(paso) % len(pad)
    return (pad[offset:] + pad[offset:offset])[:ancho]

def renderizar_imagen(fuente):
    try:
        if isinstance(fuente, str) and fuente.startswith("http"):
            req = urllib.request.Request(fuente, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as r: img = Image.open(io.BytesIO(r.read()))
        else: img = Image.open(fuente)

        img = img.convert("RGB").resize((48,26), Image.Resampling.LANCZOS)
        lineas = []
        for y in range(0, 26, 2):
            l = ""
            for x in range(48):
                r1,g1,b1 = img.getpixel((x,y))
                r2,g2,b2 = img.getpixel((x,y+1))
                l += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀"
            lineas.append(l)
        return lineas
    except: return None

def actualizar_miniatura(path):
    global arte_cache, ruta_actual
    if path == ruta_actual: return
    ruta_actual = path

    def fetch():
        global arte_cache
        if path.startswith("http") or path.startswith("ytdl://"):
            yt_id = re.search(r"(?:v=|be/|ytsearch1:)([a-zA-Z0-9_-]{11})", path)
            arte_cache = renderizar_imagen(f"https://i.ytimg.com/vi/{yt_id.group(1)}/mqdefault.jpg") if yt_id else None
        else:
            base_path = os.path.splitext(path)[0]
            if os.path.exists(f"{base_path}.png"): arte_cache = renderizar_imagen(f"{base_path}.png")
            elif os.path.exists(os.path.join(os.path.dirname(path), "cover.png")): arte_cache = renderizar_imagen(os.path.join(os.path.dirname(path), "cover.png"))
            else: arte_cache = None

    threading.Thread(target=fetch, daemon=True).start()

# --- NUEVA INTERFAZ: TIENDA DE VINILOS ---
def render_menu_vinilos(playlists_web, playlists_locales, seleccion_idx, agarrado, frame_caida):
    print("\033[2J\033[H", end="") # Limpiar pantalla

    pintar(2, 4, "=== TIENDA DE VINILOS (TERMI-MUSIC) ===", "\033[1;36m")
    pintar(3, 4, "O / P : Hojear discos  |  ENTER : Poner en el Tocadiscos", "\033[0;90m")

    todas = playlists_web + playlists_locales
    if not todas:
        pintar(10, 4, "La caja está vacía. Ve al reproductor y usa /save o /dl.", "\033[1;31m")
        sys.stdout.flush()
        return

    # --- 1. TOCADISCOS (Abajo a la derecha) ---
    color_toca = "\033[1;32m" if agarrado else "\033[1;34m"
    toca_r, toca_c = 28, 45
    pintar(toca_r, toca_c,   " ┌────────────────────────┐ ", color_toca)
    pintar(toca_r+1, toca_c, " │  TOCADISCOS PRINCIPAL  │ ", color_toca)
    pintar(toca_r+2, toca_c, " │   (Suelta el disco)    │ ", color_toca)
    pintar(toca_r+3, toca_c, " └────────────────────────┘ ", color_toca)

    # --- 2. LA CAJA DE DISCOS (Lista a la izquierda) ---
    caja_r, caja_c = 6, 4
    pintar(caja_r, caja_c, " ┌──[ CAJA DE DISCOS ]──────┐", "\033[1;33m")

    # Mostrar solo los 15 discos más cercanos para no saturar hacia abajo
    inicio = max(0, min(seleccion_idx - 7, len(todas) - 15))
    fin = min(len(todas), inicio + 15)

    for i in range(inicio, fin):
        es_web = i < len(playlists_web)
        etiqueta = "WEB" if es_web else "LOC"
        nombre = todas[i].replace(".json", "")

        fila_actual = caja_r + 2 + (i - inicio)

        if i == seleccion_idx:
            # Disco actualmente hojeado (resaltado)
            pintar(fila_actual, caja_c, f" │ > [{etiqueta}] {nombre[:18]:<18} │", "\033[1;37m")
        else:
            # Discos en la caja
            color_dim = "\033[38;5;13m" if es_web else "\033[38;5;14m"
            pintar(fila_actual, caja_c, f" │   [{etiqueta}] {nombre[:18]:<18} │", color_dim)

    pintar(caja_r + 2 + (fin - inicio), caja_c, " └──────────────────────────┘", "\033[1;33m")

    # --- 3. MOSTRADOR DEL DISCO (El disco en HD a la derecha) ---
    visor_r, visor_c = 6, 40

    # Datos del disco seleccionado
    es_web_sel = seleccion_idx < len(playlists_web)
    color_disco = "\033[1;35m" if es_web_sel else "\033[1;36m"
    etiq_sel = "WEB" if es_web_sel else "LOC"
    nom_sel = todas[seleccion_idx].replace(".json", "")

    if agarrado:
        # Animación de caída desde el mostrador hacia el tocadiscos
        r_anim = visor_r + int((toca_r - visor_r) * (frame_caida/10.0))
        c_anim = visor_c + int((toca_c - visor_c) * (frame_caida/10.0))

        for j, linea in enumerate(DISCO_DETALLADO):
            pintar(r_anim + j, c_anim, linea, "\033[1;33m") # Brilla amarillo al caer

        pintar(r_anim + 9, c_anim + 19, f"[{etiq_sel}]", "\033[1;30;47m") # Etiqueta central invertida
        pintar(r_anim + 21, c_anim + 12, f" {nom_sel[:20]:^20}", "\033[1;37m")

    else:
        # Disco en el mostrador estático esperando ser agarrado
        for j, linea in enumerate(DISCO_DETALLADO):
            pintar(visor_r + j, visor_c, linea, color_disco)

        # Sello en el centro (Agujero del vinilo)
        pintar(visor_r + 9, visor_c + 19, f"[{etiq_sel}]", "\033[1;30;47m")

        # Tarjeta con el título debajo del disco
        pintar(visor_r + 21, visor_c + 12, f" ALBUM: {nom_sel[:18]:<18} ", "\033[7;37m")

    sys.stdout.flush()
