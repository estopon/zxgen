"""Conversión de imágenes al formato de pantalla del Spectrum (6912 bytes)."""
from PIL import Image

PALETA = [(0,0,0),(0,0,0xD7),(0xD7,0,0),(0xD7,0,0xD7),(0,0xD7,0),(0,0xD7,0xD7),(0xD7,0xD7,0),(0xD7,0xD7,0xD7),
          (0,0,0),(0,0,0xFF),(0xFF,0,0),(0xFF,0,0xFF),(0,0xFF,0),(0,0xFF,0xFF),(0xFF,0xFF,0),(0xFF,0xFF,0xFF)]

def dir_pixel(y):
    """Desplazamiento dentro de la pantalla de la fila de píxeles y (columna 0)."""
    return ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)

def _d2(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2

def convertir_celda(celda):
    """celda: 64 colores RGB (8x8). Devuelve (8 bytes de bitmap, atributo)
    eligiendo el par tinta/papel y brillo con menos error."""
    mejor = None
    for brillo in (0, 8):
        pal = PALETA[brillo:brillo+8]
        dist = [[_d2(p, c) for c in pal] for p in celda]
        for i in range(8):
            for j in range(i, 8):
                err = 0
                for d in dist:
                    err += d[i] if d[i] < d[j] else d[j]
                    if mejor and err >= mejor[0]:
                        break
                if mejor is None or err < mejor[0]:
                    mejor = (err, brillo, i, j)
    _, brillo, tinta, papel = mejor
    pal = PALETA[brillo:brillo+8]
    filas = []
    for y in range(8):
        b = 0
        for x in range(8):
            p = celda[y*8+x]
            if tinta != papel and _d2(p, pal[tinta]) < _d2(p, pal[papel]):
                b |= 0x80 >> x
        filas.append(b)
    return filas, (0x40 if brillo else 0) | (papel << 3) | tinta

def imagen_a_scr(img):
    """Convierte una imagen PIL cualquiera a 6912 bytes (bitmap + atributos)."""
    img = img.convert('RGB').resize((256, 192), Image.LANCZOS)
    px = img.load()
    scr = bytearray(6912)
    for cy in range(24):
        for cx in range(32):
            celda = [px[cx*8+x, cy*8+y] for y in range(8) for x in range(8)]
            filas, atr = convertir_celda(celda)
            for y in range(8):
                scr[dir_pixel(cy*8+y) + cx] = filas[y]
            scr[6144 + cy*32 + cx] = atr
    return bytes(scr)

def cargar_pantalla(ruta):
    """Acepta .scr (6912 bytes) o cualquier imagen que lea Pillow."""
    if ruta.lower().endswith('.scr'):
        datos = open(ruta, 'rb').read()
        if len(datos) < 6912:
            raise ValueError('El .scr debe tener 6912 bytes')
        return datos[:6912]
    return imagen_a_scr(Image.open(ruta))

def scr_a_imagen(scr, escala=2, borde=None):
    """Imagen PIL de una pantalla de 6912 bytes (para previsualizar)."""
    img = Image.new('RGB', (256, 192))
    px = img.load()
    for y in range(192):
        base = dir_pixel(y)
        for cx in range(32):
            b = scr[base + cx]
            at = scr[6144 + (y >> 3)*32 + cx]
            br = 8 if at & 0x40 else 0
            tinta, papel = PALETA[(at & 7) + br], PALETA[((at >> 3) & 7) + br]
            for bit in range(8):
                px[cx*8 + bit, y] = tinta if b & (0x80 >> bit) else papel
    if borde is not None:
        marco = Image.new('RGB', (256+32, 192+32), PALETA[borde])
        marco.paste(img, (16, 16)); img = marco
    return img.resize((img.width*escala, img.height*escala), Image.NEAREST)

# ---------- fuentes de 8x8 (caracteres 32 a 127) ----------
def cargar_fuente(ruta):
    """Devuelve 768 bytes. Acepta un binario de 768 bytes (o de 2048 con los 256 caracteres)
    o una imagen con los caracteres en una rejilla de 8x8 por filas (32x3, 16x6...)."""
    datos = open(ruta, 'rb').read()
    if len(datos) == 768:
        return datos
    if len(datos) == 2048:
        return datos[256:1024]
    img = Image.open(ruta).convert('RGB'); px = img.load()
    cols, filas = img.width // 8, img.height // 8
    if cols * filas < 96:
        raise ValueError('La imagen debe contener 96 caracteres de 8×8 (por ejemplo 256×24 o 128×48 píxeles).')
    fondo = px[0, 0]
    d = bytearray()
    for n in range(96):
        cx, cy = (n % cols) * 8, (n // cols) * 8
        for y in range(8):
            b = 0
            for x in range(8):
                if _d2(px[cx + x, cy + y], fondo) > 3000:
                    b |= 0x80 >> x
            d.append(b)
    return bytes(d)

def imagen_fuente(fuente):
    """Los 96 caracteres en una rejilla de 32x3 (256x24), blanco sobre negro."""
    img = Image.new('RGB', (256, 24)); px = img.load()
    for n in range(96):
        cx, cy = (n % 32) * 8, (n // 32) * 8
        for y in range(8):
            b = fuente[n * 8 + y]
            for x in range(8):
                if b & (0x80 >> x):
                    px[cx + x, cy + y] = (255, 255, 255)
    return img
