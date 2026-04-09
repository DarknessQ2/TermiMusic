import os
import shutil
import traceback
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Instala, configura PATH, crea lanzador .desktop, chequea dependencias y muestra ASCII."""
    def run(self):
        try:
            # 1. Instalación estándar de Python
            install.run(self)

            # 2. Inyección de PATH en la Shell
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

            # 3. Creación del Lanzador de Aplicaciones (.desktop) para Rofi/Wofi
            desktop_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(desktop_dir, exist_ok=True)
            desktop_file = os.path.join(desktop_dir, "termimusic.desktop")

            desktop_content = """[Desktop Entry]
Type=Application
Name=TermiMusic
Comment=Physics-driven Terminal Music Player
Exec=termimusic
Icon=utilities-terminal
Terminal=true
Categories=AudioVideo;Audio;Player;
"""
            with open(desktop_file, "w") as f:
                f.write(desktop_content)

            # 4. Limpieza de carpetas basura
            for carpeta in ['build', 'dist', 'termimusic.egg-info']:
                if os.path.exists(carpeta):
                    shutil.rmtree(carpeta)

            # 5. Comprobación de dependencias del sistema (mpv, cava, socat)
            missing_deps = []
            for dep in ['mpv', 'cava', 'socat']:
                if shutil.which(dep) is None:
                    missing_deps.append(dep)

            # 6. Limpieza de pantalla y Arte ASCII
            os.system('clear')
            print("\033[1;36m") # Color Cyan brillante
            print("""
  _____               _ __  __           _
 |_   _|__ _ __ _ __ (_)  \/  |_   _ ___(_) ___
   | |/ _ \ '__| '_ \| | |\/| | | | / __| |/ __|
   | |  __/ |  | | | | | |  | | |_| \__ \ | (__
   |_|\___|_|  |_| |_|_|_|  |_|\__,_|___/_|\___|
            """)
            print("\033[0m") # Resetear color

            print("\033[1;32m" + "="*50)
            print("         INSTALACIÓN COMPLETADA CON ÉXITO")
            print("="*50 + "\033[0m")
            print("\033[1;36mVersión :\033[0m 1.0.1")
            print("\033[1;36mCreador :\033[0m DarknessQ2")
            print("\033[1;36mContacto:\033[0m vendiluis11@gmail.com")
            print("\033[1;32m" + "-" * 50 + "\033[0m")

            # Avisar si faltan programas del sistema
            if missing_deps:
                print("\033[1;33m[!] ADVERTENCIA: Faltan programas en tu sistema.\033[0m")
                print(f"Para que todo funcione, instala: \033[1;31m{' '.join(missing_deps)}\033[0m")
                print("(Ej: sudo pacman -S mpv cava socat)")
                print("\033[1;32m" + "-" * 50 + "\033[0m")

            print("¡Todo listo! Ya puedes buscarlo en tu menú de aplicaciones")
            print("o iniciar el reproductor desde tu terminal ejecutando:")
            print("  \033[1;33m$ termimusic\033[0m")
            print("\033[1;32m" + "="*50 + "\033[0m\n")

        except Exception as e:
            with open("log.txt", "w") as log_file:
                log_file.write("=== ERROR DE INSTALACIÓN - TERMIMUSIC ===\n")
                log_file.write(traceback.format_exc())
            print("\n\033[1;31m[!] Ocurrió un error crítico durante la instalación.\033[0m")
            print("\033[1;31m[!] Revisa el archivo 'log.txt'.\033[0m\n")
            raise e

setup(
    name='termimusic',
    version='1.0.1',
    py_modules=['termimusic'],
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
            'termimusic=termimusic:main',
        ],
    },
)
