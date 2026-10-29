"""Ejemplo de scroll libre en 8 direcciones con tiles de 8x8 y de profundidad.
  ALDEA ZX: una aldea de 3 x 3 pantallas. El fondo es de dos colores y cada personaje conserva su
            tinta. Se puede entrar en las casas por la puerta: dentro, el tejado (tile de profundidad
            sin líneas) tapa a la protagonista. Las llaves están escondidas bajo los tejados. Las
            vallas de los huertos no se cruzan y, vistas desde el norte, tapan las piernas (línea Tras
            que no se traspasa).
            Los árboles se rodean por detrás de la copa (línea Tras en la base del tronco).
Uso:  python ejemplos_v12.py      (escribe ejemplos/aldea_zx.json y juegos/aldea_zx.tap)"""
import os, random
import juego
import ejemplos_grandes as EG
from ejemplos_v11 import char, linea, COPA, TRONCO

NEGRO, AZUL, ROJO, MAGENTA, VERDE, CIAN, AMARILLO, BLANCO = range(8)
GW, GH = 3, 3                                  # pantallas
W, H = GW * 24, GH * 20                        # caracteres

def pat(f):
    return [''.join('X' if f(x, y) else '.' for x in range(8)) for y in range(8)]

HIERBA = pat(lambda x, y: (x, y) in ((1, 2), (5, 6)))
CAMINO = pat(lambda x, y: (x + y * 3) % 4 == 0 and y % 2 == 0)
BOSQUE = pat(lambda x, y: (x * 3 + y * 5) % 7 < 4)
TEJA = ["XXXXXXXX", "X...X...", "X...X...", "XXXXXXXX", "..X...X.", "..X...X.", "XXXXXXXX", "........"]
ALERO = ["XXXXXXXX", "XXXXXXXX", "X.X.X.X.", "XXXXXXXX", ".X.X.X.X", "XXXXXXXX", "X.X.X.X.", "XXXXXXXX"]
MURO = ["XXXXXXXX", "...X....", "...X....", "XXXXXXXX", ".......X", ".......X", "XXXXXXXX", "...X...."]
VENTANA = ["XXXXXXXX", "X......X", "X.XXXX.X", "X.X..X.X", "X.XXXX.X", "X.X..X.X", "X.XXXX.X", "XXXXXXXX"]
UMBRAL = ["X.......", "X.......", "X.......", "X.......", "X.......", "X.......", "X.......", "XXXXXXXX"]
UMBRAL_D = [f[::-1] for f in UMBRAL]
SUELO = pat(lambda x, y: x == 0 and y % 4 == 0)
VALLA = ["........", "XXXXXXXX", "X..X..X.", "X..X..X.", "XXXXXXXX", "X..X..X.", "X..X..X.", "........"]
POSTE = ["..XXXX..", "..X..X..", "..XXXX..", "..X..X..", "..X..X..", "..XXXX..", "..X..X..", "..XXXX.."]
SETA = ["..XXXX..", ".XX.XXX.", "XXXXX.XX", "XX.XXXXX", "XXXXXXXX", "...XX...", "...XX...", "..XXXX.."]
POZO = ["..XXXX..", ".X....X.", "X.XXXX.X", "X.X..X.X", "X.XXXX.X", ".X....X.", "..XXXX..", "........"]


