"""Ejemplo de la versión 11: tiles de 8x8 y tiles de profundidad.
  JUNGLA 8x8: acción vertical (como el de serie) con el mapa pintado carácter a carácter. Los árboles
              y las columnas son tiles de profundidad: el jugador pasa por detrás de sus copas y
              capiteles (línea Tras en su base) y por delante cuando está más abajo. Las vallas
              tienen una línea Tras que no se traspasa: si estás al norte, tapan tus piernas; no dejan pasar.
Uso:  python ejemplos_v11.py      (escribe ejemplos/jungla_8x8.json y juegos/jungla_8x8.tap)"""
import os, random
import juego
from graficos import atributo

NEGRO, AZUL, ROJO, MAGENTA, VERDE, CIAN, AMARILLO, BLANCO = range(8)


def char(filas, tinta, papel, brillo=0, **props):
    t = juego.tile8_vacio(atributo(tinta, papel, brillo))
    t['pix'] = [f.replace(' ', '.') for f in filas]
    t.update(props)
    return t


def linea(y0, y1=None, borde=0, pasable=True, x0=0, x1=7):
    return {'p': [x0, y0, x1, y0 if y1 is None else y1], 'borde': borde, 'pasable': pasable}


# copa de árbol (16x16 en cuatro caracteres) y tronco (dos caracteres, sólidos)
COPA = ["     XXXXXX     ",
        "   XX.XX.XXXX   ",
        "  XXXXXXXX.XXX  ",
        " XX.XXXX.XXXXXX ",
        " XXXXX.XXXXX.XX ",
        "XXX.XXXXXX.XXXXX",
        "XXXXXXX.XXXXXXXX",
        "X.XXXXXXXXXX.XXX",
        "XXXXX.XXXX.XXXXX",
        "XXXXXXXXXXXXXX.X",
        " XX.XXXXX.XXXXX ",
        " XXXXXXXXXXXX.X ",
        "  XXX.XX XXXXX  ",
        "   XXXX  X.XX   ",
        "     X    X     ",
        "                "]
TRONCO = ["      XXXX      ",
          "     XXXXXX     ",
          "      XXXX      ",
          "      XXXX      ",
          "      XX.X      ",
          "      XXXX      ",
          "     XXXXXX     ",
          "    XXXXXXXX    "]
# columna en ruinas: capitel y fuste (dos caracteres de ancho, tres de alto) y basa sólida
COLUMNA = ["XXXXXXXXXXXXXXXX",
           "X..............X",
           "XXXXXXXXXXXXXXXX",
           " X............X ",
           "  XXXXXXXXXXXX  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           "  X.X..X..X..X  ",
           " XXXXXXXXXXXXXX ",
           "XXXXXXXXXXXXXXXX",
           "X..............X",
           "XXXXXXXXXXXXXXXX"]
VALLA = ["X.......",
         "XXXXXXXX",
         "X.......",
         "X.......",
         "XXXXXXXX",
         "X.......",
         "X.......",
         "X......."]


