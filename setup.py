import os
import sys
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Clase para configurar el PATH automáticamente después de la instalación."""
    def run(self):
        install.run(self)
        # Directorio donde se instalan los binarios de usuario
        user_bin = os.path.expanduser("~/.local/bin")
        path_line = f'\n# TermiMusic Path\nexport PATH="{user_bin}:$PATH"\n'

        # Archivos de configuración de shell a buscar
        shells = [".bashrc", ".zshrc", ".bash_profile"]

        for shell in shells:
            config_path = os.path.expanduser(f"~/{shell}")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        content = f.read()

                    # Solo agregar si no existe ya en el archivo
                    if user_bin not in content:
                        with open(config_path, "a") as f:
                            f.write(path_line)
                        print(f"\033[1;32m[+] Configurado {shell} automáticamente.\033[0m")
                except Exception as e:
                    print(f"\033[1;31m[!] Error al configurar {shell}: {e}\033[0m")

setup(
    name='termimusic',
    version='1.0.',
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
