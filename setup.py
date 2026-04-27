import os
import shutil
import subprocess
import traceback
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Instala, verifica módulos, compila C++, configura PATH y limpia."""
    def run(self):
        try:
            print("\033[1;36m[*] Iniciando Instalación de TermiMusic v1.5 (Motor Híbrido)...\033[0m")

            # --- PASO 0: LIMPIEZA PREVIA (Forzar instalación limpia) ---
            print("\033[1;34m[*] Limpiando compilaciones anteriores en la carpeta...\033[0m")
            for basura in ['build', 'dist', 'termimusic.egg-info', 'motor_media_c.so', '__pycache__']:
                if os.path.exists(basura):
                    if os.path.isdir(basura):
                        shutil.rmtree(basura)
                    else:
                        os.remove(basura)
            print("\033[1;32m[+] Entorno limpio y listo para compilar.\033[0m")

            # 1. Verificación estricta de todos los archivos del motor modular y assets
            archivos_requeridos = [
                'main.py', 'config.py', 'motor_media_bridge.py',
                'motor_comandos.py', 'motor_grafico.py', 'motor_media.cpp',
                'animacion.txt' # <-- AHORA EXIGE LA ANIMACIÓN
            ]
            print("\033[1;34m[*] Comprobando integridad del código fuente...\033[0m")
            for arc in archivos_requeridos:
                if not os.path.exists(arc):
                    raise FileNotFoundError(f"Falta un archivo vital del motor o asset: {arc}. Verifica tu carpeta.")
            print("\033[1;32m[+] Todos los módulos y assets están presentes.\033[0m")

            # 2. Compilación nativa del motor C++ (motor_media_c.so)
            print("\033[1;34m[*] Compilando el motor de media C++ con máxima optimización...\033[0m")
            if shutil.which("g++") is None:
                raise RuntimeError("No se encontró el compilador 'g++'.")

            compile_cmd = ["g++", "-O3", "-shared", "-fPIC", "-o", "motor_media_c.so", "motor_media.cpp"]
            subprocess.check_call(compile_cmd)
            print("\033[1;32m[+] Motor compilado exitosamente.\033[0m")

            # 3. Instalación estándar de Python
            install.run(self)

            # 4. Mover el binario compilado (.so) y la animación a la ruta final
            target_dir = self.install_lib
            print(f"\033[1;34m[*] Inyectando binario C++ y arte ASCII en el sistema...\033[0m")
            shutil.copy("motor_media_c.so", target_dir)
            shutil.copy("animacion.txt", target_dir) # <-- AHORA COPIA LA ANIMACIÓN

            # --- NUEVO PASO: CONFIGURACIÓN DE COOKIES ---
            print("\n\033[1;35m" + "="*50)
            print("🔧 CONFIGURACIÓN DE YOUTUBE (ANTI-BLOQUEOS)")
            print("="*50 + "\033[0m")
            print("Para evitar restricciones de edad o captchas, TermiMusic puede")
            print("usar las cookies de tu navegador principal.")
            print("\033[1;36mOpciones válidas:\033[0m firefox, chrome, brave, edge, opera, vivaldi")

            nav = input(">> ¿Qué navegador usas? (Escribe 'none' o presiona ENTER para omitir): ").strip().lower()

            cfg_dir = os.path.expanduser("~/.config/termimusic")
            os.makedirs(cfg_dir, exist_ok=True)
            cookie_file = os.path.join(cfg_dir, "navegador.conf")

            if nav and nav != 'none':
                with open(cookie_file, "w") as f:
                    f.write(nav)
                print(f"\033[1;32m[+] ¡Listo! TermiMusic clonará las cookies de: {nav.capitalize()}\033[0m\n")
            else:
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)
                print("\033[1;33m[!] Entendido. No se usarán cookies del navegador.\033[0m\n")

            # 5. Inyección de PATH en la Shell
            user_bin = os.path.expanduser("~/.local/bin")
            path_line = f'\n# TermiMusic Path\nexport PATH="{user_bin}:$PATH"\n'
            configs = [".bashrc", ".zshrc", ".bash_profile", ".profile"]

            for config in configs:
                config_path = os.path.expanduser(f"~/{config}")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        content = f.read()
                    if user_bin not in content:
                        with open(config_path, "a") as f:
                            f.write(path_line)

            # 6. Creación del Lanzador de Aplicaciones (.desktop)
            desktop_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(desktop_dir, exist_ok=True)
            desktop_file = os.path.join(desktop_dir, "termimusic.desktop")

            desktop_content = """[Desktop Entry]
