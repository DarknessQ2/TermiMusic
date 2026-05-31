import os
import json
import ctypes
import urllib.request
import urllib.parse
import re
import config as cfg

# ===========================================================================
# 1. CARGA Y ENLACE DEL MOTOR EN C++ (Ultra Low-Latency IPC)
# ===========================================================================
lib_path = os.path.join(os.path.dirname(__file__), "motor_media_c.so")
if not os.path.exists(lib_path):
    raise FileNotFoundError(
        f"⚠️ No se encontró la librería compilada en: {lib_path}\n"
        f"Ejecuta en consola para compilar: g++ -O3 -shared -fPIC motor_media.cpp -o motor_media_c.so -lpthread"
    )

motor_c = ctypes.CDLL(lib_path)

motor_c.mpv_query_c.restype = ctypes.c_char_p
motor_c.mpv_query_c.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
motor_c.mpv_command_c.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
motor_c.yt_dlp_descargar_c.argtypes = [ctypes.c_char_p, ctypes.c_char_p]


# ===========================================================================
# 2. INTERFAZ DE COMUNICACIÓN CON MPV
# ===========================================================================

def mpv_command(cmd_list):
    try:
        comando_json = json.dumps({"command": cmd_list})
        motor_c.mpv_command_c(cfg.SOCKET.encode('utf-8'), comando_json.encode('utf-8'))
    except:
        pass


def mpv_query(prop):
    try:
        comando_json = json.dumps({"command": ["get_property", prop]})
        respuesta = motor_c.mpv_query_c(cfg.SOCKET.encode('utf-8'), comando_json.encode('utf-8'))
        if respuesta:
            linea = respuesta.decode('utf-8').split('\n')[0]
            return json.loads(linea).get("data")
    except:
        return None
    return None


# ===========================================================================
# 3. SCRAPER WEB PURO (Sin archivos, directo a memoria)
# ===========================================================================

def buscar_lyrics_web_puro(titulo_pista):
    """
    Busca letras directamente en la red usando Google y Chartlyrics.
    Devuelve una lista de líneas en memoria sin guardar archivos en el disco.
    """
    try:
        # --- ETAPA 1: Limpieza ultra-agresiva del título ---
        query_clean = titulo_pista

        # Quitar extensiones si venía de un archivo
        for ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.webm']:
            if query_clean.lower().endswith(ext):
                query_clean = query_clean[:-len(ext)]
                break

        query_clean = query_clean.replace('_', ' ').replace('-', ' ')
        basura_yt = [
            r'\s*[\[(](official|video|audio|lyric|hd|4k|clip|oficial|letra).*?[\])]',
            r'\s*visualizer\s*', r'\s*lyrics\s*', r'\s*letra\s*', r'\s*full audio\s*',
            r'\s*hq\s*', r'\s*remastered\s*', r'\s*video oficial\s*'
        ]
        for patron in basura_yt:
            query_clean = re.sub(re.compile(patron, re.IGNORECASE), '', query_clean)

        query_clean = ' '.join(query_clean.split()).strip()

        if not query_clean:
            return ["❌ Título de pista inválido o vacío"]

        lineas = []

        # --- CAPA A: Google Search (Modo ligero) ---
        try:
            search_query = f"{query_clean} lyrics"
            url_search = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&hl=es&gbv=1"

            req = urllib.request.Request(url_search)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')

            with urllib.request.urlopen(req, timeout=3) as response:
                html = response.read().decode('utf-8', errors='ignore')

                patrones_letras = [
                    r'rgba\(0,0,0,0\.87\); font-size:14px; line-height:20px">(.*?)<\/div>',
                    r'font-family:Roboto,HelveticaNeue,Arial,sans-serif;font-size:medium;line-height:1\.34">(.*?)<\/div>',
                    r'div class="BNeawe xcST9 bFormalsh8wZd px7clb">(.*?)<\/div>',
                    r'div class="BNeawe tS63be s3v9rd">(.*?)<\/div>',
                    r'div class="BNeawe iBp4i s3v9rd">(.*?)<\/div>'
                ]

                for patron in patrones_letras:
                    lyrics_matches = re.findall(patron, html)
                    if lyrics_matches:
                        raw_text = "\n".join(lyrics_matches)
                        raw_text = raw_text.replace('<br>', '\n').replace('<br/>', '\n').replace('</div>', '\n')
                        raw_text = re.sub(r'<[^>]*>', '', raw_text)

                        lineas = [l.strip() for l in raw_text.split('\n') if l.strip()]
                        if len(lineas) > 5:
                            break
                        else:
                            lineas = []
        except:
            pass

        # --- CAPA B: API Chartlyrics (Fallback inmediato) ---
        if not lineas:
            try:
                url_api = f"http://api.chartlyrics.com/apiv1.asmx/SearchLyricText?lyricText={urllib.parse.quote(query_clean)}"
                req_api = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})

                id_letra, checksum_letra = None, None
                with urllib.request.urlopen(req_api, timeout=3) as response:
                    xml_data = response.read().decode('utf-8', errors='ignore')
                    ids = re.findall(r'<LyricId>(\d+)</LyricId>', xml_data)
                    checksums = re.findall(r'<LyricChecksum>([^<]+)</LyricChecksum>', xml_data)
                    if ids and checksums and ids[0] != "0":
                        id_letra = ids[0]
                        checksum_letra = checksums[0]

                if id_letra and checksum_letra:
                    url_get = f"http://api.chartlyrics.com/apiv1.asmx/GetLyric?lyricId={id_letra}&lyricChecksum={checksum_letra}"
                    req_get = urllib.request.Request(url_get, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_get, timeout=3) as response_get:
                        xml_lyric = response_get.read().decode('utf-8', errors='ignore')
                        match_lyric = re.search(r'<Lyric>(.*?)</Lyric>', xml_lyric, re.DOTALL)
                        if match_lyric:
                            raw_text = match_lyric.group(1)
                            lineas = [l.strip() for l in raw_text.split('\n') if l.strip()]
            except:
                pass

        # Retornar las letras encontradas o el mensaje de error limpio directo a la UI
        return lineas if lineas else ["❌ No se encontró la letra en internet"]

    except Exception as e:
        return [f"❌ Error en la búsqueda: {str(e)}"]
