"""«TERRA ZX»: plataformas de scroll horizontal en modo mezcla, con la estructura de un juego de
plataformas clásico de 128K (cielo negro, suelo con huecos, filas de ladrillos que se rompen de un
cabezazo, bloques sorpresa, gemas, escalinatas, torres y enemigos que se aplastan al caerles encima),
pero con gráficos, personajes y fases propios.
Uso:  python ejemplo_terra.py      (escribe ejemplos/terra_zx.json y juegos/terra_zx.tap)"""
import random
import juego, graficos
from graficos import atributo, contorno_auto
from arte import Lienzo, patron, humano, espejo, pantalla, bala

NEGRO, AZUL, ROJO, MAGENTA, VERDE, CIAN, AMARILLO, BLANCO = range(8)
FILAS = 10                      # el mapa horizontal tiene 10 filas de tiles: 8 y 9 son el suelo
LARGO = 171                     # columnas por fase: lo más largo que cabe con 8 fases (ver maximo())


def m_si(pix, cond):
    """Pasa a 'm' (tono intermedio) los píxeles de papel que cumplen cond(x, y)."""
    return [''.join('m' if c == '.' and cond(x, y) else c for x, c in enumerate(f)) for y, f in enumerate(pix)]


def tile(pix, atr, **props):
    t = {'pix': pix, 'atr': atr if isinstance(atr, list) else [atr] * 4, 'solido': False, 'detiene': False}
    t.update(props)
    return t


# ---------------------------------------------------------------- tiles
VACIO, TIERRA, CESPED, LADRILLO, SORPRESA, USADO, GEMA, ROCA, TORRE_I, TORRE_D, CAPI_I, CAPI_D, \
    PINCHOS, CORAZON, PASARELA, MASTIL, BANDERA, AMULETO, PUERTA = range(19)
AMULETO_E, LLAVE_E = 0, 1          # elementos del inventario


