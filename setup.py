from setuptools import setup, find_packages

setup(
    name='termimusic',
    version='1.0.0',
    description='A dynamic, riced terminal music player powered by MPV and CAVA.',
    author='DarknessQ2', # Cámbialo por tu usuario de GitHub
    author_email='vendiluis11@gmail.com',
    py_modules=['termimusic'],
    install_requires=[
        'Pillow>=9.0.0',
        'psutil>=5.8.0',
        'pypresence>=4.2.1'
    ],
    entry_points={
        'console_scripts': [
            'termimusic=termimusic:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
)
