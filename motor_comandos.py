import os, re, time, random, threading
import config as cfg
import motor_media_bridge as media

def procesar(cmd):
    t_ahora = time.time()
    cmd_clean = cmd.strip()

    # 1. 🛡️ FILTRO DE COMANDOS STRICTO: Si inicia con '/' evaluamos funciones nativas
    if cmd_clean.startswith("/"):
        partes = cmd_clean.split(" ", 1)
        instruccion = partes[0].lower()

        if instruccion == "/save":
            if len(partes) > 1:
                nombre = partes[1]
                pl = media.mpv_query("playlist") or []
                canciones = [{"titulo": i.get("title") or i.get("filename"), "url": i.get("filename")} for i in pl if i.get("filename")]
                if canciones:
                    media.guardar_playlist(nombre, canciones)
                    cfg.Estado.msj_error, cfg.Estado.error_time = f"✅ Playlist '{nombre}' guardada", t_ahora
            else:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /save [nombre]", t_ahora

        elif instruccion == "/play":
            if len(partes) > 1:
                nombre = partes[1]
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
            else:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /play [nombre]", t_ahora

        elif instruccion == "/quitar":
            cola = media.mpv_query("playlist") or []
            if not cola:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ La cola está vacía", t_ahora
            elif len(partes) > 1 and partes[1].isdigit():
                indice = int(partes[1])
                if 0 <= indice < len(cola):
                    titulo_eliminada = cola[indice].get("title") or cola[indice].get("filename")
                    media.mpv_command(["playlist-remove", indice])
                    cfg.Estado.msj_error, cfg.Estado.error_time = f"🗑️ Quitada [{indice}]: {os.path.basename(str(titulo_eliminada))[:20]}...", t_ahora
                else:
                    cfg.Estado.msj_error, cfg.Estado.error_time = f"❌ Índice {indice} fuera de rango", t_ahora
            else:
                idx_actual = next((i for i, it in enumerate(cola) if it.get("current")), -1)
                if idx_actual != -1:
                    media.mpv_command(["playlist-remove", idx_actual])
                    cfg.Estado.msj_error, cfg.Estado.error_time = "⏭️ Pista actual removida", t_ahora
                else:
                    cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Nada reproduciéndose", t_ahora

        # 🖼️ COMANDO INTERRUPTOR DE CARATULA
        elif instruccion == "/caratula":
            if len(partes) > 1:
                modo = partes[1].lower()
                if modo == "off":
                    cfg.Estado.ver_caratula = False
                    cfg.Estado.guardar() if hasattr(cfg.Estado, 'guardar') else None
                    cfg.Estado.msj_error, cfg.Estado.error_time = "🖼️ Carátula OCULTADA", t_ahora
                elif modo == "on":
                    cfg.Estado.ver_caratula = True
                    cfg.Estado.guardar() if hasattr(cfg.Estado, 'guardar') else None
                    cfg.Estado.msj_error, cfg.Estado.error_time = "🖼️ Carátula VISIBLE", t_ahora
                else:
                    cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /caratula on o /caratula off", t_ahora
            else:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /caratula [on/off]", t_ahora

        # 🎤 NUEVO COMANDO INTERRUPTOR DE LYRICS (LETRA)
        elif instruccion == "/lyrics":
            if len(partes) > 1:
                modo = partes[1].lower()
                if modo == "off":
                    cfg.Estado.ver_lyrics = False
                    cfg.Estado.msj_error, cfg.Estado.error_time = "🎤 Letras OCULTADAS", t_ahora
                elif modo == "on":
                    cfg.Estado.ver_lyrics = True
                    cfg.Estado.msj_error, cfg.Estado.error_time = "🎤 Letras VISIBLES", t_ahora
                else:
                    cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /lyrics on o /lyrics off", t_ahora
            else:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /lyrics [on/off]", t_ahora

        # 📥 COMANDO PARA CARGAR MP3 DIRECTO POR RUTA
        elif instruccion == "/mp3":
            if len(partes) > 1:
                ruta_usuario = os.path.expanduser(partes[1].strip().strip('"').strip("'"))
                if os.path.exists(ruta_usuario) and os.path.isfile(ruta_usuario):
                    media.mpv_command(["loadfile", os.path.abspath(ruta_usuario), "append-play"])
                    cfg.Estado.msj_error, cfg.Estado.error_time = f"➕ Añadido: {os.path.basename(ruta_usuario)[:20]}", t_ahora
                else:
                    cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Archivo o ruta inválida", t_ahora
            else:
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Uso: /mp3 [ruta_del_archivo]", t_ahora

        elif instruccion in ["/random", "/mixall"]:
            todas = media.obtener_toda_la_biblioteca()
            if todas:
                random.shuffle(todas)
                media.mpv_command(["playlist-clear"])
                limite = min(100, len(todas))
                for url in todas[:limite]: media.mpv_command(["loadfile", url, "append"])
                media.mpv_command(["playlist-play-index", 0])
                cfg.Estado.msj_error, cfg.Estado.error_time = f"🔀 Mix creado ({limite} pistas)", t_ahora
            else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Biblioteca vacía", t_ahora

        elif instruccion in ["/rsong", "/randomsong"]:
            todas = media.obtener_toda_la_biblioteca()
            if todas:
                media.mpv_command(["loadfile", random.choice(todas), "append-play"])
                cfg.Estado.msj_error, cfg.Estado.error_time = "🎲 Añadida canción sorpresa", t_ahora
            else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Biblioteca vacía", t_ahora

        elif instruccion in ["/dl", "/download"]:
            if len(partes) > 1:
                datos = media.cargar_playlist(partes[1])
                if datos:
                    cfg.Estado.msj_error, cfg.Estado.error_time = f"⬇️ Bajando playlist '{partes[1]}'...", t_ahora
                    threading.Thread(target=media.dl_playlist_thread, args=(partes[1], datos), daemon=True).start()
                else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Playlist no encontrada", t_ahora
            else:
                ruta = media.mpv_query("path")
                if ruta:
                    cfg.Estado.msj_error, cfg.Estado.error_time = "⬇️ Descargando pista...", t_ahora
                    threading.Thread(target=media.dl_single_thread, args=(ruta,), daemon=True).start()
                else: cfg.Estado.msj_error, cfg.Estado.error_time = "❌ Nada sonando", t_ahora

        elif instruccion in ["/shuffle", "/aleatorio", "/mix"]:
            media.mpv_command(["playlist-shuffle"])
            cfg.Estado.msj_error, cfg.Estado.error_time = "🔀 Cola mezclada", t_ahora

        elif instruccion == "/loop":
            if len(partes) > 1:
                m = partes[1].lower()
                if m == "song": media.mpv_command(["set", "loop-file", "inf"]); cfg.Estado.modo_loop = "CANCION"
                elif m == "list": media.mpv_command(["set", "loop-playlist", "inf"]); cfg.Estado.modo_loop = "LISTA"
                else: media.mpv_command(["set", "loop-file", "no"]); media.mpv_command(["set", "loop-playlist", "no"]); cfg.Estado.modo_loop = "off"
            else:
                media.mpv_command(["set", "loop-file", "no"]); media.mpv_command(["set", "loop-playlist", "no"]); cfg.Estado.modo_loop = "off"

        elif instruccion == "/color":
            if len(partes) > 1 and partes[1].isdigit(): cfg.Estado.color_cava = partes[1]

        elif instruccion in ["/refresh", "/limpiar", "/clear"]:
            print("\033[2J\033[H", end="")
            cfg.Estado.msj_error, cfg.Estado.error_time = "✨ Pantalla redibujada", t_ahora

        elif instruccion == "/dynamic":
            cfg.Estado.modo_dinamico = not cfg.Estado.modo_dinamico
            cfg.Estado.msj_error, cfg.Estado.error_time = f"🎨 Modo Dinámico: {'ON' if cfg.Estado.modo_dinamico else 'OFF'}", t_ahora

        # 🛡️ Captura directa de comandos inexistentes que inicien con barra '/'
        else:
            cfg.Estado.msj_error, cfg.Estado.error_time = "❌ No se encontró el comando", t_ahora

    # 2. 🔍 SI NO LLEVA BARRA '/', ES UNA BÚSQUEDA AUTOMÁTICA EN YOUTUBE
    else:
        # Validación extra: si contiene barras de ruta pero no es un archivo real, evitamos pasarlo a yt-dlp
        if "\\" in cmd_clean or ("/" in cmd_clean and not cmd_clean.startswith("http")):
            if not os.path.exists(os.path.expanduser(cmd_clean)):
                cfg.Estado.msj_error, cfg.Estado.error_time = "❌ No se encontró el comando o ruta local", t_ahora
                return

        if re.match(r"^(https?://|www\.)", cmd_clean) or os.path.exists(os.path.expanduser(cmd_clean)):
            media.mpv_command(["loadfile", cmd_clean, "append-play"])
        else:
            cfg.Estado.msj_error, cfg.Estado.error_time = f"🔍 Buscando: {cmd_clean[:20]}...", t_ahora
            media.mpv_command(["loadfile", f"ytdl://ytsearch1:{cmd_clean}", "append-play"])