def jungla():
    random.seed(11)
    p = juego.proyecto_nuevo(); juego.actualizar(p)
    p['nombre'] = 'JUNGLA8'
    p['niveles'] = p['niveles'][:1]
    nv = p['niveles'][0]; nv['nombre'] = 'La jungla'
    juego.a_tiles8(p)
    ch = p['tiles']; M = nv['mapa']
    from collections import Counter
    cuenta = Counter(v for f in M for v in f)
    hierba = {v for v, _ in cuenta.most_common(4)}       # los caracteres de la hierba de serie
    camino = {v for v, _ in cuenta.most_common(8)} - hierba
    def nuevo(t):
        ch.append(t); return len(ch) - 1
    # --- árbol: copa (profundidad, la línea Tras está en la base del tronco) y tronco sólido
    copa = {}
    for cy in range(2):
        for cx in range(2):
            filas = [f[cx * 8:cx * 8 + 8] for f in COPA[cy * 8:cy * 8 + 8]]
            base = (2 - cy) * 8 + 7                         # base del tronco, desde este carácter
            copa[cx, cy] = nuevo(char(filas, NEGRO, VERDE, 1, profundidad=True, linea_tras=linea(base)))
    tronco = [nuevo(char([f[cx * 8:cx * 8 + 8] for f in TRONCO], NEGRO, ROJO, 0, solido=True, detiene=True))
              for cx in range(2)]
    # --- columna: capitel y fuste de profundidad, basa sólida
    col = {}
    for cy in range(3):
        for cx in range(2):
            filas = [f[cx * 8:cx * 8 + 8] for f in COLUMNA[cy * 8:cy * 8 + 8]]
            if cy == 2:
                col[cx, cy] = nuevo(char(filas, AZUL, BLANCO, 1, solido=True, detiene=True))
            else:
                col[cx, cy] = nuevo(char(filas, AZUL, BLANCO, 1, profundidad=True,
                                         linea_tras=linea((2 - cy) * 8 + 2)))
    # --- valla: línea Tras a media altura que no se traspasa (al sur, delante; al norte, detrás)
    valla = nuevo(char(VALLA, AMARILLO, VERDE, 0, profundidad=True, linea_tras=linea(5, pasable=False)))

    alto, ancho = len(M), len(M[0])
    ocupado = set((a['f'], a['c']) for a in nv['apariciones'])
    def libre(f, c, h, w):
        return all(0 <= f + y < alto - 24 and 0 <= c + x < ancho and M[f + y][c + x] in hierba and
                   not any((f + y + dy, c + x + dx) in ocupado for dy in (-2, -1, 0) for dx in (-2, -1, 0))
                   for y in range(h) for x in range(w))
    def poner(f, c, celdas):
        for (x, y), k in celdas.items(): M[f + y][c + x] = k
    n_arb = n_col = 0
    for _ in range(4000):
        f, c = random.randrange(4, alto - 24), random.randrange(0, ancho - 1)
        if random.random() < 0.75:
            if libre(f - 1, c - 1, 5, 4):
                poner(f, c, {**{(x, y): copa[x, y] for x in range(2) for y in range(2)},
                             (0, 2): tronco[0], (1, 2): tronco[1]}); n_arb += 1
        elif libre(f - 1, c - 1, 5, 4):
            poner(f, c, col); n_col += 1
    # vallas: tramos horizontales con un hueco para pasar
    for f in range(alto - 30, 10, -28):
        if sum(M[f][c] not in hierba | camino for c in range(ancho)) > 4: continue
        hueco = random.choice([1, ancho - 7])
        for c in range(ancho):
            if not hueco <= c < hueco + 6 and M[f][c] in hierba | camino: M[f][c] = valla
    # junto a la salida: un árbol y una columna para probar nada más empezar (en un claro de hierba)
    g = next((M[f][c], M[f][c + 1], M[f + 1][c], M[f + 1][c + 1]) for f in range(0, alto - 1, 2)
             for c in range(0, ancho - 1, 2) if {M[f][c], M[f][c + 1], M[f + 1][c], M[f + 1][c + 1]} <= hierba)
    for f0, c0 in ((alto - 13, 2), (alto - 12, ancho - 5)):
        for f in range(f0 - 3, f0 + 5):
            for c in range(max(0, c0 - 2), min(ancho, c0 + 4)):
                if M[f][c] not in camino: M[f][c] = g[(f % 2) * 2 + c % 2]
    poner(alto - 13, 2, {**{(x, y): copa[x, y] for x in range(2) for y in range(2)},
                         (0, 2): tronco[0], (1, 2): tronco[1]})
    poner(alto - 12, ancho - 5, col)
    return p


def textos(p):
    p['textos'] = [
        {'fila': 3, 'col': 10, 'tinta': VERDE, 'brillo': 1, 'texto': 'JUNGLA 8x8'},
        {'fila': 6, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Mapa de caracteres de 8x8.'},
        {'fila': 8, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Pasa por detrás de los árboles'},
        {'fila': 9, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'y de las columnas.'},
        {'fila': 11, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Las vallas no se cruzan:'},
        {'fila': 12, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'busca el hueco.'},
        {'fila': 15, 'col': 1, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'QAOP: mueve  ESPACIO: dispara'},
        {'fila': 20, 'col': 8, 'tinta': VERDE, 'brillo': 1, 'texto': 'PULSA UNA TECLA'}]
    return p


if __name__ == '__main__':
    import crear_ejemplos_grandes as ceg
    p = textos(jungla()); juego.actualizar(p)
    errores = juego.comprobar(p)
    if errores: raise SystemExit('; '.join(errores))
    tap = juego.generar_tap(p)
    ceg.guardar_json(p, os.path.join(ceg.EJ, 'jungla_8x8.json'))
    open(os.path.join(ceg.JU, 'jungla_8x8.tap'), 'wb').write(tap)
    print('jungla_8x8', len(tap), 'bytes ·', len(p['tiles']), 'caracteres,',
          len(juego.expandir_t8(p)['tiles']), 'tiles de 16x16 ·', ceg.ocupacion(p))
