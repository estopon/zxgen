"""Dos juegos de ejemplo con mapa en rejilla de pantallas (gráficos y personajes propios):
  CASTILLO ZX: plataformas pantalla a pantalla (variante D del motor), con salas que se visitan
               saltando hacia arriba o cayendo hacia abajo y una rejilla irregular de 3 x 4.
  SELVA ZX:    acción cenital con scroll libre en 8 direcciones píxel a píxel (variante C), fondo de
               dos colores y un mapa irregular de 4 x 3 pantallas.
Uso:  python ejemplos_2d.py      (escribe ejemplos/castillo_zx.json, ejemplos/selva_zx.json y sus .tap)"""
import os, random
import juego
import ejemplo_terra as T
import ejemplos_grandes as EG
from graficos import atributo
from arte import patron

NEGRO, AZUL, ROJO, MAGENTA, VERDE, CIAN, AMARILLO, BLANCO = range(8)
PW, PH = juego.PANT_ANCHO, juego.PANT_ALTO


def montar(salas, gw, gh, leyenda, enemigos, relleno=0):
    """Mapa de la fase a partir de las salas dibujadas con letras: {(x, y): [10 filas de 12]}."""
    nv = juego.nivel_2d('', gw, gh, 0, relleno)
    nv['pantallas'] = [[(x, y) in salas for x in range(gw)] for y in range(gh)]
    for (x, y), filas in salas.items():
        assert len(filas) == PH and all(len(f) == PW for f in filas), (x, y)
        for f, fila in enumerate(filas):
            for c, ch in enumerate(fila):
                if ch in enemigos:
                    nv['apariciones'].append({'tipo': enemigos[ch], 'f': y * PH + f, 'c': x * PW + c})
                    ch = '.'
                nv['mapa'][y * PH + f][x * PW + c] = leyenda[ch]
    return nv


# =====================================================================
#  CASTILLO ZX: plataformas, pantalla a pantalla
# =====================================================================
SALAS_CASTILLO = {
    (0, 2): ["RRRRRRRRRRRR",          # G: salida
             "R...........",
             "R...........",
             "R......g....",
             "R.....PPP...",
             "R...........",
             "R...........",
             "R...........",
             "============",
             "############"],
    (1, 2): ["RRRRRR....RR",          # H: se sube saltando por el hueco del techo
             "...........R",
             "...........R",
             "......PPPP.R",
             "...........R",
             "...........R",
             "..PPP......R",
             "........s..R",
             "============",
             "############"],
    (1, 1): ["............",          # D: cruce
             "............",
             "...g......g.",
             "..PPP...PPP.",
             "............",
             "............",
             "............",
             "......PPPP..",
             "======....==",
             "######....##"],
    (0, 1): ["RRRRRRRRRRRR",          # C: sala del corazón
             "R...........",
             "R..c........",
             "R.PPP.......",
             "R...........",
             "R......m....",
             "R...........",
             "R...........",
             "============",
             "############"],
    (2, 1): ["RRRR..RRRRRR",          # E: se sube a B por el hueco
             "............",
             "...PPPP.....",
             "............",
             "............",
             ".......PPP..",
             "............",
             "..a.........",
             "============",
             "############"],
    (3, 1): ["RRRRRRRRRRRR",          # F: hueco en el suelo hacia I
             "...........R",
             "...........R",
             "..g.....g..R",
             "..L?L...L?LR",
             "...........R",
             "...........R",
             "..e........R",
             "=====..=====",
             "#####..#####"],
    (3, 2): ["RRRRR..RRRRR",          # I: el sótano de los pinchos (se vuelve saltando)
             "R..........R",
             "R....PP....R",
             "R..........R",
             "R..PP..PP..R",
             "R..........R",
             "R.PP....PP.R",
             "R.^^..g.^^.R",
             "============",
             "############"],
    (2, 0): ["RRRRRRRRRRRR",          # B
             "...........R",
             "...........R",
             "..g.....g..R",
             "...........R",
             "......L?L..R",
             "...........R",
             "...PPPP....R",
             "====..======",
             "####..######"],
    (1, 0): ["RRRRRRRRRRRR",          # A: la bandera
             "R...........",
             "R...........",
             "R.....m.....",
             "R...........",
             "R...........",
             "R...........",
             "R..F........",
             "============",
             "############"],
}


