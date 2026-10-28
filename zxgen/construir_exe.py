"""Empaqueta el generador en un ejecutable autónomo con PyInstaller.

    pip install pyinstaller pillow
    python construir_exe.py

Deja el ejecutable en dist/ (zxgen.exe en Windows, zxgen en Linux, zxgen.app en macOS).
El motor Z80 va embebido en motor_bin.py, así que no hace falta copiar datos.
PyInstaller no compila de forma cruzada: hay que construir en cada sistema.
En macOS un .app ya es una carpeta, así que no se empaqueta en un solo fichero.
"""
import os, shutil, sys

import PyInstaller.__main__

AQUI = os.path.dirname(os.path.abspath(__file__))
TRABAJO = os.path.join(AQUI, 'build')

if __name__ == '__main__':
    PyInstaller.__main__.run([
        os.path.join(AQUI, 'generador.py'),
        '--name', 'zxgen',
        '--onedir' if sys.platform == 'darwin' else '--onefile',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--paths', AQUI,
        '--distpath', os.path.join(AQUI, 'dist'),
        '--workpath', TRABAJO,
        '--specpath', TRABAJO,
    ])
    shutil.rmtree(TRABAJO, ignore_errors=True)
    print('Ejecutable en', os.path.join(AQUI, 'dist'), file=sys.stderr)
