"""Ejecuta el reproductor PT3 de Bulba (el del generador) en el núcleo Z80 y devuelve los registros AY por fotograma."""
import z80
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motor_bin import PT3PLAYER as PLAYER

class Reproductor:
    def __init__(self, modulo, dir_mod=0xD000):
        self.m = m = z80.Z80Machine()
        m.set_memory_block(0xC000, PLAYER)
        m.set_memory_block(dir_mod, modulo)
        m.set_breakpoint(0x7F00)
        self.regs = [0] * 16; self.sel = 0; self.r13w = False
        def out(port, val):
            if port & 0xC002 == 0xC000: self.sel = val & 15
            elif port & 0xC002 == 0x8000:
                self.regs[self.sel] = val
                if self.sel == 13: self.r13w = True
        m.set_output_callback(out)
        self.llamar(0xC003, dir_mod)

    def llamar(self, addr, hl=None):
        m = self.m
        if hl is not None: m.hl = hl
        m.sp = 0x7FF0; m.memory[0x7FF0] = 0x00; m.memory[0x7FF1] = 0x7F; m.pc = addr
        for _ in range(100):
            m.ticks_to_stop = 100000
            ev = m.run()
            if ev & m._BREAKPOINT_HIT and m.pc == 0x7F00: return
        raise RuntimeError('el reproductor no vuelve')

    def frame(self):
        self.r13w = False
        self.llamar(0xC005)
        return list(self.regs[:14]) + [1 if self.r13w else 0]

def tabla_notas(n):
    """Las 96 frecuencias de la tabla de tonos n (0-3) tal como las calcula el reproductor (versión 3.6)."""
    mod = cabecera_minima(n)
    r = Reproductor(mod)
    mem = r.m.memory
    for a in range(0xC000, 0xD000, 1):
        ws = [mem[a + 2 * i] | mem[a + 2 * i + 1] << 8 for i in range(96)]
        if ws[0] > 2500 and ws[95] > 0 and ws[0] < 4096 and all(1.03 < ws[i] / ws[i + 1] < 1.09 for i in range(60)):
            return ws
    raise RuntimeError('no se encontró la tabla')

def cabecera_minima(tabla):
    h = bytearray(b'ProTracker 3.6 compilation of ' + b' ' * 32 + b' by ' + b' ' * 32)
    h += bytes([0x20, tabla, 3, 1, 0])      # 0x62 ?, 0x63 tabla, 0x64 velocidad, 0x65 posiciones, 0x66 bucle
    assert len(h) == 0x67
    # patrones en 0xCB, muestras 0x69.., ornamentos 0xA9.., posiciones 0xC9
    pat = 0xCB
    h += pat.to_bytes(2, 'little')
    h += bytes(64) + bytes(32)
    h += bytes([0, 0xFF])                  # posición 0 = patrón 0
    assert len(h) == 0xCB
    base = len(h) + 6
    h += base.to_bytes(2, 'little') * 3
    h += bytes([0xD0, 0x00])
    # muestra 1 y ornamento 0
    s = len(h); h += bytes([0, 1, 0, 0x8F, 0, 0])
    o = len(h); h += bytes([0, 1, 0])
    h[0x69 + 2:0x69 + 4] = s.to_bytes(2, 'little')
    h[0xA9:0xAB] = o.to_bytes(2, 'little')
    return bytes(h)

if __name__ == '__main__':
    for n in range(4):
        t = tabla_notas(n); print(n, t[:12], t[48:52])
