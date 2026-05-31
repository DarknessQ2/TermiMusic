#!/usr/bin/env python3
import subprocess, sys, time, os, fcntl, termios, tty, select, psutil, json, threading, re
from pypresence import Presence

# Importar nuestros motores
import config as cfg
import motor_media_bridge as media
import motor_comandos as cmd
import motor_grafico as gfx
import motor_lyrics

# Iniciar Discord RPC de forma segura
RPC = None
try:
    RPC = Presence('1491690103125573643')
    RPC.connect()
except: pass

# ===========================================================================
# 🎤 TRABAJO EN SEGUNDO PLANO: PROCESADOR DE LETRAS (BLINDADO)
# ===========================================================================
def despachar_busqueda_letras_web(titulo_cancion):
    """
    Función global aislada que invoca el motor_lyrics de forma segura.
    """
    cfg.Estado.buscando_lyric = True
    try:
        resultado_letras = motor_lyrics.buscar_lyrics(titulo_cancion)

        if not resultado_letras:
            cfg.Estado.lyrics_actuales = ["📭 Letra no encontrada", "   en base de datos."]
        else:
            if isinstance(resultado_letras, str):
                cfg.Estado.lyrics_actuales = resultado_letras.split("\n")
            elif isinstance(resultado_letras, list):
                cfg.Estado.lyrics_actuales = resultado_letras
            else:
                cfg.Estado.lyrics_actuales = ["⚠️ Formato inválido"]

    except Exception as e:
        cfg.Estado.lyrics_actuales = [
            "❌ Error de conexión",
            "   (Reintentando...)"
        ]
    finally:
        cfg.Estado.buscando_lyric = False

