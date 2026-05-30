import os
import shutil
import subprocess
import traceback
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop

def compilar_motor():
    """Limpia el entorno, comprueba archivos y compila el motor C++ antes de instalar."""
    try:
        print("\033[1;36m[*] Iniciando Fase de Compilación del Motor Híbrido...\033[0m")

        # --- PASO 0: LIMPIEZA PREVIA ---
        print("\033[1;34m[*] Limpiando residuos de compilaciones anteriores...\033[0m")
        for basura in ['build', 'dist', 'termimusic.egg-info', '__pycache__']:
            if os.path.exists(basura):
                shutil.rmtree(basura) if os.path.isdir(basura) else os.remove(basura)
        print("\033[1;32m[+] Entorno limpio para nueva compilación.\033[0m")

        # 1. Verificación de integridad
        archivos_requeridos = [
            'main.py', 'config.py', 'motor_media_bridge.py',
            'motor_comandos.py', 'motor_grafico.py', 'motor_media.cpp',
            'animacion.txt'
        ]
        print("\033[1;34m[*] Comprobando integridad del código fuente...\033[0m")
        for arc in archivos_requeridos:
            if not os.path.exists(arc):
                raise FileNotFoundError(f"Falta un archivo vital del motor o asset: {arc}. Verifica tu carpeta.")
        print("\033[1;32m[+] Todos los módulos y assets están presentes.\033[0m")

        # 2. Compilación nativa con nombre correcto
        print("\033[1;34m[*] Compilando el motor de media C++ con máxima optimización (g++)...\033[0m")
        if shutil.which("g++") is None:
            raise RuntimeError("No se encontró el compilador 'g++'. Instálalo ejecutando: sudo pacman -S gcc")

        # Nombre corregido estrictamente con guion bajo (_) para evitar OSErrors en ctypes
        compile_cmd = ["g++", "-O3", "-shared", "-fPIC", "-o", "motor_media_c.so", "motor_media.cpp"]
        subprocess.check_call(compile_cmd)
        print("\033[1;32m[+] Motor nativo 'motor_media_c.so' generado exitosamente.\033[0m")

    except Exception as e:
        with open("log.txt", "w") as log_file:
            log_file.write(traceback.format_exc())
        print("\n\033[1;31m[!] Ocurrió un error crítico durante la compilación del motor C++.\033[0m")
        print("\033[1;31m[!] Revisa el archivo 'log.txt'.\033[0m\n")
        raise e

