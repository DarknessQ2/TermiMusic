import requests
import os
import re

def buscar_lyrics(titulo):
    try:
        titulo_limpio = limpiar_titulo(titulo)

        # Intento 1: Artista - Canción
        artista = extraer_artista(titulo_limpio)
        cancion = extraer_cancion(titulo_limpio)

        resultado = buscar_lrclib(artista, cancion)

        # Intento 2: Buscar solo por nombre de canción
        if not resultado:
            resultado = buscar_lrclib("", titulo_limpio)

        if not resultado:
            return ["📭 Letra no encontrada"]

        letra_cruda = resultado.get("syncedLyrics")

        # Si no hay sincronizada usamos letra normal
        if not letra_cruda:
            letra_cruda = resultado.get("plainLyrics")

            if not letra_cruda:
                return ["📭 Sin letras"]

            return letra_cruda.splitlines()

        return letra_cruda.splitlines()

    except Exception as e:
        return [f"❌ {str(e)[:30]}"]


def buscar_lrclib(artista, cancion):
    try:
        url = "https://lrclib.net/api/search"

        params = {
            "track_name": cancion
        }

        if artista:
            params["artist_name"] = artista

        r = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "TermiMusic/1.0"
            }
        )

        if r.status_code != 200:
            return None

        datos = r.json()

        if not datos:
            return None

        return datos[0]

    except:
        return None


def limpiar_titulo(texto):
    texto = os.path.basename(str(texto))

    for ext in (
        ".mp3",
        ".wav",
        ".flac",
        ".m4a",
        ".ogg",
        ".opus"
    ):
        if texto.lower().endswith(ext):
            texto = texto[:-len(ext)]
            break

    texto = re.sub(r'\(.*?\)', '', texto)
    texto = re.sub(r'\[.*?\]', '', texto)

    texto = texto.replace("_", " ")
    texto = texto.replace(".", " ")

    return texto.strip()


def extraer_artista(titulo):
    if " - " in titulo:
        return titulo.split(" - ", 1)[0].strip()
    return ""


def extraer_cancion(titulo):
    if " - " in titulo:
        return titulo.split(" - ", 1)[1].strip()
    return titulo.strip()