Type=Application
Name=TermiMusic v1.5
Comment=Physics-driven Terminal Music Player (Hybrid Engine)
Exec=termimusic
Icon=utilities-terminal
Terminal=true
Categories=AudioVideo;Audio;Player;
"""
            with open(desktop_file, "w") as f:
                f.write(desktop_content)

            # 7. Comprobación de dependencias
            missing_deps = []
            for dep in ['mpv', 'cava', 'socat', 'yt-dlp', 'g++']:
                if shutil.which(dep) is None:
                    missing_deps.append(dep)

            # 8. Limpieza profunda
            print("\033[1;34m[*] Limpiando residuos de instalación...\033[0m")
            for basura in ['build', 'dist', 'termimusic.egg-info', 'motor_media_c.so']:
                if os.path.exists(basura):
                    if os.path.isdir(basura):
                        shutil.rmtree(basura)
                    else:
                        os.remove(basura)

            # 9. Pantalla de Éxito
            os.system('clear')
            print("\033[1;36m")
            print("""
  _____                  _ __  __            _
 |_   _|__ _ __ _ __ (_)  \/  | ___  ___(_) ___
   | |/ _ \ '__| '_ \| | |\/| |/ _ \/ __| |/ __|
   | |  __/ |  | | | | | |  | |  __/\__ \ | (__
   |_|\___|_|  |_| |_|_|_|  |_|\___||___/_|\___|
                v1.5 HYBRID ENGINE
            """)
            print("\033[0m")

            print("\033[1;32m" + "="*50)
            print("         INSTALACIÓN COMPLETADA CON ÉXITO")
            print("="*50 + "\033[0m")
            print("\033[1;36mVersión :\033[0m 1.5.0 (Release)")
            print("\033[1;36mCreador :\033[0m DarknessQ2 ")
            print("\033[1;36mContacto:\033[0m vendiluis11@gmail.com")
            print("\033[1;32m" + "-" * 50 + "\033[0m")

            if missing_deps:
                print("\033[1;33m[!] ADVERTENCIA: Faltan paquetes nativos en tu sistema.\033[0m")
                print(f"Para que todo fluya perfecto, ejecuta: \n\033[1;31msudo pacman -S {' '.join(missing_deps)}\033[0m")
                print("\033[1;32m" + "-" * 50 + "\033[0m")

            print("¡Todo listo! El ecosistema modular está instalado.")
            print("Inicia el reproductor desde tu terminal ejecutando:")
            print("  \033[1;33m$ termimusic\033[0m")
            print("\033[1;32m" + "="*50 + "\033[0m\n")

        except Exception as e:
            with open("log.txt", "w") as log_file:
                log_file.write("=== ERROR DE INSTALACIÓN - TERMIMUSIC v1.5 ===\n")
                log_file.write(traceback.format_exc())
            print("\n\033[1;31m[!] Ocurrió un error crítico durante la compilación/instalación.\033[0m")
            print("\033[1;31m[!] Revisa el archivo 'log.txt'.\033[0m\n")
            raise e

setup(
    name='termimusic',
    version='1.5.0',
    py_modules=['main', 'config', 'motor_media_bridge', 'motor_comandos', 'motor_grafico'],
    install_requires=[
        'Pillow>=9.0.0',
        'psutil>=5.8.0',
        'pypresence>=4.2.1'
    ],
    cmdclass={
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'termimusic=main:main',
        ],
    },
)
    },
)
