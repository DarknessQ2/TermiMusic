#!/usr/bin/env python3
# ==========================================================
# TermiMusic - Reproductor de Terminal Profesional
# Autor: DarknessQ2 
# ==========================================================

import subprocess, sys, time, os, json, fcntl, termios, tty, select, urllib.request, io, re, threading

# --- VERIFICACIÓN DE DEPENDENCIAS ---
try:
    from PIL import Image
    import psutil
    from pypresence import Presence
except ImportError:
    print("\033[1;31mError: Faltan librerías. Instala con:\n  pip install Pillow psutil pypresence\033[0m")
    sys.exit(1)

# --- CONFIGURACIÓN DE RUTAS Y CARPETAS ---
BASE_DIR = os.path.expanduser("~/.config/termimusic")
PLAYLIST_DIR = os.path.join(BASE_DIR, "playlists")
SOCKET = "/tmp/termimusic-socket"
CAVA_CONF_PATH = "/tmp/termimusic_cava"

# Crear carpetas si no existen
os.makedirs(PLAYLIST_DIR, exist_ok=True)

# --- DISCORD RICH PRESENCE ---
ID_DISCORD = '1226912345678901234' # Puedes crear tu propia App en Discord Developer Portal
RPC = None
try:
    RPC = Presence(ID_DISCORD)
    RPC.connect()
except:
    RPC = None

# --- GESTIÓN DE PLAYLISTS ---
def guardar_playlist(nombre, urls):
    ruta = os.path.join(PLAYLIST_DIR, f"{nombre}.json")
    with open(ruta, "w") as f:
        json.dump(urls, f, indent=4)

def cargar_playlist(nombre):
    ruta = os.path.join(PLAYLIST_DIR, f"{nombre}.json")
    if os.path.exists(ruta):
        with open(ruta, "r") as f: return json.load(f)
    return None

