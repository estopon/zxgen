"""Formato y dibujo de tiles y sprites.
Tiles 16x16: 'pix' = 16 cadenas de 16 caracteres ('X' tinta, '.' papel, 'm' mezcla), 'atr' = 4
             atributos (arriba-izq, arriba-dcha, abajo-izq, abajo-dcha).
             'm' (modo mezcla, estilo Super Mario Bros de 128K): el pixel se enciende en una de las dos
             pantallas y se apaga en la otra, en damero; al alternarlas a 50 Hz se ve el tono intermedio
             entre tinta y papel. Fuera del modo mezcla se dibuja como un damero fijo.
Sprites:     'pix' = cadenas ('X' tinta, 'o' contorno opaco, '.' transparente)."""
from PIL import Image
from pantalla import PALETA

# tamaños de personaje: ancho (8, 16, 24 o 32) x alto (8, 16, 24 o 32); y de las balas
TAMANOS = {f'{w}x{h}': (w, h) for w in (8, 16, 24, 32) for h in (8, 16, 24, 32)}
TAMANOS_PERSONAJE = list(TAMANOS)
TAMANOS_FRECUENTES = ('8x8', '16x16', '16x24', '16x32', '24x24', '32x32')   # los que más se usan
TAMANOS_BALA = ('8x8', '8x16', '16x8')

def atributo(tinta, papel, brillo=0):
    return (0x40 if brillo else 0) | ((papel & 7) << 3) | (tinta & 7)

def partes_atr(a):
    return a & 7, (a >> 3) & 7, 1 if a & 0x40 else 0

def tile_vacio(a=atributo(0, 4)):
    return {'pix': ['.' * 16] * 16, 'atr': [a] * 4, 'solido': False, 'detiene': False}

def sprite_vacio(w, h):
    return ['.' * w for _ in range(h)]

def redimensionar(pix, w, h):
    filas = [(f + '.' * w)[:w] for f in pix[:h]]
    return filas + ['.' * w] * (h - len(filas))

def contorno_auto(pix):
    """Rodea la tinta con un contorno opaco de 1 píxel (8 vecinos)."""
    h, w = len(pix), len(pix[0])
    res = [list(f.replace('o', '.')) for f in pix]
    for y in range(h):
        for x in range(w):
            if pix[y][x] == 'X':
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w and res[yy][xx] == '.':
                            res[yy][xx] = 'o'
    return [''.join(f) for f in res]

# ---------- codificación para el Spectrum ----------
def bit_pixel(c, x, y, fase=0):
    """1 si el pixel (x, y) del tile se enciende en la pantalla 'fase' (0 o 1)."""
    return 1 if c == 'X' or (c == 'm' and (x + y) % 2 == fase) else 0

def fila_bits(fila, y, fase=0, x0=0):
    v = 0
    for x, c in enumerate(fila):
        v = (v << 1) | bit_pixel(c, x0 + x, y, fase)
    return v

def usa_mezcla(t):
    return any('m' in f for f in t['pix'])

def bytes_tile(t):
    d = bytearray()
    for y, fila in enumerate(t['pix']):
        v = fila_bits(fila, y)
        d += bytes([v >> 8, v & 0xFF])
    d += bytes(t['atr'])
    return bytes(d)

DESPLAZAMIENTOS = (0, 2, 4, 6)

def bytes_sprite(pix):
    """4 versiones pre-desplazadas (0, 2, 4, 6 píxeles a la derecha).
    Cada versión: por línea, (ancho/8 + 1) pares (máscara AND, datos)."""
    w = len(pix[0]); nb = w // 8 + 1
    d = bytearray()
    for s in DESPLAZAMIENTOS:
        for fila in pix:
            opaco = int(''.join('1' if c in 'Xo' else '0' for c in fila), 2) << (8 - s)
            tinta = int(''.join('1' if c == 'X' else '0' for c in fila), 2) << (8 - s)
            for k in range(nb):
                rs = (nb - 1 - k) * 8
                d += bytes([~(opaco >> rs) & 0xFF, (tinta >> rs) & 0xFF])
    return bytes(d)

# ---------- imágenes para el editor ----------
def imagen_tile(t, escala=1):
    img = Image.new('RGB', (16, 16)); px = img.load()
    for y in range(16):
        for x in range(16):
            a = t['atr'][(y // 8) * 2 + x // 8]
            tinta, papel, br = partes_atr(a)
            c = t['pix'][y][x]
            if c == 'm':
                ti, pa = PALETA[tinta + 8 * br], PALETA[papel + 8 * br]
                px[x, y] = tuple((u + v) // 2 for u, v in zip(ti, pa))
            else:
                px[x, y] = PALETA[(tinta if c == 'X' else papel) + 8 * br]
    return img.resize((16 * escala, 16 * escala), Image.NEAREST) if escala != 1 else img

def imagen_sprite(pix, escala=1, fondo=(0, 0, 0), tinta=(255, 255, 255), contorno=(0, 0, 0)):
    h, w = len(pix), len(pix[0])
    img = Image.new('RGB', (w, h), fondo); px = img.load()
    for y in range(h):
        for x in range(w):
            c = pix[y][x]
            if c == 'X': px[x, y] = tinta
            elif c == 'o': px[x, y] = contorno
    return img.resize((w * escala, h * escala), Image.NEAREST)


# ---------- sprites compilados (modo bloques) ----------
def compilar_sprite(pix, nl):
    """Compila un fotograma en sus 4 desplazamientos (0, 2, 4, 6). Cada versión es código Z80 que,
    entrando con HL = primera línea en pantalla y C = su byte bajo, dibuja el sprite:
    bytes transparentes = nada; opacos = ld (hl),n; de borde = ld a,(hl) / and m / or d / ld (hl),a.
    nl = dirección de la rutina del motor que pasa a la siguiente línea."""
    datos = bytes_sprite(pix)
    h = len(pix); nb = len(pix[0]) // 8 + 1
    por_version = h * nb * 2
    versiones = []
    for v in range(4):
        c = bytearray()
        bloque = datos[v * por_version:(v + 1) * por_version]
        for y in range(h):
            avance = 0                                   # inc l pendientes
            for k in range(nb):
                m, d = bloque[(y * nb + k) * 2], bloque[(y * nb + k) * 2 + 1]
                if m == 0xFF and d == 0:                 # transparente
                    avance += 1; continue
                c += bytes([0x2C]) * avance; avance = 1  # inc l
                if m == 0x00:
                    c += bytes([0x36, d])                # ld (hl),d
                else:
                    c += bytes([0x7E, 0xE6, m])          # ld a,(hl) / and m
                    if d: c += bytes([0xF6, d])          # or d
                    c += bytes([0x77])                   # ld (hl),a
            if y < h - 1:
                c += bytes([0xCD, nl & 0xFF, nl >> 8])   # call siguiente línea
        c.append(0xC9)                                   # ret
        versiones.append(bytes(c))
    return versiones
