#!/usr/bin/env python3
import subprocess, sys, time, os, fcntl, termios, tty, select, psutil
from pypresence import Presence

# Importar nuestros motores
import config as cfg
import motor_media_bridge as media
import motor_comandos as cmd
import motor_grafico as gfx

# Iniciar Discord
RPC = None
try:
    RPC = Presence('1491690103125573643')
    RPC.connect()
except: pass

def main():
    # 🛡️ ESCUDO DE CONTROL (Evita fallos si config.py o motor_grafico.py no se actualizaron)
    if not hasattr(cfg.Estado, 'modo_dinamico'):
        cfg.Estado.modo_dinamico = True
    if not hasattr(gfx, 'COLOR_CARATULA'):
        gfx.COLOR_CARATULA = (0, 255, 255)
    # ---------------------------------------------------------------------------

    with open(cfg.CAVA_CONF_PATH, "w") as f:
        f.write("[general]\nbars = 40\nsensitivity = 100\n[output]\nmethod = raw\nraw_target = /dev/stdout\nbit_format = 8bit\n")

    os.system("clear")
    print("\033[?25l", end="")

    mpv = subprocess.Popen(["mpv","--idle=yes","--no-video","--vid=no","--ytdl-format=bestaudio",
         "--force-window=no","--audio-display=no","--quiet",f"--input-ipc-server={cfg.SOCKET}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(100):
        if os.path.exists(cfg.SOCKET): break
        time.sleep(0.01)

    cava_proc = subprocess.Popen(["cava","-p",cfg.CAVA_CONF_PATH], stdout=subprocess.PIPE)
    fcntl.fcntl(cava_proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    # --- INICIALIZAR ESTADO GRÁFICO DEL MENÚ ---
    gfx.cargar_animacion()

    # Se fuerza el inicio siempre en MENU
    estado_pantalla = "MENU"
    seleccion_disco = 0
    disco_agarrado = False
    anim_drop = 0
    # -------------------------------------------

    input_buffer = ""
    input_mode = False
    disco_f, disco_v = 0.0, 0.0
    t_anterior = time.time()
    raw_cava = bytearray(40)

    last_mpv_update = 0
    media_title, esta_pausado = "TermiMusic: Esperando...", True
    t_pos, t_dur, volumen, cpu_stat, ram_stat = 0, 0, 0, 0.0, 0.0
    cola, ruta_archivo = [], None
    COL_R = 54

    fd = sys.stdin.fileno()
    original_tty = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    try:
        while True:
            t_ahora = time.time()
            dt = t_ahora - t_anterior
            t_anterior = t_ahora

            if select.select([sys.stdin], [], [], 0)[0]:
                tecla = sys.stdin.read(1)

                # ==== MODO MENÚ (ESTANTE DE DISCOS) ====
                if estado_pantalla == "MENU":
                    pl_web = [f for f in os.listdir(cfg.PLAYLIST_DIR) if f.endswith(".json")] if os.path.exists(cfg.PLAYLIST_DIR) else []
                    pl_loc = [f for f in os.listdir(cfg.DOWNLOAD_DIR) if os.path.isdir(os.path.join(cfg.DOWNLOAD_DIR, f))] if os.path.exists(cfg.DOWNLOAD_DIR) else []
                    total_discos = len(pl_web) + len(pl_loc)

                    if tecla == '\x1b':
                        seq = ""
                        while select.select([sys.stdin], [], [], 0.05)[0]:
                            seq += sys.stdin.read(1)

                        if seq == "":
                            estado_pantalla = "REPRODUCTOR"
                            gfx.pintar(1,1, "\033[2J\033[H")
                        elif "A" in seq and total_discos > 0:
                            seleccion_disco = (seleccion_disco - 1) % total_discos
                        elif "B" in seq and total_discos > 0:
                            seleccion_disco = (seleccion_disco + 1) % total_discos

                    elif tecla in ['o', 'O'] and total_discos > 0:
                        seleccion_disco = (seleccion_disco - 1) % total_discos
                    elif tecla in ['p', 'P'] and total_discos > 0:
                        seleccion_disco = (seleccion_disco + 1) % total_discos
                    elif tecla in ['\n', '\r']:
                        if total_discos > 0 and not disco_agarrado:
                            disco_agarrado = True

                # ==== MODO REPRODUCTOR ====
                else:
                    if tecla == '\x1b':
                        seq = ""
                        while select.select([sys.stdin], [], [], 0.05)[0]:
                            seq += sys.stdin.read(1)

                        if not input_mode:
                            if "C" in seq: media.mpv_command(["playlist-next"])
                            elif "D" in seq: media.mpv_command(["playlist-prev"])
                            elif "A" in seq: media.mpv_command(["add", "volume", 5])
                            elif "B" in seq: media.mpv_command(["add", "volume", -5])
                            elif seq == "":
                                estado_pantalla = "MENU"
                                gfx.pintar(1,1, "\033[2J\033[H")
                        else:
                            if seq == "": input_mode = False; gfx.pintar(37, 5, " "*80)

                    elif tecla in ['\n', '\r']:
                        if input_mode:
                            comando_usuario = input_buffer.strip()
                            input_buffer, input_mode = "", False
                            gfx.pintar(37, 5, " "*80)
                            if comando_usuario:
                                # 🔄 INTERCEPTOR CORREGIDO: Resetea el motor gráfico al cambiar de modo
                                if comando_usuario == "/dynamic":
                                    cfg.Estado.modo_dinamico = not cfg.Estado.modo_dinamico
                                    cfg.Estado.guardar()  # 💾 Persistencia inmediata
                                    gfx.COLOR_CARATULA = gfx.COLOR_DEFECTO # Forzar reset de paleta
                                    if ruta_archivo:
                                        gfx.ruta_actual = "" # Forzar recarga de miniatura
                                        gfx.actualizar_miniatura(ruta_archivo)
                                else:
                                    cmd.procesar(comando_usuario)
                        else: input_mode = True

                    elif tecla == '\x7f' and input_mode:
                        input_buffer = input_buffer[:-1]; gfx.pintar(37, 5, " "*80)

                    else:
                        if not input_mode:
                            if tecla == '/': input_mode, input_buffer = True, ""
                            elif tecla == ' ': media.mpv_command(["cycle", "pause"])
                            elif tecla in ['p', 'P']: media.mpv_command(["playlist-next"])
                            elif tecla in ['o', 'O']: media.mpv_command(["playlist-prev"])
                            elif tecla in ['+', '=']: media.mpv_command(["add", "volume", 5])
                            elif tecla == '-': media.mpv_command(["add", "volume", -5])
                        else: input_buffer += tecla

            # --- LÓGICA Y ANIMACIÓN DE LA TIENDA DE VINILOS ---
            if estado_pantalla == "MENU":
                pl_web = [f for f in os.listdir(cfg.PLAYLIST_DIR) if f.endswith(".json")] if os.path.exists(cfg.PLAYLIST_DIR) else []
                pl_loc = [f for f in os.listdir(cfg.DOWNLOAD_DIR) if os.path.isdir(os.path.join(cfg.DOWNLOAD_DIR, f))] if os.path.exists(cfg.DOWNLOAD_DIR) else []

                # CORRECCIÓN DE RUTA COMPLETA PARA ACTUALIZAR COLOR DINÁMICO AL HOJEAR
                if (pl_web + pl_loc) and not disco_agarrado:
                    es_web = seleccion_disco < len(pl_web)
                    item_actual = (pl_web + pl_loc)[seleccion_disco]
                    ruta_completa = os.path.join(cfg.PLAYLIST_DIR, item_actual) if es_web else os.path.join(cfg.DOWNLOAD_DIR, item_actual)
                    gfx.actualizar_miniatura(ruta_completa)

                if disco_agarrado:
                    anim_drop += 1
                    if anim_drop > 10:
                        disco_agarrado, anim_drop = False, 0
                        estado_pantalla = "REPRODUCTOR"
                        gfx.pintar(1,1, "\033[2J\033[H")
                        sys.stdout.flush()

                        if (pl_web + pl_loc):
                            nombre_target = (pl_web + pl_loc)[seleccion_disco].replace(".json", "")
                            cmd.procesar(f"/play {nombre_target}")
                        continue

                gfx.render_menu_vinilos(pl_web, pl_loc, seleccion_disco, disco_agarrado, anim_drop)
                try:
                    while cava_proc.stdout.read(40): pass
                except: pass
                time.sleep(0.04)
                continue

            # --- OBTENER DATOS DEL REPRODUCTOR (THROTTLED) ---
            if t_ahora - last_mpv_update > 0.25:
                media_title = media.mpv_query("media-title") or "TermiMusic: Esperando..."
                esta_pausado = media.mpv_query("pause")
                t_pos = media.mpv_query("time-pos") or 0
                t_dur = media.mpv_query("duration") or 0
                volumen = media.mpv_query("volume") or 0
                cola = media.mpv_query("playlist") or []
                ruta_archivo = media.mpv_query("path")
                cpu_stat = psutil.cpu_percent()
                ram_stat = psutil.virtual_memory().percent
                last_mpv_update = t_ahora

                if ruta_archivo: gfx.actualizar_miniatura(ruta_archivo)
                if RPC and int(t_ahora) % 5 == 0:
                    try: RPC.update(state=f"Modo: {cfg.Estado.modo_loop.upper()}", details=media_title[:120], large_image="logo")
                    except: pass

            try:
                while True:
                    chunk = cava_proc.stdout.read(40)
                    if not chunk: break
                    raw_cava = chunk
            except: pass
            if esta_pausado: raw_cava = bytearray(40)

            # Físicas del disco
            reproduciendo = not esta_pausado and media_title != "TermiMusic: Esperando..."
            v_objetivo = (4.0 + (sum(raw_cava[:6])/(6*255.0) * 25.0)) if reproduciendo else 0.0
            disco_v = disco_v + 45.0 * dt if disco_v < v_objetivo else disco_v - 6.0 * dt
            disco_v = max(0.0, disco_v)
            disco_f += disco_v * dt

            term_cols, term_lines = os.get_terminal_size()
            if term_lines < 38: gfx.pintar(1, 2, f"\033[41;37m ⚠️ MAXIMIZA LA TERMINAL (Requiere 38 filas) \033[0m")

            # =====================================================================
            # 🎨 EVALUACIÓN DEL [DYNAMIC MODE BLOCK]
            # =====================================================================
            if cfg.Estado.modo_dinamico:
                r_c, g_c, b_c = gfx.COLOR_CARATULA
                color_ui = f"\033[38;2;{r_c};{g_c};{b_c}m"
                color_ui_b = f"\033[38;2;{r_c};{g_c};{b_c};1m"
                bg_control = f"\033[48;2;{r_c};{g_c};{b_c}m\033[1;30m"
                color_cava_render = color_ui
            else:
                color_ui = "\033[1;36m"          # Cyan estático
                color_ui_b = "\033[1;35m"        # Magenta de acento
                bg_control = "\033[44;30m"        # Fondo azul para barra
                color_cava_render = f"\033[38;5;{cfg.Estado.color_cava}m"

            # --- RENDERIZAR INTERFAZ DEL REPRODUCTOR ---
            frames_disco = gfx.DISCO_ANIM if len(gfx.DISCO_ANIM) > 1 else [gfx.DISCO_ANIM[0]]
            frame_actual = frames_disco[int(disco_f) % len(frames_disco)]
            lines_disco = frame_actual.split("\n")

            for i, l in enumerate(lines_disco): gfx.pintar(2+i, 2, l, color_ui_b)

            if gfx.arte_cache:
                for i, l in enumerate(gfx.arte_cache): gfx.pintar(2+i, COL_R, l)
            else:
                for i in range(13): gfx.pintar(2+i, COL_R, " "*48)

            y_base = 16
            gfx.pintar(y_base, COL_R, f"{'⏸ PAUSADO' if esta_pausado else '▶ SONANDO'} | LOOP: {cfg.Estado.modo_loop}", color_ui_b)
            clean_title = os.path.basename(str(media_title)) if ruta_archivo and not str(ruta_archivo).startswith("http") else str(media_title)
            gfx.pintar(y_base+1, COL_R, f"🎵 {gfx.scroll_texto(clean_title, 48, t_ahora*4) if not esta_pausado else clean_title[:48]}", "\033[1;37m")
            gfx.pintar(y_base+2, COL_R, f"🔊 VOL: {int(volumen)}%", color_ui)

            if t_dur > 0:
                caja_t = f"|{gfx.format_tiempo(t_pos)}/-{gfx.format_tiempo(t_dur-t_pos)}|"
                l_barra = max(20, term_cols - COL_R - len(caja_t) - 2)
                prog = min(int((t_pos/t_dur)*l_barra), l_barra)
                gfx.pintar(y_base+3, COL_R, f"|{'█'*prog}{'-'*(l_barra-prog)}| {caja_t}{' '*(term_cols-COL_R-(l_barra+len(caja_t)+4))}", color_ui)

            gfx.pintar(y_base+5, COL_R, "┌─[ TERMI-STATS ]", color_ui)
            gfx.pintar(y_base+6, COL_R, f"└─ CPU: {cpu_stat:04.1f}% | RAM: {ram_stat:04.1f}% | DSC: {'ON' if RPC else 'OFF'}", color_ui)

            # RENDERIZADO DEL ESPECTRO CAVA CON COLOR ADAPTATIVO
            for b in range(len(raw_cava)):
                h = int((raw_cava[b]/255)*8)
                for r in range(8): gfx.pintar(33-r, 4+b, "┃" if r < h else " ", color_cava_render)

            gfx.pintar(25, COL_R, "➔ COLA ACTUAL:", color_ui_b)
            idx_act = next((i for i, it in enumerate(cola) if it.get("current")), -1)
            sig = cola[idx_act:] if idx_act != -1 else []
            for i in range(6):
                if i < len(sig):
                    t = sig[i].get("title") or sig[i].get("filename")
                    clean_t = os.path.basename(str(t)) if t and not str(t).startswith("http") else str(t)
                    color_item = color_ui_b if sig[i].get("current") else "\033[0;90m"
                    gfx.pintar(26+i, COL_R+2, f"{'▶' if sig[i].get('current') else str(i)}. {str(clean_t)[:44]:<44}", color_item)
                else: gfx.pintar(26+i, COL_R+2, " "*48)

            if cfg.Estado.dl_active:
                pct = int((cfg.Estado.dl_current / cfg.Estado.dl_total) * 20) if cfg.Estado.dl_total > 0 else 0
                gfx.pintar(34, 4, f"\033[44;37m ⬇️ DL '{cfg.Estado.dl_name[:15]}': [{'█'*pct}{'-'*(20-pct)}] {cfg.Estado.dl_current}/{cfg.Estado.dl_total} \033[0m".ljust(80))
            elif t_ahora - cfg.Estado.error_time < 3:
                gfx.pintar(34, 4, f" \033[41;37m {cfg.Estado.msj_error} \033[0m".ljust(80))
            else: gfx.pintar(34, 4, " "*80)

            # Barra inferior adaptativa
            bg_modo = "\033[42;30m" if input_mode else bg_control
            gfx.pintar(35, 4, f"{bg_modo} [MODO ESCRITURA] \033[0m" if input_mode else f"{bg_modo} [TermiMusic CONTROL] \033[0m Space: Pausa | '/': Comandos | /dynamic: Alternar Color")
            gfx.pintar(36, 4, " \033[90m/save, /play, /quitar | /random, /rsong | /shuffle | /loop | /fx\033[0m")
            if input_mode: gfx.pintar(37, 4, f" \033[1;37m> {input_buffer}█\033[0m{' '*(60-len(input_buffer))}")
            else: gfx.pintar(37, 4, " "*80)

            sys.stdout.flush(); time.sleep(0.04)

    except KeyboardInterrupt: pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_tty)
        mpv.terminate(); cava_proc.terminate()
        print("\033[49;39m\033[?25h\033[H\033[2J")

if __name__ == "__main__":
    main()