def castillo():
    p = T.proyecto(12, 1)
    p['nombre'] = 'CASTILLO'
    tiles = p['tiles']
    meta = dict(tiles[T.BANDERA]); meta.update(objeto=True, accion='ganar', puntos=500, tras=T.VACIO,
                                                mensaje='LA BANDERA ES TUYA')
    tiles.append(meta)
    META = len(tiles) - 1
    p['scroll'].update(direccion='pantallas', gravedad=True, paso=8, mezcla=False, color_sprites=False,
                       compilar_sprites=False, modo='sigue')
    p['scroll'].pop('ritmo', None)
    p['scroll']['fisica'] = {'altura': 80, 'subida': 13, 'caida_max': 6}
    leyenda = {'.': T.VACIO, '#': T.TIERRA, '=': T.CESPED, 'R': T.ROCA, 'L': T.LADRILLO, '?': T.SORPRESA,
               'g': T.GEMA, 'P': T.PASARELA, '^': T.PINCHOS, 'c': T.CORAZON, 'F': META}
    enem = {'s': 0, 'e': 1, 'a': 2, 'm': 3}
    nv = montar(SALAS_CASTILLO, 4, 3, leyenda, enem)
    nv['nombre'] = 'El castillo'; nv['inicio'] = [0, 2]
    p['niveles'] = [nv]
    p['jugador']['x'], p['jugador']['y'] = 24, 104
    p['estrategia']['reglas'] = []
    p['estrategia']['hud']['activo'] = False
    p['textos'] = [
        {'fila': 2, 'col': 11, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'CASTILLO'},
        {'fila': 5, 'col': 2, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Pantalla a pantalla: llega a'},
        {'fila': 6, 'col': 2, 'tinta': BLANCO, 'brillo': 0, 'texto': 'la bandera de la torre.'},
        {'fila': 8, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'Salta por los huecos del'},
        {'fila': 9, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'techo para subir de sala y'},
        {'fila': 10, 'col': 2, 'tinta': CIAN, 'brillo': 1, 'texto': 'deja caerte para bajar.'},
        {'fila': 16, 'col': 2, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'O P andar   Q saltar'},
        {'fila': 20, 'col': 8, 'tinta': VERDE, 'brillo': 1, 'texto': 'PULSA UNA TECLA'}]
    pa = p['partida']
    pa['mensajes'].update(fase='CASTILLO', game_over='FIN DEL VIAJE', final='LA BANDERA ES TUYA')
    p['pantalla_carga'] = T.pantalla('CASTILLO', 'PANTALLA A PANTALLA', T._escena,
                                     [(0, 0, 0), (255, 255, 0), (255, 255, 255)], 'carga')
    p['pantalla_titulo'] = T.pantalla('CASTILLO', 'PANTALLA A PANTALLA', T._escena,
                                      [(0, 0, 0), (255, 255, 0), (255, 255, 255)], 'titulo')
    return p


# =====================================================================
#  SELVA ZX: cenital, scroll libre en 8 direcciones (fondo de dos colores)
# =====================================================================
REJILLA_SELVA = ["XXX.",      # X = hay pantalla
                 "XXXX",
                 ".XXX"]


def sala_selva(r, x, y, gw, gh, hay):
    """Una pantalla de selva: hierba, árboles y rocas, con el paso abierto hacia las vecinas."""
    m = [[0] * PW for _ in range(PH)]
    for f in range(PH):
        for c in range(PW):
            v = r.random()
            if v < 0.13: m[f][c] = 2
            elif v < 0.17: m[f][c] = 3
    # caminos de tierra en cruz hacia las salas vecinas
    cf, cc = 4 + r.randint(0, 1), 5 + r.randint(0, 1)
    for c in range(PW):
        if (c < cc and hay(x - 1, y)) or (c >= cc and hay(x + 1, y)) or abs(c - cc) <= 1: m[cf][c] = m[cf + 1][c] = 1
    for f in range(PH):
        if (f < cf and hay(x, y - 1)) or (f >= cf and hay(x, y + 1)) or abs(f - cf) <= 1: m[f][cc] = m[f][cc + 1] = 1
    return m


def selva():
    p = EG.comando(40)
    p['nombre'] = 'SELVA ZX'
    tiles = p['tiles']
    # fondo de dos colores: la hierba con muy pocos puntos y los caminos lisos, para que se lean bien
    tiles[0] = dict(tiles[0]); tiles[0]['pix'] = patron(lambda x, y: (x * 5 + y * 3) % 31 == 0 or (x * 7 + y * 11) % 37 == 0)
    tiles[1] = dict(tiles[1]); tiles[1]['pix'] = patron(lambda x, y: False)
    helipuerto = dict(tiles[15])
    helipuerto.update(pix=patron(lambda x, y: x in (1, 14) or y in (1, 14) or (x in (5, 10) and 4 <= y <= 11) or
                                 (y in (7, 8) and 5 <= x <= 10)), objeto=True, accion='ganar', puntos=990,
                      tras=1, mensaje='RESCATE COMPLETADO', solido=False, detiene=False)
    tiles.append(helipuerto)
    HELI = len(tiles) - 1
    p['scroll'].update(direccion='libre', gravedad=False, paso=8, modo='sigue', umbral=72, umbral_v=56,
                       mezcla=False, color_sprites=False, retroceso=False)
    p['scroll']['colores'] = {'tinta': NEGRO, 'papel': VERDE, 'brillo': 1}
    gw, gh = len(REJILLA_SELVA[0]), len(REJILLA_SELVA)
    hay = lambda x, y: 0 <= x < gw and 0 <= y < gh and REJILLA_SELVA[y][x] == 'X'
    r = random.Random(77)
    nv = juego.nivel_2d('La selva', gw, gh, 0, 2)
    nv['pantallas'] = [[hay(x, y) for x in range(gw)] for y in range(gh)]
    for y in range(gh):
        for x in range(gw):
            if not hay(x, y): continue
            sala = sala_selva(r, x, y, gw, gh, hay)
            for f in range(PH):
                nv['mapa'][y * PH + f][x * PW:(x + 1) * PW] = sala[f]
    def poner(t, x, y, f, c):
        nv['mapa'][y * PH + f][x * PW + c] = t
        for df in (-1, 0, 1):
            for dc in (-1, 0, 1):
                ff, cc = y * PH + f + df, x * PW + c + dc
                if (df or dc) and 0 <= ff < gh * PH and 0 <= cc < gw * PW and nv['mapa'][ff][cc] in (2, 3):
                    nv['mapa'][ff][cc] = 0
    # inicio despejado, rehenes repartidos y el helipuerto en la otra punta
    for f in range(2, 8):
        for c in range(2, 9): nv['mapa'][f][c] = 0 if nv['mapa'][f][c] in (2, 3) else nv['mapa'][f][c]
    poner(10, 2, 0, 2, 9); poner(11, 0, 1, 7, 2); poner(12, 3, 1, 2, 9)
    poner(16, 1, 1, 6, 3); poner(17, 2, 2, 3, 3)
    poner(HELI, 3, 2, 7, 9)
    nv['inicio'] = [0, 0]
    nv['relleno'] = 2
    # enemigos: unos pocos por pantalla, más duros cuanto más lejos del inicio
    for y in range(gh):
        for x in range(gw):
            if not hay(x, y) or (x, y) == (0, 0): continue
            dist = x + y
            for _ in range(2 + dist // 2):
                for _intento in range(20):
                    f, c = r.randint(1, PH - 2), r.randint(1, PW - 2)
                    t, t2 = nv['mapa'][y * PH + f][x * PW + c], nv['mapa'][y * PH + f][x * PW + c + 1]
                    if t in (0, 1) and t2 in (0, 1): break
                tipo = r.choice([0, 0, 1, 3, 4] + ([2, 5, 6] if dist >= 3 else []))
                nv['apariciones'].append({'tipo': tipo, 'f': y * PH + f, 'c': x * PW + c})
    p['niveles'] = [nv]
    p['jugador']['x'], p['jugador']['y'] = 64, 64
    e = juego.estrategia(p)
    e['elementos'] = e['elementos']                  # (la dinamita y el detonador no se usan aquí)
    e['reglas'] = [{'necesita': [0, 1, 2], 'modo': 'contiene', 'cuando': 'al_completar', 'accion': 'vida',
                    'mensaje': 'RESCATE COMPLETO', 'gasta': False, 'puntos': 900}]
    e['falta'] = ''
    p['textos'] = [
        {'fila': 3, 'col': 12, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'SELVA ZX'},
        {'fila': 6, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Scroll libre en 8 direcciones.'},
        {'fila': 8, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Rescata a los tres rehenes'},
        {'fila': 9, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'y llega al helipuerto.'},
        {'fila': 12, 'col': 1, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'QAOP: mueve  ESPACIO: dispara'},
        {'fila': 20, 'col': 8, 'tinta': VERDE, 'brillo': 1, 'texto': 'PULSA UNA TECLA'}]
    p['partida']['mensajes'].update(fase='SELVA', final='MISION CUMPLIDA')
    p['partida']['marcador']['fase']['activo'] = False
    return p


if __name__ == '__main__':
    import crear_ejemplos_grandes as ceg
    for nombre, fn in (('castillo_zx', castillo), ('selva_zx', selva)):
        p = fn(); juego.actualizar(p)
        errores = juego.comprobar(p)
        if errores: raise SystemExit(f'{nombre}: ' + '; '.join(errores))
        tap = juego.generar_tap(p)
        ceg.guardar_json(p, os.path.join(ceg.EJ, nombre + '.json'))
        open(os.path.join(ceg.JU, nombre + '.tap'), 'wb').write(tap)
        print(nombre, len(tap), 'bytes ·', ceg.ocupacion(p))
