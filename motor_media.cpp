// ==========================================================
// TermiMusic - Motor Media C++ (Ultra Low-Latency IPC)
// Features: Buffer Dinámico Expandido (256KB) para Playlists
// ==========================================================
#include <iostream>
#include <string>
#include <cstring>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cstdlib>

extern "C" {

    // Función para enviar comandos sin esperar respuesta
    void mpv_command_c(const char* socket_path, const char* json_cmd) {
        int sock = socket(AF_UNIX, SOCK_STREAM, 0);
        if (sock < 0) return;

        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 50000; // 50ms timeout
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof tv);

        struct sockaddr_un addr;
        memset(&addr, 0, sizeof(addr));
        addr.sun_family = AF_UNIX;
        strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

        if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == 0) {
            send(sock, json_cmd, strlen(json_cmd), 0);
            send(sock, "\n", 1, 0);
        }
        close(sock);
    }

    // Función expandida para consultar propiedades masivas (como la playlist)
    const char* mpv_query_c(const char* socket_path, const char* json_cmd) {
        static char buffer[262144]; // BUFFER AMPLIADO A 256KB
        memset(buffer, 0, sizeof(buffer));

        int sock = socket(AF_UNIX, SOCK_STREAM, 0);
        if (sock < 0) return "";

        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 50000;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof tv);

        struct sockaddr_un addr;
        memset(&addr, 0, sizeof(addr));
        addr.sun_family = AF_UNIX;
        strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

        if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == 0) {
            send(sock, json_cmd, strlen(json_cmd), 0);
            send(sock, "\n", 1, 0);

            // Bucle de recolección: Lee fragmentos hasta encontrar el salto de línea '\n'
            int bytes_recibidos = 0;
            while (bytes_recibidos < sizeof(buffer) - 1) {
                int bytes = recv(sock, buffer + bytes_recibidos, sizeof(buffer) - bytes_recibidos - 1, 0);
                if (bytes <= 0) break; // Termina si no hay más datos o hay error
                bytes_recibidos += bytes;
                if (buffer[bytes_recibidos - 1] == '\n') break; // Termina si MPV cerró el JSON
            }
        }
        close(sock);
        return buffer;
    }

    // Envoltorio de C++ para yt-dlp
    void yt_dlp_descargar_c(const char* directorio, const char* url) {
        std::string comando = "yt-dlp -f bestaudio -x --audio-format mp3 --write-thumbnail --convert-thumbnails png -o '";
        comando += directorio;
        comando += "/%(title)s.%(ext)s' --no-playlist '";
        comando += url;
        comando += "' > /dev/null 2>&1";

        int result = std::system(comando.c_str());
        (void)result;
    }
}
