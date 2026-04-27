import os, re, time, random, threading
import config as cfg
import motor_media_bridge as media  # <--- Importamos el puente aquí también

def procesar(cmd):
    t_ahora = time.time()

    if cmd.startswith("/save "):
        nombre = cmd.split(" ", 1)[1]
        pl = media.mpv_query("playlist") or []
        canciones = [{"titulo": i.get("title") or i.get("filename"), "url": i.get("filename")} for i in pl if i.get("filename")]
        if canciones:
            media.guardar_playlist(nombre, canciones)
            cfg.Estado.msj_error, cfg.Estado.error_time = f"✅ Playlist '{nombre}' guardada", t_ahora

    elif cmd.startswith("/play "):
        nombre = cmd.split(" ", 1)[1]
        carpeta_local = os.path.join(cfg.DOWNLOAD_DIR, nombre)

        if os.path.isdir(carpeta_local):
            archivos = [os.path.join(carpeta_local, f) for f in os.listdir(carpeta_local) if f.lower().endswith(('.mp3', '.m4a', '.webm', '.ogg', '.flac', '.wav'))]
            if archivos:
                media.mpv_command(["playlist-clear"])
                for arch in sorted(archivos): media.mpv_command(["loadfile", arch, "append"])
                media.mpv_command(["playlist-play-index", 0])
                cfg.Estado.msj_error, cfg.Estado.error_time = f"📂 Local Offline: '{nombre}'", t_ahora
            else: cfg.Estado.msj_error, cfg.Estado.error_time = f"❌ Carpeta '{nombre}' vacía", t_ahora
        else:
            datos = media.cargar_playlist(nombre)
            if datos:
                media.mpv_command(["playlist-clear"])
                for item in datos: media.mpv_command(["loadfile", item["url"] if isinstance(item, dict) else item, "append"])
                media.mpv_command(["playlist-play-index", 0])
                cfg.Estado.msj_error, cfg.Estado.error_time = f"🌐 Streaming Web: '{nombre}'", t_ahora
            else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ No existe esa playlist", t_ahora

    elif cmd in ["/random", "/mixall"]:
        todas = media.obtener_toda_la_biblioteca()
        if todas:
            random.shuffle(todas)
            media.mpv_command(["playlist-clear"])
            limite = min(100, len(todas))
            for url in todas[:limite]: media.mpv_command(["loadfile", url, "append"])
            media.mpv_command(["playlist-play-index", 0])
            cfg.Estado.msj_error, cfg.Estado.error_time = f"🔀 Mix creado ({limite} pistas)", t_ahora
        else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Biblioteca vacía", t_ahora

    elif cmd in ["/rsong", "/randomsong"]:
        todas = media.obtener_toda_la_biblioteca()
        if todas:
            media.mpv_command(["loadfile", random.choice(todas), "append-play"])
            cfg.Estado.msj_error, cfg.Estado.error_time = "🎲 Añadida canción sorpresa", t_ahora
        else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Biblioteca vacía", t_ahora

    elif cmd.startswith(("/dl", "/download")):
        args = cmd.split(" ", 1)
        if len(args) > 1:
            datos = media.cargar_playlist(args[1])
            if datos:
                cfg.Estado.msj_error, cfg.Estado.error_time = f"⬇️ Bajando playlist '{args[1]}'...", t_ahora
                threading.Thread(target=media.dl_playlist_thread, args=(args[1], datos), daemon=True).start()
            else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Playlist no encontrada", t_ahora
        else:
            ruta = media.mpv_query("path")
            if ruta:
                cfg.Estado.msj_error, cfg.Estado.error_time = "⬇️ Descargando pista...", t_ahora
                threading.Thread(target=media.dl_single_thread, args=(ruta,), daemon=True).start()
            else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Nada sonando", t_ahora

    elif cmd in ["/shuffle", "/aleatorio", "/mix"]:
        media.mpv_command(["playlist-shuffle"])
        cfg.Estado.msj_error, cfg.Estado.error_time = "🔀 Cola mezclada", t_ahora

    elif cmd.startswith("/loop "):
        m = cmd.split(" ")[1]
        if m == "song": media.mpv_command(["set", "loop-file", "inf"]); cfg.Estado.modo_loop = "CANCION"
        elif m == "list": media.mpv_command(["set", "loop-playlist", "inf"]); cfg.Estado.modo_loop = "LISTA"
        else: media.mpv_command(["set", "loop-file", "no"]); media.mpv_command(["set", "loop-playlist", "no"]); cfg.Estado.modo_loop = "off"

    elif cmd.startswith("/color "):
        c = cmd.split(" ", 1)[1]
        if c.isdigit(): cfg.Estado.color_cava = c

    elif cmd in ["/refresh", "/limpiar", "/clear"]:
        print("\033[2J\033[H", end="")
        cfg.Estado.msj_error, cfg.Estado.error_time = "✨ Pantalla redibujada", t_ahora

    elif cmd:
        if re.match(r"^(https?://|www\.)", cmd) or os.path.exists(os.path.expanduser(cmd)):
            media.mpv_command(["loadfile", cmd, "append-play"])
        else:
            cfg.Estado.msj_error, cfg.Estado.error_time = f"🔍 Buscando: {cmd[:20]}...", t_ahora
            media.mpv_command(["loadfile", f"ytdl://ytsearch1:{cmd}", "append-play"])
