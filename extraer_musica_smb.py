"""Saca las melodías del Super Mario Bros de 128K (CAFe 2019) de su .tap y las guarda como .pt3.

En el juego la música no está en PT3: son volcados de los registros del AY, comprimidos, que toca
un reproductor propio (en 0x8A20 del bloque «World»). Este programa:
  1. lee el .tap, descomprime «World» con el descompresor del propio cargador (dzx7),
  2. ejecuta el reproductor del juego en un Z80 emulado y graba los registros del AY, fotograma a
     fotograma, de cada melodía de los bloques «MusicNN» (sin repetir las que están en varios),
  3. convierte cada grabación en un módulo PT3 (ay2pt3.py) y lo comprueba tocándolo con el
     reproductor de Bulba del generador: tiene que dar exactamente los mismos registros.

Requisitos: pip install z80     (núcleo Z80 de Ivan Kosarev)
Uso:        python extraer_musica_smb.py juego.tap [carpeta_de_salida]

Las melodías de Super Mario Bros son de Nintendo: úsalas para estudiar o en juegos que no vayas a
distribuir."""
import os, sys
import z80
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ay2pt3 import convertir, canal
from pt3emu import Reproductor, tabla_notas


def bloques_tap(ruta):
    d = open(ruta, 'rb').read(); i = 0; nombre = None; res = {}
    while i < len(d):
        n = d[i] | d[i + 1] << 8; b = d[i + 2:i + 2 + n]
        if b[0] == 0: nombre = b[2:12].decode('latin-1').strip()
        else: res[nombre] = b[1:-1]
        i += 2 + n
    return res


def dzx7(cargador, empaquetado):
    """Descomprime con la rutina del cargador (0x654A-0x65A1), reubicada en 0xFF00."""
    r = bytearray(cargador[0x54A:0x5A2]); base = 0xFF00
    for i in range(len(r) - 2):
        for op, lo, dest in ((0xCC, 0x9E, 0x54), (0xC3, 0x6D, 0x23), (0xD2, 0x4E, 0x04)):
            if r[i] == op and r[i + 1] == lo and r[i + 2] == 0x65:
                r[i + 1:i + 3] = (base + dest).to_bytes(2, 'little')
    m = z80.Z80Machine()
    m.set_memory_block(base, bytes(r)); m.set_memory_block(0x8000, empaquetado[:0x7E00])
    m.set_memory_block(0x7FFE, b'\xf0\xfe'); m.set_breakpoint(0xFEF0)
    m.hl = 0x8000; m.de = 0x0000; m.sp = 0x7FFE; m.pc = base
    for _ in range(20000):
        m.ticks_to_stop = 200000
        if m.run() & m._BREAKPOINT_HIT: break
    return bytes(m.memory[0:m.hl - 1])          # al terminar, HL = final de lo descomprimido + 1


def grabar(world, bloque, dir_cancion, maximo=20000):
    """Registros del AY por fotograma hasta que la melodía vuelve a empezar."""
    m = z80.Z80Machine()
    m.set_memory_block(0x8000, world); m.set_memory_block(0xC000, bloque)
    regs = [0] * 16; est = {'sel': 0, 'r13': False}
    def out(port, val):
        if port & 0xC002 == 0xC000: est['sel'] = val & 15
        elif port & 0xC002 == 0x8000:
            regs[est['sel']] = val
            if est['sel'] == 13: est['r13'] = True
    m.set_output_callback(out)
    m.set_breakpoint(0x7F00); m.set_breakpoint(0x8BD9)        # retorno y vuelta al principio
    def llamar(addr, hl=None):
        if hl is not None: m.hl = hl
        m.sp = 0x7FF0; m.memory[0x7FF0] = 0x00; m.memory[0x7FF1] = 0x7F; m.pc = addr
        bucle = False
        while True:
            m.ticks_to_stop = 100000
            if m.run() & m._BREAKPOINT_HIT:
                if m.pc == 0x7F00: return bucle
                bucle = True; m.step_over_breakpoint()
    llamar(0x8BDF, dir_cancion)                                # elige la melodía
    frames = []
    for f in range(maximo):
        est['r13'] = False
        llamar(0x8A2B)                                         # vuelca los registros
        frames.append(list(regs[:14]) + [1 if est['r13'] else 0])
        if llamar(0x8A26) and f > 0:                           # calcula el siguiente
            return frames
    raise RuntimeError('la melodía no termina')


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    salida = sys.argv[2] if len(sys.argv) > 2 else 'musica_smb'
    os.makedirs(salida, exist_ok=True)
    tap = bloques_tap(sys.argv[1])
    world = dzx7(tap['Loader'], tap['World'])
    tablas = [tabla_notas(n) for n in range(4)]
    vistas, n = set(), 0
    for nombre in sorted(k for k in tap if k.startswith('Music')):
        d = tap[nombre]; i = 0
        while i < len(d) and d[i] not in (0, 0xFF):
            largo = d[i + 1] | d[i + 2] << 8; datos = d[i + 3:i + 3 + largo]
            if datos not in vistas:
                vistas.add(datos)
                fr = grabar(world, d, 0xC000 + i + 3)
                cancion = fr[1:]                               # el primer fotograma es el silencio inicial
                periodos = {r[2 * c] | (r[2 * c + 1] & 15) << 8 for r in cancion for c in range(3)
                            if canal(r, c)[5] and canal(r, c)[3]}
                t = max(range(4), key=lambda k: len(periodos & set(tablas[k])))
                n += 1
                mod = convertir(cancion, tablas[t], t, titulo=f'SMB {n}', autor='AY a PT3')
                rep = Reproductor(mod); fallos = 0
                for k in range(len(cancion)):
                    o, r = rep.frame(), cancion[k]
                    for c in range(3):
                        a, b = canal(o, c), canal(r, c)
                        if a[5] != b[5] or (b[5] and (a[1:5] != b[1:5] or (b[3] and a[0] != b[0]))): fallos += 1
                ruta = os.path.join(salida, f'smb_{n}.pt3')
                open(ruta, 'wb').write(mod)
                print(f'{ruta}: {nombre} n.º {d[i]}, {len(cancion) / 50:.1f} s, tabla {t}, {len(mod)} bytes, '
                      f'{"idéntica" if not fallos else f"{fallos} diferencias"}')
            i += 3 + largo


if __name__ == '__main__':
    main()
