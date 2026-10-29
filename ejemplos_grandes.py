"""Cinco juegos de ejemplo, uno por tipo de scroll y género, con 16 fases cada uno.
La longitud de las fases se busca para llenar la memoria (ver maximizar)."""
import random
import juego
import graficos
from graficos import atributo
from arte import (tile, patron, humano, humano_cenital, criatura, nave, bala, espejo, girar,
                  melodia, componer, pantalla, Lienzo)
from graficos import contorno_auto

NEGRO, AZUL, ROJO, MAGENTA, VERDE, CIAN, AMARILLO, BLANCO = range(8)


# ---------------- comunes ----------------
def base(nombre, titulo, lineas):
    p = juego.proyecto_nuevo()
    p['nombre'] = nombre[:10]
    p['textos'] = [{'fila': 3, 'col': max(0, (32 - len(titulo)) // 2), 'tinta': AMARILLO, 'brillo': 1, 'texto': titulo}]
    for k, (texto, tinta) in enumerate(lineas):
        p['textos'].append({'fila': 6 + k * 2, 'col': 1, 'tinta': tinta, 'brillo': 1 if tinta != BLANCO else 0,
                            'texto': texto[:30]})
    return p


def enemigo(nombre, tam, frames, comp, vel=1, energia=1, cadencia=0, puntos=50, direccion='abajo',
            voltear=False, vel_anim=4):
    puntos = max(0, min(990, round(puntos / 10) * 10))
    return {'nombre': nombre, 'tamano': tam, 'fotogramas': frames, 'comportamiento': comp, 'velocidad': vel,
            'energia': energia, 'cadencia': cadencia, 'puntos': puntos, 'direccion': direccion,
            'voltear': voltear, 'vel_anim': vel_anim}


def anim_lateral(nd, ni, quieto=None, disparo=None):
    """Animaciones de un personaje de perfil: nd fotogramas a la derecha y ni a la izquierda."""
    a = {k: [] for k in ('arriba', 'arriba-dcha', 'dcha', 'abajo-dcha', 'abajo', 'abajo-izq', 'izq', 'arriba-izq')}
    a['dcha'] = nd; a['izq'] = ni
    a['arriba-dcha'] = a['abajo-dcha'] = nd; a['arriba-izq'] = a['abajo-izq'] = ni
    a['arriba'] = nd; a['abajo'] = nd
    return a


def musica(p, pt3):
    p['partida']['musica'].update(menu=pt3, juego=pt3)


def marcador(p, energia_tinta=VERDE):
    m = p['partida']['marcador']
    m['energia']['tinta'] = energia_tinta


# =====================================================================
#  NEBULOSA: shoot'em up horizontal, scroll fino por bloques, monocromo
# =====================================================================
def tiles_nebulosa():
    r = random.Random(4)
    est = {(r.randrange(16), r.randrange(16)) for _ in range(3)}
    roca = lambda s: (lambda x, y: (x - 7.5) ** 2 + (y - 7.5) ** 2 < 52 + random.Random(s * 97 + x * 16 + y).random() * 14
                      and (x * 3 + y * 5 + s) % 7 != 0)
    T = [
        patron(lambda x, y: False),                                                   # 0 vacío
        patron(lambda x, y: (x, y) in est),                                           # 1 estrellas
        patron(roca(1)),                                                              # 2 asteroide
        patron(lambda x, y: y in (0, 15) or x in (0, 15) or (x + y) % 6 == 0),        # 3 pared metálica
        patron(lambda x, y: 4 <= y <= 11 and (y in (4, 11) or x % 4 == 0)),           # 4 tubería
        patron(lambda x, y: (x * 7 + y * 3) % 5 == 0 and 2 <= x <= 13),               # 5 campo de fuerza
        patron(lambda x, y: (y % 8 in (0, 1)) or (x % 8 == 0) or (x % 8 == 4 and y % 8 == 4)),  # 6 casco de nave
        patron(roca(5)),                                                              # 7 asteroide grande
        patron(lambda x, y: y >= 10 and (x + y) % 3 != 0),                            # 8 suelo rocoso
        patron(lambda x, y: y <= 5 and (x + y) % 3 != 0),                             # 9 techo rocoso
    ]
    props = [{}, {}, {'solido': True, 'detiene': True, 'rompible': True, 'tras': 0, 'puntos': 20},
             {'solido': True, 'detiene': True}, {'solido': True, 'detiene': True},
             {'mortal': True}, {'solido': True, 'detiene': True},
             {'solido': True, 'detiene': True, 'rompible': True, 'tras': 1, 'puntos': 30},
             {'solido': True, 'detiene': True}, {'solido': True, 'detiene': True}]
    return [tile(pix, CIAN, NEGRO, 1, **pr) for pix, pr in zip(T, props)]


def mapa_nebulosa(cols, n):
    r = random.Random(100 + n)
    m = [[0] * cols for _ in range(10)]
    techo, suelo = 1, 1
    for c in range(cols):
        if c % 6 == 0:
            techo = max(0, min(3, techo + r.choice((-1, 0, 1))))
            suelo = max(0, min(3, suelo + r.choice((-1, 0, 1))))
        estrecho = 12 < c < cols - 12 and (c // 30) % 3 == 2           # zonas de nave nodriza
        for f in range(10):
            if f < techo: m[f][c] = 6 if estrecho else 3
            elif f == techo and techo: m[f][c] = 9
            elif f >= 10 - suelo: m[f][c] = 6 if estrecho else 3
            elif f == 9 - suelo and suelo: m[f][c] = 8
            elif r.random() < 0.04: m[f][c] = 1
        if 16 < c < cols - 14 and (c // 20) % 2 == 1 and r.random() < 0.35 + n * 0.02:   # campos de asteroides
            f = r.randint(techo + 1, 8 - suelo)
            m[f][c] = r.choice((2, 2, 7))
        if 16 < c < cols - 14 and c % 45 == 40 and n >= 2:                              # barreras de fuerza
            for f in range(techo + 1, 9 - suelo): m[f][c] = 5 if f % 3 else 0
        if c % 50 == 25 and 2 + techo < 8 - suelo:                                      # tuberías
            m[(techo + 9 - suelo) // 2][c] = 4
    for c in range(14):                                                                 # salida despejada
        for f in range(2, 8): m[f][c] = 0 if m[f][c] in (2, 7, 5, 4) else m[f][c]
    return m


def nebulosa(largo):
    p = base('NEBULOSA', 'NEBULOSA X', [
        ('La flota de la nebulosa avanza.', BLANCO), ('Destruye asteroides y naves.', BLANCO),
        ('No toques los campos de fuerza.', BLANCO), ('Q A O P mueve  ESPACIO dispara', CIAN),
        ('16 sectores hasta el núcleo.', AMARILLO)])
    p['tiles'] = tiles_nebulosa()
    p['scroll'].update(direccion='horizontal', modo='auto', vel_auto=1, paso=2, retroceso=False,
                       compilar_sprites=True)
    sh = [girar(nave(variante=1, fase=k)) for k in range(2)]
    p['jugador'] = {'tamano': '16x16', 'velocidad': 2, 'x': 16, 'y': 72, 'cadencia': 5, 'vel_anim': 3,
                    'quieto': {}, 'disparo': {}, 'disparo_fijo': 'dcha', 'fotogramas': sh,
                    'anim': anim_lateral([0, 1], [0, 1]), 'arma': 'disparo'}
    nombres = ['Sonda', 'Medusa', 'Cangrejo', 'Ojo', 'Avispa', 'Calamar', 'Escarabajo', 'Torreta',
               'Mina', 'Nodriza', 'Espora', 'Centinela']
    comps = ['cruza', 'rebota', 'patrulla', 'persigue', 'cruza', 'rebota', 'patrulla', 'quieto',
             'quieto', 'rebota', 'persigue', 'quieto']
    p['enemigos'] = []
    for k, nom in enumerate(nombres):
        tam = '24x24' if nom in ('Nodriza', 'Centinela') else '16x16'
        w, h = graficos.TAMANOS[tam]
        frames = [girar(girar(girar(criatura(w, h, 30 + k, fase=f)))) for f in range(2)]
        p['enemigos'].append(enemigo(nom, tam, frames, comps[k], vel=1 + (k % 3 == 0), energia=1 + (tam == '24x24') * 3,
                                     cadencia=60 if comps[k] == 'quieto' or tam == '24x24' else 0,
                                     puntos=50 + k * 25, direccion='izq'))
    p['balas'] = {'jugador': {'nombre': 'Láser', 'tamano': '8x8', 'fotogramas': [bala('rayo_h')]},
                  'enemigo': {'nombre': 'Plasma', 'tamano': '8x8', 'fotogramas': [bala('estrella')]}}
    p['niveles'] = []
    for n in range(16):
        m = mapa_nebulosa(largo, n)
        r = random.Random(200 + n)
        apar = []
        for c in range(20, largo - 8, max(3, 7 - n // 4)):
            libres = [f for f in range(1, 9) if m[f][c] == 0 and m[f][c + 1] == 0]
            if not libres: continue
            tipo = r.choice(range(min(len(nombres), 4 + n)))
            apar.append({'tipo': tipo, 'f': r.choice(libres), 'c': c})
        p['niveles'].append({'nombre': f'Sector {n + 1}', 'mapa': m, 'apariciones': apar})
    p['partida']['mensajes'].update(fase='SECTOR', final='NUCLEO DESTRUIDO')
    marcador(p, CIAN)
    return p


# =====================================================================
#  TEMPLO: plataformas por bloques, golpe, pisar, rompibles y estrategia
# =====================================================================
def tiles_templo():
    ladr = lambda x, y: not (y % 8 == 0 or (x + (8 if y // 8 % 2 else 0)) % 16 == 0)
    piedra = lambda x, y: not (y in (0, 15) or x in (0, 15)) and (x * 5 + y * 3) % 11 != 0
    T = [
        (patron(lambda x, y: False), BLANCO, {}),                                                  # 0 vacío
        (patron(piedra), AMARILLO, {'solido': True, 'detiene': True}),                             # 1 piedra
        (patron(ladr), ROJO, {'solido': True, 'detiene': True, 'rompible': True, 'tras': 0, 'puntos': 10}),  # 2 ladrillo
        (patron(lambda x, y: y < 6 and (x + y) % 4 != 0), AMARILLO, {'solido': True, 'fragil': True, 'tras': 0}),  # 3 frágil
        (patron(lambda x, y: y < 4 and x % 8 != 7), BLANCO, {'plataforma': True}),                 # 4 plataforma
        (patron(lambda x, y: y > 8 and abs((x % 4) - 1.5) < (y - 8) / 4), BLANCO, {'mortal': True}),  # 5 pinchos
        (patron(lambda x, y: y > 4 and ((x + y // 2) % 5 < 3 or y > 10)), ROJO, {'mortal': True}),  # 6 lava
        (patron(lambda x, y: (6 <= x <= 9 and y > 6) or ((x - 7.5) ** 2 + (y - 4) ** 2 < 6 and y < 6)), AMARILLO, {}),  # 7 antorcha
        (patron(lambda x, y: 3 <= x <= 12 and x % 3 != 0), BLANCO, {}),                            # 8 columna
        (patron(lambda x, y: abs(x - 7.5) + abs(y - 7.5) < 6), CIAN, {'objeto': True, 'accion': 'puntos', 'puntos': 50}),  # 9 gema
        (patron(lambda x, y: ((x - 4) ** 2 + (y - 7) ** 2 < 10 and (x - 4) ** 2 + (y - 7) ** 2 > 2) or (6 <= x <= 13 and y == 7) or (x in (10, 12) and 7 <= y <= 10)),
         AMARILLO, {'objeto': True, 'accion': 'guardar', 'valor': 0, 'puntos': 100}),             # 10 llave
        (patron(lambda x, y: ((x - 7.5) ** 2 + (y - 9) ** 2 < 14) or (7 <= x <= 8 and 2 <= y <= 6)),
         MAGENTA, {'objeto': True, 'accion': 'guardar', 'valor': 1, 'puntos': 100}),              # 11 amuleto
        (patron(lambda x, y: ((x - 7.5) ** 2 + (y - 6) ** 2 < 20 and not ((x in (5, 6, 9, 10)) and 5 <= y <= 7)) or (5 <= x <= 10 and 10 <= y <= 12 and x % 2)),
         BLANCO, {'objeto': True, 'accion': 'guardar', 'valor': 2, 'puntos': 100}),               # 12 calavera
        (patron(lambda x, y: (y >= 8 and 1 <= x <= 14) or (y == 7 and 3 <= x <= 12) or (y < 7 and x in (7, 8) and y > 2)),
         MAGENTA, {'objeto': True, 'accion': 'altar', 'tras': 13}),                               # 13 altar
        (patron(lambda x, y: (abs(x - 7.5) + (y - 4) * 0.9 < 7 and y > 3) or ((x - 5) ** 2 + (y - 5) ** 2 < 7) or ((x - 10) ** 2 + (y - 5) ** 2 < 7)),
         ROJO, {'objeto': True, 'accion': 'vida', 'puntos': 50}),                                 # 14 corazón
        (patron(lambda x, y: (5 <= x <= 10 and y >= 6) or (7 <= x <= 8 and 2 <= y < 6)), VERDE,
         {'objeto': True, 'accion': 'energia', 'puntos': 20}),                                     # 15 poción
    ]
    return [tile(pix, tinta, NEGRO, 1, **pr) for pix, tinta, pr in T]


def mapa_templo(cols, n):
    r = random.Random(300 + n)
    m = [[0] * cols for _ in range(10)]
    for c in range(cols):
        m[9][c] = 1; m[0][c] = 1 if c % 9 else 8
    c = 12
    while c < cols - 14:
        tramo = r.choice(('hueco', 'plataformas', 'ladrillos', 'pinchos', 'fragil', 'lava', 'escalera'))
        if tramo == 'hueco':
            for k in range(3): m[9][c + k] = 0
            m[6][c + 1] = 4
        elif tramo == 'plataformas':
            for k in range(5): m[6 - (k % 2)][c + k] = 4
            m[4][c + 2] = 9
        elif tramo == 'ladrillos':
            for k in range(4): m[5][c + k] = 2
            m[4][c + 1] = 9
        elif tramo == 'pinchos':
            m[8][c + 1] = 5; m[8][c + 2] = 5; m[6][c + 1] = 4; m[6][c + 2] = 4
        elif tramo == 'fragil':
            for k in range(4): m[9][c + k] = 3
        elif tramo == 'lava':
            for k in range(3): m[9][c + k] = 6
            for k in range(3): m[6][c + k] = 4 if k != 1 else 3
        else:
            for k in range(4):
                for f in range(9 - k, 9): m[f][c + k] = 1
            m[4][c + 3] = 9
        if r.random() < 0.3: m[1][c] = 7
        c += 6 + r.randint(0, 3)
    # objetos de la estrategia: llave en la fase 3, calavera en la 5 y la 11, amuleto en la 7,
    # altares al final de las fases 8 y 16; vidas y pociones de vez en cuando
    especiales = {2: 10, 4: 12, 6: 11, 10: 12, 12: 10, 13: 11}
    if n in especiales: m[8][cols // 2] = especiales[n]; m[9][cols // 2] = 1
    if n in (7, 15):
        m[8][cols - 8] = 13; m[9][cols - 8] = 1
    if n % 3 == 1: m[3][cols // 3] = 14; m[4][cols // 3] = 4
    if n % 2 == 0: m[3][2 * cols // 3] = 15; m[4][2 * cols // 3] = 4
    for c in range(12):                                                  # inicio seguro
        m[9][c] = 1
    for c in range(cols - 12, cols):
        m[9][c] = 1
    return m


def templo(largo):
    p = base('TEMPLO', 'EL TEMPLO PERDIDO', [
        ('Salta sobre los guardianes.', BLANCO), ('Rompe ladrillos con la cabeza', BLANCO),
        ('o con el latigo (ESPACIO).', BLANCO), ('Lleva al altar LLAVE y AMULETO', AMARILLO),
        ('...pero nunca la CALAVERA.', ROJO), ('Q A O P  salta con Q', CIAN)])
    p['tiles'] = tiles_templo()
    p['scroll'].update(direccion='plataformas', modo='sigue', paso=2, umbral=88, retroceso=True, umbral_ret=40,
                       compilar_sprites=True)
    p['scroll']['fisica'] = {'altura': 44, 'subida': 11, 'caida_max': 6}
    est = {'casco': True}
    fr = [humano(16, 24, 'andar', k, est) for k in range(4)]
    fr += [espejo(f) for f in fr]
    fr += [humano(16, 24, 'golpe', 0, est), espejo(humano(16, 24, 'golpe', 0, est))]
    p['jugador'] = {'tamano': '16x24', 'velocidad': 2, 'x': 24, 'y': 72, 'cadencia': 8, 'vel_anim': 3,
                    'quieto': {'dcha': 0, 'izq': 4}, 'disparo': {'dcha': 8, 'izq': 9}, 'fotogramas': fr,
                    'anim': anim_lateral([0, 1, 2, 3], [4, 5, 6, 7]), 'arma': 'golpe', 'alcance': 14,
                    'pisar': True}
    p['enemigos'] = [
        enemigo('Momia', '16x24', [humano(16, 24, 'andar', k, {'gordo': True, 'pelo': False}) for k in (1, 3)],
                'patrulla', vel=1, energia=2, puntos=100, direccion='izq', voltear=True),
        enemigo('Esqueleto', '16x24', [humano(16, 24, 'andar', k, {'pelo': False}) for k in (1, 3)],
                'patrulla', vel=1, energia=1, puntos=80, direccion='izq', voltear=True),
        enemigo('Murcielago', '16x16', [criatura(16, 16, 61, fase=k, densidad=0.45) for k in range(2)],
                'rebota', vel=1, puntos=60, direccion='abajo-izq'),
        enemigo('Arana', '16x16', [criatura(16, 16, 77, fase=k, densidad=0.6) for k in range(2)],
                'patrulla', vel=1, puntos=60, direccion='izq', voltear=True),
        enemigo('Espiritu', '16x16', [criatura(16, 16, 90, fase=k, densidad=0.4) for k in range(2)],
                'persigue', vel=1, energia=2, puntos=120),
        enemigo('Guardian', '16x32', [humano(16, 32, 'andar', k, {'casco': True, 'arma': True}) for k in (1, 3)],
                'patrulla', vel=1, energia=3, cadencia=80, puntos=200, direccion='izq', voltear=True),
    ]
    p['balas'] = {'jugador': {'nombre': 'Latigo', 'tamano': '8x8', 'fotogramas': [bala('punto')]},
                  'enemigo': {'nombre': 'Dardo', 'tamano': '8x8', 'fotogramas': [bala('rayo_h')]}}
    e = juego.estrategia(p)
    e['elementos'] = [{'nombre': 'Llave', 'simbolo': 'L'}, {'nombre': 'Amuleto', 'simbolo': 'A'},
                      {'nombre': 'Calavera', 'simbolo': 'C'}]
    e['reglas'] = [
        {'necesita': [2], 'modo': 'contiene', 'cuando': 'altar', 'accion': 'perder', 'mensaje': 'LA CALAVERA MALDICE',
         'gasta': True, 'puntos': 0},
        {'necesita': [0, 1], 'modo': 'exacta', 'cuando': 'altar', 'accion': 'fase', 'valor': 13,
         'mensaje': 'PASAJE SECRETO', 'gasta': True, 'puntos': 500},
        {'necesita': [0], 'modo': 'contiene', 'cuando': 'altar', 'accion': 'vida', 'mensaje': 'UN COFRE: VIDA EXTRA',
         'gasta': True, 'puntos': 200},
    ]
    e['falta'] = 'EL ALTAR CALLA'
    e['hud'] = {'activo': True, 'fila': 23, 'col': 28, 'atr': atributo(MAGENTA, NEGRO, 1)}
    p['partida']['marcador']['fase']['activo'] = False
    p['niveles'] = []
    for n in range(16):
        m = mapa_templo(largo, n)
        r = random.Random(400 + n)
        apar = []
        for c in range(16, largo - 12, max(4, 9 - n // 3)):
            tipo = r.choice(range(min(6, 2 + n // 2)))
            f = 3 if p['enemigos'][tipo]['comportamiento'] in ('rebota', 'persigue') else 7
            apar.append({'tipo': tipo, 'f': f, 'c': c})
        p['niveles'].append({'nombre': f'Sala {n + 1}', 'mapa': m, 'apariciones': apar})
    p['partida']['mensajes'].update(fase='SALA', final='EL TESORO ES TUYO')
    marcador(p, AMARILLO)
    return p


# =====================================================================
#  PUÑOS: beat'em up, horizontal de 8 en 8, sin disparo, a golpes
# =====================================================================
def tiles_punos():
    T = [
        (patron(lambda x, y: (x + y * 3) % 23 == 0), BLANCO, AZUL, {}),                              # 0 noche
        (patron(lambda x, y: x % 8 in (0, 7) or y % 8 == 0 or (2 <= x % 8 <= 5 and 2 <= y % 8 <= 5)), AMARILLO, NEGRO,
         {'solido': True, 'detiene': True}),                                                          # 1 fachada con ventanas
        (patron(lambda x, y: y % 4 == 0 or (x + (y // 4) * 4) % 8 == 0), ROJO, NEGRO, {'solido': True, 'detiene': True}),  # 2 ladrillo
        (patron(lambda x, y: y == 15 or (y == 7 and x % 6 < 3)), BLANCO, NEGRO, {}),                # 3 calle
        (patron(lambda x, y: y == 0 or y == 15 or (x + y) % 9 == 0), BLANCO, NEGRO, {}),            # 4 acera
        (patron(lambda x, y: 3 <= x <= 12 and y >= 3 and (y in (3, 4) or x in (3, 12) or y % 4 == 0)), BLANCO, NEGRO,
         {'solido': True, 'detiene': True, 'rompible': True, 'tras': 7, 'puntos': 20}),                # 5 cubo de basura
        (patron(lambda x, y: 1 <= x <= 14 and 2 <= y <= 14 and (x in (1, 14) or y in (2, 14) or x == y or x == 15 - y)), AMARILLO, NEGRO,
         {'solido': True, 'detiene': True, 'rompible': True, 'tras': 8, 'puntos': 20}),                # 6 caja
        (patron(lambda x, y: 4 <= x <= 11 and 6 <= y <= 12 and not (y == 9)), AMARILLO, NEGRO,
         {'objeto': True, 'accion': 'energia', 'tras': 3, 'puntos': 50}),                              # 7 hamburguesa
        (patron(lambda x, y: 3 <= x <= 12 and 5 <= y <= 13 and (x + y) % 3), VERDE, NEGRO,
         {'objeto': True, 'accion': 'puntos', 'tras': 3, 'puntos': 200}),                              # 8 bolsa de dinero
        (patron(lambda x, y: 7 <= x <= 8 or (y < 3 and 4 <= x <= 11)), AMARILLO, NEGRO, {}),        # 9 farola
        (patron(lambda x, y: (x - 7.5) ** 2 + (y - 9) ** 2 < 20 and y > 4), ROJO, NEGRO, {'solido': True, 'detiene': True}),  # 10 boca de riego
        (patron(lambda x, y: y > 9 or (x % 4 == 0 and y > 4)), MAGENTA, NEGRO, {'solido': True, 'detiene': True}),  # 11 valla
        (patron(lambda x, y: abs(x - 7.5) + abs(y - 7.5) < 6), ROJO, NEGRO,
         {'objeto': True, 'accion': 'vida', 'tras': 3, 'puntos': 100}),                                # 12 corazón
    ]
    return [tile(pix, tinta, papel, 1 if tinta != BLANCO else 0, **pr) for pix, tinta, papel, pr in T]


def mapa_punos(cols, n):
    r = random.Random(500 + n)
    m = [[3] * cols for _ in range(10)]
    for c in range(cols):
        m[0][c] = 0
        m[1][c] = 0 if (c // 3 + n) % 5 == 0 else (1 if (c // 4) % 2 else 2)
        m[2][c] = 1 if (c // 4) % 2 else 2
        m[3][c] = 4
        m[9][c] = 4
        if c % 7 == 3: m[3][c] = 9
    for c in range(14, cols - 10, 1):
        if r.random() < 0.06: m[r.randint(4, 8)][c] = r.choice((5, 6, 5, 6, 10))
        if r.random() < 0.02: m[r.choice((4, 8))][c] = 11
    if n % 4 == 3: m[6][cols // 2] = 12
    for c in range(10):
        for f in range(4, 9): m[f][c] = 3
    return m


def punos(largo):
    p = base('PUNOS', 'PUÑOS DE ACERO', [
        ('La banda del Cuervo domina', BLANCO), ('las calles. Tu solo contra', BLANCO),
        ('todos. ESPACIO: puñetazo.', BLANCO), ('Rompe cajas y cubos: dentro', CIAN),
        ('hay comida, dinero y vidas.', CIAN), ('Q A O P mueve', AMARILLO)])
    p['tiles'] = tiles_punos()
    p['scroll'].update(direccion='horizontal', modo='sigue', paso=8, umbral=72, retroceso=False)
    est = {'pelo': True}
    fr = [humano(16, 24, 'andar', k, est) for k in range(4)]
    fr += [espejo(f) for f in fr]
    fr += [humano(16, 24, 'golpe', 0, est), espejo(humano(16, 24, 'golpe', 0, est))]
    p['jugador'] = {'tamano': '16x24', 'velocidad': 2, 'x': 24, 'y': 96, 'cadencia': 6, 'vel_anim': 3,
                    'quieto': {'dcha': 0, 'izq': 4}, 'disparo': {'dcha': 8, 'izq': 9, 'arriba-dcha': 8, 'abajo-dcha': 8,
                                                                   'arriba-izq': 9, 'abajo-izq': 9},
                    'fotogramas': fr, 'anim': anim_lateral([0, 1, 2, 3], [4, 5, 6, 7]), 'arma': 'golpe', 'alcance': 12}
    # banco de sprites (16 KB): jugador 10 x 576, tres matones volteables 4 x 576, jefe 2 x 768, perro 2 x 384
    estilos = [('Punk', {'pelo': True}, 1, 1, 60, True), ('Maton', {'gordo': True}, 1, 3, 120, True),
               ('Motero', {'casco': True}, 2, 2, 100, True), ('Jefe', {'gordo': True, 'casco': True}, 1, 6, 500, False)]
    p['enemigos'] = []
    for nom, est_e, vel, ener, pts, volt in estilos:
        tam = '16x32' if nom == 'Jefe' else '16x24'
        w, h = graficos.TAMANOS[tam]
        p['enemigos'].append(enemigo(nom, tam, [humano(w, h, 'andar', k, est_e) for k in (1, 3)],
                                     'persigue', vel=vel, energia=ener, puntos=pts, voltear=volt, vel_anim=5))
    p['enemigos'].append(enemigo('Perro', '16x16', [criatura(16, 16, 123, fase=k, densidad=0.5) for k in range(2)],
                                 'cruza', vel=3, puntos=40, direccion='izq'))
    p['balas'] = {'jugador': {'nombre': 'Golpe', 'tamano': '8x8', 'fotogramas': [bala('punto')]},
                  'enemigo': {'nombre': 'Botella', 'tamano': '8x8', 'fotogramas': [bala('punto')]}}
    p['niveles'] = []
    for n in range(16):
        m = mapa_punos(largo, n)
        r = random.Random(600 + n)
        apar = []
        for c in range(14, largo - 6, max(3, 6 - n // 4)):
            tipo = r.choice([0, 1, 2, 4][:min(4, 2 + n // 3)])     # el jefe (3), solo al final de la calle
            apar.append({'tipo': tipo, 'f': r.randint(4, 7), 'c': c})
        apar.append({'tipo': 3, 'f': 4, 'c': largo - 8})
        p['niveles'].append({'nombre': f'Calle {n + 1}', 'mapa': m, 'apariciones': apar})
    p['partida']['mensajes'].update(fase='CALLE', final='LA CIUDAD ES LIBRE')
    marcador(p, ROJO)
    return p


# =====================================================================
#  ASALTO: shoot'em up vertical, scroll fino automático, en color
# =====================================================================
def tiles_asalto():
    ola = lambda s: (lambda x, y: (y + s) % 8 == 0 and (x + y // 8 * 5) % 8 < 4)
    T = [
        (patron(ola(0)), BLANCO, AZUL),                                                     # 0 mar
        (patron(ola(4)), CIAN, AZUL),                                                       # 1 mar 2
        (patron(lambda x, y: (x * 3 + y * 7) % 13 == 0), ROJO, AMARILLO),                   # 2 arena
        (patron(lambda x, y: (x * 5 + y * 3) % 11 == 0), NEGRO, VERDE),                     # 3 hierba
        (patron(lambda x, y: (x % 8 - 3.5) ** 2 + (y % 8 - 3.5) ** 2 < 11 and (x + y) % 3), NEGRO, VERDE),  # 4 selva
        (patron(lambda x, y: x in (0, 15) or (x in (7, 8) and y % 8 < 4)), AMARILLO, NEGRO),  # 5 carretera
        (patron(lambda x, y: y % 4 == 0 or x == 0), AMARILLO, ROJO),                        # 6 tejados
        (patron(lambda x, y: x % 8 == 0 or y % 8 == 0 or (x % 8 == 4 and y % 8 == 4)), AZUL, CIAN),  # 7 placas de la base
        (patron(lambda x, y: y < 3 or (x - 7.5) ** 2 / 50 + (y - 15) ** 2 / 100 < 1), NEGRO, CIAN),  # 8 hangar
        (patron(lambda x, y: 9 < (x - 7.5) ** 2 + (y - 7.5) ** 2 < 30), NEGRO, VERDE),     # 9 cráter
        (patron(lambda x, y: (x - 6) ** 2 + (y - 8) ** 2 < 20 or (x - 11) ** 2 + (y - 9) ** 2 < 12), BLANCO, AZUL),  # 10 nube
        (patron(lambda x, y: (x + y) % 2 == 0 and y % 4 < 2), NEGRO, AMARILLO),             # 11 orilla
    ]
    return [tile(pix, tinta, papel, 0) for pix, tinta, papel in T]


def mapa_asalto(filas, n):
    r = random.Random(700 + n)
    biomas = ['mar', 'costa', 'selva', 'ciudad', 'base']
    m = []                                  # de abajo arriba; al final se da la vuelta
    for f in range(filas):
        b = biomas[min(4, (f * 5 // filas + n) % 5)]
        fila = []
        for c in range(12):
            if b == 'mar': t = 10 if r.random() < 0.03 else (0 if (c + f) % 3 else 1)
            elif b == 'costa': t = 11 if c in (f % 4 + 2, f % 4 + 3) else (2 if c > f % 4 + 3 else 0)
            elif b == 'selva': t = 4 if r.random() < 0.6 else (9 if r.random() < 0.1 else 3)
            elif b == 'ciudad': t = 5 if c in (3, 8) or f % 6 == 0 else 6
            else: t = 8 if (c in (2, 9) and f % 5 < 2) else 7
            fila.append(t)
        m.append(fila)
    return m[::-1]


def asalto(largo):
    p = base('ASALTO', 'ASALTO AEREO', [
        ('Cruza el oceano, la costa,', BLANCO), ('la selva y la ciudad hasta', BLANCO),
        ('la base del enemigo.', BLANCO), ('Q A O P mueve  ESPACIO dispara', CIAN),
        ('16 misiones. Suerte, piloto.', AMARILLO)])
    p['tiles'] = tiles_asalto()
    p['scroll'].update(direccion='vertical', modo='auto', vel_auto=1, paso=2, retroceso=False)
    p['jugador'] = {'tamano': '16x16', 'velocidad': 2, 'x': 88, 'y': 128, 'cadencia': 5, 'vel_anim': 3,
                    'quieto': {}, 'disparo': {}, 'disparo_fijo': 'arriba',
                    'fotogramas': [nave(fase=k) for k in range(2)],
                    'anim': {d: [0, 1] for d in juego.DIRECCIONES}, 'arma': 'disparo'}
    abajo = lambda pix: pix[::-1]
    p['enemigos'] = [
        enemigo('Caza', '16x16', [abajo(nave(variante=1, fase=k)) for k in range(2)], 'cruza', vel=2, puntos=50),
        enemigo('Interceptor', '16x16', [abajo(nave(variante=2, fase=k)) for k in range(2)], 'persigue', vel=1, puntos=80),
        enemigo('Helicoptero', '16x16', [criatura(16, 16, 11, fase=k, densidad=0.45) for k in range(2)], 'rebota',
                vel=1, cadencia=90, puntos=100, direccion='abajo-dcha'),
        enemigo('Torreta', '16x16', [criatura(16, 16, 19, fase=k, densidad=0.7) for k in range(2)], 'quieto',
                energia=2, cadencia=50, puntos=150),
        enemigo('Lancha', '16x16', [criatura(16, 16, 27, fase=k, densidad=0.5) for k in range(2)], 'patrulla',
                vel=1, cadencia=100, puntos=90, direccion='dcha', voltear=True),
        enemigo('Bombardero', '24x24', [abajo(nave(24, 24, variante=0, fase=k)) for k in range(2)], 'patrulla',
                vel=1, energia=4, cadencia=60, puntos=300, direccion='dcha'),
        enemigo('Zeppelin', '24x24', [criatura(24, 24, 41, fase=k, densidad=0.65) for k in range(2)], 'rebota',
                vel=1, energia=6, cadencia=70, puntos=400, direccion='abajo-izq'),
        enemigo('Mina', '16x16', [criatura(16, 16, 53, fase=k, densidad=0.35) for k in range(2)], 'quieto', puntos=30),
        enemigo('Fortaleza', '24x24', [criatura(24, 24, 59, fase=k, densidad=0.8) for k in range(2)], 'quieto',
                energia=10, cadencia=35, puntos=1000),
    ]
    p['balas'] = {'jugador': {'nombre': 'Cañon', 'tamano': '8x8', 'fotogramas': [bala('rayo')]},
                  'enemigo': {'nombre': 'Bala', 'tamano': '8x8', 'fotogramas': [bala('punto')]}}
    p['niveles'] = []
    for n in range(16):
        m = mapa_asalto(largo, n)
        r = random.Random(800 + n)
        apar = []
        for f in range(len(m) - 14, 4, -max(2, 5 - n // 4)):
            tipo = r.choice(range(min(8, 3 + n // 2)))
            apar.append({'tipo': tipo, 'f': f, 'c': r.randint(0, 10)})
        apar.append({'tipo': 8, 'f': 6, 'c': 5})                              # fortaleza al final
        p['niveles'].append({'nombre': f'Mision {n + 1}', 'mapa': m, 'apariciones': apar})
    p['partida']['mensajes'].update(fase='MISION', final='VICTORIA TOTAL')
    marcador(p, CIAN)
    return p


# =====================================================================
#  COMANDO: run'n'gun vertical que sigue al jugador, con estrategia
# =====================================================================
def tiles_comando():
    T = [
        (patron(lambda x, y: (x * 5 + y * 3) % 13 == 0), NEGRO, VERDE, {}),                                   # 0 hierba
        (patron(lambda x, y: (x * 3 + y * 7) % 11 == 0), ROJO, AMARILLO, {}),                                 # 1 tierra
        (patron(lambda x, y: ((x - 7.5) ** 2 + (y - 7) ** 2 < 42) and (x + y) % 4), NEGRO, VERDE,
         {'solido': True, 'detiene': True}),                                                                   # 2 árbol
        (patron(lambda x, y: (x - 7.5) ** 2 / 50 + (y - 8) ** 2 / 40 < 1 and (x * y) % 7), BLANCO, NEGRO,
         {'solido': True, 'detiene': True}),                                                                   # 3 roca
        (patron(lambda x, y: (y % 6 == 0 and x % 6 < 3)), BLANCO, AZUL, {'solido': True}),                    # 4 agua
        (patron(lambda x, y: y % 4 == 0 or x in (0, 15)), NEGRO, AMARILLO, {}),                               # 5 puente
        (patron(lambda x, y: y > 5 and ((x + (y // 3) * 4) % 8 < 6) and y % 3), AMARILLO, VERDE,
         {'solido': True, 'detiene': True, 'rompible': True, 'tras': 1, 'puntos': 10}),                       # 6 sacos
        (patron(lambda x, y: 2 <= x <= 13 and 3 <= y <= 13 and (x in (2, 13) or y in (3, 13) or y == 8)), AMARILLO, VERDE,
         {'solido': True, 'detiene': True, 'rompible': True, 'tras': 16, 'puntos': 20}),                      # 7 caja de munición
        (patron(lambda x, y: y < 7 and abs(x - 7.5) < y + 1 or (y >= 7 and 1 <= x <= 14)), ROJO, VERDE,
         {'solido': True, 'detiene': True}),                                                                   # 8 cabaña
        (patron(lambda x, y: (x + y) % 4 == 0 or (x - y) % 4 == 0), BLANCO, VERDE, {'mortal': True}),        # 9 alambrada
    ]
    rehen = lambda: patron(lambda x, y: ((x - 7.5) ** 2 + (y - 3) ** 2 < 6) or (5 <= x <= 10 and 6 <= y <= 11) or
                           (x in (5, 6, 9, 10) and y > 11))
    T += [
        (rehen(), BLANCO, VERDE, {'objeto': True, 'accion': 'guardar', 'valor': 0, 'tras': 0, 'puntos': 100}),  # 10 rehén A
        (rehen(), CIAN, VERDE, {'objeto': True, 'accion': 'guardar', 'valor': 1, 'tras': 0, 'puntos': 100}),   # 11 rehén B
        (rehen(), AMARILLO, VERDE, {'objeto': True, 'accion': 'guardar', 'valor': 2, 'tras': 0, 'puntos': 100}),  # 12 rehén C
        (patron(lambda x, y: 4 <= x <= 11 and 5 <= y <= 13 and x % 3 != 0 or (y < 5 and x == 10 and y > 1)), ROJO, VERDE,
         {'objeto': True, 'accion': 'guardar', 'valor': 3, 'tras': 0, 'puntos': 100}),                         # 13 dinamita
        (patron(lambda x, y: 3 <= x <= 12 and 7 <= y <= 13 or (7 <= x <= 8 and 2 <= y < 7)), MAGENTA, VERDE,
         {'objeto': True, 'accion': 'guardar', 'valor': 4, 'tras': 0, 'puntos': 100}),                         # 14 detonador
        (patron(lambda x, y: 2 <= x <= 13 and 6 <= y <= 14 or (x == 12 and y < 6) or (y == 1 and 9 <= x <= 15)), CIAN, NEGRO,
         {'objeto': True, 'accion': 'altar', 'tras': 15}),                                                     # 15 radio
        (patron(lambda x, y: 3 <= x <= 12 and 3 <= y <= 12 and not (7 <= x <= 8 or 7 <= y <= 8) or
                (7 <= x <= 8 and 4 <= y <= 11) or (7 <= y <= 8 and 4 <= x <= 11)), ROJO, BLANCO,
         {'objeto': True, 'accion': 'energia', 'tras': 1, 'puntos': 50}),                                      # 16 botiquín
        (patron(lambda x, y: (x - 7.5) ** 2 + (y - 9) ** 2 < 16 or (6 <= x <= 9 and y < 6)), AMARILLO, VERDE,
         {'objeto': True, 'accion': 'puntos', 'tras': 0, 'puntos': 300}),                                      # 17 medalla
    ]
    return [tile(pix, tinta, papel, 0, **pr) for pix, tinta, papel, pr in T]


def mapa_comando(filas, n):
    r = random.Random(900 + n)
    m = []
    camino = 5
    for f in range(filas):
        fila = [0] * 12
        if f % 3 == 0: camino = max(2, min(9, camino + r.choice((-1, 0, 1))))
        for c in range(12):
            if abs(c - camino) <= 1: fila[c] = 1
            elif r.random() < 0.18: fila[c] = 2
            elif r.random() < 0.05: fila[c] = 3
        if f % 40 == 20:                                         # río con puente
            fila = [4] * 12; fila[camino] = fila[camino + 1] = 5
        if f % 25 == 12:                                         # trinchera de sacos
            for c in range(12):
                if fila[c] in (0, 1) and r.random() < 0.6: fila[c] = 6
        if f % 31 == 7 and camino > 3: fila[camino - 3] = 8
        if r.random() < 0.04: fila[r.choice([c for c in range(12) if fila[c] == 0] or [0])] = 7
        if f % 33 == 16 and n > 3:
            for c in range(12):
                if fila[c] == 0 and r.random() < 0.5: fila[c] = 9
        m.append(fila)
    def poner(t, f):
        f = max(8, min(filas - 10, f)); c = r.randint(1, 10); m[f][c] = t
        for cc in (c - 1, c + 1):
            if m[f][cc] in (2, 3, 4, 8, 9): m[f][cc] = 1
    # rehenes en las fases 3, 7 y 11; dinamita en la 2 y detonador en la 4; la radio, en la 6
    especiales = {2: [10], 6: [11], 10: [12], 1: [13], 3: [14]}
    for t in especiales.get(n, []): poner(t, filas // 2)
    if n == 5: poner(15, filas // 3)
    poner(16, filas // 4); poner(17, 3 * filas // 4)
    for f in range(filas - 8, filas):                            # inicio despejado
        m[f] = [1 if abs(c - 5.5) < 3 else 0 for c in range(12)]
    return m[::-1]


def comando(largo):
    p = base('COMANDO', 'COMANDO JUNGLA', [
        ('Rescata a los tres rehenes', BLANCO), ('(vida extra si los salvas).', BLANCO),
        ('Con dinamita y detonador,', CIAN), ('usa la radio de la fase 6:', CIAN),
        ('volaras el puente enemigo.', CIAN), ('QAOP: mueve  ESPACIO: dispara', AMARILLO)])
    p['tiles'] = tiles_comando()
    p['scroll'].update(direccion='vertical', modo='sigue', paso=2, umbral=64, retroceso=False)
    a, b = humano_cenital(16, 16, 0), humano_cenital(16, 16, 1)
    der = [girar(a), girar(b)]
    fr = [a, b, a[::-1], b[::-1], der[0], der[1], espejo(der[0]), espejo(der[1])]
    p['jugador'] = {'tamano': '16x16', 'velocidad': 2, 'x': 88, 'y': 128, 'cadencia': 6, 'vel_anim': 4,
                    'quieto': {}, 'disparo': {}, 'fotogramas': fr, 'arma': 'disparo',
                    'anim': {'arriba': [0, 1], 'arriba-dcha': [0, 1], 'dcha': [4, 5], 'abajo-dcha': [2, 3],
                             'abajo': [2, 3], 'abajo-izq': [2, 3], 'izq': [6, 7], 'arriba-izq': [0, 1]}}
    sold = lambda k: humano_cenital(16, 16, k)[::-1]
    tanque = []
    for k in range(2):
        L = Lienzo(24, 24)
        L.rect(2, 3, 5, 21); L.rect(18, 3, 21, 21)                # cadenas
        for y in range(3 + k, 22, 3): L.pon(3, y, '.'); L.pon(20, y, '.')
        L.rect(6, 5, 17, 19); L.circulo(11.5, 12, 4, '.'); L.circulo(11.5, 12, 3)
        L.rect(11, 15, 12, 23)                                    # cañón hacia abajo
        tanque.append(contorno_auto(L.filas()))
    p['enemigos'] = [
        enemigo('Soldado', '16x16', [sold(0), sold(1)], 'persigue', vel=1, puntos=50),
        enemigo('Tirador', '16x16', [sold(0), sold(0)], 'quieto', cadencia=60, puntos=80),
        enemigo('Sargento', '16x16', [sold(1), sold(0)], 'persigue', vel=2, energia=2, cadencia=90, puntos=120),
        enemigo('Patrulla', '16x16', [girar(sold(0)), girar(sold(1))], 'patrulla', vel=1, cadencia=100, puntos=70,
                direccion='dcha', voltear=True),
        enemigo('Perro', '16x16', [criatura(16, 16, 137, fase=k, densidad=0.5) for k in range(2)], 'persigue',
                vel=2, puntos=40),
        enemigo('Tanque', '24x24', tanque, 'patrulla', vel=1, energia=6, cadencia=45, puntos=500, direccion='dcha'),
        enemigo('Nido', '16x16', [criatura(16, 16, 149, fase=k, densidad=0.75) for k in range(2)], 'quieto',
                energia=3, cadencia=40, puntos=200),
        enemigo('Helicoptero', '24x24', [criatura(24, 24, 157, fase=k, densidad=0.45) for k in range(2)], 'rebota',
                vel=1, energia=5, cadencia=60, puntos=400, direccion='abajo-dcha'),
    ]
    p['balas'] = {'jugador': {'nombre': 'Rafaga', 'tamano': '8x8', 'fotogramas': [bala('punto')]},
                  'enemigo': {'nombre': 'Bala', 'tamano': '8x8', 'fotogramas': [bala('punto')]}}
    e = juego.estrategia(p)
    e['elementos'] = [{'nombre': 'Rehen 1', 'simbolo': '1'}, {'nombre': 'Rehen 2', 'simbolo': '2'},
                      {'nombre': 'Rehen 3', 'simbolo': '3'}, {'nombre': 'Dinamita', 'simbolo': 'D'},
                      {'nombre': 'Detonador', 'simbolo': 'T'}]
    e['reglas'] = [
        {'necesita': [0, 1, 2], 'modo': 'contiene', 'cuando': 'al_completar', 'accion': 'vida',
         'mensaje': 'RESCATE COMPLETO', 'gasta': True, 'puntos': 900},
        {'necesita': [3, 4], 'modo': 'contiene', 'cuando': 'altar', 'accion': 'fase', 'valor': 10,
         'mensaje': 'PUENTE VOLADO!', 'gasta': True, 'puntos': 990},
        {'necesita': [3], 'modo': 'contiene', 'cuando': 'altar', 'accion': 'mensaje',
         'mensaje': 'FALTA EL DETONADOR', 'gasta': False, 'puntos': 0},
    ]
    e['falta'] = 'RADIO: SIN ORDENES'
    e['hud'] = {'activo': True, 'fila': 23, 'col': 26, 'atr': atributo(AMARILLO, NEGRO, 1)}
    p['partida']['marcador']['fase']['activo'] = False
    p['niveles'] = []
    for n in range(16):
        m = mapa_comando(largo, n)
        r = random.Random(1000 + n)
        apar = []
        for f in range(len(m) - 14, 4, -max(3, 7 - n // 3)):
            libres = [c for c in range(11) if m[f][c] in (0, 1) and m[f][c + 1] in (0, 1)]
            if not libres: continue
            tipo = r.choice(range(min(8, 2 + n // 2)))
            apar.append({'tipo': tipo, 'f': f, 'c': r.choice(libres)})
        p['niveles'].append({'nombre': f'Zona {n + 1}', 'mapa': m, 'apariciones': apar})
    p['partida']['mensajes'].update(fase='ZONA', final='MISION CUMPLIDA')
    marcador(p, VERDE)
    return p


# =====================================================================
#  música, pantallas y búsqueda del tamaño máximo
# =====================================================================
MUSICA = {
    # Grieg, «En la gruta del rey de la montaña»
    'asalto': ('MOUNTAIN KING', 'A4:.5 B4:.5 C5:.5 D5:.5 E5:.5 C5:.5 E5:1 D#5:.5 B4:.5 D#5:1 D5:.5 Bb4:.5 D5:1 '
               'A4:.5 B4:.5 C5:.5 D5:.5 E5:.5 C5:.5 E5:.5 A5:.5 G5:.5 E5:.5 C5:.5 E5:.5 G5:2',
               'A2:1 E3:1 A2:1 E3:1 B2:1 F#3:1 Bb2:1 F3:1 A2:1 E3:1 A2:1 E3:1 E2:1 B2:1 E2:1 B2:1', 170),
    # Bach, Tocata y fuga en re menor
    'nebulosa': ('TOCCATA', 'A5:.25 G5:.25 A5:1.5 R:.5 G5:.25 F5:.25 E5:.25 D5:.25 C#5:1 D5:2 R:1 '
                 'A4:.25 G4:.25 A4:1.5 R:.5 E4:.5 F4:.5 C#4:.5 D4:2 R:.5 A3:.5 D4:1.5',
                 'D2:1 D3:1 D2:1 D3:1 A1:1 A2:1 D2:1 D3:1', 120),
    # Mozart, Marcha turca
    'templo': ('MARCHA TURCA', 'B4:.25 A4:.25 G#4:.25 A4:.25 C5:1 D5:.25 C5:.25 B4:.25 C5:.25 E5:1 '
               'F5:.25 E5:.25 D#5:.25 E5:.25 B5:.25 A5:.25 G#5:.25 A5:.25 B5:.25 A5:.25 G#5:.25 A5:.25 C6:2 '
               'A5:.5 C6:.5 B5:.5 A5:.5 G5:.5 A5:.5 B5:.5 A5:.5 G5:.5 A5:.5 B5:.5 A5:.5 G5:.5 F#5:.5',
               'A2:1 E3:1 A2:1 E3:1 A2:1 E3:1 E2:1 B2:1', 130),
    # Beethoven, Para Elisa (a ritmo de rock)
    'punos': ('PARA ELISA', 'E5:.5 D#5:.5 E5:.5 D#5:.5 E5:.5 B4:.5 D5:.5 C5:.5 A4:1.5 R:.5 C4:.5 E4:.5 A4:.5 '
              'B4:1.5 R:.5 E4:.5 G#4:.5 B4:.5 C5:1.5 R:.5 E4:.5 E5:.5 D#5:.5 E5:.5 D#5:.5 E5:.5',
              'A2:.5 A3:.5 A2:.5 A3:.5 E2:.5 E3:.5 E2:.5 E3:.5', 160),
    # tradicional, «When Johnny Comes Marching Home»
    'comando': ('MARCHING HOME', 'E4:.5 A4:.75 A4:.25 A4:.75 B4:.25 C5:.75 B4:.25 A4:.75 G4:.25 E4:1.5 R:.5 '
                'E4:.5 G4:.75 G4:.25 G4:.75 A4:.25 B4:.75 A4:.25 G4:.75 E4:.25 A4:1.5 R:.5 '
                'E5:.75 E5:.25 E5:.75 D5:.25 C5:.75 B4:.25 A4:1 G4:.5 A4:1.5',
                'A2:.5 E3:.5 A2:.5 E3:.5 G2:.5 D3:.5 E2:.5 B2:.5', 140),
}


def _escena(clave):
    """Dibujo de fondo de las pantallas de cada juego (PIL)."""
    def asalto(d, w, h):
        d.rectangle((0, 0, w, h), fill=(0, 0, 205))
        d.rectangle((0, 120, w, h), fill=(0, 205, 205))
        for k in range(5): d.polygon([(40 + k * 45, 150), (52 + k * 45, 120), (64 + k * 45, 150)], fill=(255, 255, 255))
        d.polygon([(110, 112), (128, 88), (146, 112), (128, 105)], fill=(255, 255, 0))
    def nebulosa(d, w, h):
        r = random.Random(1)
        for _ in range(120): d.point((r.randrange(w), r.randrange(h)), fill=(0, 255, 255))
        d.ellipse((150, 90, 250, 190), outline=(0, 255, 255)); d.ellipse((10, 110, 70, 170), outline=(0, 205, 205))
    def templo(d, w, h):
        d.rectangle((0, 150, w, h), fill=(205, 205, 0))
        for k in range(6): d.rectangle((20 + k * 40, 104, 34 + k * 40, 150), fill=(205, 205, 205))
        d.polygon([(10, 104), (128, 84), (246, 104)], fill=(205, 0, 0))
    def punos(d, w, h):
        d.rectangle((0, 0, w, h), fill=(0, 0, 205))
        for k in range(8):
            alto = 60 + (k * 37) % 70
            d.rectangle((k * 32, h - alto, k * 32 + 28, h), fill=(0, 0, 0))
            for y in range(h - alto + 6, h - 8, 12):
                d.rectangle((k * 32 + 6, y, k * 32 + 10, y + 5), fill=(255, 255, 0))
    def comando(d, w, h):
        d.rectangle((0, 0, w, h), fill=(0, 205, 0))
        r = random.Random(2)
        for _ in range(40):
            x, y = r.randrange(w), r.randrange(70, h)
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(0, 100, 0))
        d.rectangle((0, 100, w, 115), fill=(0, 0, 205))
    return locals()[clave]


COLORES = {'asalto': [(0, 0, 205), (255, 255, 0), (255, 255, 255)],
           'nebulosa': [(0, 0, 0), (0, 255, 255), (255, 255, 255)],
           'templo': [(0, 0, 0), (255, 255, 0), (255, 0, 255)],
           'punos': [(0, 0, 205), (255, 0, 0), (255, 255, 0)],
           'comando': [(0, 205, 0), (255, 255, 0), (255, 255, 255)]}
TITULOS = {'asalto': ('ASALTO', 'SHOOT EM UP VERTICAL'), 'nebulosa': ('NEBULOSA X', 'SHOOT EM UP HORIZONTAL'),
           'templo': ('EL TEMPLO', 'PLATAFORMAS Y ESTRATEGIA'), 'punos': ('PUÑOS', 'TU CONTRA LA CALLE'),
           'comando': ('COMANDO', 'TU CONTRA EL EJERCITO')}
CONSTRUCTORES = {'asalto': asalto, 'nebulosa': nebulosa, 'templo': templo, 'punos': punos, 'comando': comando}


def completar(p, clave, musica_pt3):
    """Pantallas de carga y título y música."""
    t, sub = TITULOS[clave]
    p['pantalla_carga'] = pantalla(t, sub, _escena(clave), COLORES[clave], 'carga')
    p['pantalla_titulo'] = pantalla(t, sub, _escena(clave), COLORES[clave], 'titulo')
    musica(p, musica_pt3)
    return p


def crear_musica(clave):
    nombre, tema, bajo, tempo = MUSICA[clave]
    return componer(nombre, melodia(tema), melodia(bajo), tempo=tempo, repeticiones=2)


def cabe(clave, largo, pt3, pantallas):
    p = CONSTRUCTORES[clave](largo)
    p['pantalla_carga'], p['pantalla_titulo'] = pantallas
    musica(p, pt3)
    if juego.comprobar(p): return None
    try:
        return p, juego.generar_tap(p)
    except ValueError:
        return None


def maximizar(clave, minimo, maximo, informe=print):
    """Busca (por bisección) la mayor longitud de fase con la que el juego cabe en memoria."""
    pt3 = crear_musica(clave)
    t, sub = TITULOS[clave]
    pantallas = (pantalla(t, sub, _escena(clave), COLORES[clave], 'carga'),
                 pantalla(t, sub, _escena(clave), COLORES[clave], 'titulo'))
    mejor = cabe(clave, minimo, pt3, pantallas)
    if mejor is None:
        p = CONSTRUCTORES[clave](minimo); musica(p, pt3)
        raise ValueError(f'{clave}: no cabe ni con fases de {minimo}: {juego.comprobar(p)[:3]}')
    lo, hi = minimo, maximo
    while hi - lo > 1:
        mid = (lo + hi) // 2
        r = cabe(clave, mid, pt3, pantallas)
        if r: lo, mejor = mid, r
        else: hi = mid
    informe(f'{clave}: fases de {lo} {"filas" if not juego.horizontal(mejor[0]) else "columnas"}')
    return lo, mejor[0], mejor[1]


def cabe_con_todo(clave, largo):
    """El juego completo (música y pantallas) con fases de esa longitud, o None si no cabe."""
    t, sub = TITULOS[clave]
    pantallas = (pantalla(t, sub, _escena(clave), COLORES[clave], 'carga'),
                 pantalla(t, sub, _escena(clave), COLORES[clave], 'titulo'))
    return cabe(clave, largo, crear_musica(clave), pantallas)
