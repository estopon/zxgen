"""Reensambla asm/motor.asm SIN pasmo, con pyz80 (pip install pyz80), y regenera motor_bin.py.
El cargador y el reproductor PT3 no cambian: se conservan los que ya hay en motor_bin.py.
pyz80 no entiende algunas cosas de pasmo (rept/endm, 'equ' sin dos puntos, caracteres entre
comillas simples, 'end'), así que el fuente se adapta antes. Comprobado: con el motor.asm original
el resultado es idéntico byte a byte al que da pasmo.
Hay tres variantes del motor, una por tipo de scroll, y cada juego lleva solo la suya:
  V  vertical;  H  horizontal o plataformas de 8 en 8;  B  horizontal o plataformas fino (bloques).
En motor.asm, lo que solo hace falta en algunas va entre «;@ SOLO <variantes>» y «;@ FIN». Las
etiquetas que se quitan apuntan a stub_nada (un ret): solo se usan en ramas que esa variante no
ejecuta nunca.
Uso:  python construir_motor_pyz80.py"""
import os, re, sys, pickle, subprocess, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.join(AQUI, 'asm')
FIN = 0xBE00                     # tabla IM2: el motor y sus variables tienen que acabar antes


def adaptar(src):
    lineas = src.split('\n')
    consts = {}
    for s in lineas:
        m = re.match(r'^([A-Za-z_]\w*)\s+equ\s+([^;]+)', s, re.I)
        if m: consts[m.group(1)] = m.group(2).strip()

    def valor(expr, prof=0):
        e = re.sub(r'\b0x([0-9A-Fa-f]+)\b', lambda m: str(int(m.group(1), 16)), expr)
        def sub(m):
            n = m.group(0)
            if n in consts and prof < 10: return '(' + str(valor(consts[n], prof + 1)) + ')'
            return n
        e = re.sub(r'[A-Za-z_]\w*', sub, e)
        return int(eval(e.replace('/', '//')))

    def expandir(i):
        res = []
        while i < len(lineas):
            s = lineas[i]
            m = re.match(r'^\s*rept\s+([^;]+)', s, re.I)
            if m:
                cuerpo, i = expandir(i + 1)
                res += cuerpo * valor(m.group(1).strip())
                continue
            if re.match(r'^\s*endm\b', s, re.I):
                return res, i + 1
            s = re.sub(r'^([A-Za-z_]\w*)\s+equ\b', r'\1: EQU', s, flags=re.I)
            codigo, _, com = s.partition(';')
            codigo = re.sub(r"(?<![A-Za-z])'(.)'", lambda m: str(ord(m.group(1))), codigo)
            if re.match(r'^\s*end\s*$', codigo, re.I): codigo = ''
            res.append(codigo + (';' + com if com else ''))
            i += 1
        return res, i

    return '\n'.join(expandir(0)[0])


VARIANTES = ('V', 'H', 'B')


def filtrar(src, variante):
    """Quita los bloques «;@ SOLO ...» que no son de la variante (None = no quita nada)."""
    if variante is None: return src
    salida, quitadas, dentro = [], [], None
    for linea in src.split('\n'):
        m = re.match(r';@ SOLO (.*)', linea)
        if m: dentro = m.group(1).split(); continue
        if linea.startswith(';@ FIN'): dentro = None; continue
        if dentro is not None and variante not in dentro and not re.match(r'^[A-Za-z_]\w*\s+equ\b', linea, re.I):
            e = re.match(r'^([A-Za-z_]\w*):', linea)
            if e: quitadas.append(e.group(1))
            continue
        salida.append(linea)
    definidas = {m.group(1) for l in salida for m in [re.match(r'^([A-Za-z_]\w*):', l)] if m}
    quitadas = [e for e in dict.fromkeys(quitadas) if e not in definidas]
    fin = max(i for i, l in enumerate(salida) if re.match(r'^\s*end\s*$', l.split(';')[0]) or i == len(salida) - 1)
    salida[fin:fin] = [f'{e} equ stub_nada' for e in quitadas]
    return '\n'.join(salida)


def ensamblar(nombre, variante=None):
    with tempfile.TemporaryDirectory() as tmp:
        fuente = os.path.join(tmp, nombre + '.asm')
        texto = filtrar(open(os.path.join(ASM, nombre + '.asm'), encoding='latin-1').read(), variante)
        open(fuente, 'w', encoding='latin-1').write(adaptar(texto))
        binario, simb = os.path.join(tmp, nombre + '.bin'), os.path.join(tmp, nombre + '.sym')
        orden = [sys.executable, '-c', 'import sys; sys.argv[0] = "pyz80"; import pyz80.pyz80']
        r = subprocess.run(orden + ['--nozip', '--intdiv', f'--obj={binario}', '-o', os.path.join(tmp, 'disco.dsk'),
                                    f'--exportfile={simb}', fuente], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stdout + r.stderr)
        return open(binario, 'rb').read(), pickle.load(open(simb, 'rb'))


if __name__ == '__main__':
    org = re.search(r'^\s+org\s+0x([0-9A-Fa-f]+)', open(os.path.join(ASM, 'motor.asm')).read(), re.M)
    dir_motor = int(org.group(1), 16)
    motores, simbolos = {}, {}
    for v in VARIANTES:
        datos, sym = ensamblar('motor', v)
        fin = sym['fin_motor']
        if fin > FIN:
            raise SystemExit(f'El motor {v} no cabe: acaba en 0x{fin:04X} (máximo 0x{FIN:04X}).')
        motores[v] = datos.ljust(fin - dir_motor, b'\x00')     # las variables 'ds' del final, a cero
        simbolos[v] = sym
        print(f'motor {v}: {len(motores[v])} bytes, de 0x{dir_motor:04X} a 0x{fin:04X} (quedan {FIN - fin} bytes)')
    import motor_bin as viejo
    with open(os.path.join(AQUI, 'motor_bin.py'), 'w') as f:
        f.write('# Generado por construir_motor_pyz80.py. No editar a mano.\n')
        f.write(f'DIR_MOTOR = 0x{dir_motor:04X}   # dirección de carga (org de motor.asm)\n')
        def volcar(n, d):
            f.write(f'{n} = bytes.fromhex(\n')
            h = d.hex()
            for i in range(0, len(h), 96):
                f.write(f'    "{h[i:i+96]}"\n')
            f.write(')\n')
        volcar('CARGADOR', viejo.CARGADOR)
        volcar('PT3PLAYER', viejo.PT3PLAYER)
        for v in VARIANTES: volcar(f'MOTOR_{v}', motores[v])
        f.write('MOTORES = {' + ', '.join(f"'{v}': MOTOR_{v}" for v in VARIANTES) + '}\n')
        f.write('MOTOR = MOTOR_B   # (compatibilidad)\n')
        f.write(f"SPRITE_NL = 0x{simbolos['B']['sprite_nl']:04X}   # rutina de cambio de línea para sprites compilados (variante B)\n")
