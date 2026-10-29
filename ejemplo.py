import copy
"""Contenido de ejemplo: tiles, mapa, jugador y tres enemigos (uno de cada tamaño)."""
import random
from graficos import atributo, contorno_auto

def _patron(f):
    return [''.join('X' if f(x, y) else '.' for x in range(16)) for y in range(16)]

def tiles_ejemplo():
    r = random.Random(7)
    puntos = {(r.randrange(16), r.randrange(16)) for _ in range(14)}
    piedras = {(r.randrange(16), r.randrange(16)) for _ in range(8)}
    t = []
    t.append({'pix': _patron(lambda x, y: (x, y) in puntos), 'atr': [atributo(0, 4)] * 4})            # 0 césped
    t.append({'pix': _patron(lambda x, y: (x, y) in piedras), 'atr': [atributo(2, 6)] * 4})           # 1 camino
    t.append({'pix': _patron(lambda x, y: (y % 8 in (2, 3)) and ((x + y // 8 * 4) % 8 < 4) ^ (y % 8 == 3)),
              'atr': [atributo(5, 1)] * 4})                                                           # 2 agua
    t.append({'pix': _patron(lambda x, y: (x - 7.5) ** 2 + (y - 7.5) ** 2 < 49 and
                             not ((x - 5) ** 2 + (y - 5) ** 2 < 6)), 'atr': [atributo(0, 4, 1)] * 4}) # 3 árbol
    t.append({'pix': _patron(lambda x, y: y % 4 == 3 or (x + (4 if (y // 4) % 2 else 0)) % 8 == 0),
              'atr': [atributo(0, 2)] * 4})                                                           # 4 muro
    t.append({'pix': _patron(lambda x, y: y % 4 == 0 or x in (0, 15)), 'atr': [atributo(0, 6)] * 4}) # 5 puente
    t.append({'pix': _patron(lambda x, y: (x * 7 + y * 3) % 11 == 0), 'atr': [atributo(0, 6, 1)] * 4})# 6 arena
    # propiedades: el agua no se puede cruzar pero deja pasar los disparos;
    # árboles y muros bloquean ambas cosas
    for i, tile in enumerate(t):
        tile['solido'] = i in (2, 3, 4)
        tile['detiene'] = i in (3, 4)
    return t

def mapa_ejemplo(filas=80, semilla=3, muros=0.0):
    r = random.Random(semilla)
    m = []
    for y in range(filas):
        fila = [0] * 12
        for x in range(12):
            if 4 <= x <= 7:
                fila[x] = 1
            elif r.random() < 0.15:
                fila[x] = 3
            elif r.random() < 0.05:
                fila[x] = 6
        if y % 30 in (10, 11):
            fila = [2] * 12
            fila[5] = fila[6] = 5
        if y % 30 == 20:
            for x in (0, 1, 2, 9, 10, 11):
                fila[x] = 4
        elif muros and 2 < y < filas - 10 and r.random() < muros:     # obstáculos sobre el camino
            x = r.choice((4, 7)); fila[x] = 4
        m.append(fila)
    return m

SOLDADO_A = """
.......XX.......
.......XX.......
.....XXXXXX.....
....XX.XX.XX....
...XXXXXXXXXX...
...XX.XXXX.XX...
..XXXXXXXXXXXX..
..XX.XXXXXX.XX..
..XX.XXXXXX.XX..
...X.XXXXXX.X...
.....XXXXXX.....
.....XX..XX.....
.....XX..XX.....
.....XX...XX....
....XXX...XXX...
................"""
SOLDADO_B = """
.......XX.......
.......XX.......
.....XXXXXX.....
....XX.XX.XX....
...XXXXXXXXXX...
...XX.XXXX.XX...
..XXXXXXXXXXXX..
..XX.XXXXXX.XX..
..XX.XXXXXX.XX..
...X.XXXXXX.X...
.....XXXXXX.....
.....XX..XX.....
.....XX..XX.....
....XX...XX.....
...XXX...XXX....
................"""

def _arte(s):
    return [f for f in s.strip('\n').split('\n')]

def _girar(pix):          # 90 grados en sentido horario
    h, w = len(pix), len(pix[0])
    return [''.join(pix[h - 1 - x][y] for x in range(h)) for y in range(w)]

def _espejo_h(pix):
    return [f[::-1] for f in pix]

def _espejo_v(pix):
    return pix[::-1]

def jugador_ejemplo():
    a, b = _arte(SOLDADO_A), _arte(SOLDADO_B)
    frames = [a, b, _espejo_v(a), _espejo_v(b), _girar(a), _girar(b), _espejo_h(_girar(a)), _espejo_h(_girar(b))]
    frames = [contorno_auto(f) for f in frames]
    return {'tamano': '16x16', 'velocidad': 2, 'x': 88, 'y': 128, 'cadencia': 6, 'vel_anim': 4,
            'quieto': {}, 'disparo': {},
            'fotogramas': frames,
            'anim': {'arriba': [0, 1], 'arriba-dcha': [], 'dcha': [4, 5], 'abajo-dcha': [],
                     'abajo': [2, 3], 'abajo-izq': [], 'izq': [6, 7], 'arriba-izq': []}}

def _figura(w, h, f):
    return contorno_auto([''.join('X' if f(x, y) else '.' for x in range(w)) for y in range(h)])

def enemigos_ejemplo():
    bicho = lambda fase: _figura(16, 16, lambda x, y: ((x - 7.5) ** 2 / 30 + (y - 7) ** 2 / 20 < 1 and
                                 not (y == 6 and x in (5, 6, 9, 10))) or (y >= 12 and (x + fase) % 4 == 0))
    robot = lambda fase: _figura(16, 24, lambda x, y: (3 <= x <= 12 and 1 <= y <= 9 and not (y == 4 and x in (5, 6, 9, 10)))
                                 or (2 <= x <= 13 and 11 <= y <= 17) or
                                 (18 <= y <= 22 and (x in ((4, 5) if fase else (5, 6)) or x in ((10, 11) if fase else (9, 10)))))
    tanque = lambda fase: _figura(24, 24, lambda x, y: (1 <= x <= 4 or 19 <= x <= 22) and 2 <= y <= 21 and (y + fase) % 3 != 0
                                  or (6 <= x <= 17 and 5 <= y <= 18 and not (9 <= x <= 14 and 8 <= y <= 15))
                                  or (11 <= x <= 12 and 0 <= y <= 9))
    base = {'direccion': 'abajo', 'vel_anim': 4, 'voltear': False}
    return [
        dict(base, nombre='Bicho', tamano='16x16', fotogramas=[bicho(0), bicho(1)],
             comportamiento='persigue', velocidad=1, energia=1, cadencia=0, puntos=50),
        dict(base, nombre='Robot', tamano='16x24', fotogramas=[robot(0), robot(1)],
             comportamiento='patrulla', velocidad=1, energia=2, cadencia=60, puntos=100),
        dict(base, nombre='Tanque', tamano='24x24', fotogramas=[tanque(0), tanque(1)],
             comportamiento='quieto', velocidad=1, energia=5, cadencia=40, puntos=250),
    ]

def apariciones_ejemplo(mapa=None, semilla=11, separacion=5):
    """Un enemigo cada pocas filas, en casillas libres, fuera de la pantalla inicial."""
    r = random.Random(semilla)
    mapa = mapa or mapa_ejemplo()
    tiles = tiles_ejemplo()
    res = []
    for f in range(len(mapa) - 16, 1, -separacion):
        tipo = r.choice((0, 0, 1, 2))
        for _ in range(20):
            c = r.randrange(11)
            if not any(tiles[mapa[ff][cc]]['solido'] for ff in (f, min(f + 1, len(mapa) - 1)) for cc in (c, c + 1)):
                res.append({'tipo': tipo, 'f': f, 'c': c}); break
    return res

def niveles_ejemplo():
    m1 = mapa_ejemplo(80, 3)
    m2 = mapa_ejemplo(100, 5, muros=0.12)
    return [{'nombre': 'Fase 1', 'mapa': m1, 'apariciones': apariciones_ejemplo(m1, 11, 5)},
            {'nombre': 'Fase 2', 'mapa': m2, 'apariciones': apariciones_ejemplo(m2, 13, 3)}]

def balas_ejemplo():
    jugador = ['........', '........', '...XX...', '..XXXX..', '..XXXX..', '...XX...', '........', '........']
    enemigo = ['........', '...XX...', '..X..X..', '.X....X.', '.X....X.', '..X..X..', '...XX...', '........']
    return {'jugador': {'nombre': 'Disparo del jugador', 'tamano': '8x8', 'fotogramas': [contorno_auto(jugador)]},
            'enemigo': {'nombre': 'Disparo enemigo', 'tamano': '8x8', 'fotogramas': [contorno_auto(enemigo)]}}

# ---------------- ejemplo de plataformas ----------------
PERSONAJE_LADO = ["""
......XXXX......
.....XXXXXX.....
.....XX.X.X.....
.....XXXXXX.....
......XXXX......
.......XX.......
.....XXXXXX.....
....XX.XX.XX....
....XX.XX.XX....
.......XX.......
......XXXX......
......X..X......
......X..X......
......X..X......
.....XX..XX.....
................""", """
......XXXX......
.....XXXXXX.....
.....XX.X.X.....
.....XXXXXX.....
......XXXX......
.......XX.......
.....XXXXXX.....
....XX.XX.XX....
...XX..XX..XX...
.......XX.......
......XXXX......
.....XX..XX.....
....XX....XX....
...XX......X....
...X.......XX...
................""", """
......XXXX......
.....XXXXXX.....
.....XX.X.X.....
.....XXXXXX.....
......XXXX......
.......XX.......
.....XXXXXX.....
....XX.XX.XX....
....XX.XX.XX....
.......XX.......
......XXXX......
.......XX.......
......XXX.......
.......XX.......
......XXX.......
................""", """
......XXXX......
.....XXXXXX.....
.....XX.X.X.....
.....XXXXXX.....
..XX..XXXX..XX..
...XX..XX..XX...
....XXXXXXXX....
.......XX.......
.......XX.......
.......XX.......
......XXXX......
.....XX..XX.....
....XX....XX....
................
................
................"""]

def tiles_plataformas():
    r = random.Random(5)
    estrellas = {(r.randrange(16), r.randrange(16)) for _ in range(3)}
    t = []
    t.append({'pix': _patron(lambda x, y: (x, y) in estrellas), 'atr': [atributo(7, 0)] * 4})            # 0 cielo
    t.append({'pix': _patron(lambda x, y: y % 4 == 3 or (x + (4 if (y // 4) % 2 else 0)) % 8 == 0),
              'atr': [atributo(0, 2)] * 4})                                                               # 1 tierra
    t.append({'pix': _patron(lambda x, y: y < 3 or (y < 6 and (x * 3 + y) % 5 == 0)),
              'atr': [atributo(4, 2, 1)] * 2 + [atributo(0, 2)] * 2})                                     # 2 hierba
    t.append({'pix': _patron(lambda x, y: y < 4 and not (y == 3 and x % 4 == 0)),
              'atr': [atributo(6, 0, 1)] * 2 + [atributo(0, 0)] * 2})                                     # 3 plataforma
    t.append({'pix': _patron(lambda x, y: y >= 8 and abs((x % 8) - 3.5) <= (y - 8) / 2),
              'atr': [atributo(7, 0)] * 2 + [atributo(7, 0, 1)] * 2})                                     # 4 pinchos
    t.append({'pix': _patron(lambda x, y: x in (0, 15) or y in (0, 15) or (x == y) or (x == 15 - y)),
              'atr': [atributo(0, 7)] * 4})                                                               # 5 bloque
    for i, tile in enumerate(t):
        tile['solido'] = i in (1, 2, 5)
        tile['detiene'] = i in (1, 2, 5)
        tile['plataforma'] = i == 3
        tile['mortal'] = i == 4
    return t

def mapa_plataformas(columnas=140, semilla=8):
    """10 filas x N columnas: suelo con huecos, pinchos, bloques y plataformas."""
    r = random.Random(semilla)
    m = [[0] * columnas for _ in range(10)]
    c = 0
    while c < columnas:
        seguro = c < 14 or c > columnas - 14
        hueco = not seguro and r.random() < 0.3
        ancho = r.randint(2, 3) if hueco else r.randint(3, 7)
        for k in range(c, min(columnas, c + ancho)):
            if not hueco:
                m[8][k], m[9][k] = 2, 1
        if hueco:                                   # plataforma para cruzar el hueco (32 px sobre el suelo)
            for k in range(c - 1, min(columnas, c + ancho + 1)):
                m[6][k] = 3
        elif not seguro and r.random() < 0.25:      # pinchos o un bloque
            k = c + ancho // 2
            if r.random() < 0.5: m[7][k] = 4
            else: m[7][k] = m[6][k] = 5
        elif not seguro and r.random() < 0.3:       # plataforma (y otra más alta encima, a veces)
            for k in range(c, min(columnas, c + 3)):
                m[6][k] = 3
                if r.random() < 0.5 and k < columnas - 1: m[4][k + 1] = 3
        c += ancho
    return m

def convertir_a_plataformas(p):
    """Convierte un proyecto nuevo en el ejemplo de plataformas."""
    p['scroll'].update(direccion='plataformas', modo='sigue', retroceso=False, umbral=80, umbral_ret=16)
    p['tiles'] = tiles_plataformas()
    f = [contorno_auto(_arte(a)) for a in PERSONAJE_LADO]
    f += [[fila[::-1] for fila in x] for x in f]
    j = p['jugador']
    j.update(tamano='16x16', fotogramas=f, x=16, y=80, velocidad=2, vel_anim=4,
             anim={'dcha': [1, 0, 2, 0], 'izq': [5, 4, 6, 4], 'arriba-dcha': [3], 'arriba-izq': [7],
                   'arriba': [], 'abajo': [], 'abajo-dcha': [], 'abajo-izq': []},
             quieto={'dcha': 0, 'izq': 4}, disparo={})
    en = p['enemigos']
    en[0].update(comportamiento='rebota', direccion='abajo-dcha', velocidad=1, energia=1, cadencia=0, puntos=50)
    en[1].update(comportamiento='patrulla', velocidad=1, energia=2, cadencia=0, puntos=100, voltear=True)
    en[2].update(comportamiento='quieto', energia=4, cadencia=50, puntos=250)
    p['niveles'] = []
    for n, (largo, semilla) in enumerate(((140, 8), (180, 21))):
        m = mapa_plataformas(largo, semilla)
        r = random.Random(semilla)
        ap = []
        for c in range(16, largo - 14, 9):
            if m[8][c] == 2 and m[8][c + 1] == 2 and m[7][c] == 0 and m[7][c + 1] == 0:
                tipo = r.choice((1, 1, 2, 0))
                ap.append({'tipo': tipo, 'f': 2 if tipo == 0 else 6, 'c': c})
        p['niveles'].append({'nombre': f'Fase {n + 1}', 'mapa': m, 'apariciones': ap})
    p['textos'][1]['texto'] = 'O P andar  Q saltar'
    p['textos'][3]['texto'] = 'Cuidado con los huecos'
    return p

# ---------------- ejemplos en monocromo ----------------
def monocromo(tiles, tinta, brillo=1):
    """Todos los tiles con la misma tinta sobre negro: los sprites, que toman el color
    del fondo, se ven siempre igual y no hay choque de color."""
    for t in tiles:
        t['atr'] = [atributo(tinta, 0, brillo)] * 4
    return tiles

NAVE = """
................
....XXX.........
....XXXXX.......
.....XXXXXX.....
..XXXXXXXXXXXX..
.XXXXXX..XXXXXX.
XXXXXXX..XXXXXXX
.XXXXXX..XXXXXX.
..XXXXXXXXXXXX..
.....XXXXXX.....
....XXXXX.......
....XXX.........
................
................
................
................"""

def proyecto_naves(p):
    """«ESTRELLA ZX»: naves con scroll horizontal automático de 2 píxeles, en cian."""
    r = random.Random(4)
    estrellas = {(r.randrange(16), r.randrange(16)) for _ in range(2)}
    tiles = [
        {'pix': _patron(lambda x, y: False)},                                                  # 0 espacio vacío
        {'pix': _patron(lambda x, y: (x * 5 + y * 3) % 7 < 3 or y in (0, 15))},               # 1 roca
        {'pix': _patron(lambda x, y: y >= 6 and (x * 5 + y * 3) % 7 < 3 or y == 6)},          # 2 roca (borde de arriba)
        {'pix': _patron(lambda x, y: y <= 9 and (x * 5 + y * 3) % 7 < 3 or y == 9)},          # 3 roca (borde de abajo)
        {'pix': _patron(lambda x, y: x in (0, 15) or y in (0, 15) or (x % 5 == 2 and y % 5 == 2))},  # 4 bloque
        {'pix': _patron(lambda x, y: (x + y) % 4 == 0 and 3 <= x <= 12)},                     # 5 campo de fuerza
        {'pix': _patron(lambda x, y: (x, y) in estrellas)},                                   # 6 estrellas sueltas
    ]
    for i, t in enumerate(tiles):
        t.update(solido=i in (1, 2, 3, 4), detiene=i in (1, 2, 3, 4), plataforma=False, mortal=i == 5)
    p['tiles'] = monocromo(tiles, 5)
    p['scroll'].update(direccion='horizontal', modo='auto', vel_auto=1, paso=2, retroceso=False)
    nave = contorno_auto(_arte(NAVE))
    llama = [f[:0] + ('X' if 4 <= y <= 8 and f[0] == '.' and y % 2 == 0 else f[0]) + f[1:] for y, f in enumerate(_arte(NAVE))]
    j = p['jugador']
    j.update(tamano='16x16', fotogramas=[nave, contorno_auto(llama)], x=24, y=72, velocidad=2, vel_anim=3,
             anim={d: [0, 1] for d in ('arriba', 'abajo', 'dcha', 'izq')} | {'arriba-dcha': [], 'abajo-dcha': [],
                                                                            'abajo-izq': [], 'arriba-izq': []},
             quieto={}, disparo={}, disparo_fijo='dcha', cadencia=5)
    platillo = lambda f: _figura(16, 16, lambda x, y: (y in (6, 7, 8) and 1 <= x <= 14) or
                                 ((x - 7.5) ** 2 + (y - 5) ** 2 < 10 and y < 7) or (y == 9 and (x + f) % 4 == 0))
    roca = lambda f: _figura(16, 16, lambda x, y: (x - 7.5) ** 2 + (y - 7.5) ** 2 < 42 and
                             not ((x - 5 - f) ** 2 + (y - 5) ** 2 < 4))
    torreta = lambda f: _figura(16, 16, lambda x, y: (y >= 10 and 2 <= x <= 13) or
                                ((x - 7.5) ** 2 + (y - 9) ** 2 < 20 and y < 10) or (y < 6 and x in ((6, 7) if f else (8, 9))))
    p['enemigos'] = [
        {'nombre': 'Platillo', 'tamano': '16x16', 'fotogramas': [platillo(0), platillo(2)], 'comportamiento': 'rebota',
         'direccion': 'abajo-izq', 'velocidad': 1, 'energia': 1, 'cadencia': 0, 'puntos': 50, 'vel_anim': 4, 'voltear': False},
        {'nombre': 'Asteroide', 'tamano': '16x16', 'fotogramas': [roca(0), roca(2)], 'comportamiento': 'cruza',
         'direccion': 'izq', 'velocidad': 2, 'energia': 3, 'cadencia': 0, 'puntos': 100, 'vel_anim': 8, 'voltear': False},
        {'nombre': 'Torreta', 'tamano': '16x16', 'fotogramas': [torreta(0), torreta(1)], 'comportamiento': 'quieto',
         'direccion': 'abajo', 'velocidad': 1, 'energia': 2, 'cadencia': 35, 'puntos': 150, 'vel_anim': 12, 'voltear': False},
    ]
    p['niveles'] = []
    for n, (largo, sem) in enumerate(((150, 31), (190, 47))):
        r = random.Random(sem)
        m = [[0] * largo for _ in range(10)]
        for c in range(largo):
            m[0][c], m[9][c] = 1, 1                                     # techo y suelo de roca
            if r.random() < 0.08: m[r.randint(2, 7)][c] = 6             # alguna estrella
            if c > 14 and r.random() < 0.25: m[1][c] = 2               # estalactitas
            if c > 14 and r.random() < 0.25: m[8][c] = 3               # estalagmitas
        ap = []
        for c in range(16, largo - 12, 4):
            k = r.random() * 2                                          # obstáculos en la mitad de los casos
            if k < 0.15:                                                # un bloque en medio
                f = r.randint(3, 6); m[f][c] = 4
            elif k < 0.22:                                              # campo de fuerza
                for f in range(3, 7): m[f][c] = 5
            tipo = r.choice((0, 0, 1, 1, 2))
            if tipo == 2:
                f = 7 if m[8][c] == 0 else 1
                if m[f][c] == 0: ap.append({'tipo': 2, 'f': f, 'c': c})
            else:
                ap.append({'tipo': tipo, 'f': r.randint(2, 7), 'c': c})
        p['niveles'].append({'nombre': f'Sector {n + 1}', 'mapa': m, 'apariciones': ap})
    p['textos'] = [
        {'fila': 4, 'col': 6, 'tinta': 5, 'brillo': 1, 'texto': 'ESTRELLA ZX'},
        {'fila': 8, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'Q A O P  mover la nave'},
        {'fila': 10, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'ESPACIO  disparar'},
        {'fila': 12, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'Evita las rocas y los'},
        {'fila': 13, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'campos de fuerza'},
        {'fila': 20, 'col': 8, 'tinta': 5, 'brillo': 0, 'texto': 'PULSA UNA TECLA'}]
    p['partida']['mensajes'].update(fase='SECTOR', final='MISION CUMPLIDA', tinta=5)
    for t in p['partida']['menu']: t['tinta'] = 5
    p['partida']['controles']['tinta'] = 5
    for clave, h in p['partida']['marcador'].items():
        h['tinta'] = 5
    return p

def proyecto_saltos(p):
    """«SALTAMONTES ZX»: plataformas con scroll de 2 píxeles, en verde."""
    convertir_a_plataformas(p)
    p['tiles'][0]['pix'] = ['.' * 16] * 16           # cielo vacío: no se dibuja (como el Mario de Smirnov)
    # objetos y ladrillos (antes de pasar a monocromo, para que tomen el verde)
    moneda = {'pix': _patron(lambda x, y: 4 <= x <= 11 and 3 <= y <= 12 and (x - 7.5) ** 2 / 16 + (y - 7.5) ** 2 / 25 <= 1
                             and not (6 <= x <= 9 and 6 <= y <= 9 and (x - 7.5) ** 2 + (y - 7.5) ** 2 < 3)),
              'atr': [0x44] * 4, 'objeto': True, 'accion': 'puntos', 'puntos': 50, 'tras': 0}
    ladrillo = dict(copy.deepcopy(p['tiles'][1]), rompible=True, solido=True, tras=0, puntos=10)
    corazon = {'pix': _patron(lambda x, y: (y >= 4 and abs(x - 7.5) <= (13 - y) * 0.9 and y <= 13) or
                              (3 <= y <= 6 and ((x - 4.5) ** 2 + (y - 5) ** 2 <= 5 or (x - 10.5) ** 2 + (y - 5) ** 2 <= 5))),
               'atr': [0x44] * 4, 'objeto': True, 'accion': 'vida', 'puntos': 100, 'tras': 0}
    p['tiles'] += [moneda, ladrillo, corazon]
    MON, LAD, COR = len(p['tiles']) - 3, len(p['tiles']) - 2, len(p['tiles']) - 1
    for n, nv in enumerate(p['niveles']):
        m = nv['mapa']; largo = len(m[0]); puesto_corazon = False
        for c in range(12, largo - 12):
            for f in range(1, 9):
                if m[f][c] == 3 and m[f - 1][c] == 0 and c % 3 == 0:              # moneda sobre plataforma
                    if not puesto_corazon and c > 40:
                        m[f - 1][c] = COR; puesto_corazon = True
                    else:
                        m[f - 1][c] = MON
        for c in range(20, largo - 16, 23):                                     # ladrillos a la altura del cabezazo
            if all(m[8][k] == 2 and all(m[f][k] == 0 for f in range(3, 8)) for k in (c, c + 1)):
                m[4][c] = m[4][c + 1] = LAD
    p['jugador']['pisar'] = True
    p['tiles'] = monocromo(p['tiles'], 4)
    p['scroll']['paso'] = 2
    p['textos'][0].update(texto='SALTAMONTES ZX', col=8, tinta=4)
    p['partida']['mensajes'].update(final='HAS LLEGADO!', tinta=4)
    for t in p['partida']['menu']: t['tinta'] = 4
    p['partida']['controles']['tinta'] = 4
    for clave, h in p['partida']['marcador'].items():
        h['tinta'] = 4
    return p

# ---------------- ejemplo del modo mezcla (estilo Super Mario Bros de 128K) ----------------
def _rellenar_mezcla(pix, cond=lambda x, y: True):
    """Convierte en 'm' (tono intermedio) los píxeles de papel que cumplen cond."""
    return [''.join('m' if c == '.' and cond(x, y) else c for x, c in enumerate(f)) for y, f in enumerate(pix)]

def proyecto_mezcla(p):
    """«MEZCLA ZX»: plataformas con cielo negro, tiles con tonos intermedios (dos pantallas alternadas
    a 50 Hz) y personajes que pintan su propio color, como el Super Mario Bros de 128K."""
    proyecto_saltos(p)
    t = p['tiles']
    t[0]['pix'] = ['.' * 16] * 16; t[0]['atr'] = [atributo(7, 0, 1)] * 4                 # cielo vacío
    t[1]['pix'] = ['.' * 16] * 16; t[1]['atr'] = [atributo(2, 2, 0)] * 4                 # tierra: solo color (gratis)
    t[2]['pix'] = _rellenar_mezcla(t[2]['pix'], lambda x, y: y >= 4)                        # hierba sobre tierra
    t[2]['atr'] = [atributo(4, 0, 1)] * 2 + [atributo(2, 0, 1)] * 2
    t[3]['pix'] = _rellenar_mezcla(t[3]['pix'], lambda x, y: y < 4); t[3]['atr'] = [atributo(6, 0, 1)] * 4
    t[4]['atr'] = [atributo(7, 0, 1)] * 4                                                  # pinchos
    t[5]['pix'] = _rellenar_mezcla(t[5]['pix'], lambda x, y: 0 < x < 15 and 0 < y < 15)
    t[5]['atr'] = [atributo(6, 2, 1)] * 4                                                  # bloque: naranja
    mon, lad, cor = len(t) - 3, len(t) - 2, len(t) - 1
    t[mon]['pix'] = _rellenar_mezcla(t[mon]['pix'], lambda x, y: x < 8 and 3 <= y <= 12 and 4 <= x)
    t[mon]['atr'] = [atributo(6, 0, 1)] * 4
    t[lad]['pix'] = _rellenar_mezcla(t[lad]['pix']); t[lad]['atr'] = [atributo(6, 2, 1)] * 4
    t[cor]['atr'] = [atributo(2, 0, 1)] * 4
    sc = p['scroll']
    sc.update(paso=2, mezcla=True, color_sprites=True, compilar_sprites=True)
    p['jugador']['color'] = atributo(7, 0, 1)
    for en, c in zip(p['enemigos'], (5, 3, 6)):
        en['color'] = atributo(c, 0, 1)
    p['textos'][0].update(texto='MEZCLA ZX', col=11, tinta=6)
    p['partida']['mensajes'].update(final='HAS LLEGADO!', tinta=6)
    for txt in p['partida']['menu']: txt['tinta'] = 7
    p['partida']['controles']['tinta'] = 7
    for clave, h in p['partida']['marcador'].items(): h['tinta'] = 6
    return p