# ===========================================================================
# 🚀 FUNCIÓN PRINCIPAL DEL REPRODUCTOR
# ===========================================================================
def main():
    if not hasattr(cfg.Estado, 'modo_dinamico'):
        cfg.Estado.modo_dinamico = True
    if not hasattr(gfx, 'COLOR_CARATULA'):
        gfx.COLOR_CARATULA = (0, 255, 255)
    if not hasattr(cfg.Estado, 'ver_caratula'):
        cfg.Estado.ver_caratula = True
    if not hasattr(cfg.Estado, 'ver_lyrics'):
        cfg.Estado.ver_lyrics = True
    if not hasattr(cfg.Estado, 'last_track_lyric'):
        cfg.Estado.last_track_lyric = ""
    if not hasattr(cfg.Estado, 'lyrics_actuales'):
        cfg.Estado.lyrics_actuales = ["  Esperando metadatos..."]
    if not hasattr(cfg.Estado, 'buscando_lyric'):
        cfg.Estado.buscando_lyric = False
    if not hasattr(cfg.Estado, 'dl_active'):
        cfg.Estado.dl_active = False
    if not hasattr(cfg.Estado, 'error_time'):
        cfg.Estado.error_time = 0

    EXT_AUDIO = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus")

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

    gfx.cargar_animacion()

    estado_pantalla = "MENU"
    seleccion_disco = 0
    disco_agarrado = False
    anim_drop = 0

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

            pl_web = [f for f in os.listdir(cfg.PLAYLIST_DIR) if f.endswith(".json")] if os.path.exists(cfg.PLAYLIST_DIR) else []

            pl_loc = []
            if os.path.exists(cfg.DOWNLOAD_DIR):
                for f in os.listdir(cfg.DOWNLOAD_DIR):
                    ruta_f = os.path.join(cfg.DOWNLOAD_DIR, f)
                    if os.path.isdir(ruta_f) or f.lower().endswith(EXT_AUDIO):
                        pl_loc.append(f)

            lista_total = pl_web + pl_loc
            total_discos = len(lista_total)

            if select.select([sys.stdin], [], [], 0)[0]:
                tecla = sys.stdin.read(1)

                # ==== MODO MENÚ (ESTANTE DE DISCOS) ====
                if estado_pantalla == "MENU":
                    if tecla == '\x1b':
                        seq = ""
                        while select.select([sys.stdin], [], [], 0.05)[0]:
                            seq += sys.stdin.read(1)

                        if seq == "":
                            estado_pantalla = "REPRODUCTOR"
                            gfx.limpiar_pantalla()
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
                                gfx.limpiar_pantalla()
                        else:
                            if seq == "": input_mode = False; gfx.pintar(37, 5, " "*80)

                    elif tecla in ['\n', '\r']:
                        if input_mode:
                            comando_usuario = input_buffer.strip()
                            input_buffer, input_mode = "", False
                            gfx.pintar(37, 5, " "*80)

                            if comando_usuario:
                                # 🛠️ FIX: TU LÓGICA DE REFRESH CON PAUSA
                                if comando_usuario.lower() in ["/refresh", "/limpiar", "/clear"]:
                                    print("\033[2J\033[H", end="")
                                    sys.stdout.flush()
                                    time.sleep(2)
                                    cfg.Estado.msj_error = "✨ Pantalla redibujada"
                                    cfg.Estado.error_time = time.time()
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
                if lista_total and not disco_agarrado:
                    es_web = seleccion_disco < len(pl_web)
                    item_actual = lista_total[seleccion_disco]
                    ruta_completa = os.path.join(cfg.PLAYLIST_DIR, item_actual) if es_web else os.path.join(cfg.DOWNLOAD_DIR, item_actual)
                    gfx.actualizar_miniatura(ruta_completa)

                if disco_agarrado:
                    anim_drop += 1
                    if anim_drop > 10:
                        disco_agarrado, anim_drop = False, 0
                        estado_pantalla = "REPRODUCTOR"
                        gfx.limpiar_pantalla()

                        if lista_total:
                            item_target = lista_total[seleccion_disco]
                            es_cancion = item_target.lower().endswith(EXT_AUDIO)

                            if es_cancion:
                                ruta_cancion = os.path.abspath(os.path.join(cfg.DOWNLOAD_DIR, item_target))
                                media.mpv_command(["playlist-clear"])
                                media.mpv_command(["loadfile", ruta_cancion, "replace"])
                                cfg.Estado.msj_error = f"🎵 Sonando: {item_target[:25]}..."
                                cfg.Estado.error_time = time.time()
                            else:
                                nombre_target = item_target
                                for ext in ('.json', '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus'):
                                    if nombre_target.lower().endswith(ext):
                                        nombre_target = nombre_target[: -len(ext)]
                                        break
                                cmd.procesar(f"/play {nombre_target}")

                              # --- PROCESAMIENTO LIMPIO DE ETIQUETAS PARA LA CAJA DE DISCOS ---
                pl_web_PROCESADA = [x.replace('.json', '') for x in pl_web]
                pl_loc_PROCESADA = []
                for x in pl_loc:
                    if x.lower().endswith(EXT_AUDIO):
                        nombre_limpio = x
                        for ext in EXT_AUDIO:
                            if nombre_limpio.lower().endswith(ext):
                                nombre_limpio = nombre_limpio[: -len(ext)]
                                break
                        pl_loc_PROCESADA.append(nombre_limpio)
                    else:
                        pl_loc_PROCESADA.append(x)

                # 🛑 FIX: BARRERA DE ESTADO PARA EVITAR RENDERIZADO FANTASMA
                # Solo se permite ejecutar el renderizado del menú si el estado ES estrictamente MENU.
                # Si estado_pantalla cambió a "REPRODUCTOR" durante la animación, esta línea se omite.
                if estado_pantalla == "MENU":
                    gfx.render_menu_vinilos(pl_web_PROCESADA, pl_loc_PROCESADA, seleccion_disco, disco_agarrado, anim_drop)

            # --- LÓGICA Y RENDERIZADO DEL REPRODUCTOR ---
            else:
                if t_ahora - last_mpv_update > 0.5:
                    media_title = media.mpv_query("media-title") or "TermiMusic: Esperando..."
                    t_pos = media.mpv_query("time-pos") or 0
                    last_mpv_update = t_ahora

                    if (media_title and media_title != "TermiMusic: Esperando..." and media_title != cfg.Estado.last_track_lyric):
                        cfg.Estado.last_track_lyric = media_title
                        cfg.Estado.lyrics_actuales = ["🔎 Buscando letra..."]
                        threading.Thread(
                            target=despachar_busqueda_letras_web,
                            args=(media_title,),
                            daemon=True
                        ).start()

                    esta_pausado = media.mpv_query("pause")
                    t_dur = media.mpv_query("duration") or 0
                    volumen = media.mpv_query("volume") or 0
                    cola = media.mpv_query("playlist") or []
                    ruta_archivo = media.mpv_query("path")
                    cpu_stat = psutil.cpu_percent()
                    ram_stat = psutil.virtual_memory().percent

                    if ruta_archivo:
                        gfx.actualizar_miniatura(ruta_archivo)

                reproduciendo = not esta_pausado and media_title != "TermiMusic: Esperando..."
                v_objetivo = (4.0 + (sum(raw_cava[:6])/(6*255.0) * 25.0)) if reproduciendo else 0.0
                disco_v = disco_v + 45.0 * dt if disco_v < v_objetivo else disco_v - 6.0 * dt
                disco_v = max(0.0, disco_v)
                disco_f += disco_v * dt

                term_cols, term_lines = os.get_terminal_size()
                if term_lines < 38: gfx.pintar(1, 2, "\033[41;37m ⚠️ MAXIMIZA LA TERMINAL (Requiere 38 filas) \033[0m")

                if getattr(cfg.Estado, 'modo_dinamico', True):
                    r_c, g_c, b_c = gfx.COLOR_CARATULA if hasattr(gfx, 'COLOR_CARATULA') else (0, 255, 255)
                    color_ui = f"\033[38;2;{r_c};{g_c};{b_c}m"
                    color_ui_b = f"\033[38;2;{r_c};{g_c};{b_c};1m"
                    bg_control = f"\033[48;2;{r_c};{g_c};{b_c}m\033[1;30m"
                    color_cava_render = color_ui
                else:
                    color_ui = "\033[1;36m"
                    color_ui_b = "\033[1;35m"
                    bg_control = "\033[44;30m"
                    color_cava_render = f"\033[38;5;{getattr(cfg.Estado, 'color_cava', 6)}m"

                frames_disco = gfx.DISCO_ANIM if len(gfx.DISCO_ANIM) > 1 else [gfx.DISCO_ANIM[0]]
                frame_actual = frames_disco[int(disco_f) % len(frames_disco)]
                lines_disco = frame_actual.split("\n")
                for i, l in enumerate(lines_disco): gfx.pintar(2+i, 2, l, color_ui_b)

                if cfg.Estado.ver_caratula:
                    if hasattr(gfx, 'arte_cache') and gfx.arte_cache:
                        for i, l in enumerate(gfx.arte_cache): gfx.pintar(2+i, COL_R, l)
                    else:
                        for i in range(13): gfx.pintar(2+i, COL_R, " "*48)
                else:
                    for i in range(13): gfx.pintar(2+i, COL_R, " "*48)

                COL_LIRY = COL_R + 52
                if cfg.Estado.ver_lyrics:
                    ancho_caja = max(30, term_cols - COL_LIRY - 2)
                    ancho_texto = ancho_caja - 6

                    parsed_lyrics = []
                    for linea in cfg.Estado.lyrics_actuales:
                        match = re.search(r'\[(\d{2}:\d{2}\.\d{2})\]', linea)
                        texto = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', linea).strip()
                        marca = -1
                        if match:
                            try:
                                m, s = match.group(1).split(":")
                                marca = int(m) * 60 + float(s)
                            except: pass
                        parsed_lyrics.append((marca, texto))

                    active_idx = -1
                    for i, (marca, txt) in enumerate(parsed_lyrics):
                        if marca != -1 and t_pos >= marca:
                            active_idx = i
                        elif marca != -1 and t_pos < marca:
                            break

                    if active_idx == -1: active_idx = 0
                    start_idx = max(0, active_idx - 5)

                    borde_sup = "┌── Letras / Lyrics " + "─" * max(0, ancho_caja - 21) + "┐"
                    gfx.pintar(2, COL_LIRY, borde_sup, color_ui)

                    for i in range(11):
                        idx_real = start_idx + i
                        if idx_real < len(parsed_lyrics):
                            marca, texto = parsed_lyrics[idx_real]
                            es_activa = (idx_real == active_idx and marca != -1)

                            if es_activa:
                                if len(texto) > ancho_texto:
                                    txt_disp = gfx.scroll_texto(texto, ancho_texto, t_ahora*4)
                                else:
                                    txt_disp = texto[:ancho_texto]
                                gfx.pintar(3+i, COL_LIRY, f"│ {color_ui}▶ {txt_disp:<{ancho_texto}}\033[0m │", color_ui)
                            else:
                                txt_disp = texto[:ancho_texto]
                                if marca != -1 and t_pos >= marca:
                                    gfx.pintar(3+i, COL_LIRY, f"│ \033[0;37m  {txt_disp:<{ancho_texto}}\033[0m │", color_ui)
                                else:
                                    gfx.pintar(3+i, COL_LIRY, f"│ \033[0;90m  {txt_disp:<{ancho_texto}}\033[0m │", color_ui)
                        else:
                            gfx.pintar(3+i, COL_LIRY, f"│ {' ':<{ancho_caja-4}} │", color_ui)

                    borde_inf = "└" + "─" * max(0, ancho_caja - 2) + "┘"
                    gfx.pintar(14, COL_LIRY, borde_inf, color_ui)
                else:
                    espacio_limpiar = max(30, term_cols - COL_LIRY - 2)
                    for i in range(13): gfx.pintar(2+i, COL_LIRY, " "*espacio_limpiar)

                y_base = 16
                modo_loop = getattr(cfg.Estado, 'modo_loop', 'off')
                gfx.pintar(y_base, COL_R, f"{'⏸ PAUSADO' if esta_pausado else '▶ SONANDO'} | LOOP: {modo_loop}", color_ui_b)
                clean_title = os.path.basename(str(media_title)) if ruta_archivo and not str(ruta_archivo).startswith("http") else str(media_title)
                gfx.pintar(y_base+1, COL_R, f"🎵 {gfx.scroll_texto(clean_title, 48, t_ahora*4) if not esta_pausado else clean_title[:48]}", "\033[1;37m")
                gfx.pintar(y_base+2, COL_R, f"🔊 VOL: {int(volumen)}%", color_ui)

                if t_dur > 0:
                    caja_t = f"|{gfx.format_tiempo(t_pos)}/-{gfx.format_tiempo(t_dur-t_pos)}|"
                    l_barra = max(20, term_cols - COL_R - len(caja_t) - 35)
                    prog = min(int((t_pos/t_dur)*l_barra), l_barra)
                    gfx.pintar(y_base+3, COL_R, f"|{'█'*prog}{'-'*(l_barra-prog)}| {caja_t}{' '*(term_cols-COL_R-(l_barra+len(caja_t)+4))}", color_ui)

                gfx.pintar(y_base+5, COL_R, "┌─[ TERMI-STATS ]", color_ui)
                gfx.pintar(y_base+6, COL_R, f"└─ CPU: {cpu_stat:04.1f}% | RAM: {ram_stat:04.1f}% | DSC: {'ON' if RPC else 'OFF'}", color_ui)

                for b in range(len(raw_cava)):
                    h = int((raw_cava[b]/255)*8)
                    for r in range(8): gfx.pintar(33-r, 4+b, "┃" if r < h else " ", color_cava_render)

                gfx.pintar(24, COL_R, "➔ COLA ACTUAL:", color_ui_b)
                idx_act = next((i for i, it in enumerate(cola) if it.get("current")), -1)
                sig = cola[idx_act:] if idx_act != -1 else cola

                max_filas_cola = 8
                ancho_col = 38

                for fila in range(max_filas_cola):
                    idx_1 = fila
                    if idx_1 < len(sig):
                        t1 = sig[idx_1].get("title") or sig[idx_1].get("filename")
                        ct1 = os.path.basename(str(t1)) if t1 and not str(t1).startswith("http") else str(t1)
                        is_cur1 = sig[idx_1].get("current")
                        col_item1 = color_ui_b if is_cur1 else "\033[0;90m"

                        num1 = "▶" if is_cur1 else str(idx_act + idx_1 if idx_act != -1 else idx_1)
                        if is_cur1 and len(ct1) > (ancho_col - 4):
                            txt_disp1 = gfx.scroll_texto(ct1, ancho_col - 4, t_ahora*4)
                        else:
                            txt_disp1 = str(ct1)[:ancho_col - 4]

                        gfx.pintar(25+fila, COL_R, f"{num1}. {txt_disp1:<{ancho_col-4}}", col_item1)
                    else:
                        gfx.pintar(25+fila, COL_R, " " * ancho_col)

                    idx_2 = fila + max_filas_cola
                    if idx_2 < len(sig):
                        t2 = sig[idx_2].get("title") or sig[idx_2].get("filename")
                        ct2 = os.path.basename(str(t2)) if t2 and not str(t2).startswith("http") else str(t2)
                        is_cur2 = sig[idx_2].get("current")
                        col_item2 = color_ui_b if is_cur2 else "\033[0;90m"

                        num2 = "▶" if is_cur2 else str(idx_act + idx_2 if idx_act != -1 else idx_2)
                        if is_cur2 and len(ct2) > (ancho_col - 4):
                            txt_disp2 = gfx.scroll_texto(ct2, ancho_col - 4, t_ahora*4)
                        else:
                            txt_disp2 = str(ct2)[:ancho_col - 4]

                        gfx.pintar(25+fila, COL_R + ancho_col + 2, f"{num2}. {txt_disp2:<{ancho_col-4}}", col_item2)
                    else:
                        gfx.pintar(25+fila, COL_R + ancho_col + 2, " " * ancho_col)

                if getattr(cfg.Estado, 'dl_active', False):
                    dl_total = getattr(cfg.Estado, 'dl_total', 1)
                    dl_current = getattr(cfg.Estado, 'dl_current', 0)
                    dl_name = getattr(cfg.Estado, 'dl_name', 'Descarga')
                    pct = int((dl_current / dl_total) * 20) if dl_total > 0 else 0
                    gfx.pintar(34, 4, f"\033[44;37m ⬇️ DL '{dl_name[:15]}': [{'█'*pct}{'-'*(20-pct)}] {dl_current}/{dl_total} \033[0m".ljust(80))
                elif t_ahora - getattr(cfg.Estado, 'error_time', 0) < 3:
                    msj_error = getattr(cfg.Estado, 'msj_error', '')
                    gfx.pintar(34, 4, f" \033[41;37m {msj_error} \033[0m".ljust(80))
                else:
                    gfx.pintar(34, 4, " "*80)

                bg_modo = "\033[42;30m" if input_mode else bg_control
                gfx.pintar(35, 4, f"{bg_modo} [MODO ESCRITURA] \033[0m" if input_mode else f"{bg_modo} [TermiMusic CONTROL] \033[0m Space: Pausa | '/': Comandos | /dynamic: Alternar Color")
                gfx.pintar(36, 4, " \033[90m/save, /play, /quitar, /caratula, /lyrics, /mp3 | /random, /shuffle | /loop | /refresh\033[0m")
                if input_mode: gfx.pintar(37, 4, f" \033[1;37m> {input_buffer}█\033[0m{' '*(60-len(input_buffer))}")
                else: gfx.pintar(37, 4, " "*80)

            try:
                while True:
                    chunk = cava_proc.stdout.read(40)
                    if not chunk: break
                    if len(chunk) == 40:
                        raw_cava = bytearray(chunk)
            except IOError:
                pass

            if RPC and int(t_ahora) % 5 == 0:
                try:
                    RPC.update(
                        state=f"Modo: {getattr(cfg.Estado, 'modo_loop', 'off').upper()}",
                        details=media_title[:120],
                        large_image="logo"
                    )
                except:
                    pass

            sys.stdout.flush()
            time.sleep(0.04)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_tty)
        mpv.terminate()
        cava_proc.terminate()
        print("\033[49;39m\033[?25h\033[H\033[2J")

if __name__ == "__main__":
    main()
