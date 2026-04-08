import os
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Configura automáticamente el PATH en la shell del usuario tras la instalación."""
    def run(self):
        install.run(self)
        user_bin = os.path.expanduser("~/.local/bin")
        # Línea que exporta el PATH
        path_line = f'\n# TermiMusic Path\nexport PATH="{user_bin}:$PATH"\n'
        
        # Detectar qué archivos de configuración existen en el HOME del usuario
        configs = [".bashrc", ".zshrc", ".bash_profile", ".profile"]
        
        for config in configs:
            config_path = os.path.expanduser(f"~/{config}")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        content = f.read()
                    
                    # Evitar duplicados: solo escribir si no está ya la ruta
                    if user_bin not in content:
                        with open(config_path, "a") as f:
                            f.write(path_line)
                        print(f"\033[1;32m[+] PATH configurado en {config}\033[0m")
                except Exception as e:
                    print(f"\033[1;31m[!] No se pudo escribir en {config}: {e}\033[0m")

setup(
    name='termimusic',
    version='1.0.2',
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
