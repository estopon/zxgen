"""Herramientas para crear contenido de ejemplo: dibujo sobre rejillas de píxeles, personajes,
naves y criaturas generados, música a partir de notas y pantallas de carga y título."""
import math
import random
from graficos import atributo, contorno_auto


# ---------------- rejillas de píxeles ----------------
class Lienzo:
    """Rejilla de w x h con 'X' (tinta) y '.' (transparente / papel)."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [['.'] * w for _ in range(h)]

    def pon(self, x, y, c='X'):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h: self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c='X'):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1): self.pon(x, y, c)

    def linea(self, x0, y0, x1, y1, grosor=1, c='X'):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / max(1, n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(grosor):
                for dy in range(grosor): self.pon(x + dx - grosor // 2, y + dy - grosor // 2, c)

    def circulo(self, cx, cy, r, c='X'):
        for y in range(self.h):
            for x in range(self.w):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.5: self.pon(x, y, c)

    def filas(self):
        return [''.join(f) for f in self.p]


def patron(f, w=16, h=16):
    return [''.join('X' if f(x, y) else '.' for x in range(w)) for y in range(h)]


def tile(pix, tinta, papel=0, brillo=0, **props):
    t = {'pix': pix, 'atr': [atributo(tinta, papel, brillo)] * 4, 'solido': False, 'detiene': False}
    t.update(props)
    return t


def espejo(pix):
    return [f[::-1] for f in pix]


def girar(pix):                       # 90 grados en sentido horario
    h, w = len(pix), len(pix[0])
    return [''.join(pix[h - 1 - x][y] for x in range(h)) for y in range(w)]


# ---------------- personajes de perfil ----------------
def humano(w, h, pose, fase=0, estilo=None):
    """Figura humana de perfil mirando a la derecha, diseñada en 16x24 y escalada a w x h.
    pose: 'quieto', 'andar' (fase 0-3), 'golpe', 'patada', 'salto'.
    estilo: {'casco', 'capa', 'arma', 'pelo', 'gordo'} (booleanos)."""
    e = {'casco': False, 'capa': False, 'arma': False, 'pelo': True, 'gordo': False}
    e.update(estilo or {})
    L = Lienzo(w, h)
    sy, sx = h / 24, w / 16
    X = lambda v: v * sx
    Y = lambda v: v * sy
    g = 1 if e['gordo'] else 0
    # brazo de atrás (se dibuja primero)
    zanc = {0: 0, 1: 1, 2: 0, 3: -1}[fase % 4] if pose == 'andar' else 0
    if pose not in ('golpe', 'salto'):
        L.linea(X(7), Y(8), X(7 + zanc * 2), Y(13), 2)
    # cabeza, cuello y tronco
    L.circulo(X(8), Y(3.2), 3.1 * min(sx, sy))
    if e['casco']: L.rect(X(5), Y(0), X(11), Y(1.4))
    elif e['pelo']: L.rect(X(5), Y(0), X(9), Y(1)); L.rect(X(5), Y(1), X(6), Y(3))
    L.pon(X(10), Y(3), '.')                                   # ojo
    L.rect(X(7), Y(6), X(8), Y(7))                            # cuello
    L.rect(X(5 - g), Y(7), X(10 + g), Y(14))                  # tronco
    L.rect(X(5 - g), Y(13), X(10 + g), Y(13), '.')            # cinturón
    if e['capa']: L.linea(X(5), Y(7), X(2), Y(16), 2)
    # piernas
    if pose == 'salto':
        L.linea(X(6), Y(14), X(4), Y(18), 2); L.linea(X(4), Y(18), X(6), Y(22), 2)
        L.linea(X(9), Y(14), X(12), Y(17), 2); L.linea(X(12), Y(17), X(11), Y(21), 2)
    elif pose == 'patada':
        L.linea(X(9), Y(14), X(15), Y(13), 2)
        L.linea(X(6), Y(14), X(6), Y(23), 2); L.rect(X(6), Y(23), X(8), Y(23))
    else:
        for d in (zanc, -zanc):
            pie = 7.5 + d * 3.5
            L.linea(X(7.5), Y(14), X(7.5 + d * 1.5), Y(18.5), 2)        # muslo
            L.linea(X(7.5 + d * 1.5), Y(18.5), X(pie), Y(23), 2)        # pierna
            L.rect(X(pie), Y(23), X(pie + 2), Y(23))                    # pie
    # brazo de delante
    if pose == 'golpe':
        L.linea(X(9), Y(8), X(14), Y(8), 2); L.rect(X(14), Y(7), X(15), Y(9))
    elif pose == 'salto':
        L.linea(X(9), Y(8), X(12), Y(5), 2)
    else:
        mano = (X(9 - zanc * 2), Y(13))
        L.linea(X(9), Y(8), mano[0], mano[1], 2)
        if e['arma']: L.linea(mano[0], mano[1] - 1, min(w - 1, mano[0] + 5 * sx), mano[1] - 2, 1)
    return contorno_auto(L.filas())


def humano_cenital(w, h, fase=0):
    """Soldado visto desde arriba, mirando hacia arriba (para rotar a 8 direcciones)."""
    L = Lienzo(w, h)
    cx, cy = w / 2 - 0.5, h / 2
    L.circulo(cx + 0.5, cy, w * 0.22)            # casco
    L.rect(cx - w * 0.33, cy - 1, cx + w * 0.33 + 1, cy + 2)   # hombros
    L.linea(cx + w * 0.25, cy - 1, cx + w * 0.25, 1, 2)      # fusil
    pierna = 2 if fase % 2 else -2
    L.rect(cx - 3, cy + 3, cx - 2, h - 3 + pierna)
    L.rect(cx + 3, cy + 3, cx + 4, h - 3 - pierna)
    return contorno_auto(L.filas())


def criatura(w, h, semilla, fase=0, densidad=0.55):
    """Criatura simétrica generada (al estilo de los marcianitos clásicos), dentro de una silueta
    elíptica; la fase mueve patas y antenas."""
    r = random.Random(semilla)
    mitad = w // 2
    cy = h / 2 - 0.5
    celdas = []
    for y in range(h):
        fila = []
        for x in range(mitad):
            dist = ((x + 0.5 - mitad) / mitad) ** 2 + ((y - cy) / (h / 2)) ** 2
            fila.append(dist < 0.95 and r.random() < densidad * (1.3 - dist))
        celdas.append(fila)
    for y in range(2, h - 2): celdas[y][mitad - 1] = True          # cuerpo
    for y in range(int(cy) - 1, int(cy) + 2):
        for x in range(mitad // 2, mitad): celdas[y][x] = True
    ojo = int(cy) - 2
    celdas[ojo][mitad - 2] = False
    if fase % 2:
        for y in range(h - 3, h): celdas[y] = celdas[y][1:] + [False]
        for y in range(0, 2): celdas[y] = [False] + celdas[y][:-1]
    filas = []
    for y in range(h):
        izq = ''.join('X' if c else '.' for c in celdas[y])
        filas.append(izq + izq[::-1])
    return contorno_auto(filas)


def nave(w=16, h=16, variante=0, fase=0):
    """Nave vista desde arriba con el morro hacia arriba (simétrica: se dibuja media y se refleja)."""
    m = w // 2
    L = Lienzo(m, h)
    L.rect(m - 2, 1, m - 1, h - 4)                    # fuselaje
    L.rect(m - 3, 5, m - 1, h - 5)
    a0, a1 = [(5, 10), (3, 11), (6, 9)][variante % 3]
    for y in range(a0, a1 + 1):                        # ala
        L.rect(m - 1 - (y - a0) * (m - 1) / max(1, a1 - a0), y, m - 1, y)
    L.rect(m - 5, h - 5, m - 4, h - 3)                # motor
    L.pon(m - 5 + (fase % 2), h - 2)                  # llama
    L.pon(m - 1, 3, '.')                              # cabina
    if variante % 3 == 2: L.rect(0, 7, 0, 10)          # puntas de ala
    filas = [f + f[::-1] for f in L.filas()]
    return contorno_auto(filas)


def bala(forma='punto'):
    L = Lienzo(8, 8)
    if forma == 'punto': L.circulo(3.5, 3.5, 2)
    elif forma == 'rayo': L.rect(3, 0, 4, 7)
    elif forma == 'rayo_h': L.rect(0, 3, 7, 4)
    elif forma == 'estrella': L.linea(1, 1, 6, 6); L.linea(6, 1, 1, 6); L.rect(3, 3, 4, 4)
    return L.filas()


# ---------------- música ----------------
NOTAS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(n):
    """'C4', 'F#5', 'Bb3' -> número MIDI."""
    nota, resto = n[0], n[1:]
    alt = 0
    while resto and resto[0] in '#b':
        alt += 1 if resto[0] == '#' else -1; resto = resto[1:]
    return 12 * (int(resto) + 1) + NOTAS[nota] + alt


def melodia(texto):
    """'E5:1 D#5:.5 R:1 ...' -> lista de (midi o None, duración en tiempos)."""
    out = []
    for tok in texto.split():
        n, d = tok.split(':')
        out.append((None if n == 'R' else midi(n), float(d)))
    return out


def componer(nombre, tema, bajo, tempo=140, repeticiones=2, arps=False):
    """Melodía + bajo (lista de (nota, tiempos)) -> módulo PT3. Necesita spectrumizer en /tmp/sp."""
    import sys
    if '/tmp/sp' not in sys.path: sys.path.insert(0, '/tmp/sp')
    from spectrumizer.ir import Song, Note
    from spectrumizer.arrange import arrange
    notas, t = [], 0.0
    largo_tema = sum(d for _, d in tema)
    for k in range(repeticiones):
        t = k * largo_tema
        for n, d in tema:
            if n is not None: notas.append(Note(pitch=n, start=t, dur=d * 0.9, velocity=100, track=0))
            t += d
    t, total = 0.0, largo_tema * repeticiones
    while t < total:
        for n, d in bajo:
            if t >= total: break
            if n is not None: notas.append(Note(pitch=n, start=t, dur=d * 0.8, velocity=80, track=1))
            t += d
    pt3, _ = arrange(Song(notes=notas, tempo_bpm=tempo, name=nombre[:32]), arps=arps)
    return pt3


# ---------------- pantallas ----------------
def pantalla(titulo, subtitulo, fondo, colores, tipo='carga'):
    """Pantalla de 256x192 con escena de fondo (fondo(dibujo, w, h)), título y subtítulo -> SCR."""
    from PIL import Image, ImageDraw, ImageFont
    from pantalla import imagen_a_scr
    img = Image.new('RGB', (256, 192), colores[0])
    d = ImageDraw.Draw(img)
    fondo(d, 256, 192)
    fuente = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    try:
        grande = ImageFont.truetype(fuente, 34 if len(titulo) <= 9 else 26)
        peq = ImageFont.truetype(fuente, 11)
    except OSError:
        grande = peq = ImageFont.load_default()
    w = d.textlength(titulo, font=grande)
    y = 22 if tipo == 'carga' else 14
    for dx, dy in ((2, 2), (1, 1)):
        d.text(((256 - w) / 2 + dx, y + dy), titulo, font=grande, fill=(0, 0, 0))
    d.text(((256 - w) / 2, y), titulo, font=grande, fill=colores[1])
    ws = d.textlength(subtitulo, font=peq)
    d.text(((256 - ws) / 2, y + 44), subtitulo, font=peq, fill=colores[2])
    if tipo == 'titulo':
        d.rectangle((0, 128, 255, 191), fill=(0, 0, 0))          # el menú va de la fila 16 en adelante
    return imagen_a_scr(img)