def tiles():
    br = lambda tinta, papel=NEGRO: atributo(tinta, papel, 1)
    T = [None] * 19
    T[VACIO] = tile(['.' * 16] * 16, br(BLANCO))
    # tierra: grietas en tinta y relleno en tono medio -> rojo oscuro
    # (los dibujos se repiten cada 8 píxeles en horizontal: así las dos mitades del tile son iguales
    # y hay menos combinaciones de columnas vecinas que guardar)
    grieta = lambda x, y: (y % 8 == 7) or (x + (4 if (y // 8) % 2 else 0)) % 8 == 0 or (x % 8 == 5 and y % 8 == 3)
    # tierra de abajo: sin píxeles, solo color (el motor no la dibuja: sale gratis)
    T[TIERRA] = tile(['.' * 16] * 16, atributo(ROJO, ROJO, 0), solido=True, detiene=True)
    # suelo de arriba: también solo color (hierba verde sobre tierra roja); el dibujo queda para
    # ladrillos, bloques, rocas y torres
    T[CESPED] = tile(['.' * 16] * 16, [atributo(VERDE, VERDE, 1)] * 2 + [atributo(ROJO, ROJO, 0)] * 2,
                     solido=True, detiene=True)
    # ladrillo: amarillo sobre rojo con tono medio -> naranja
    lad = patron(lambda x, y: y % 4 == 3 or (x + (4 if (y // 4) % 2 else 0)) % 8 == 0)
    T[LADRILLO] = tile(m_si(lad, lambda x, y: True), br(AMARILLO, ROJO), solido=True, detiene=True,
                       rompible=True, tras=VACIO, puntos=10)
    # bloque sorpresa: marco y un rombo; al golpearlo da puntos y queda vacío
    marco = lambda x, y: x in (0, 15) or y in (0, 15) or (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13))
    rombo = lambda x, y: abs(x - 7.5) + abs(y - 7.5) <= 4.5
    T[SORPRESA] = tile(m_si(patron(lambda x, y: marco(x, y) or rombo(x, y)), lambda x, y: not rombo(x, y)),
                       br(AMARILLO), solido=True, detiene=True, rompible=True, tras=VACIO, puntos=50)
    T[USADO] = tile(m_si(patron(marco), lambda x, y: True), atributo(AMARILLO, NEGRO, 0), solido=True, detiene=True)
    # gema que se recoge
    gema = lambda x, y: abs(x - 7.5) + abs(y - 7.5) * 0.8 <= 5.5
    T[GEMA] = tile(m_si(patron(lambda x, y: gema(x, y) and (x < 8 or y < 5)), gema), br(CIAN),
                   objeto=True, accion='puntos', puntos=50, tras=VACIO)
    # roca de escalinata: gris (blanco en tono medio)
    T[ROCA] = tile(m_si(patron(lambda x, y: x in (0, 15) or y in (0, 15) or x == y or x + y == 15),
                        lambda x, y: 0 < x < 15 and 0 < y < 15 and abs(x - y) > 1 and abs(x + y - 15) > 1),
                   br(BLANCO), solido=True, detiene=True)
    # torre de piedra de dos tiles de ancho, con capitel
    fuste_i = patron(lambda x, y: x in (0, 1) or x == 5 or x == 10 or (y % 8 == 0 and x > 1))
    fuste_d = patron(lambda x, y: x in (14, 15) or x == 5 or x == 10 or (y % 8 == 4 and x < 14))
    T[TORRE_I] = tile(m_si(fuste_i, lambda x, y: x > 1), br(CIAN), solido=True, detiene=True)
    T[TORRE_D] = tile(m_si(fuste_d, lambda x, y: x < 14), br(CIAN), solido=True, detiene=True)
    cap = lambda x, y: y < 2 or y > 13 or (y in (6, 7) and x % 4 < 2)
    T[CAPI_I] = tile(m_si(patron(lambda x, y: cap(x, y) or x == 0), lambda x, y: 1 < y < 14), br(CIAN),
                     solido=True, detiene=True)
    T[CAPI_D] = tile(m_si(patron(lambda x, y: cap(x, y) or x == 15), lambda x, y: 1 < y < 14), br(CIAN),
                     solido=True, detiene=True)
    T[PINCHOS] = tile(patron(lambda x, y: y >= 8 and abs((x % 8) - 3.5) <= (y - 8) / 2), br(BLANCO), mortal=True)
    corazon = lambda x, y: (y >= 5 and abs(x - 7.5) <= (13 - y) * 0.9 and y <= 13) or \
        (3 <= y <= 6 and ((x - 4.5) ** 2 + (y - 5) ** 2 <= 5 or (x - 10.5) ** 2 + (y - 5) ** 2 <= 5))
    T[CORAZON] = tile(m_si(patron(lambda x, y: corazon(x, y) and y < 8), corazon), br(MAGENTA),
                      objeto=True, accion='vida', puntos=100, tras=VACIO)
    T[PASARELA] = tile(m_si(patron(lambda x, y: y in (0, 4) or (y < 4 and x % 4 == 0)), lambda x, y: y < 4),
                       br(AMARILLO), plataforma=True)
    T[MASTIL] = tile(patron(lambda x, y: x in (7, 8)), br(BLANCO))
    T[BANDERA] = tile(m_si(patron(lambda x, y: x in (7, 8) or (y < 9 and 8 < x <= 8 + (9 - abs(y - 4) * 2))),
                           lambda x, y: False), br(VERDE))
    # amuleto (se guarda en el inventario) y puerta de piedra (lleva a otra fase; esta necesita la llave)
    T[AMULETO] = tile(m_si(patron(lambda x, y: ((x - 7.5) ** 2 + (y - 9) ** 2 < 16) or (7 <= x <= 8 and 2 <= y <= 5)),
                           lambda x, y: (x - 7.5) ** 2 + (y - 9) ** 2 < 9), br(MAGENTA),
                      objeto=True, accion='guardar', valor=AMULETO_E, puntos=100, tras=VACIO)
    PUERTA_PIX = ['.....XXXXXX.....',
                  '...XXmmXXmmXX...',
                  '..XmmmmXXmmmmX..',
                  '.XmmmmmXXmmmmmX.',
                  '.XmmmmmXXmmmmmX.',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmXXmX',
                  'XmmmmmmXXmmmXXmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XmmmmmmXXmmmmmmX',
                  'XXXXXXXXXXXXXXXX']
    T[PUERTA] = tile(PUERTA_PIX, br(AMARILLO),
                     objeto=True, accion='puerta', valor=6, columna=0, llave=LLAVE_E,
                     mensaje='PUERTA CERRADA|FALTA UNA LLAVE')
    return T


def aplastar(pix, alto=6):
    """El mismo dibujo aplastado contra el suelo (fotograma de muerte al pisarlo)."""
    h, w = len(pix), len(pix[0])
    filas = [pix[round(k * (h - 1) / (alto - 1))] for k in range(alto)]
    return contorno_auto(['.' * w] * (h - alto) + [f.replace('o', '.') for f in filas])


# ---------------------------------------------------------------- personajes
def heroe():
    """Exploradora con casco y capa (16x24): andar (4), salto y sus espejos."""
    est = {'casco': True, 'capa': True}
    # pocos fotogramas: así el jugador cabe compilado (código Z80 en el banco 7), que dibuja mucho más rápido
    der = [humano(16, 24, 'andar', k, est) for k in (1, 3)] + [humano(16, 24, 'salto', 0, est)]
    fr = der + [espejo(f) for f in der]          # 0-1 andar dcha, 2 salto dcha, 3-4 andar izq, 5 salto izq
    # 6 agachada (de frente: sirve para los dos lados) y 7 muerte (de frente, brazos arriba)
    L = Lienzo(16, 24)
    L.circulo(7.5, 13.5, 3); L.rect(4, 11, 11, 12); L.pon(6, 13, '.'); L.pon(9, 13, '.')
    L.rect(3, 17, 12, 20); L.rect(2, 21, 6, 23); L.rect(9, 21, 13, 23); L.linea(3, 17, 0, 21, 2); L.linea(12, 17, 15, 21, 2)
    agachada = contorno_auto(L.filas())
    L = Lienzo(16, 24)
    L.circulo(7.5, 6, 3); L.rect(4, 3, 11, 3); L.rect(5, 10, 10, 16)
    L.linea(5, 10, 1, 2, 2); L.linea(10, 10, 14, 2, 2); L.linea(6, 16, 4, 23, 2); L.linea(9, 16, 11, 23, 2)
    L.pon(6, 6, '.'); L.pon(9, 6, '.')
    muerte = contorno_auto(L.filas())
    fr += [agachada, muerte]
    anim = {k: [] for k in juego.DIRECCIONES}
    anim.update({'dcha': [0, 1], 'izq': [3, 4], 'arriba-dcha': [2], 'arriba-izq': [5]})
    return {'tamano': '16x24', 'velocidad': 2, 'x': 24, 'y': 104, 'cadencia': 8, 'vel_anim': 5,
            'quieto': {'dcha': 0, 'izq': 3}, 'disparo': {}, 'fotogramas': fr, 'anim': anim,
            'agachado': {'dcha': 6, 'izq': 6}, 'muerte': 7,
            'arma': 'ninguna', 'alcance': 12, 'pisar': True, 'color': atributo(BLANCO, NEGRO, 1)}


def caracol(fase):
    L = Lienzo(16, 16)
    L.circulo(9, 7.5, 5.5)                              # concha
    L.circulo(9, 7.5, 3.6, '.'); L.circulo(9, 7.5, 2.2); L.circulo(9.6, 7.5, 0.9, '.')
    L.rect(0, 12, 15, 14)                               # cuerpo
    L.rect(1, 8 - fase, 3, 12)                          # cabeza
    L.linea(1, 8 - fase, 0, 4 - fase); L.linea(3, 8 - fase, 4, 4 - fase)    # antenas
    L.pon(2, 9 - fase, '.')
    if fase: L.pon(15, 14, '.'); L.pon(13, 14, '.')
    return contorno_auto(L.filas())


def escarabajo(fase):
    L = Lienzo(16, 16)
    L.circulo(7.5, 8, 6)
    L.linea(7.5, 3, 7.5, 13, 1, '.')
    L.rect(5, 1, 10, 3)
    for k, y in enumerate((6, 9, 12)):
        d = 1 if (k + fase) % 2 else 0
        L.pon(0 + d, y); L.pon(15 - d, y)
    L.pon(5, 2, '.'); L.pon(10, 2, '.')
    return contorno_auto(L.filas())


def abeja(fase):
    L = Lienzo(16, 16)
    L.circulo(8, 10, 4.5)
    for x in (6, 9): L.linea(x, 6, x, 14, 1, '.')
    L.circulo(13, 9, 2)
    L.pon(14, 8, '.')
    if fase: L.circulo(5, 4, 3); L.circulo(9, 3, 2.5)
    else: L.circulo(5, 6, 2.5); L.circulo(9, 6, 2.2)
    L.linea(2, 11, 0, 12)
    return contorno_auto(L.filas())


def murcielago(fase):
    L = Lienzo(16, 16)
    L.circulo(7.5, 8, 3)
    L.pon(6, 7, '.'); L.pon(9, 7, '.')
    L.rect(5, 3, 5, 5); L.rect(10, 3, 10, 5)
    if fase:
        L.linea(5, 8, 0, 3, 2); L.linea(10, 8, 15, 3, 2); L.linea(0, 3, 2, 9); L.linea(15, 3, 13, 9)
    else:
        L.linea(5, 8, 0, 12, 2); L.linea(10, 8, 15, 12, 2); L.linea(0, 12, 3, 8); L.linea(15, 12, 12, 8)
    return contorno_auto(L.filas())


def golem(fase):
    """Guardián de piedra (16x24) que patrulla al final de las fases."""
    L = Lienzo(16, 24)
    L.rect(3, 1, 12, 8); L.pon(5, 4, '.'); L.pon(10, 4, '.'); L.rect(6, 6, 9, 6, '.')
    L.rect(2, 10, 13, 17); L.rect(4, 12, 11, 15, '.'); L.rect(6, 13, 9, 14)
    L.rect(0, 10, 1, 15 + fase); L.rect(14, 10, 15, 16 - fase)
    for x0 in ((3, 9) if fase else (4, 8)):
        L.rect(x0, 18, x0 + 3, 23)
    return contorno_auto(L.filas())


def sabio(fase):
    """Anciano con bastón (16x24): personaje con el que se habla."""
    L = Lienzo(16, 24)
    L.circulo(7, 4, 3); L.rect(3, 0, 11, 1)                      # cabeza y sombrero
    L.pon(5, 4, '.'); L.pon(8, 4, '.')
    L.rect(5, 7, 9, 10)                                         # barba
    L.rect(3, 9, 11, 22); L.rect(5, 12, 9, 12, '.')            # túnica
    L.linea(13, 6 + fase, 13, 23); L.linea(11, 12, 13, 11)      # bastón y brazo
    return contorno_auto(L.filas())


def muerte_volador(pix):
    """Fotograma de muerte de un bicho que vuela: boca abajo."""
    return contorno_auto([f.replace('o', '.') for f in pix[::-1]])


def enemigos():
    def e(nombre, tam, frames, comp, color, vel=1, energia=1, puntos=100, direccion='izq', voltear=True, vel_anim=6,
          muerte=None, **extra):
        en = {'nombre': nombre, 'tamano': tam, 'fotogramas': frames, 'comportamiento': comp, 'velocidad': vel,
              'energia': energia, 'cadencia': 0, 'puntos': puntos, 'direccion': direccion, 'voltear': voltear,
              'vel_anim': vel_anim, 'color': atributo(color, NEGRO, 1)}
        if muerte is not None:                  # el último fotograma es el de muerte
            en['fotogramas'] = frames + [muerte]; en['muerte'] = len(frames)
        en.update(extra)
        return en
    return [
        e('Caracol', '16x16', [caracol(0), caracol(1)], 'patrulla', VERDE, puntos=100, muerte=aplastar(caracol(0), 5)),
        e('Escarabajo', '16x16', [escarabajo(0), escarabajo(1)], 'patrulla', MAGENTA, vel=2, puntos=150,
          muerte=aplastar(escarabajo(0), 5)),
        e('Abeja', '16x16', [abeja(0), abeja(1)], 'rebota', AMARILLO, puntos=200, direccion='abajo-izq',
          voltear=False, vel_anim=3, muerte=muerte_volador(abeja(0))),
        e('Murcielago', '16x16', [murcielago(0), murcielago(1)], 'persigue', CIAN, puntos=200, voltear=False, vel_anim=4,
          muerte=muerte_volador(murcielago(0))),
        e('Golem', '16x24', [golem(0), golem(1)], 'patrulla', BLANCO, energia=3, puntos=500, voltear=False, vel_anim=8,
          muerte=aplastar(golem(0), 10)),
        e('Sabio', '16x24', [sabio(0), sabio(1)], 'personaje', VERDE, puntos=0, voltear=False, vel_anim=20,
          mensaje='TRAEME EL AMULETO|DE LA TIERRA 1-2'),
    ]
SABIO = 5


# ---------------------------------------------------------------- fases
def fase(cols, n):
    """Mapa de 10 filas x cols columnas. Tramos al azar (con semilla fija por fase), cada vez más difíciles."""
    r = random.Random(1000 + n)
    m = [[VACIO] * cols for _ in range(FILAS)]
    apar = []

    def suelo(c0, c1):
        for c in range(c0, min(c1, cols)):
            m[8][c], m[9][c] = CESPED, TIERRA

    def enemigo(tipo, c, f=7):
        if 14 <= c < cols - 4: apar.append({'tipo': tipo, 'f': f, 'c': c})

    suelo(0, 14)
    c = 14
    dificultad = min(1.0, 0.25 + n * 0.1)
    while c < cols - 16:
        tramo = r.choices(['llano', 'ladrillos', 'hueco', 'escalinata', 'torres', 'pasarelas', 'pinchos'],
                          [3, 4, 2 + 2 * dificultad, 2, 2, 1 + dificultad, dificultad])[0]
        if tramo == 'llano':
            ancho = r.randint(5, 8); suelo(c, c + ancho)
            enemigo(r.choice((0, 0, 1)) if n else 0, c + ancho // 2)
            if r.random() < 0.5: m[5][c + 2] = GEMA
        elif tramo == 'ladrillos':
            ancho = r.randint(7, 10); suelo(c, c + ancho)
            fila = [LADRILLO] * r.randint(3, 5)
            for k in r.sample(range(len(fila)), r.randint(1, 2)): fila[k] = SORPRESA
            x0 = c + 2
            for k, t in enumerate(fila): m[5][x0 + k] = t
            if r.random() < 0.4 + 0.3 * dificultad:                   # segunda fila arriba
                for k in range(2, len(fila)): m[2][x0 + k] = LADRILLO if k % 2 else SORPRESA
                m[1][x0 + 3] = GEMA
            enemigo(r.choice((0, 1)), c + ancho - 2)
        elif tramo == 'hueco':
            suelo(c, c + 2); ancho = r.randint(2, 2 + int(dificultad * 1.5))
            if ancho >= 3: m[5][c + 2 + ancho // 2] = PASARELA         # ayuda en los huecos largos
            suelo(c + 2 + ancho, c + 5 + ancho)
            if r.random() < dificultad: enemigo(2, c + 2, 3)          # una abeja vigila el hueco
            ancho += 5
        elif tramo == 'escalinata':
            alto = r.randint(2, 3); ancho = 2 * alto + 4; suelo(c, c + ancho)
            for k in range(alto):
                for f in range(7 - k, 8): m[f][c + 1 + k] = ROCA
                for f in range(7 - k, 8): m[f][c + ancho - 2 - k] = ROCA
            m[7 - alto - 1][c + alto + 1] = GEMA
        elif tramo == 'torres':
            ancho = r.randint(9, 12); suelo(c, c + ancho)
            for x in (c + 2, c + ancho - 4):
                alto = r.randint(1, 2)          # con el capitel, como mucho 3 tiles (48 px)
                for f in range(8 - alto, 8): m[f][x], m[f][x + 1] = TORRE_I, TORRE_D
                m[7 - alto][x], m[7 - alto][x + 1] = CAPI_I, CAPI_D
            enemigo(r.choice((0, 1)), c + ancho // 2)
        elif tramo == 'pasarelas':
            ancho = r.randint(8, 10); suelo(c, c + 2); suelo(c + ancho - 2, c + ancho)
            for k in range(c + 2, c + ancho - 2): m[9][k] = VACIO
            for k in range(c + 2, c + ancho - 2, 3):
                m[5 if (k // 3) % 2 else 6][k] = PASARELA; m[5 if (k // 3) % 2 else 6][k + 1] = PASARELA
            m[3][c + ancho // 2] = GEMA
            enemigo(3, c + ancho // 2, 2)
        else:                                                         # pinchos en el suelo
            ancho = r.randint(6, 8); suelo(c, c + ancho)
            for k in range(c + 2, c + ancho - 2, 2): m[7][k] = PINCHOS
            m[4][c + ancho // 2] = PASARELA; m[4][c + ancho // 2 + 1] = PASARELA
            m[3][c + ancho // 2] = GEMA
        c += ancho
    suelo(c, cols)
    # estrategia: el amuleto (Tierra 1-2) se lleva al sabio (1-3), que da la llave de la puerta (1-4)
    # que lleva a la Tierra 2-2. Van al principio, en el tramo llano de la salida.
    if n == 1: m[5][9] = AMULETO
    if n == 2: apar.append({'tipo': SABIO, 'f': 6, 'c': 10})
    if n == 3:
        m[7][10] = PUERTA
    enemigo(4, cols - 14, 5)                                          # guardián antes de la meta
    for f in range(5, 8): m[f][cols - 8] = ROCA                       # meta: un muro que saltar al final
    apar.sort(key=lambda a: a['c'])
    return {'nombre': f'Tierra {n // 4 + 1}-{n % 4 + 1}', 'mapa': m, 'apariciones': apar}


# ---------------------------------------------------------------- pantallas
def _escena(d, w, h):
    d.rectangle((0, 0, w, h), fill=(0, 0, 0))
    r = random.Random(3)
    for _ in range(40): d.point((r.randrange(w), r.randrange(110)), fill=(255, 255, 255))
    for k, (x, y, rad) in enumerate(((40, 170, 50), (150, 180, 70), (240, 170, 40))):
        d.ellipse((x - rad, y - rad // 2, x + rad, y + rad), fill=(0, 205, 0) if k % 2 else (0, 150, 0))
    d.rectangle((0, 168, w, h), fill=(205, 0, 0))
    for x in range(0, w, 16): d.line((x, 168, x, h), fill=(110, 0, 0))
    d.polygon([(196, 168), (204, 110), (212, 168)], fill=(205, 205, 205))
    d.polygon([(204, 110), (226, 118), (204, 126)], fill=(0, 220, 0))


def proyecto(cols=150, nfases=8):
    p = juego.proyecto_nuevo()
    p['nombre'] = 'TERRA ZX'
    p['tiles'] = tiles()
    p['jugador'] = heroe()
    p['enemigos'] = enemigos()
    p['balas'] = {'jugador': {'nombre': 'Disparo', 'tamano': '8x8', 'fotogramas': [bala('punto')]},
                  'enemigo': {'nombre': 'Disparo enemigo', 'tamano': '8x8', 'fotogramas': [bala('punto')]}}
    p['scroll'].update(direccion='plataformas', modo='sigue', paso=2, umbral=96, retroceso=False, umbral_ret=16,
                       mezcla=True, color_sprites=True, compilar_sprites=True)
    p['scroll']['fisica'] = {'altura': 60, 'subida': 12, 'caida_max': 6}
    p['niveles'] = [fase(cols, n) for n in range(nfases)]
    p['estrategia'] = {
        'elementos': [{'nombre': 'Amuleto', 'simbolo': 'A'}, {'nombre': 'Llave', 'simbolo': 'L'}],
        'reglas': [{'cuando': 'personaje', 'personaje': SABIO, 'necesita': [AMULETO_E], 'modo': 'incluye',
                    'gasta': True, 'accion': 'guardar', 'valor': LLAVE_E, 'puntos': 200,
                    'mensaje': 'TOMA ESTA LLAVE|ABRE LA PUERTA'}],
        'falta': '',
        'hud': {'activo': True, 'fila': 23, 'col': 12, 'atr': atributo(MAGENTA, NEGRO, 1)}}
    p['textos'] = [
        {'fila': 2, 'col': 11, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'TERRA ZX'},
        {'fila': 5, 'col': 2, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Cruza las ocho tierras hasta'},
        {'fila': 6, 'col': 2, 'tinta': BLANCO, 'brillo': 0, 'texto': 'el final de cada una.'},
        {'fila': 8, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'Caeles encima a los bichos.'},
        {'fila': 9, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'Golpea con la cabeza los'},
        {'fila': 10, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'ladrillos y los bloques.'},
        {'fila': 12, 'col': 2, 'tinta': MAGENTA, 'brillo': 1, 'texto': 'Gemas y bloques dan puntos.'},
        {'fila': 13, 'col': 2, 'tinta': VERDE, 'brillo': 1, 'texto': 'Habla con el sabio y entra'},
        {'fila': 14, 'col': 2, 'tinta': VERDE, 'brillo': 1, 'texto': 'en la puerta con A (abajo).'},
        {'fila': 16, 'col': 2, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'O P andar Q saltar A agachar'},
        {'fila': 20, 'col': 8, 'tinta': VERDE, 'brillo': 1, 'texto': 'PULSA UNA TECLA'}]
    pa = p['partida']
    pa['vidas'], pa['energia'] = 3, 1
    pa['mensajes'].update(fase='TIERRA', game_over='FIN DEL VIAJE', final='LAS OCHO TIERRAS!', tinta=AMARILLO)
    for t in pa['menu']: t['tinta'] = BLANCO
    pa['controles']['tinta'] = BLANCO
    for clave, h in pa['marcador'].items(): h['tinta'] = AMARILLO
    pa['marcador']['energia']['activo'] = False
    p['pantalla_carga'] = pantalla('TERRA ZX', 'PLATAFORMAS EN MODO MEZCLA', _escena,
                                   [(0, 0, 0), (255, 255, 0), (255, 255, 255)], 'carga')
    p['pantalla_titulo'] = pantalla('TERRA ZX', 'PLATAFORMAS EN MODO MEZCLA', _escena,
                                    [(0, 0, 0), (255, 255, 0), (255, 255, 255)], 'titulo')
    return p


def maximo(nfases=8, lo=60, hi=400):
    """Mayor longitud de fase (columnas) con la que el juego cabe."""
    def cabe(c):
        p = proyecto(c, nfases)
        if juego.comprobar(p): return None
        try: return p, juego.generar_tap(p)
        except ValueError: return None
    mejor = cabe(lo)
    if not mejor: raise SystemExit(juego.comprobar(proyecto(lo, nfases))[:5])
    while hi - lo > 1:
        mid = (lo + hi) // 2
        r = cabe(mid)
        if r: lo, mejor = mid, r
        else: hi = mid
    return lo, mejor


if __name__ == '__main__':
    import os, json
    from crear_ejemplos_grandes import guardar_json, EJ, JU
    largo, (p, tap) = maximo(lo=LARGO - 10, hi=LARGO + 40)
    os.makedirs(EJ, exist_ok=True); os.makedirs(JU, exist_ok=True)
    guardar_json(p, os.path.join(EJ, 'terra_zx.json'))
    open(os.path.join(JU, 'terra_zx.tap'), 'wb').write(tap)
    print(f'TERRA ZX: 8 fases de {largo} columnas, {len(tap)} bytes')
