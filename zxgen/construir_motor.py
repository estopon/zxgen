"""Reensambla el código Z80 (asm/*.asm) y regenera motor_bin.py.
Solo hace falta si modificas el ensamblador. Requiere 'pasmo' instalado."""
import subprocess, os, re

AQUI = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.join(AQUI, 'asm')

def ensamblar(nombre):
    src = os.path.join(ASM, nombre + '.asm')
    out = os.path.join(ASM, nombre + '.bin')
    sym = os.path.join(ASM, nombre + '.sym')
    subprocess.run(['pasmo', '--bin', src, out, sym], check=True)
    return open(out, 'rb').read()

if __name__ == '__main__':
    with open(os.path.join(AQUI, 'motor_bin.py'), 'w') as f:
        f.write('# Generado por construir_motor.py. No editar a mano.\n')
        org = re.search(r'^\s+org\s+0x([0-9A-Fa-f]+)', open(os.path.join(ASM, 'motor.asm')).read(), re.M)
        f.write(f'DIR_MOTOR = 0x{org.group(1).upper()}   # dirección de carga (org de motor.asm)\n')
        for n in ('cargador', 'motor'):
            datos = ensamblar(n)
            f.write(f'{n.upper()} = bytes.fromhex(\n')
            h = datos.hex()
            for i in range(0, len(h), 96):
                f.write(f'    "{h[i:i+96]}"\n')
            f.write(')\n')
            print(n, len(datos), 'bytes')
        # reproductor PT3 de Sergey Bulba, adaptado mecánicamente para pasmo, en 0xC000 del banco 6
        import sys
        sys.path.insert(0, ASM)
        from convertir_pt3 import convertir
        fuente = os.path.join(ASM, 'pt3player_pasmo.asm')
        open(fuente, 'w').write(convertir(open(os.path.join(ASM, 'pt3player.asm')).read(), '0xC000'))
        datos = ensamblar('pt3player_pasmo')
        f.write('PT3PLAYER = bytes.fromhex(\n')
        h = datos.hex()
        for i in range(0, len(h), 96):
            f.write(f'    "{h[i:i+96]}"\n')
        f.write(')\n')
        print('reproductor PT3', len(datos), 'bytes')
        # direcciones del motor que necesita el generador (código compilado de los sprites)
        sym = {l.split()[0].lower(): int(l.split()[2].rstrip('H'), 16)
               for l in open(os.path.join(ASM, 'motor.sym')) if 'EQU' in l}
        f.write(f"SPRITE_NL = 0x{sym['sprite_nl']:04X}   # rutina de cambio de línea para sprites compilados\n")