def aldea():
    r = random.Random(12)
    p = EG.comando(40)
    p['nombre'] = 'ALDEA ZX'
    p['tiles8'] = True
    ch = []
    def nuevo(filas, **props):
        ch.append(char(filas, NEGRO, VERDE, 1, **props)); return len(ch) - 1
    G = nuevo(HIERBA)                                  # 0: hierba (y tile de relleno)
    C = nuevo(CAMINO)
    B = nuevo(BOSQUE, solido=True, detiene=True)
    copa = {}
    for cy in range(2):
        for cx in range(2):
            copa[cx, cy] = nuevo([f[cx * 8:cx * 8 + 8] for f in COPA[cy * 8:cy * 8 + 8]], profundidad=True,
                                 linea_tras=linea((2 - cy) * 8 + 7))
    tronco = [nuevo([f[cx * 8:cx * 8 + 8] for f in TRONCO], solido=True, detiene=True) for cx in range(2)]
    # casa: alero sólido alrededor, tejado de profundidad sin líneas (tapa siempre), muro con ventanas y puerta
    ALE = nuevo(ALERO, solido=True, detiene=True)
    TEJ = nuevo(TEJA, profundidad=True)
    MUR = nuevo(MURO, solido=True, detiene=True)
    VEN = nuevo(VENTANA, solido=True, detiene=True)
    UMI, UMD, SUE = nuevo(UMBRAL), nuevo(UMBRAL_D), nuevo(SUELO)
    llaves = [nuevo(TEJA, profundidad=True, objeto=True, accion='guardar', valor=k, tras=TEJ, puntos=100)
              for k in range(3)]
    # huerto: vallas (línea Tras a media altura, no se traspasa) y postes sólidos
    VAL = nuevo(VALLA, profundidad=True, linea_tras=linea(5, pasable=False))
    POS = nuevo(POSTE, solido=True)
    SET = nuevo(SETA, objeto=True, accion='puntos', puntos=50, tras=G)
    POZ = nuevo(POZO, solido=True, detiene=True)
    p['tiles'] = ch

    M = [[G] * W for _ in range(H)]
    ocupado = [[False] * W for _ in range(H)]
    def libre(f, c, h, w, margen=2):
        return all(0 <= f + y < H and 0 <= c + x < W and not ocupado[f + y][c + x]
                   for y in range(-margen, h + margen) for x in range(-margen, w + margen))
    def marcar(f, c, h, w):
        for y in range(h):
            for x in range(w): ocupado[f + y][c + x] = True
    # bosque alrededor y caminos entre pantallas
    for f in range(H):
        for c in range(W):
            if f < 2 or f >= H - 2 or c < 2 or c >= W - 2: M[f][c] = B; ocupado[f][c] = True
    for gy in range(GH - 1):
        for c in range(2, W - 2):
            for f in (gy * 20 + 18, gy * 20 + 19): M[f][c] = C; ocupado[f][c] = True
    for gx in range(GW - 1):
        for f in range(2, H - 2):
            for c in (gx * 24 + 22, gx * 24 + 23): M[f][c] = C; ocupado[f][c] = True

    def casa(f, c, llave):
        """10 x 6 caracteres: alero, 3 filas de tejado (interior), muro con puerta de 3."""
        for x in range(10):
            M[f][c + x] = ALE
            for y in (1, 2, 3): M[f + y][c + x] = ALE if x in (0, 9) else TEJ
            for y in (4, 5): M[f + y][c + x] = MUR
        M[f + 4][c + 2] = M[f + 4][c + 7] = VEN
        for y in (4, 5):
            M[f + y][c + 4], M[f + y][c + 5], M[f + y][c + 6] = UMI, SUE, UMD
        if llave is not None: M[f + 2][c + 5] = llaves[llave]
        marcar(f, c, 6, 10)
        for y in (6, 7):                               # delante de la puerta, despejado
            for x in range(3, 8): ocupado[f + y][c + x] = True
    def huerto(f, c):
        """10 x 6: vallas arriba y abajo (con hueco abajo), postes a los lados, setas dentro."""
        hueco = r.choice((2, 6))
        for x in range(10):
            M[f][c + x] = VAL
            if not hueco <= x < hueco + 3: M[f + 5][c + x] = VAL
        for y in range(6): M[f + y][c] = M[f + y][c + 9] = POS
        for _ in range(3): M[f + r.randint(2, 3)][c + r.randint(2, 7)] = SET
        marcar(f, c, 6, 10)
        for x in range(hueco, hueco + 3): ocupado[f + 6][c + x] = True
    def arbol(f, c):
        for (x, y), k in copa.items(): M[f + y][c + x] = k
        M[f + 2][c], M[f + 2][c + 1] = tronco
        marcar(f, c, 3, 2)

    # en cada pantalla, cuatro huecos de 10 x 6: una casa (con llave en tres de ellas), un huerto o una
    # segunda casa, y árboles y un pozo en el resto
    pant = [(x, y) for y in range(GH) for x in range(GW)]
    con_llave = [(0, 0), (2, 0), (0, 2)]
    for (gx, gy) in pant:
        x0, y0 = gx * 24, gy * 20
        huecos = [(y0 + 2, x0 + 2), (y0 + 2, x0 + 12), (y0 + 10, x0 + 2), (y0 + 10, x0 + 12)]
        if (gx, gy) == (1, 2): huecos = [huecos[0], huecos[1], huecos[3], huecos[2]]
        else: r.shuffle(huecos)
        k = con_llave.index((gx, gy)) if (gx, gy) in con_llave else None
        casa(*huecos[0], k)
        if r.random() < 0.7: huerto(*huecos[1])
        else: casa(*huecos[1], None)
        for f, c in huecos[2:]:
            for (dy, dx) in r.sample([(0, 0), (0, 4), (0, 8), (3, 2), (3, 6)], 3):
                if libre(f + dy, c + dx, 3, 2, 0): arbol(f + dy, c + dx)
        for intento in range(40):
            f, c = y0 + r.randint(2, 16), x0 + r.randint(2, 20)
            if libre(f, c, 1, 1, 1): M[f][c] = POZ; marcar(f, c, 1, 1); break

    nv = juego.nivel_2d('La aldea', GW, GH, G, G, f=2)
    nv['mapa'] = M
    nv['inicio'] = [1, 2]
    # enemigos: soldados, perros y patrullas, más cuanto más lejos del inicio
    for (gx, gy) in pant:
        if (gx, gy) == (1, 2): continue
        dist = abs(gx - 1) + abs(gy - 2)
        for _ in range(1 + dist):
            for intento in range(60):
                f, c = gy * 20 + r.randint(2, 16), gx * 24 + r.randint(2, 20)
                f -= f % 2; c -= c % 2
                if all(M[f + y][c + x] in (G, C) for y in range(2) for x in range(2)): break
            nv['apariciones'].append({'tipo': r.choice([0, 0, 3, 4]), 'f': f, 'c': c})
    p['niveles'] = [nv]
    p['scroll'].update(direccion='libre', gravedad=False, paso=8, modo='sigue', umbral=72, umbral_v=56,
                       mezcla=False, color_sprites=True, retroceso=False)
    p['scroll']['colores'] = {'tinta': NEGRO, 'papel': VERDE, 'brillo': 1}
    # cada personaje con su tinta (sobre el papel verde del fondo)
    p['jugador']['color'] = 0x41                       # azul brillante
    tintas = {0: 0x42, 3: 0x43, 4: 0x40}              # soldado rojo, patrulla magenta, perro negro
    for i, en in enumerate(p['enemigos']): en['color'] = tintas.get(i, 0x42)
    p['jugador']['x'], p['jugador']['y'] = 88, 64
    e = juego.estrategia(p)
    e['elementos'] = [{'nombre': 'Llave roja', 'simbolo': 'R'}, {'nombre': 'Llave azul', 'simbolo': 'A'},
                      {'nombre': 'Llave verde', 'simbolo': 'V'}]
    e['reglas'] = [{'necesita': [0, 1, 2], 'modo': 'contiene', 'cuando': 'al_completar', 'accion': 'ganar',
                    'mensaje': 'LA ALDEA|ESTÁ A SALVO', 'gasta': False, 'puntos': 900}]
    e['falta'] = ''
    p['textos'] = [
        {'fila': 3, 'col': 11, 'tinta': VERDE, 'brillo': 1, 'texto': 'ALDEA ZX'},
        {'fila': 6, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Scroll libre, fondo de dos'},
        {'fila': 7, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'colores y personajes con tinta.'},
        {'fila': 9, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Entra en las casas: las tres'},
        {'fila': 10, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'llaves están bajo los tejados.'},
        {'fila': 12, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'Las vallas no se saltan: busca'},
        {'fila': 13, 'col': 1, 'tinta': BLANCO, 'brillo': 0, 'texto': 'el hueco de cada huerto.'},
        {'fila': 16, 'col': 1, 'tinta': AMARILLO, 'brillo': 1, 'texto': 'QAOP: mueve  ESPACIO: dispara'},
        {'fila': 20, 'col': 8, 'tinta': VERDE, 'brillo': 1, 'texto': 'PULSA UNA TECLA'}]
    p['partida']['mensajes'].update(fase='ALDEA', final='ENHORABUENA')
    p['partida']['marcador']['fase']['activo'] = False
    return p


if __name__ == '__main__':
    import crear_ejemplos_grandes as ceg
    p = aldea(); juego.actualizar(p)
    errores = juego.comprobar(p)
    if errores: raise SystemExit('; '.join(errores))
    tap = juego.generar_tap(p)
    ceg.guardar_json(p, os.path.join(ceg.EJ, 'aldea_zx.json'))
    open(os.path.join(ceg.JU, 'aldea_zx.tap'), 'wb').write(tap)
    print('aldea_zx', len(tap), 'bytes ·', len(p['tiles']), 'caracteres,',
          len(juego.expandir_t8(p)['tiles']), 'tiles de 16x16 ·', ceg.ocupacion(p))