def acciones_post_instalacion(install_lib_dir=None):
    """Ejecuta la inyección de assets, configuración de entorno y despliegue visual."""
    try:
        # Mover binarios compilados solo si no estamos en modo editable/local
        if install_lib_dir and os.path.exists(install_lib_dir) and install_lib_dir != os.getcwd():
            print(f"\033[1;34m[*] Inyectando binario C++ y arte ASCII en el sistema...\033[0m")
            shutil.copy("motor_media_c.so", install_lib_dir)
            shutil.copy("animacion.txt", install_lib_dir)

        # --- CONFIGURACIÓN DE COOKIES ---
        print("\n\033[1;35m" + "="*50)
        print("🔧 CONFIGURACIÓN DE YOUTUBE (ANTI-BLOQUEOS)")
        print("="*50 + "\033[0m")
        print("Para evitar restricciones de edad o captchas, TermiMusic puede")
        print("usar las cookies de tu navegador principal.")
        print("\033[1;36mOpciones válidas:\033[0m firefox, chrome, brave, edge, opera, vivaldi")

        nav = ""
        try:
            nav = input(">> ¿Qué navegador usas? (Escribe 'none' o presiona ENTER para omitir): ").strip().lower()
        except (EOFError, IOError):
            pass  # Evita congelarse en entornos no interactivos

        cfg_dir = os.path.expanduser("~/.config/termimusic")
        os.makedirs(cfg_dir, exist_ok=True)
        cookie_file = os.path.join(cfg_dir, "navegador.conf")

        if nav and nav != 'none':
            with open(cookie_file, "w") as f:
                f.write(nav)
            print(f"\033[1;32m[+] ¡Listo! TermiMusic clonará las cookies de: {nav.capitalize()}\033[0m\n")
        else:
            if nav == 'none' or nav == '':
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)
                print("\033[1;33m[!] Entendido. No se usarán cookies del navegador.\033[0m\n")

        # Inyección de PATH Multi-Shell
        user_bin = os.path.expanduser("~/.local/bin")
        print("\033[1;34m[*] Configurando variables de entorno (PATH)...\033[0m")
        path_line = f'\n# TermiMusic Path\nexport PATH="{user_bin}:$PATH"\n'
        for config in [".bashrc", ".zshrc", ".bash_profile", ".profile"]:
            config_path = os.path.expanduser(f"~/{config}")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    content = f.read()
                if user_bin not in content:
                    with open(config_path, "a") as f:
                        f.write(path_line)

        if shutil.which("fish"):
            os.system(f'fish -c "fish_add_path {user_bin} >/dev/null 2>&1"')

        # Creación del Lanzador (.desktop)
        desktop_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_file = os.path.join(desktop_dir, "termimusic.desktop")
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=TermiMusic v1.6.0
Comment=Tienda de Vinilos Retro (Hybrid Engine)
Exec={user_bin}/termimusic
Icon=utilities-terminal
Terminal=true
Categories=AudioVideo;Audio;Player;
"""
        with open(desktop_file, "w") as f:
            f.write(desktop_content)

        if shutil.which("update-desktop-database"):
            os.system(f"update-desktop-database {desktop_dir}")
            print("\033[1;32m[+] Caché de íconos actualizada.\033[0m")

        # Comprobación de dependencias del sistema
        missing_deps = [dep for dep in ['mpv', 'cava', 'socat', 'yt-dlp'] if shutil.which(dep) is None]

        # Limpieza final (OJO: No borramos motor_media_c.so para mantener funcional el venv local)
        for basura in ['build', 'dist', 'termimusic.egg-info']:
            if os.path.exists(basura):
                shutil.rmtree(basura) if os.path.isdir(basura) else os.remove(basura)

        os.system('clear')
        print("\033[1;36m")
        print("""
  _____                    _ __  __            _
 |_   _|__ _ __ _ __ (_) \/  | ___  ___(_) ___
   | |/ _ \ '__| '_ \| | |\/| |/ _ \/ __| |/ __|
   | |  __/ |  | | | | | |  | |  __/\__ \ | (__
   |_|\___|_|  |_| |_|_|_|  |_|\___||___/_|\___|
                v1.6.0 HYBRID ENGINE
        """)
        print("\033[0m")
        print("\033[1;32m" + "="*50)
        print("         INSTALACIÓN COMPLETADA CON ÉXITO")
        print("="*50 + "\033[0m")
        print("\033[1;36mVersión :\033[0m 1.6.0 (Release)")
        print("\033[1;36mCreador :\033[0m DarknessQ2 ")
        print("\033[1;36mContacto:\033[0m vendiluis11@gmail.com")
        print("\033[1;32m" + "-" * 50 + "\033[0m")

        if missing_deps:
            print("\033[1;33m[!] ADVERTENCIA: Faltan paquetes nativos en tu sistema.\033[0m")
            print(f"Para que todo fluya perfecto, ejecuta: \n\033[1;31msudo pacman -S {' '.join(missing_deps)}\033[0m")
            print("\033[1;32m" + "-" * 50 + "\033[0m")

        print("¡Todo listo! Inicia el reproductor con: \033[1;33m$ termimusic\033[0m\n")

    except Exception as e:
        with open("log.txt", "w") as log_file:
            log_file.write(traceback.format_exc())
        print("\n\033[1;31m[!] Ocurrió un error crítico en la post-instalación.\033[0m")
        print("\033[1;31m[!] Revisa el archivo 'log.txt'.\033[0m\n")
        raise e

class CustomInstallCommand(install):
    """Intercepta 'pip install .'"""
    def run(self):
        compilar_motor()
        install.run(self)
        acciones_post_instalacion(self.install_lib)

class CustomDevelopCommand(develop):
    """Intercepta 'pip install -e .'"""
    def run(self):
        compilar_motor()
        develop.run(self)
        acciones_post_instalacion(os.getcwd())

setup(
    name='termimusic',
    version='1.6.0',
    py_modules=['main', 'config', 'motor_media_bridge', 'motor_comandos', 'motor_grafico'],
    install_requires=[
        'Pillow>=9.0.0',
        'psutil>=5.8.0',
        'pypresence>=4.2.1'
    ],
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
    },
    entry_points={
        'console_scripts': [
            'termimusic=main:main',
        ],
    },
)
