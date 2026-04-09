import os
import shutil
import traceback
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Instala, configura el PATH, limpia basura, limpia la terminal y muestra información."""
    def run(self):
        try:
            # 1. Ejecutar la instalación estándar de Python
            install.run(self)

            # 2. Configurar PATH universal en segundo plano
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

            # 3. Limpiar carpetas residuales (build, dist, egg-info)
            carpetas_basura = ['build', 'dist', 'termimusic.egg-info']
            for carpeta in carpetas_basura:
                if os.path.exists(carpeta):
                    shutil.rmtree(carpeta)

            # 4. LIMPIAR LA TERMINAL ANTES DE MOSTRAR EL MENSAJE
            os.system('clear')

            # 5. Tarjeta de presentación (Información del creador)
            print("\n\033[1;32m" + "="*50)
            print(" " * 11 + "🎵 TERMIMUSIC INSTALADO 🎵")
            print("="*50 + "\033[0m")
            print("\033[1;36mVersión :\033[0m 1.0")
            print("\033[1;36mCreador :\033[0m DarknessQ2")
            print("\033[1;36mContacto:\033[0m vendiluis11@gmail.com(Para reportar bugs)")
            print("\033[1;32m" + "-" * 50 + "\033[0m")
            print("¡Todo listo! Para iniciar el reproductor, ejecuta:")
            print("  \033[1;33m$ termimusic\033[0m")
            print("\033[1;32m" + "="*50 + "\033[0m\n")

        except Exception as e:
            # 6. Interceptar errores y crear log.txt si algo falla
            with open("log.txt", "w") as log_file:
                log_file.write("=== ERROR DE INSTALACIÓN - TERMIMUSIC ===\n")
                log_file.write(traceback.format_exc())

            print("\n\033[1;31m[!] Ocurrió un error crítico durante la instalación.\033[0m")
            print("\033[1;31m[!] Se ha generado un archivo 'log.txt' con los detalles para reportar el bug.\033[0m\n")
            raise e

setup(
    name='termimusic',
    version='1.0',
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
