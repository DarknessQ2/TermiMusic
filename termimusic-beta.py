#!/usr/bin/env python3
import subprocess, sys, time, os, json, fcntl, termios, tty, select, urllib.request, io, re, threading

try:
    from PIL import Image
    import psutil
    from pypresence import Presence
except ImportError:
    print("\033[1;31mError: Faltan dependencias. Ejecuta:\n  pip install Pillow psutil pypresence --break-system-packages\033[0m")
    sys.exit(1)

SOCKET = "/tmp/mpv-socket"
CAVA_CONF = "/tmp/cava_tmp_config"
PLAYLIST_FILE = os.path.expanduser("~/.config/webmusic_playlists.json")

os.makedirs(os.path.dirname(PLAYLIST_FILE), exist_ok=True)

# CONFIG DISCORD (ID genérico para TermiMusic)
client_id = '1226912345678901234'
RPC = None
try:
    RPC = Presence(client_id)
    RPC.connect()
except: RPC = None

def load_playlists():
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "r") as f: return json.load(f)
    return {}

def save_playlists(data):
    with open(PLAYLIST_FILE, "w") as f: json.dump(data, f, indent=4)

saved_playlists = load_playlists()

with open(CAVA_CONF, "w") as f:
    f.write("[general]\nbars = 40\nsensitivity = 100\n[output]\nmethod = raw\nraw_target = /dev/stdout\nbit_format = 8bit\n")

os.system("clear")
print("\033[?25l", end="")