# --- COMUNICACIÓN CON MPV ---
def mpv_query(prop):
    try:
        cmd = json.dumps({"command": ["get_property", prop]}) + "\n"
        p = subprocess.Popen(["socat", "-", f"UNIX-CONNECT:{SOCKET}"],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = p.communicate(input=cmd.encode(), timeout=0.03)
        return json.loads(out.decode()).get("data")
    except: return None

def mpv_command(cmd):
    try:
        data = json.dumps({"command": cmd}) + "\n"
        subprocess.Popen(["socat", "-", f"UNIX-CONNECT:{SOCKET}"],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate(input=data.encode(), timeout=0.03)
    except: pass

# --- MOTOR DE INTERFAZ (UI) ---
def pintar(r, c, texto, color="\033[0m"):
    sys.stdout.write(f"\033[{r};{c}H{color}{texto}\033[0m")

def format_tiempo(s):
    if not s: return "00:00"
    m, s = divmod(int(s), 60)
    return f"{m:02d}:{s:02d}"

def scroll_texto(texto, ancho, paso):
    if len(texto) <= ancho: return f"{texto:<{ancho}}"
    pad = texto + "   •   "
    offset = int(paso) % len(pad)
    return (pad[offset:] + pad[offset:offset])[:ancho]

# --- PROCESAMIENTO DE IMÁGENES (THUMBNAILS) ---
arte_cache = None
ruta_actual = ""
def actualizar_miniatura(path):
    global arte_cache, ruta_actual
    if path == ruta_actual: return
    ruta_actual = path
    yt_id = re.search(r"(?:v=|be/)([a-zA-Z0-9_-]{11})", path) if path else None
    if yt_id:
        def fetch():
            global arte_cache
            try:
                url = f"https://i.ytimg.com/vi/{yt_id.group(1)}/mqdefault.jpg"
                with urllib.request.urlopen(url, timeout=2) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB").resize((48,26), Image.Resampling.LANCZOS)
                    lineas = []
                    for y in range(0, 26, 2):
                        l = ""
                        for x in range(48):
                            r1,g1,b1 = img.getpixel((x,y))
                            r2,g2,b2 = img.getpixel((x,y+1))
                            l += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀"
                        lineas.append(l)
                    arte_cache = lineas
            except: arte_cache = None
        threading.Thread(target=fetch, daemon=True).start()
    else: arte_cache = None

# --- FRAMES DEL DISCO ASCII ---
DISCO_ANIM = [
r"""
                    ..........
               ...++====-===+*##=...
            ...%+==========+*#%%%%%%..
         .-%%@%#+======++*#%%@@@@@%%...
        .. %@@@@%#**++=--==#%@@@@@@@%%%*..
         #%@@@@@@%#*++==+*%%@@@@@@@@@%%%...
        .#@@@@@@@@@%##@@%@@@@@@@@@@@@@@%%#..
       .*%@@@@@@@@@%%#*******%%@@@@@@@@@%%..
       .%@@@@@@@@@#%*=*********#%@@@@@@@@@#.
        -@@@@@@@@@%%*=**-+-**:**##@@@@@@@@@%..
     ..-%@@@@@@@@%%*+*+**:-*****%@@@@@@@@@%..
       .@@@@@@@@@@%%***********%@@@@@@@@@@%.
      ..%@@@@@@@@@@%%********#@@@@@@@@@@@@=.
       ..%@%@@@@@@@@@@@@@@@@@*#%%@@@@@@@@@.
        ..%@@@@@@@@@@@%%#*+*#*+*%%%@@@@@@.
         ..#@@%@@@@@@@@%#+=+##****#%%@@@.
         ...#@@@@@@@@@%%#*+++*##**##%@...
            ..-@@@@@@@%%#*++=+*####%..
              ..:@@%%%%#*+==+**%...
                   .. ......... . .
""",
r"""
                  .  ......... .
                  ..+*#%%@@%###*...
               ..*%@@@%@@@@@%#====+-..
           ...-#@@@@@@@@@@%##+====-==#...
            .@@@@@@@@@@@@@@%*+=+===--=+..
          ..%@@@@@@@@@@@@@@%*+=-====++**+.
         ..#@@@@@@@@@@@#%%%@@#=+==+###%%#=.
         .%%%@@@@@@@%%#**.***+%@##%%%@%@%%.
         .#@@@@@@@@@%***:+*****%@@@@@@@@@%#
         .@%@@@@@@@%%****-:*****%@@@@@@@@%%.
        ..@@@@@@@@@@@******++***%@@@@@@@%%#.
         .@@@@@@@@@%@*****::***#%@@@@@@@%%*.
         :%@@@@@@%%#@@******+%%@@@@@@@@%%.
         .@%@@@%%#**+*@@@@@@@@@@@@@@@@@%+
            .@%@%%#*+=*#**#@@@@@@@@@@@@@%#.
             .*##*++=*##**%%@@@@@@@@@@@%-.
              ..#+===*#***#%@@@@@@@@@@%.
                 .#**##***#%@@@@@@@@#..
                   ..:@%##%%@@@@@...
                       .... ..
""",
r"""
                    ..........
               ...%#@@@@@@%%%##.
             ...@@%@@@@@@@@@@@@@@%*..
            ..@@@@@@@@@@@@@@@@@@@@@@*.
            %@@@@@@@@@@@@@@@@@@@@@@%@@%.
          .@%@@@@@@@@@@@@@@@@@@@@@@@@@@%..
         .%%@@%@@@@@@@%%%%%%%@@@@@@@@@@%%.
        ..*##%%%%%%%@@*******%#@@@@%####+.
        .%++++***##@******=-:**@##**+==-=#.
        .#====+=++@@******:****@#+=======*.
        .#***###**%@****+******@+==-=====#.
        .%#*****+*#@****--****#@*+=====-=+
         .##**##%%@@@@*+****+@@@%%##++--+.
         .@##%%%@@@@@@@%%%%%@@@@@@%%##*+-.
         @%@@@@@@@@@@@@@@@@@@@@@@%%%**.
         .*@@@@@@@@@@@@@@@@@@@@@@@%%:.
            .@@@@@@@@@@@@@@@@@@@@%%#.
            ...%@@@@@@@@@@@%%%%%%=.
                ....%%%%%%%%##*.....
                     .  .   ..
""",
r"""
                     .=@@@@@@*...
                ..*%%%%@@@@@@%@@@@#: ..
                :**%%@@@@@@@@@@@@@@%@%%..
            .:*=++##%@@@@@@@@@@@@@@@@@%@..
         ...%*+==++*%%%@@@@@@@@@@@@@@@@@#..
         ..%##***+==+#%%%@@@@@@@@@@@@@@@@%.
         .%##***%#**++@@@@%%%%%@@@@@@@@@@@*..
        ..%#*****+**@@+*******+%%@@@@@@@@@@%
        .@%%%%#%%##%@*********-*%%@@@@@@@@@*.
        .@@@@@@@@@@@***+**===+*=*%@@@@@@@%%%..
        .@@@@@@@@@@@#****=*****+*%@@@@@@@@@%.
        .@@@@@@@@@@@%***+*******@@#%%@%%@@@%.
         .@@@@@@@@@@@%#*******%@*+++*###%%#:.
         @@@@@@@@@@@@%%%%@@@@+++=-=+==+**%..
         ..%@@@@@@@@@@@@@@@@%%*=========+#.
           .@@@@@@@@@@@@@@@@@%#*=+===-==#..
            ..%@%@@@@@@@@@@@@%#**==--=*.
             ...#%%%%%@@@@@@@@%#*+==#..
               ...-#%%%%%@%%%%#**#:.
                   . ...-++=:....
                         ..
"""
]

# --- FUNCIÓN PRINCIPAL (ENTRY POINT) ---
def main():
    # Inicializar CAVA
    with open(CAVA_CONF_PATH, "w") as f:
        f.write("[general]\nbars = 40\nsensitivity = 100\n[output]\nmethod = raw\nraw_target = /dev/stdout\nbit_format = 8bit\n")

    os.system("clear")
    print("\033[?25l", end="") # Ocultar cursor

    # Lanzar MPV
    mpv = subprocess.Popen(
        ["mpv","--idle=yes","--no-video","--vid=no","--ytdl-format=bestaudio",
         "--force-window=no","--audio-display=no","--quiet",f"--input-ipc-server={SOCKET}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Esperar al Socket
    for _ in range(100):
        if os.path.exists(SOCKET): break
        time.sleep(0.01)

    # Lanzar CAVA
    cava_proc = subprocess.Popen(["cava","-p",CAVA_CONF_PATH], stdout=subprocess.PIPE)
    fcntl.fcntl(cava_proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    # Variables de Estado
    input_buffer = ""
    input_mode = False
    color_cava = "197"
    msj_error = ""
    error_time = 0
    modo_loop = "off"
    disco_f = 0.0
    disco_v = 0.0
    t_anterior = time.time()
    raw_cava = bytearray(40)

    COL_R = 54
    psutil.cpu_percent()

    # Configuración de Terminal (Input sin Enter)
    fd = sys.stdin.fileno()
    original_tty = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    try:
        while True:
            t_ahora = time.time()
            dt = t_ahora - t_anterior
            t_anterior = t_ahora

            # --- 1. PROCESAR ENTRADA DE USUARIO ---
            if select.select([sys.stdin], [], [], 0)[0]:
                tecla = sys.stdin.read(1)

                if tecla == '\x1b': # Esc / Secuencias
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        seq = sys.stdin.read(2)
                        if not input_mode:
                            if seq == "[C": mpv_command(["playlist-next"])
                            elif seq == "[D": mpv_command(["playlist-prev"])
                            elif seq == "[A": mpv_command(["add", "volume", 5])
                            elif seq == "[B": mpv_command(["add", "volume", -5])
                    else: input_mode = False; pintar(37, 5, " "*80)

                elif tecla == '\n': # Enter
                    if input_mode:
                        cmd = input_buffer.strip()
                        input_buffer = ""
                        input_mode = False
                        pintar(37, 5, " "*80)

                        # Comandos
                        if cmd.startswith("/save "):
                            nombre = cmd.split(" ", 1)[1]
                            pl = mpv_query("playlist") or []
                            urls = [i.get("filename") for i in pl if i.get("filename")]
                            if urls: guardar_playlist(nombre, urls)
                        elif cmd.startswith("/play "):
                            nombre = cmd.split(" ", 1)[1]
                            urls = cargar_playlist(nombre)
                            if urls:
                                mpv_command(["playlist-clear"])
                                for u in urls: mpv_command(["loadfile", u, "append"])
                                mpv_command(["playlist-play-index", 0])
                            else: msj_error = "❌ No existe esa playlist"; error_time = t_ahora
                        elif cmd.startswith("/loop "):
                            m = cmd.split(" ")[1]
                            if m == "song": mpv_command(["set", "loop-file", "inf"]); modo_loop = "CANCION"
                            elif m == "list": mpv_command(["set", "loop-playlist", "inf"]); modo_loop = "LISTA"
                            else: mpv_command(["set", "loop-file", "no"]); mpv_command(["set", "loop-playlist", "no"]); modo_loop = "off"
                        elif cmd.startswith("/fx "):
                            m = cmd.split(" ")[1]
                            if m == "bass": mpv_command(["set", "af", "equalizer=f=60:w=1:g=12"])
                            elif m == "lofi": mpv_command(["set", "af", "lowpass=f=3000,highpass=f=200"])
                            else: mpv_command(["set", "af", ""])
                        elif cmd.startswith("/color "):
                            c = cmd.split(" ", 1)[1]
                            if c.isdigit(): color_cava = c
                        elif cmd: # Carga Directa
                            if re.match(r"^(https?://|www\.)", cmd) or os.path.exists(os.path.expanduser(cmd)):
                                mpv_command(["loadfile", cmd, "append-play"])
                    else: input_mode = True

                elif tecla == '\x7f' and input_mode: # Backspace
                    input_buffer = input_buffer[:-1]; pintar(37, 5, " "*80)

                else:
                    if not input_mode:
                        if tecla == '/': input_mode = True; input_buffer = ""
                        elif tecla == ' ': mpv_command(["cycle", "pause"])
                        elif tecla in ['p', 'P']: mpv_command(["playlist-next"])
                        elif tecla in ['o', 'O']: mpv_command(["playlist-prev"])
                        elif tecla in ['+', '=']: mpv_command(["add", "volume", 5])
                        elif tecla == '-': mpv_command(["add", "volume", -5])
                    else: input_buffer += tecla

            # --- 2. OBTENER DATOS DE MPV Y CAVA ---
            media_title = mpv_query("media-title") or "TermiMusic: Esperando..."
            esta_pausado = mpv_query("pause")
            t_pos = mpv_query("time-pos") or 0
            t_dur = mpv_query("duration") or 0
            volumen = mpv_query("volume") or 0
            cola = mpv_query("playlist") or []
            ruta_archivo = mpv_query("path")
            if ruta_archivo: actualizar_miniatura(ruta_archivo)

            # Discord RPC (Cada 5s)
            if RPC and int(t_ahora) % 5 == 0:
                try: RPC.update(state=f"Modo: {modo_loop.upper()}", details=media_title[:120], large_image="logo")
                except: pass

            # Datos CAVA
            try:
                while True:
                    chunk = cava_proc.stdout.read(40)
                    if not chunk: break
                    raw_cava = chunk
            except: pass
            if esta_pausado: raw_cava = bytearray(40)

            # --- 3. MOTOR FÍSICO DEL DISCO ---
            reproduciendo = not esta_pausado and media_title != "TermiMusic: Esperando..."
            v_objetivo = (4.0 + (sum(raw_cava[:6])/(6*255.0) * 25.0)) if reproduciendo else 0.0

            if disco_v < v_objetivo: disco_v += 45.0 * dt
            else: disco_v -= 6.0 * dt

            disco_v = max(0.0, disco_v)
            disco_f += disco_v * dt

            # --- 4. RENDERIZADO DE INTERFAZ ---
            # Disco
            lines_disco = DISCO_ANIM[int(disco_f)%4].split("\n")
            for i, l in enumerate(lines_disco): pintar(2+i, 2, l, "\033[1;35m")

            # Miniatura / Arte
            if arte_cache:
                for i, l in enumerate(arte_cache): pintar(2+i, COL_R, l)
            else:
                for i in range(13): pintar(2+i, COL_R, " "*48)

            # Info de Canción
            y_base = 16
            pintar(y_base, COL_R, f"{'⏸ PAUSADO' if esta_pausado else '▶ SONANDO'} | LOOP: {modo_loop}", "\033[1;32m")
            pintar(y_base+1, COL_R, f"🎵 {scroll_texto(media_title, 48, t_ahora*4) if not esta_pausado else media_title[:48]}", "\033[1;37m")
            pintar(y_base+2, COL_R, f"🔊 VOL: {int(volumen)}%", "\033[1;36m")

            # Barra de Progreso Expansiva
            if t_dur > 0:
                columnas = os.get_terminal_size().columns
                caja_t = f"|{format_tiempo(t_pos)}/-{format_tiempo(t_dur-t_pos)}|"
                l_barra = max(20, columnas - COL_R - len(caja_t) - 2)
                prog = min(int((t_pos/t_dur)*l_barra), l_barra)
                str_barra = f"|{'█'*prog}{'-'*(l_barra-prog)}| {caja_t}"
                pintar(y_base+3, COL_R, f"{str_barra}{' '*(columnas-COL_R-len(str_barra))}", "\033[1;32m")

            # Módulo de Sistema
            cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
            pintar(y_base+5, COL_R, "┌─[ TERMI-STATS ]", "\033[1;36m")
            pintar(y_base+6, COL_R, f"└─ CPU: {cpu:04.1f}% | RAM: {ram:04.1f}% | DSC: {'ON' if RPC else 'OFF'}", "\033[1;36m")

            # Visualizador CAVA
            for b in range(len(raw_cava)):
                h = int((raw_cava[b]/255)*8)
                for r in range(8): pintar(33-r, 4+b, "┃" if r < h else " ", f"\033[38;5;{color_cava}m")

            # Cola de Reproducción
            pintar(25, COL_R, "➔ COLA ACTUAL:", "\033[1;34m")
            idx_act = next((i for i, it in enumerate(cola) if it.get("current")), -1)
            sig = cola[idx_act:] if idx_act != -1 else []
            for i in range(6):
                if i < len(sig):
                    t = sig[i].get("title") or sig[i].get("filename")
                    pintar(26+i, COL_R+2, f"{'▶' if sig[i].get('current') else str(i)}. {str(t)[:44]:<44}", "\033[1;32m" if sig[i].get("current") else "\033[0;90m")
                else: pintar(26+i, COL_R+2, " "*48)

            # Footer / Controles
            if t_ahora - error_time < 3: pintar(34, 4, f" \033[41;37m {msj_error} \033[0m")
            else: pintar(34, 4, " "*70)

            txt_modo = "\033[42;30m [MODO ESCRITURA] \033[0m" if input_mode else "\033[44;30m [TermiMusic CONTROL] \033[0m Space: Pausa | '/': Comandos"
            pintar(35, 4, txt_modo)
            pintar(36, 4, " \033[90m/save, /play <nom> | /loop <song|list|off> | /fx <bass|lofi|clear> | /color <N>\033[0m")
            if input_mode: pintar(37, 4, f" \033[1;37m> {input_buffer}█\033[0m{' '*(60-len(input_buffer))}")
            else: pintar(37, 4, " "*80)

            sys.stdout.flush(); time.sleep(0.04)

    except KeyboardInterrupt: pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_tty)
        mpv.terminate(); cava_proc.terminate()
        print("\033[?25h\033[H\033[2J") # Mostrar cursor y limpiar

if __name__ == "__main__":
    main()