# PROCESOS
mpv = subprocess.Popen(
    ["mpv","--idle=yes","--no-video","--vid=no","--ytdl-format=bestaudio",
     "--force-window=no","--audio-display=no","--quiet",f"--input-ipc-server={SOCKET}"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

for _ in range(100):
    if os.path.exists(SOCKET): break
    time.sleep(0.01)

cava_proc = subprocess.Popen(["cava","-p",CAVA_CONF],stdout=subprocess.PIPE)
fcntl.fcntl(cava_proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

RAW_FRAMES = [
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

def mpv_query(prop):
    try:
        cmd=json.dumps({"command":["get_property",prop]})+"\n"
        p=subprocess.Popen(["socat","-",f"UNIX-CONNECT:{SOCKET}"],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        out,_=p.communicate(input=cmd.encode(),timeout=0.03)
        return json.loads(out.decode()).get("data")
    except: return None

def mpv_command(cmd):
    try:
        data=json.dumps({"command":cmd})+"\n"
        subprocess.Popen(["socat","-",f"UNIX-CONNECT:{SOCKET}"],
            stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\
            .communicate(input=data.encode(),timeout=0.03)
    except: pass

def draw_at(r, c, text, color="\033[0m"):
    sys.stdout.write(f"\033[{r};{c}H{color}{text}\033[0m")

def format_time(s):
    if not s: return "00:00"
    m, s = divmod(int(s), 60)
    return f"{m:02d}:{s:02d}"

def scroll_text(text, width, t_step):
    if len(text) <= width: return f"{text:<{width}}"
    pad_text = text + "   •   "
    offset = int(t_step) % len(pad_text)
    return (pad_text[offset:] + pad_text[:offset])[:width]

# CARÁTULA
thumb_art = None
curr_path = ""
def update_thumb(path):
    global thumb_art, curr_path
    if path == curr_path: return
    curr_path = path
    yt_id = re.search(r"(?:v=|be/)([a-zA-Z0-9_-]{11})", path) if path else None
    if yt_id:
        def fetch():
            global thumb_art
            try:
                url = f"https://i.ytimg.com/vi/{yt_id.group(1)}/mqdefault.jpg"
                with urllib.request.urlopen(url, timeout=2) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB").resize((48,26), Image.Resampling.LANCZOS)
                    lines = []
                    for y in range(0, 26, 2):
                        l = ""
                        for x in range(48):
                            r1,g1,b1 = img.getpixel((x,y))
                            r2,g2,b2 = img.getpixel((x,y+1))
                            l += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀"
                        lines.append(l)
                    thumb_art = lines
            except: thumb_art = None
        threading.Thread(target=fetch, daemon=True).start()
    else: thumb_art = None

# VARIABLES GLOBALES
input_buffer = ""
input_mode = False
cava_color = "197"
error_msg = ""
error_time = 0
loop_mode = "off"

disco_frame = 0.0
disco_speed = 0.0
last_time = time.time()
ultimo_cava = bytearray(40)

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
tty.setcbreak(fd)

COL_INFO = 54
ANCHO_UI = 48

# Inicializar psutil
psutil.cpu_percent()

try:
    while True:
        sys_time = time.time()
        dt = sys_time - last_time
        last_time = sys_time

        # INPUT
        if select.select([sys.stdin], [], [], 0)[0]:
            k = sys.stdin.read(1)
            if k == '\x1b':
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    seq = sys.stdin.read(2)
                    if not input_mode:
                        if seq == "[C": mpv_command(["playlist-next"])
                        elif seq == "[D": mpv_command(["playlist-prev"])
                        elif seq == "[A": mpv_command(["add", "volume", 5])
                        elif seq == "[B": mpv_command(["add", "volume", -5])
                else: input_mode = False; draw_at(37, 5, " "*80)
            elif k == '\n':
                if input_mode:
                    cmd = input_buffer.strip()
                    input_buffer = ""
                    input_mode = False
                    draw_at(37, 5, " "*80)

                    # --- GESTOR DE PLAYLISTS ---
                    if cmd.startswith("/save "):
                        name = cmd.split(" ", 1)[1]
                        pl = mpv_query("playlist") or []
                        urls = [item.get("filename") for item in pl if item.get("filename")]
                        if urls:
                            saved_playlists[name] = urls
                            save_playlists(saved_playlists)
                    elif cmd.startswith("/play "):
                        name = cmd.split(" ", 1)[1]
                        if name in saved_playlists:
                            mpv_command(["playlist-clear"])
                            for u in saved_playlists[name]: mpv_command(["loadfile", u, "append"])
                            mpv_command(["playlist-play-index", 0])
                        else: error_msg = "❌ Error: Playlist no encontrada."; error_time = sys_time
                    elif cmd.startswith("/add "):
                        name = cmd.split(" ", 1)[1]
                        if name in saved_playlists:
                            for u in saved_playlists[name]: mpv_command(["loadfile", u, "append"])
                        else: error_msg = "❌ Error: Playlist no encontrada."; error_time = sys_time

                    # --- EFECTOS Y CONTROL ---
                    elif cmd.startswith("/loop "):
                        mode = cmd.split(" ")[1]
                        if mode == "song": mpv_command(["set", "loop-file", "inf"]); loop_mode = "SONG"
                        elif mode == "list": mpv_command(["set", "loop-playlist", "inf"]); loop_mode = "LIST"
                        else: mpv_command(["set", "loop-file", "no"]); mpv_command(["set", "loop-playlist", "no"]); loop_mode = "off"
                    elif cmd.startswith("/fx "):
                        mode = cmd.split(" ")[1]
                        if mode == "bass": mpv_command(["set", "af", "equalizer=f=60:width_type=o:w=1:g=12"])
                        elif mode == "lofi": mpv_command(["set", "af", "lowpass=f=3000,highpass=f=200,acompressor"])
                        else: mpv_command(["set", "af", ""])
                    elif cmd.startswith("/color "):
                        c = cmd.split(" ", 1)[1]
                        if c.isdigit() and 0 <= int(c) <= 255: cava_color = c
                        else: error_msg = "❌ Error: Color inválido (0-255)."; error_time = sys_time

                    # --- CARGA DIRECTA ---
                    elif cmd:
                        if re.match(r"^(https?://|www\.)", cmd) or os.path.exists(os.path.expanduser(cmd)):
                            mpv_command(["loadfile", cmd, "append-play"])
                        else: error_msg = "❌ Error: Link o archivo inválido."; error_time = sys_time
                else: input_mode = True
            elif k == '\x7f' and input_mode: input_buffer = input_buffer[:-1]; draw_at(37, 5, " "*80)
            elif k == '\x12': os.system("clear"); draw_at(37, 5, " "*80)
            else:
                if not input_mode:
                    if k == '/': input_mode = True; input_buffer = ""
                    elif k == ' ': mpv_command(["cycle", "pause"])
                    elif k in ['+', '=']: mpv_command(["add", "volume", 5])
                    elif k == '-': mpv_command(["add", "volume", -5])
                    elif k in ['p', 'P']: mpv_command(["playlist-next"])
                    elif k in ['o', 'O']: mpv_command(["playlist-prev"])
                else: input_buffer += k

        # DATOS MPV
        title = mpv_query("media-title") or "Esperando música..."
        paused = mpv_query("pause")
        curr_t = mpv_query("time-pos") or 0
        dur_t = mpv_query("duration") or 0
        vol = mpv_query("volume") or 0
        playlist = mpv_query("playlist") or []
        path = mpv_query("path")
        if path: update_thumb(path)

        # DISCORD UPDATE
        if RPC and int(sys_time) % 5 == 0:
            try:
                RPC.update(state=f"En {loop_mode.upper()}" if loop_mode != "off" else "Escuchando",
                           details=title[:120], large_image="logo", large_text="TermiMusic")
            except: pass

        # CAVA
        try:
            while True:
                chunk = cava_proc.stdout.read(40)
                if not chunk: break
                ultimo_cava = chunk
        except: pass
        if paused: ultimo_cava = bytearray(40)

        # FÍSICAS DISCO
        is_playing = not paused and title != "Esperando música..."
        target_speed = (4.0 + (sum(ultimo_cava[:6])/(6*255.0) * 25.0)) if is_playing else 0.0
        if disco_speed < target_speed: disco_speed += 45.0 * dt
        else: disco_speed -= 6.0 * dt
        disco_speed = max(0.0, disco_speed)
        disco_frame += disco_speed * dt

        # DIBUJO DISCO
        disco_lines = RAW_FRAMES[int(disco_frame)%4].split("\n")
        for i, line in enumerate(disco_lines): draw_at(2+i, 2, line, "\033[1;35m")

        # INFO PANEL
        if thumb_art:
            for i, l in enumerate(thumb_art): draw_at(2+i, COL_INFO, l)
        else:
            for i in range(13): draw_at(2+i, COL_INFO, " "*ANCHO_UI)

        base_y = 16
        draw_at(base_y, COL_INFO, f"{'⏸ PAUSADO' if paused else '▶ SONANDO'} | LOOP: {loop_mode}", "\033[1;32m")
        draw_at(base_y+1, COL_INFO, f"🎵 {scroll_text(title, ANCHO_UI, sys_time*4) if not paused else title[:ANCHO_UI]}", "\033[1;37m")
        draw_at(base_y+2, COL_INFO, f"🔊 VOL: {int(vol)}%", "\033[1;36m")

        # BARRA DINÁMICA
        if dur_t > 0:
            try: term_cols = os.get_terminal_size().columns
            except: term_cols = 120

            t_box = f"|{format_time(curr_t)}/-{format_time(dur_t-curr_t)}|"
            b_len = max(20, term_cols - COL_INFO - len(t_box) - 2)
            p = int((curr_t/dur_t)*b_len)
            p = min(p, b_len)
            bar = f"|{'█'*p}{'-'*(b_len-p)}|"

            full_str = f"{bar} {t_box}"
            limpiador = " " * max(0, term_cols - COL_INFO - len(full_str))
            draw_at(base_y+3, COL_INFO, f"{full_str}{limpiador}", "\033[1;32m")

        # SYS STATS
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        temp_str = "--°C"
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps and list(temps.values())[0]:
                temp_str = f"{list(temps.values())[0][0].current:.0f}°C"

        draw_at(base_y+5, COL_INFO, "┌─[ SYS STATS ]", "\033[1;36m")
        draw_at(base_y+6, COL_INFO, f"└─ CPU: \033[0m{cpu:04.1f}%\033[1;36m | RAM: \033[0m{ram:04.1f}%\033[1;36m | TMP: \033[0m{temp_str:<5}\033[1;36m | DSC: \033[0m{'ON' if RPC else 'OFF'}", "\033[1;36m")

        # CAVA VISUAL
        cava_base = 33
        max_h = 8
        for b in range(len(ultimo_cava)):
            h = int((ultimo_cava[b]/255)*max_h)
            for r in range(max_h):
                char = "┃" if r < h else " "
                draw_at(cava_base-r, 4+b, char, f"\033[38;5;{cava_color}m")

        # PLAYLIST
        draw_at(25, COL_INFO, "➔ COLA TermiMusic:", "\033[1;34m")
        curr_idx = next((i for i, it in enumerate(playlist) if it.get("current")), -1)
        upcoming = playlist[curr_idx:] if curr_idx != -1 else []
        for idx in range(6):
            if idx < len(upcoming):
                t = upcoming[idx].get("title") or upcoming[idx].get("filename")
                draw_at(26+idx, COL_INFO+2, f"{'▶' if upcoming[idx].get('current') else str(idx)}. {str(t)[:ANCHO_UI-4]:<{ANCHO_UI-4}}", "\033[1;32m" if upcoming[idx].get("current") else "\033[0;90m")
            else: draw_at(26+idx, COL_INFO+2, " "*ANCHO_UI)

        # UI INF
        if sys_time - error_time < 3: draw_at(34, 4, f" \033[41;37m {error_msg} \033[0m{' '*(60-len(error_msg))}")
        else: draw_at(34, 4, " "*70)

        modo_txt = "\033[42;30m [ESCRIBIENDO] \033[0m" if input_mode else "\033[44;30m [CONTROLES] \033[0m Space: Pausa | p/o: Nav | '/': Comandos"
        draw_at(35, 4, modo_txt)
        draw_at(36, 4, " \033[90mCmds: /save, /play, /add <nom> | /loop <song|list|off> | /fx <bass|lofi|clear> | /color <N>\033[0m")
        if input_mode: draw_at(37, 4, f" \033[1;37m> {input_buffer}█\033[0m{' '*(60-len(input_buffer))}")
        else: draw_at(37, 4, " "*80)

        sys.stdout.flush(); time.sleep(0.04)

except KeyboardInterrupt: pass
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
    mpv.terminate(); cava_proc.terminate()
    print("\033[?25h\033[H\033[2J")
