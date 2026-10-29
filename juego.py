"""Montaje del juego: proyecto (diccionario) -> archivo .tap para Spectrum 128K."""
import unicodedata
import tap, graficos, ejemplo, sonido, fuente_es
from pantalla import dir_pixel
from motor_bin import CARGADOR, MOTORES, DIR_MOTOR, PT3PLAYER, SPRITE_NL
try: from motor_bin import APARTES
except ImportError: APARTES = {}

DIR_CARGADOR = 0x5E00
CLEAR = DIR_CARGADOR - 1
MAX_MOTOR = 0xBE00 - DIR_MOTOR
AREA_ANCHO, AREA_ALTO = 24, 20          # caracteres
MAPA_ANCHO = 12                         # vertical: tiles de ancho
MAPA_ALTO = 10                          # horizontal: tiles de alto
MAX_TIPOS = 16
MAX_NIVELES = 16
HUD = ['puntos', 'record', 'vidas', 'energia', 'fase']
MAX_APARICIONES = 1000
COMPORTAMIENTOS = ['quieto', 'patrulla', 'persigue', 'rebota', 'cruza', 'personaje']
DIRECCIONES = ['arriba', 'arriba-dcha', 'dcha', 'abajo-dcha', 'abajo', 'abajo-izq', 'izq', 'arriba-izq']

def proyecto_nuevo():
    return {
        'version': 9,
        'nombre': 'MIJUEGO',
        'pantalla_carga': None, 'pantalla_titulo': None, 'pantalla_marco': None,
        'textos': [
            {'fila': 4, 'col': 7, 'tinta': 6, 'brillo': 1, 'texto': 'INSTRUCCIONES'},
            {'fila': 8, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'Q A O P  o  joystick Sinclair'},
            {'fila': 10, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'ESPACIO o 0 para disparar'},
            {'fila': 12, 'col': 3, 'tinta': 7, 'brillo': 0, 'texto': 'Avanza para mover el scroll'},
            {'fila': 20, 'col': 8, 'tinta': 5, 'brillo': 0, 'texto': 'PULSA UNA TECLA'},
        ],
        'area': {'col': 4, 'fila': 2},
        'scroll': scroll_defecto(),
        'tiles': ejemplo.tiles_ejemplo(),
        'jugador': ejemplo.jugador_ejemplo(),
        'enemigos': ejemplo.enemigos_ejemplo(),
        'niveles': ejemplo.niveles_ejemplo(),
        'balas': ejemplo.balas_ejemplo(),
        'partida': partida_defecto(),
    }

def partida_defecto():
    def h(fila, col, etiqueta, tinta):
        return {'activo': True, 'fila': fila, 'col': col, 'etiqueta': etiqueta, 'tinta': tinta, 'brillo': 1}
    return {
        'vidas': 3, 'energia': 3, 'kempston': False,
        'marcador': {'puntos': h(0, 1, 'PUNTOS ', 6), 'record': h(0, 18, 'RECORD ', 5),
                     'vidas': h(23, 1, 'VIDAS ', 7), 'energia': h(23, 10, 'ENERGIA ', 4),
                     'fase': h(23, 24, 'FASE ', 7)},
        'menu': [{'fila': 17, 'col': 9, 'tinta': 7, 'brillo': 1, 'texto': '1 JUGAR'},
                 {'fila': 18, 'col': 9, 'tinta': 7, 'brillo': 1, 'texto': '2 INSTRUCCIONES'}],
        'controles': {'fila': 19, 'col': 9, 'tinta': 7, 'brillo': 1,
                      'teclado': '3 CONTROL: TECLADO', 'kempston': '3 CONTROL: KEMPSTON'},
        'mensajes': {'fase': 'FASE', 'game_over': 'GAME OVER', 'final': 'ENHORABUENA!', 'tinta': 6, 'brillo': 1},
        'fuente': None,          # 768 bytes (caracteres 32-127) o None para la de la ROM
        'musica': {'menu': None, 'juego': None},   # módulos PT3 (bytes) o None
        'efectos': dict(sonido.POR_DEFECTO),        # efectos de sonido por evento (nombre o None)
        'efectos_propios': {},                     # efectos importados: {nombre: [(vol, tono, ruido, periodo, ruido_p)]}
        'a_la_vez': dict(A_LA_VEZ),                 # enemigos, balas del jugador y enemigas a la vez
    }

def info_pt3(datos):
    """(formato, título, autor) de un módulo PT3, o None si no lo parece."""
    if not datos or len(datos) < 0xCA: return None
    if datos.startswith(b'ProTracker 3.'): formato = 'ProTracker 3.' + chr(datos[13])
    elif datos.startswith(b'Vortex Tracker II'): formato = 'Vortex Tracker II'
    else: return None
    texto = lambda b: b.decode('latin-1').strip()
    return formato, texto(datos[0x1E:0x3E]), texto(datos[0x42:0x62])

def cargar_pt3(ruta):
    datos = open(ruta, 'rb').read()
    if info_pt3(datos) is None:
        raise ValueError('No es un módulo PT3 (ProTracker 3 o Vortex Tracker II).')
    if len(datos) > 16384 - len(PT3PLAYER):
        raise ValueError('El módulo es demasiado grande para el banco de música.')
    return datos

def scroll_defecto():
    return {'direccion': 'vertical',   # o 'horizontal'
            'modo': 'sigue',           # o 'auto'
            'retroceso': False,
            'vel_auto': 6,             # fotogramas de juego por carácter (modo automático)
            'umbral': 56,              # distancia al borde de avance
            'umbral_ret': 16,          # distancia al borde contrario (retroceso)
            'fisica': fisica_defecto(),   # modo plataformas
            'paso': 8,                    # píxeles por paso del scroll (1, 2, 4 u 8)
            'mezcla': False,              # modo mezcla (estilo SMB): dos pantallas alternadas a 50 Hz
            'color_sprites': False}       # los personajes pintan su propio color (modo bloques)

def enemigo_defecto(nombre='Enemigo', tamano='16x16', fotogramas=None):
    w, h = graficos.TAMANOS[tamano]
    return {'nombre': nombre, 'tamano': tamano,
            'fotogramas': fotogramas or [graficos.sprite_vacio(w, h)],
            'comportamiento': 'persigue', 'velocidad': 1, 'direccion': 'abajo',
            'energia': 1, 'cadencia': 0, 'puntos': 100, 'vel_anim': 4, 'voltear': False}

ARMAS = ['disparo', 'golpe', 'ninguna', 'laser']
A_LA_VEZ = {'enemigos': 6, 'balas_j': 3, 'balas_e': 4}
MAX_A_LA_VEZ = {'enemigos': 10, 'balas_j': 6, 'balas_e': 8}
SAVE_TOTAL = 1024                    # fondo guardado de todos los sprites (modos con anillo: V y H)
PATRONES_LASER = {                   # dibujo del láser: un byte por línea de grosor (8 píxeles que se repiten)
    'Línea continua': [0xFF, 0xFF, 0xFF], 'Discontinua': [0xF0, 0xF0, 0xF0], 'Punteada': [0xAA, 0x55, 0xAA],
    'Rayas cortas': [0xCC, 0xCC, 0xCC], 'Estrellas': [0x22, 0x77, 0x22], 'Doble línea': [0xFF, 0x00, 0xFF],
    'Onda': [0x81, 0x42, 0x24], 'Cadena': [0x66, 0x99, 0x66]}

def laser_defecto():
    return {'patron': list(PATRONES_LASER['Línea continua']), 'grosor': 1, 'duracion': 4, 'alcance': 0,
            'para_enemigo': True, 'para_tiles': True, 'animar': True}

def bytes_fondo(tam):
    """Bytes de fondo que guarda un sprite de ese tamaño en los modos con anillo."""
    w, h = graficos.TAMANOS[tam]
    return (w // 8 + 1) * h

def tamanos_a_la_vez(p):
    """(jugador, enemigo más grande, bala del jugador, bala enemiga) en bytes de fondo guardado."""
    ene = [bytes_fondo(en['tamano']) for en in p['enemigos'] if en.get('comportamiento') != 'personaje' or True]
    return (bytes_fondo(p['jugador']['tamano']), max(ene) if ene else 16,
            bytes_fondo(p['balas']['jugador'].get('tamano', '8x8')), bytes_fondo(p['balas']['enemigo'].get('tamano', '8x8')))

def limites_a_la_vez(p):
    """Cuántos personajes y balas puede mover el motor a la vez con estos tamaños.
    Devuelve {'max': {...}, 'usar': {...} (lo pedido, recortado al máximo), 'por_memoria': bool, 'motivo': str}.
    En el scroll fino (bloques) el límite es la tabla de huecos del motor (10 enemigos, 6 y 8 balas). En
    los modos con anillo (vertical y horizontal de 8 en 8) cada sprite guarda el fondo que tapa en una
    zona de 1024 bytes: cuanto más pequeños, más caben."""
    pedido = dict(A_LA_VEZ); pedido.update(p['partida'].get('a_la_vez') or {})
    pedido = {k: max(1, min(MAX_A_LA_VEZ[k], int(v))) for k, v in pedido.items()}
    maximo = dict(MAX_A_LA_VEZ)
    motivo = 'la tabla de huecos del motor'
    if not modo_bloques(p) and not libre(p):
        svj, sve, svb, svbe = tamanos_a_la_vez(p)
        libre_ = SAVE_TOTAL - svj
        maximo['balas_j'] = max(1, min(MAX_A_LA_VEZ['balas_j'], (libre_ - sve - svbe * pedido['balas_e']) // svb))
        maximo['balas_e'] = max(1, min(MAX_A_LA_VEZ['balas_e'], (libre_ - sve - svb * pedido['balas_j']) // svbe))
        bj, be = min(pedido['balas_j'], maximo['balas_j']), min(pedido['balas_e'], maximo['balas_e'])
        maximo['enemigos'] = max(1, min(MAX_A_LA_VEZ['enemigos'], (libre_ - bj * svb - be * svbe) // sve))
        motivo = (f'la zona de 1024 bytes donde cada sprite guarda el fondo que tapa (jugador {svj}, '
                  f'enemigo más grande {sve}, balas {svb} y {svbe} bytes)')
    usar = {k: min(pedido[k], maximo[k]) for k in pedido}
    return {'max': maximo, 'usar': usar, 'motivo': motivo}

def coste_sprites(p):
    """Estimación de ciclos por fotograma para dibujar a la vez todo lo que permite «a la vez»."""
    lim = limites_a_la_vez(p)['usar']
    comp, _, _ = plan_compilados(p)
    def coste(tam, compilado):
        w, h = graficos.TAMANOS[tam]
        b = (w // 8 + 1) * h
        por_byte = 16 if compilado else (45 if modo_bloques(p) or libre(p) else 66)
        return 400 + b * por_byte
    ene = [coste(en['tamano'], n in comp) for n, en in enumerate(p['enemigos'])] or [coste('16x16', False)]
    total = coste(p['jugador']['tamano'], 'j' in comp) + 600
    total += lim['enemigos'] * (max(ene) + 700)
    total += lim['balas_j'] * coste(p['balas']['jugador'].get('tamano', '8x8'), 'bala_j' in comp)
    total += lim['balas_e'] * coste(p['balas']['enemigo'].get('tamano', '8x8'), 'bala_e' in comp)
    return total

def estimacion_fps(p, fondo=None):
    """(fotogramas por segundo estimados con todo en pantalla, ciclos usados, ciclos disponibles).
    «fondo» permite pasar ya calculado el coste del fondo (es lo más lento de calcular)."""
    p = expandir_t8(p)
    r = ritmo(p)
    if fondo is None: fondo = coste_fondo(p) if modo_bloques(p) else (COSTE_LIBRE if libre(p) else 70000)
    usado = fondo + coste_sprites(p) + 8000
    disponible = r * 69888
    if usado <= disponible: return round(50 / r, 1), usado, disponible
    vueltas = -(-usado // 69888)
    return round(50 / vueltas, 1), usado, disponible

def velocidad_scroll(p):
    """Píxeles por fotograma de juego a los que avanza el scroll (aprox.): sigue a la jugadora a su
    velocidad o, en automático, un carácter cada vel_auto fotogramas."""
    sc = p['scroll']
    if pantallas(p): return 0
    if sc.get('modo') == 'auto': return max(1, -(-8 // max(1, sc.get('vel_auto', 6))))
    return max(1, min(4, p['jugador'].get('velocidad', 2)))

def velocidad_minima_bala(p):
    """Una bala tiene que ir al menos un píxel más deprisa que el scroll (si no, el scroll la alcanza)."""
    return min(12, velocidad_scroll(p) + 1)

def info_compilado(p, clave):
    """¿Se compila este personaje? clave: 'j', 'bala_j', 'bala_e' o el número de enemigo.
    Devuelve (compilado, bytes usados del banco 7, bytes del banco 7, texto)."""
    if not modo_bloques(p):
        return False, 0, BANCO7_TAM, 'Este tipo de scroll no usa sprites compilados.'
    if not p['scroll'].get('compilar_sprites', True):
        return False, 0, BANCO7_TAM, 'Sprites compilados desactivados (pestaña Scroll).'
    comp, _, datos = plan_compilados(p)
    si = clave in comp
    return si, len(datos), BANCO7_TAM, (
        f'Compilado (rápido). Banco 7: {len(datos)} de {BANCO7_TAM} bytes.' if si else
        f'⚠ No cabe entre los compilados (banco 7: {len(datos)} de {BANCO7_TAM} bytes): se dibuja con la '
        'rutina normal, unas 3 veces más lenta. Usa menos fotogramas o un tamaño menor.')

def valores_inercia(p):
    """Inercia del jugador en plataformas (0 = sin inercia, 1-10 = cada vez más resbaladiza):
    (aceleración, frenada) en 1/16 de píxel por fotograma. Con k, tarda unos 3k fotogramas en
    alcanzar la velocidad máxima y otros tantos en pararse."""
    k = max(0, min(10, int(p['jugador'].get('inercia', 0) or 0)))
    if not plataformas(p) or not k: return 0, 0
    vmax = 16 * max(1, min(4, p['jugador'].get('velocidad', 2)))
    paso = max(1, min(63, -(-vmax // (3 * k))))
    return paso, paso

def actualizar(p):
    """Completa proyectos de versiones anteriores."""
    if 'scroll' not in p:
        p['scroll'] = scroll_defecto()
        p['scroll']['umbral'] = p.get('jugador', {}).get('umbral', 56)
    p['scroll'].setdefault('fisica', fisica_defecto())
    p['scroll'].setdefault('paso', 8)
    p['scroll'].setdefault('compilar_sprites', True)
    p['scroll'].setdefault('mezcla', False); p['scroll'].setdefault('color_sprites', False)
    p['scroll'].setdefault('gravedad', False); p['scroll'].setdefault('umbral_v', 48)
    p['scroll'].setdefault('colores', {'tinta': 7, 'papel': 0, 'brillo': 0})
    p['jugador'].setdefault('color', 0)
    for en in p.get('enemigos', []): en.setdefault('color', 0)
    p['jugador'].setdefault('arma', 'disparo'); p['jugador'].setdefault('alcance', 12)
    p['jugador'].setdefault('pisar', False)
    p['jugador'].setdefault('inercia', 0)
    p['jugador'].setdefault('laser', laser_defecto())
    for k, v in laser_defecto().items(): p['jugador']['laser'].setdefault(k, v)
    estrategia(p)
    for t in p.get('tiles', []):
        t.setdefault('plataforma', False); t.setdefault('mortal', False)
        for k, v in (('rompible', False), ('fragil', False), ('objeto', False), ('tras', 0), ('puntos', 0),
                     ('accion', 'puntos'), ('valor', 1), ('mensaje', '')):
            t.setdefault(k, v)
    for t in p.get('tiles', []):
        t.setdefault('solido', False); t.setdefault('detiene', False)
    for i, en in enumerate(p.get('enemigos', [])):
        base = enemigo_defecto(en.get('nombre', f'Enemigo {i}'), en.get('tamano', '16x16'), en.get('fotogramas'))
        base.update({k: v for k, v in en.items() if k != 'demo'})
        p['enemigos'][i] = base
    if 'niveles' not in p:
        p['niveles'] = [{'nombre': 'Fase 1', 'mapa': p.pop('mapa', ejemplo.mapa_ejemplo()),
                         'apariciones': p.pop('apariciones', [])}]
    p.setdefault('balas', ejemplo.balas_ejemplo())
    for quien, vel in (('jugador', 4), ('enemigo', 2)):
        b = p['balas'][quien]
        if b.get('tamano') not in graficos.TAMANOS_BALA: b['tamano'] = '8x8'
        b.setdefault('velocidad', vel)
    for en in p.get('enemigos', []):
        en.setdefault('puntos', 100); en.setdefault('vel_anim', 4); en.setdefault('voltear', False)
    if 'jugador' in p:
        p['jugador'].setdefault('vel_anim', 4)
        p['jugador'].setdefault('quieto', {}); p['jugador'].setdefault('disparo', {})
    if 'partida' not in p:
        p['partida'] = partida_defecto()
    p['partida'].setdefault('musica', {'menu': None, 'juego': None})
    p['partida'].setdefault('efectos', dict(sonido.POR_DEFECTO))
    p['partida'].setdefault('efectos_propios', {})
    p['partida'].setdefault('a_la_vez', dict(A_LA_VEZ))
    p.setdefault('optimizar', True)
    if 'jugador' in p:
        p['jugador'].setdefault('cadencia', 6)
    if multidir(p):
        for nv in p['niveles']:
            rejilla(nv, factor(p)); nv['inicio'] = list(inicio_rejilla(nv, factor(p))); nv.setdefault('relleno', 0)
    p['version'] = 10
    return p

def horizontal(p):
    """Mapa horizontal (10 tiles de alto): modos horizontal y plataformas."""
    return p['scroll']['direccion'] in ('horizontal', 'plataformas')

def pantallas(p):
    """Pantalla a pantalla (sin scroll): el mapa es una rejilla de salas."""
    return p['scroll']['direccion'] == 'pantallas'

def libre(p):
    """Scroll libre en 8 direcciones, píxel a píxel, con el fondo de dos colores."""
    return p['scroll']['direccion'] == 'libre'

def multidir(p):
    """Modos con mapa en dos dimensiones (rejilla de pantallas): pantalla a pantalla y libre."""
    return p['scroll']['direccion'] in ('pantallas', 'libre')

def plataformas(p):
    d = p['scroll']['direccion']
    return d == 'plataformas' or (d in ('pantallas', 'libre') and bool(p['scroll'].get('gravedad')))

# ---------------- tiles de 8x8 ----------------
# Con tiles de 8x8 (p['tiles8']), cada tile del proyecto es un carácter: 'pix' de 8 filas de 8 y 'atr'
# con un solo color, y el mapa tiene el doble de celdas en cada eje (también las posiciones de los
# enemigos). Al generar, cada grupo de 2x2 caracteres que aparece en algún mapa se convierte en un
# tile de 16x16 del motor (como mucho 256, o 128 en el scroll fino horizontal); el motor mira los
# choques, los objetos y los cambios carácter a carácter con las tablas META (los 4 caracteres de cada
# tile) y TRASM (el tile que queda al cambiar cada uno de sus cuartos).
PROPS_JUNTAS = ('solido', 'detiene', 'plataforma', 'mortal', 'rompible', 'fragil', 'objeto', 'profundidad')

def tile8_vacio(atr=0x07):
    return {'pix': ['.' * 8 for _ in range(8)], 'atr': [atr], 'solido': False, 'detiene': False}

def _tile_de_cuartos(chars, k):
    """Tile de 16x16 con los caracteres k = (arriba-izq, arriba-dcha, abajo-izq, abajo-dcha)."""
    cs = [chars[c] for c in k]
    pix = [cs[(y // 8) * 2]['pix'][y % 8] + cs[(y // 8) * 2 + 1]['pix'][y % 8] for y in range(16)]
    t = {'pix': pix, 'atr': [c['atr'][0] for c in cs], '_cuartos': tuple(k)}
    for clave in PROPS_JUNTAS: t[clave] = any(c.get(clave) for c in cs)
    for clave in ('linea_tras', 'linea_ante'):        # las líneas del primer cuarto que tenga
        for q, c in enumerate(cs):
            l = c.get(clave)
            if l and c.get('profundidad'):
                dx, dy = (q % 2) * 8, (q // 2) * 8
                t[clave] = dict(l, p=[l['p'][0] + dx, l['p'][1] + dy, l['p'][2] + dx, l['p'][3] + dy]); break
    for c in cs:                     # para el generador (objetos en el mapa, enemigos apoyados...)
        if cambia(c):
            for clave in ('accion', 'valor', 'mensaje', 'puntos', 'tras', 'llave', 'columna'):
                if clave in c: t[clave] = c[clave]
            break
    return t

def expandir_t8(p):
    """Proyecto equivalente con tiles de 16x16 (los grupos de 2x2 caracteres) para el generador.
    Sin tiles de 8x8, el mismo proyecto. Lleva '_t8': caracteres y tablas META y TRASM."""
    if not p.get('tiles8'): return p
    chars = p['tiles']
    metas, lista = {(0, 0, 0, 0): 0}, [(0, 0, 0, 0)]
    def meta(k):
        if k not in metas: metas[k] = len(lista); lista.append(k)
        return metas[k]
    niveles = []
    for nv in p['niveles']:
        m = nv['mapa']; H, W = len(m) // 2, (len(m[0]) // 2 if m else 0)
        n2 = dict(nv)
        n2['mapa'] = [[meta((m[2 * y][2 * x], m[2 * y][2 * x + 1], m[2 * y + 1][2 * x], m[2 * y + 1][2 * x + 1]))
                       for x in range(W)] for y in range(H)]
        vistas, ap = set(), []
        for a in nv['apariciones']:
            b = {'tipo': a['tipo'], 'f': a['f'] // 2, 'c': a['c'] // 2}
            if (b['f'], b['c']) not in vistas: vistas.add((b['f'], b['c'])); ap.append(b)
        n2['apariciones'] = ap
        if 'relleno' in nv:
            r = nv['relleno'] if 0 <= nv['relleno'] < len(chars) else 0
            n2['relleno'] = meta((r, r, r, r))
        if 'pantallas' in nv: n2['pantallas'] = [list(f) for f in nv['pantallas']]
        niveles.append(n2)
    trasm, i = [], 0                 # cierre: los tiles que aparecen al cambiar caracteres
    while i < len(lista):
        k = lista[i]; fila = []
        for q in range(4):
            c = chars[k[q]] if k[q] < len(chars) else {}
            t = c.get('tras', 0)
            if cambia(c) and 0 <= t < len(chars) and t != k[q]:
                k2 = list(k); k2[q] = t; fila.append(meta(tuple(k2)))
            else: fila.append(i)
        trasm.append(fila); i += 1
    q = dict(p)
    q['tiles8'] = False
    q['tiles'] = [_tile_de_cuartos(chars, k) for k in lista]
    q['niveles'] = niveles
    q['_t8'] = {'chars': chars, 'meta': bytes(c for k in lista for c in k),
                'trasm': bytes(min(255, v) for f in trasm for v in f), 'sig': trasm}
    return q

def props_tiles(p):
    """Lista de tiles con las propiedades que lee el motor (con 8x8, los caracteres)."""
    return p['_t8']['chars'] if '_t8' in p else p['tiles']

def a_tiles8(p):
    """Pasa el proyecto a tiles de 8x8: cada tile de 16x16 se parte en sus 4 caracteres (los repetidos se
    juntan) y el mapa y los enemigos pasan a tener el doble de celdas en cada eje."""
    if p.get('tiles8'): return
    chars, idx, cuartos = [], {}, []
    for t in p['tiles']:
        k = []
        for q in range(4):
            fy, fx = (q // 2) * 8, (q % 2) * 8
            c = {key: v for key, v in t.items() if key not in ('pix', 'atr', 'linea_tras', 'linea_ante')}
            for clave in ('linea_tras', 'linea_ante'):       # las líneas, movidas al cuarto
                l = t.get(clave)
                if l and t.get('profundidad'):
                    x0, y0, x1, y1 = l['p']
                    c[clave] = dict(l, p=[x0 - fx, y0 - fy, x1 - fx, y1 - fy])
            c['pix'] = [t['pix'][fy + y][fx:fx + 8] for y in range(8)]
            c['atr'] = [t['atr'][q]]
            firma = (tuple(c['pix']), c['atr'][0], tuple(sorted((a, str(b)) for a, b in c.items() if a not in ('pix', 'atr'))))
            if firma not in idx: idx[firma] = len(chars); chars.append(c)
            k.append(idx[firma])
        cuartos.append(k)
    for t, k in zip(p['tiles'], cuartos):
        if cambia(t) and 0 <= t.get('tras', 0) < len(cuartos):
            for q in range(4): chars[k[q]]['tras'] = cuartos[t['tras']][q]
    if len(chars) > 256: raise ValueError(f'Salen {len(chars)} caracteres distintos (máximo 256).')
    for nv in p['niveles']:
        m = nv['mapa']
        nv['mapa'] = [[cuartos[v][(y % 2) * 2 + x % 2] for x in range(len(m[0]) * 2) for v in [m[y // 2][x // 2]]]
                      for y in range(len(m) * 2)]
        nv['apariciones'] = [{'tipo': a['tipo'], 'f': a['f'] * 2, 'c': a['c'] * 2} for a in nv['apariciones']]
        if 'relleno' in nv and 0 <= nv['relleno'] < len(cuartos): nv['relleno'] = cuartos[nv['relleno']][0]
    p['tiles'] = chars
    p['tiles8'] = True

def de_tiles8(p):
    """Vuelve a tiles de 16x16: cada grupo de 2x2 caracteres usado pasa a ser un tile (con las propiedades
    juntadas de sus caracteres: sólido si alguno lo es...)."""
    if not p.get('tiles8'): return
    q = expandir_t8(p)
    for t in q['tiles']: t.pop('_cuartos', None)
    p['tiles'] = q['tiles']; p['niveles'] = q['niveles']; p['tiles8'] = False

# ---------------- tiles de profundidad ----------------
# Un tile de profundidad tapa a los personajes salvo que una línea diga otra cosa (ver el manual):
#   'linea_tras': si el borde elegido del personaje queda por debajo de ella, manda el personaje;
#   'linea_ante': si queda por debajo o en ella, manda el tile (y si está por encima, el personaje).
# Cada línea: {'p': [x0, y0, x1, y1] (píxeles del tile; pueden salirse del tile hasta un tile más
# por cada lado), 'borde': 0 inferior, 1 superior, 2 izquierdo, 3 derecho, 'pasable': True/False,
# 'invertir': False/True}. El lado que cuenta como «por debajo»: debajo de la línea (bordes inferior y
# superior) o a su derecha (izquierdo y derecho); con 'invertir', encima o a su izquierda.
BORDES = ('inferior', 'superior', 'izquierdo', 'derecho')

def valores_linea(l, lado=16):
    """16 valores de la línea: su altura en cada columna (bordes inferior y superior) o su columna en
    cada fila (izquierdo y derecho). Fuera del trozo dibujado, la del extremo más cercano."""
    x0, y0, x1, y1 = l['p']
    if l.get('borde', 0) >= 2: x0, y0, x1, y1 = y0, x0, y1, x1      # x en función de y
    if x0 > x1: x0, y0, x1, y1 = x1, y1, x0, y0
    res = []
    for x in range(16):
        xx = min(max(x, x0), x1)
        v = y0 if x1 == x0 else y0 + (y1 - y0) * (xx - x0) / (x1 - x0)
        res.append(int(round(v)) & 0xFF)
    return res

def bytes_linea(l, lado=16):
    if not l: return bytes(17)
    op = 0x80 | (l.get('borde', 0) & 3) | (0 if l.get('pasable', True) else 4) | (8 if l.get('invertir') else 0)
    return bytes([op] + valores_linea(l, lado))

def tabla_profundidad(p):
    """(tabla, FLG): número de entradas y, por cada tile (o carácter) de profundidad, su número y sus
    dos líneas; FLG: bits 0-3 bordes con líneas que no se traspasan, bit 4 hay profundidad."""
    lado = 8 if '_t8' in p else 16
    d, flg, n = bytearray(), 0, 0
    for i, t in enumerate(props_tiles(p)):
        if not t.get('profundidad'): continue
        n += 1; flg |= 0x10
        d += bytes([i]) + bytes_linea(t.get('linea_tras'), lado) + bytes_linea(t.get('linea_ante'), lado)
        for l in (t.get('linea_tras'), t.get('linea_ante')):
            if l and not l.get('pasable', True): flg |= 1 << (l.get('borde', 0) & 3)
    return bytes([n]) + bytes(d), flg

def hay_profundidad(p):
    return any(t.get('profundidad') for t in p['tiles'])

def max_pares_mem(p):
    """Memoria para los bloques del scroll fino: si hay tiles de profundidad, sus rutinas van en el final."""
    return MAX_PARES_MEM - (0x600 if hay_profundidad(p) else 0)

# ---------------- mapa en dos dimensiones (pantalla a pantalla y scroll libre) ----------------
PANT_ANCHO, PANT_ALTO = 12, 10            # una pantalla: 12 x 10 tiles (192 x 160 píxeles, el área entera)
MAX_REJILLA = 16                          # hasta 16 x 16 pantallas por fase
COPIAS_LIBRE = (0xDB00, 0xF900)           # banco 7: dos de las cuatro copias del fondo del scroll libre

def factor(p):
    """Celdas del mapa por cada tile de 16 píxeles, en cada eje: 2 con tiles de 8x8, 1 con los de 16x16."""
    return 2 if p.get('tiles8') else 1

def lado_tile(p):
    return 8 if p.get('tiles8') else 16

def rejilla(nv, f=1):
    """Rejilla de pantallas de una fase en dos dimensiones: filas de True (hay pantalla) / False.
    f: factor (2 si el mapa es de tiles de 8x8)."""
    m = nv['mapa']
    gh, gw = max(1, len(m) // (PANT_ALTO * f)), max(1, len(m[0]) // (PANT_ANCHO * f))
    g = nv.get('pantallas')
    if not g or len(g) != gh or len(g[0]) != gw:
        g = [[bool(g[y][x]) if g and y < len(g) and x < len(g[0]) else True for x in range(gw)] for y in range(gh)]
        nv['pantallas'] = g
    return g

def inicio_rejilla(nv, f=1):
    """(columna, fila) de la pantalla en la que se empieza (la primera que exista si no se ha elegido)."""
    g = rejilla(nv, f)
    ini = nv.get('inicio')
    if ini and 0 <= ini[1] < len(g) and 0 <= ini[0] < len(g[0]) and g[ini[1]][ini[0]]:
        return tuple(ini)
    for y, fila in enumerate(g):
        for x, v in enumerate(fila):
            if v: return (x, y)
    return (0, 0)

def nivel_2d(nombre, gw=3, gh=2, tile=0, relleno=1, f=1):
    return {'nombre': nombre, 'mapa': [[tile] * (gw * PANT_ANCHO * f) for _ in range(gh * PANT_ALTO * f)],
            'apariciones': [], 'pantallas': [[True] * gw for _ in range(gh)], 'inicio': [0, 0],
            'relleno': relleno}

def fijar_rejilla(nv, gw, gh, tile=0, k=1):
    """Cambia el tamaño de la rejilla (por la derecha y por abajo). Las pantallas nuevas existen.
    k: factor (2 con tiles de 8x8)."""
    g = rejilla(nv, k); m = nv['mapa']; PA, PL = PANT_ANCHO * k, PANT_ALTO * k
    nm = [[m[f][c] if f < len(m) and c < len(m[0]) else tile for c in range(gw * PA)]
          for f in range(gh * PL)]
    ng = [[g[y][x] if y < len(g) and x < len(g[0]) else True for x in range(gw)] for y in range(gh)]
    nv['mapa'], nv['pantallas'] = nm, ng
    nv['apariciones'] = [a for a in nv['apariciones'] if a['f'] < gh * PL and a['c'] < gw * PA]
    nv['inicio'] = list(inicio_rejilla(nv, k))

def a_rejilla(nv, era_horizontal, k=1):
    """Convierte una fase de una tira (horizontal o vertical) en una rejilla de pantallas."""
    m = nv['mapa']
    PANT_ANCHO, PANT_ALTO = globals()['PANT_ANCHO'] * k, globals()['PANT_ALTO'] * k
    if era_horizontal:
        gw = max(1, -(-len(m[0]) // PANT_ANCHO)); gh = 1
        nm = [[fila[c] if c < len(fila) else 0 for c in range(gw * PANT_ANCHO)] for fila in m]
        ap = list(nv['apariciones'])
    else:                                  # el vertical empieza abajo: se rellena por arriba
        gh = max(1, -(-len(m) // PANT_ALTO)); gw = 1
        falta = gh * PANT_ALTO - len(m)
        nm = [[0] * PANT_ANCHO for _ in range(falta)] + [list(f) for f in m]
        ap = [{'tipo': a['tipo'], 'f': a['f'] + falta, 'c': a['c']} for a in nv['apariciones']]
    nv['mapa'], nv['apariciones'] = nm, ap
    nv['pantallas'] = [[True] * gw for _ in range(gh)]
    nv['inicio'] = [0, gh - 1] if not era_horizontal else [0, 0]
    nv.setdefault('relleno', 0)

def de_rejilla(nv, a_horizontal, k=1):
    """De rejilla a tira: la primera fila de pantallas (horizontal) o la primera columna (vertical)."""
    m = nv['mapa']
    PANT_ANCHO, PANT_ALTO = globals()['PANT_ANCHO'] * k, globals()['PANT_ALTO'] * k
    if a_horizontal:
        nv['mapa'] = [list(f) for f in m[:PANT_ALTO]]
        nv['apariciones'] = [a for a in nv['apariciones'] if a['f'] < PANT_ALTO]
    else:
        nv['mapa'] = [list(f[:PANT_ANCHO]) for f in m]
        nv['apariciones'] = [a for a in nv['apariciones'] if a['c'] < PANT_ANCHO]
    for k in ('pantallas', 'inicio'): nv.pop(k, None)

def mapa_libre(p, nv):
    """(ancho W, alto H, desplazamiento k, bytes) del mapa del scroll libre: por filas, cada fila de 2^k
    bytes (para que el motor multiplique con desplazamientos). Las pantallas que no existen se rellenan
    con el tile de relleno."""
    g = rejilla(nv); m = nv['mapa']
    W, H = len(g[0]) * PANT_ANCHO, len(g) * PANT_ALTO
    k = max(4, (W - 1).bit_length())
    rell = nv.get('relleno', 0)
    if not 0 <= rell < len(p['tiles']): rell = 0
    d = bytearray()
    for f in range(H):
        fila = [m[f][c] if g[f // PANT_ALTO][c // PANT_ANCHO] else rell for c in range(W)]
        d += bytes(fila) + bytes((1 << k) - W)
    return W, H, k, bytes(d)

def fisica_defecto():
    return {'altura': 40, 'subida': 10, 'caida_max': 6}

def tablas_salto(f):
    """Subida (píxeles por fotograma, hasta la cumbre) y caída (con la misma gravedad, hasta caida_max)."""
    H, T = f['altura'], f['subida']
    v0 = 2 * H / T; g = v0 / T
    y = lambda t: v0 * t - g * t * t / 2
    subida = [round(y(t)) - round(y(t - 1)) for t in range(1, T + 1)]
    subida = [d for d in subida if d > 0][:23]
    d = lambda t: g * t * t / 2
    caida = [max(1, min(f['caida_max'], round(d(t)) - round(d(t - 1)))) for t in range(1, 17)]
    return subida, caida

def convertir_apariciones(apariciones, mapa_antes, a_horizontal, k=1):
    """Gira las posiciones de los enemigos igual que el mapa."""
    MAPA_ALTO, MAPA_ANCHO, AREA_ALTO = globals()['MAPA_ALTO'] * k, globals()['MAPA_ANCHO'] * k, globals()['AREA_ALTO'] * k
    res = []
    for a in apariciones:
        if a_horizontal:
            n = len(mapa_antes)
            f, c = a['c'], n - 1 - a['f']
        else:
            n = len(mapa_antes[0]); largo = max(n, AREA_ALTO // 2)
            f, c = largo - 1 - a['c'], a['f']
        if a_horizontal and f >= MAPA_ALTO: continue
        if not a_horizontal and c >= MAPA_ANCHO: continue
        res.append({'tipo': a['tipo'], 'f': f, 'c': c})
    return res

def convertir_mapa(mapa, a_horizontal, k=1):
    """Gira el mapa al cambiar de dirección: lo que estaba abajo (inicio vertical)
    pasa a la izquierda (inicio horizontal), y al revés. k: factor (2 con tiles de 8x8)."""
    MAPA_ALTO, MAPA_ANCHO = globals()['MAPA_ALTO'] * k, globals()['MAPA_ANCHO'] * k
    AREA_ANCHO, AREA_ALTO = globals()['AREA_ANCHO'] * k, globals()['AREA_ALTO'] * k
    if a_horizontal:                      # filas de 12 -> 10 filas de N columnas
        n = len(mapa)
        largo = max(n, AREA_ANCHO // 2)
        return [[mapa[n - 1 - c][f] if c < n else 0 for c in range(largo)]
                for f in range(MAPA_ALTO)]
    n = len(mapa[0])                      # 10 filas de N columnas -> N filas de 12
    largo = max(n, AREA_ALTO // 2)
    return [[mapa[f][largo - 1 - y] if f < MAPA_ALTO and largo - 1 - y < n else 0
             for f in range(MAPA_ANCHO)] for y in range(largo)]

# ---------------- scroll horizontal fino por bloques pre-desplazados ----------------
MAX_PARES_MEM = 0x1A00            # 6656 bytes en memoria baja para los bloques
MAX_PARES = 175                   # límite de la tabla de colores

def modo_bloques(p):
    """Scroll horizontal (o de plataformas) con paso de 1, 2 o 4 píxeles."""
    return horizontal(p) and p['scroll'].get('paso', 8) < 8

def _media_col(p, mapa, f, c):
    """(tile, mitad) de la columna de caracteres c en la fila de tiles f."""
    c = max(0, min(c, len(mapa[0]) * 2 - 1))
    return (mapa[f][c // 2], c % 2)

def _vacia(p, mc):
    t, m = mc
    return all(f[m * 8:m * 8 + 8] == '.' * 8 for f in p['tiles'][t]['pix'])

def _color_par(p, par):
    (ta, ma), (tb, mb) = par
    A, B = p['tiles'][ta], p['tiles'][tb]
    col = [A['atr'][ma], A['atr'][2 + ma], B['atr'][mb], B['atr'][2 + mb]]
    # una media columna sin píxeles solo aporta su papel: si el papel coincide, toma el color de su
    # vecina, y así el color no salta a mitad de camino cuando el borde de un tile pasa por la casilla
    for fila in (0, 1):
        va = all(f[ma * 8:ma * 8 + 8] == '.' * 8 for f in A['pix'][fila * 8:fila * 8 + 8])
        vb = all(f[mb * 8:mb * 8 + 8] == '.' * 8 for f in B['pix'][fila * 8:fila * 8 + 8])
        a, b = col[fila], col[2 + fila]
        if va and vb: col[2 + fila] = a                # sin píxeles: el color no puede partirse; no cambia a mitad
        elif va and not vb and (a & 0x78) == (b & 0x78): col[fila] = b
        elif vb and not va and (a & 0x78) == (b & 0x78): col[2 + fila] = a
    return tuple(col)

ACCIONES = ['puntos', 'vida', 'energia', 'fase', 'ganar', 'perder', 'mensaje', 'guardar', 'altar', 'puerta']
ACCIONES_REGLA = ACCIONES[:8]           # una regla puede dar un elemento, pero no ser un altar ni una puerta
SIN_MSG = 15                            # entrada de la tabla de mensajes que siempre está vacía
MAX_ELEMENTOS, MAX_REGLAS = 8, 12

def estrategia(p):
    e = p.setdefault('estrategia', {})
    e.setdefault('elementos', []); e.setdefault('reglas', []); e.setdefault('falta', '')
    e.setdefault('hud', {'activo': False, 'fila': 23, 'col': 22, 'atr': 0x46})
    return e

def cambia(t):
    """El tile puede cambiar durante la partida (romperse o recogerse). Las puertas no cambian."""
    if t.get('objeto') and t.get('accion') == 'puerta' and not (t.get('rompible') or t.get('fragil')):
        return False
    return bool(t.get('rompible') or t.get('fragil') or t.get('objeto'))

def es_puerta(t):
    return bool(t.get('objeto')) and t.get('accion') == 'puerta'

def personajes(p):
    """Tipos de enemigo que son personajes con los que se habla: {tipo: número de personaje (1..15)}."""
    res = {}
    for i, en in enumerate(p['enemigos']):
        if en.get('comportamiento') == 'personaje' and len(res) < 15: res[i] = len(res) + 1
    return res

def mensaje_valido(m):
    return all(len(l) <= 20 for l in (m or '').split('|')) and (m or '').count('|') <= 1

def lineas_mensaje(m):
    """Un mensaje puede tener dos líneas separadas por '|' (20 letras cada una)."""
    return (m or '').split('|')[:2]

def variantes(p, n):
    """Tiles en los que puede convertirse el tile n (él incluido), siguiendo la cadena de «tras»."""
    if '_t8' in p:                  # tiles de 8x8: todos a los que se llega cambiando sus cuartos
        vistos, pend = [n], [n]
        while pend:
            for v in p['_t8']['sig'][pend.pop()]:
                if v not in vistos: vistos.append(v); pend.append(v)
        return vistos
    vistos = [n]
    while cambia(p['tiles'][vistos[-1]]):
        sig = p['tiles'][vistos[-1]].get('tras', 0)
        if sig in vistos or sig >= len(p['tiles']): break
        vistos.append(sig)
    return vistos

def pares_proyecto(p):
    """Índice de cada pareja (media columna izquierda, media columna derecha) de todas las fases.
    La 0 es la pareja vacía (sin píxeles) más frecuente: el motor no la dibuja nunca, solo borra
    las casillas que se ensuciaron. Las demás parejas sin píxeles pero de otro color, sí se dibujan."""
    cuenta = {}
    for nv in p['niveles']:
        m = nv['mapa']
        for f in range(MAPA_ALTO):
            for c in range(len(m[0]) * 2):
                (ta, ma), (tb, mb) = _media_col(p, m, f, c), _media_col(p, m, f, c + 1)
                cuenta[((ta, ma), (tb, mb))] = cuenta.get(((ta, ma), (tb, mb)), 0) + 1
                for va in variantes(p, ta):            # también las parejas que aparecen al romper/recoger
                    for vb in variantes(p, tb):
                        if (va, vb) != (ta, tb) and (ta != tb or va == vb or c % 2 == 0):
                            cuenta.setdefault(((va, ma), (vb, mb)), 0)
    vacias = {}
    for par, n in cuenta.items():
        if _vacia(p, par[0]) and _vacia(p, par[1]):
            col = _color_par(p, par); vacias[col] = vacias.get(col, 0) + n
    color0 = max(vacias, key=vacias.get) if vacias else None
    # las parejas que se ven igual (mismos píxeles y colores) comparten número aunque vengan de tiles distintos
    def firma(par):
        (ta, ma), (tb, mb) = par
        A, B = p['tiles'][ta], p['tiles'][tb]
        return (tuple(f[ma * 8:ma * 8 + 8] for f in A['pix']), tuple(f[mb * 8:mb * 8 + 8] for f in B['pix']),
                _color_par(p, par))
    indices, por_firma, siguiente = {}, {}, 1
    # primero las parejas sin píxeles (solo color): el motor no las dibuja, como la vacía
    sin_pix = lambda q: _vacia(p, q[0]) and _vacia(p, q[1])
    for par in sorted(cuenta, key=lambda q: (not sin_pix(q), -cuenta[q])):
        if color0 is not None and _vacia(p, par[0]) and _vacia(p, par[1]) and _color_par(p, par) == color0:
            indices[par] = 0
            continue
        f = firma(par)
        if f not in por_firma:
            por_firma[f] = siguiente; siguiente += 1
        indices[par] = por_firma[f]
    return indices

def parejas_sin_pixeles(p, pares):
    """Cuántos índices iniciales (0 incluido) corresponden a parejas sin píxeles."""
    rep = representantes(p, pares); k = 1
    while k < len(rep) and rep[k] is not None and _vacia(p, rep[k][0]) and _vacia(p, rep[k][1]): k += 1
    return k

def representantes(p, pares):
    """Una pareja por índice, en orden (la 0 es la vacía; si no hay, un hueco vacío)."""
    rep = {}
    for par, k in pares.items():
        rep.setdefault(k, par)
    n = max(rep) + 1 if rep else 1
    return [rep.get(k) for k in range(n)]

def _byte_tile(t, linea, mitad, fase=0):
    return graficos.fila_bits(t['pix'][linea][mitad * 8:mitad * 8 + 8], linea, fase, mitad * 8)

def mezcla(p):
    """Modo mezcla activo (solo con scroll horizontal fino)."""
    return bool(p['scroll'].get('mezcla')) and modo_bloques(p)

def color_sprites(p):
    return bool(p['scroll'].get('color_sprites')) and (modo_bloques(p) or libre(p))

def atr_color(c):
    """Color propio de un personaje -> byte para el motor (brillo + tinta, 0 = el del fondo)."""
    return 0 if not c else (int(c) & 0x47)

def datos_bloques(p, pares, fase=0):
    """Bloques: por pareja, una versión de 16 bytes por posición de desplazamiento (0, paso, 2*paso...).
    Colores: cuatro tablas (arriba-izquierda, abajo-izquierda, arriba-derecha, abajo-derecha)."""
    paso = p['scroll']['paso']
    bloques, colores = bytearray(), []
    for par in representantes(p, pares):
        if par is None:                       # no hay ninguna pareja vacía: hueco
            bloques += bytes(16 * (8 // paso)); colores.append((0, 0, 0, 0)); continue
        (ta, ma), (tb, mb) = par
        A, B = p['tiles'][ta], p['tiles'][tb]
        for f in range(0, 8, paso):
            for l in range(16):
                x, y = _byte_tile(A, l, ma, fase), _byte_tile(B, l, mb, fase)
                bloques.append(((x << f) | (y >> (8 - f))) & 0xFF if f else x)
        colores.append(_color_par(p, par))
    tablas = b''.join(bytes(c[i] for c in colores) for i in range(4))
    return bytes(bloques), tablas

LONG_COMPILADO = 50               # bytes de código por versión de un bloque compilado

def _codigo_bloque(bytes16, largo=None):
    """Bloque compilado: escribe sus 16 bytes en pantalla. Entra con HL = mitad superior,
    DE = mitad inferior y A = 0. Cada línea: ld (hl),n (o ld (hl),a si es 0) e inc h."""
    c = bytearray()
    for mitad in (0, 1):
        for l in range(8):
            v = bytes16[mitad * 8 + l]
            c += bytes([0x77]) if v == 0 else bytes([0x36, v])
            if l < 7: c.append(0x24)                       # inc h
        if mitad == 0: c.append(0xEB)                      # ex de,hl
    c.append(0xC9)                                         # ret
    return bytes(c).ljust(largo or 0, b'\x00')

def largo_compilado(bloques):
    """Bytes por versión: la del bloque más largo (todas ocupan lo mismo para poder indexarlas)."""
    return max((len(_codigo_bloque(bloques[i:i + 16])) for i in range(0, len(bloques), 16)), default=1)

def compilar_bloques(bloques):
    """Convierte los bloques de datos (16 bytes por versión) en código, versión a versión."""
    L = largo_compilado(bloques)
    return b''.join(_codigo_bloque(bloques[i:i + 16], L) for i in range(0, len(bloques), 16))

def usa_compilados(p, n_pares=None):
    """Los bloques compilados ocupan unas tres veces más: solo si caben en memoria baja."""
    if not modo_bloques(p): return False
    p = expandir_t8(p)
    pares = pares_proyecto(p)
    if n_pares is None: n_pares = len(representantes(p, pares))
    bloques, _ = datos_bloques(p, pares)
    if mezcla(p):
        bloques += datos_bloques(p, pares, 1)[0]
        tam = _pag(n_pares * (8 // p['scroll']['paso']) * largo_compilado(bloques))
        return 2 * tam <= max_pares_mem(p)
    return n_pares * (8 // p['scroll']['paso']) * largo_compilado(bloques) <= max_pares_mem(p)

def _pag(n):
    return (n + 255) // 256 * 256

def bloques_memoria(p, pares):
    """Bloques tal como se copian a memoria baja y, en modo mezcla, separación (en páginas)
    entre las versiones A (pantalla 5) y B (pantalla 7). Devuelve (bytes, compilados, largo_version, delta)."""
    n = len(representantes(p, pares))
    bloq_a, cols = datos_bloques(p, pares)
    bloq_b = datos_bloques(p, pares, 1)[0] if mezcla(p) else b''
    comp = usa_compilados(p, n)
    L = largo_compilado(bloq_a + bloq_b) if comp else 0
    if comp:
        bloq_a = b''.join(_codigo_bloque(bloq_a[i:i + 16], L) for i in range(0, len(bloq_a), 16))
        if bloq_b:
            bloq_b = b''.join(_codigo_bloque(bloq_b[i:i + 16], L) for i in range(0, len(bloq_b), 16))
    if not bloq_b:
        return bloq_a, cols, comp, L, 0
    return bloq_a.ljust(_pag(len(bloq_a)), b'\x00') + bloq_b, cols, comp, L, _pag(len(bloq_a)) // 256

def mapa_pares(p, n, pares):
    """Por columna de caracteres, los índices de pareja de sus 10 filas de tiles."""
    m = p['niveles'][n]['mapa']
    return bytes(pares[(_media_col(p, m, f, c), _media_col(p, m, f, c + 1))]
                 for c in range(len(m[0]) * 2) for f in range(MAPA_ALTO))

COSTE_LIBRE = 98000                 # scroll libre: volcado de las 4 copias del fondo y filas o columnas nuevas

def ritmo(p):
    """Interrupciones por fotograma de juego (cadencia fija): 2 = 25 fps, 3 = 16,7 fps."""
    if mezcla(p): return 1                  # las dos pantallas se alternan en cada interrupción
    if p['scroll'].get('ritmo'): return p['scroll']['ritmo']
    if libre(p):
        return 2 if COSTE_LIBRE + coste_sprites(p) + 8000 <= 2 * 69888 else 3
    if not modo_bloques(p): return 2
    return 2 if coste_fondo(p) <= 95000 else 3

def coste_fondo(p):
    """Estimación del coste (ciclos) de dibujar el fondo en el tramo de 24 columnas más cargado de
    todas las fases: casillas con contenido (más caras si los bloques no van compilados) y vacías."""
    p = expandir_t8(p)
    pares = pares_proyecto(p)
    por_casilla = 350 if usa_compilados(p) else 520
    k = parejas_sin_pixeles(p, pares)             # las parejas sin píxeles no se dibujan
    peor = 0
    for n in range(len(p['niveles'])):
        mp = mapa_pares(p, n, pares)
        cols = [sum(1 for f in range(MAPA_ALTO) if mp[c * MAPA_ALTO + f] >= k) for c in range(len(mp) // MAPA_ALTO)]
        for c in range(max(1, len(cols) - AREA_ANCHO + 1)):
            peor = max(peor, sum(cols[c:c + AREA_ANCHO]))
    return peor * por_casilla + (AREA_ANCHO * MAPA_ALTO - peor) * 77

_ESPANOL = True                          # (lo fija repartir_bancos según la fuente del proyecto)

def tipo_fuente(p):
    """'espanola' (por defecto: la fuente propia del generador con tildes, ñ, ¿ y ¡), 'rom' o 'propia'."""
    pa = p['partida']
    if pa.get('fuente'): return 'propia'
    return 'rom' if pa.get('fuente_rom') else 'espanola'

def fuente_efectiva(p):
    """Los 768 bytes de la fuente que lleva el juego, o None para la de la ROM."""
    t = tipo_fuente(p)
    if t == 'propia': return bytes(p['partida']['fuente'])
    return fuente_es.datos() if t == 'espanola' else None

def a_ascii(texto):
    """Texto -> bytes del motor. Con la fuente española conserva tildes, ñ, ¿ y ¡; si no, las quita."""
    return fuente_es.codificar(texto, _ESPANOL)

def datos_textos(textos):
    d = bytearray()
    for t in textos:
        fila = max(0, min(23, int(t['fila']))); col = max(0, min(31, int(t['col'])))
        atr = (0x40 if t.get('brillo') else 0) | (int(t['tinta']) & 7)
        d += bytes([fila, col, atr]) + a_ascii(t['texto']) + b'\x00'
    d.append(0xFF)
    return bytes(d)

def pantalla_vacia(atr=0x07):
    return bytes(6144) + bytes([atr] * 768)

def marco_defecto(col, fila):
    """Pantalla negra con un recuadro alrededor del área de juego."""
    scr = bytearray(6144) + bytearray(768)
    def celda(cx, cy, patron, atr):
        if 0 <= cx < 32 and 0 <= cy < 24:
            for y in range(8):
                scr[dir_pixel(cy * 8 + y) + cx] = patron[y]
            scr[6144 + cy * 32 + cx] = atr
    lad = [0x55, 0xAA] * 4
    for cx in range(col - 1, col + AREA_ANCHO + 1):
        celda(cx, fila - 1, lad, 0x4D); celda(cx, fila + AREA_ALTO, lad, 0x4D)
    for cy in range(fila - 1, fila + AREA_ALTO + 1):
        celda(col - 1, cy, lad, 0x4D); celda(col + AREA_ANCHO, cy, lad, 0x4D)
    return bytes(scr)

def comprobar(p):
    """Devuelve una lista de problemas (vacía si todo está bien)."""
    if p.get('tiles8'):            # tiles de 8x8: lo propio, y lo demás con los grupos de 2x2
        e = []
        if not p['tiles']: return ['No hay tiles.']
        if len(p['tiles']) > 256: e.append('Máximo 256 tiles de 8x8.')
        if any(len(t['pix']) != 8 or any(len(f) != 8 for f in t['pix']) or len(t['atr']) != 1 for t in p['tiles']):
            e.append('Con tiles de 8x8, todos los tiles tienen que ser de 8x8 (un color cada uno).')
        for nv in p['niveles']:
            m = nv['mapa']
            if not m or len(m) % 2 or any(len(f) != len(m[0]) or len(f) % 2 for f in m):
                e.append(f'{nv["nombre"]}: con tiles de 8x8, el mapa tiene que tener un número par de filas y de columnas.')
            elif any(v >= len(p['tiles']) for f in m for v in f):
                e.append(f'{nv["nombre"]}: el mapa usa un tile que no existe.')
        if e: return e
        q = expandir_t8(p)
        e = _comprobar(q)
        if len(q['tiles']) > 256:
            e.append(f'Los mapas usan {len(q["tiles"])} grupos distintos de 2x2 tiles de 8x8 (contando los que salen al '
                     'romper o recoger): el motor admite 256. Repite más las mismas combinaciones.')
        elif modo_bloques(q) and len(q['tiles']) > 128:
            e.append(f'El scroll fino horizontal admite 128 grupos distintos de 2x2 tiles de 8x8 y los mapas usan '
                     f'{len(q["tiles"])} (contando los que salen al romper o recoger).')
        return [x for x in e if not x.startswith(('Máximo 256 tiles', 'El scroll fino horizontal admite como máximo 128'))]
    return _comprobar(p)

def _comprobar(p):
    e = []
    a = p['area']
    if not 0 <= a['col'] <= 7: e.append('La columna del área debe estar entre 0 y 7.')
    if not 0 <= a['fila'] <= 24 - AREA_ALTO: e.append(f'La fila del área debe estar entre 0 y {24 - AREA_ALTO}.')
    if not p['tiles']: e.append('No hay tiles.')
    if len(p['tiles']) > 256: e.append('Máximo 256 tiles.')
    sc = p['scroll']
    if not 1 <= len(p['niveles']) <= MAX_NIVELES: e.append(f'Hace falta de 1 a {MAX_NIVELES} fases.')
    for nv in p['niveles']:
        m, n = nv['mapa'], nv['nombre']
        if multidir(p):
            g = rejilla(nv); gh, gw = len(g), len(g[0])
            if not (1 <= gw <= MAX_REJILLA and 1 <= gh <= MAX_REJILLA):
                e.append(f'{n}: la rejilla de pantallas va de 1x1 a {MAX_REJILLA}x{MAX_REJILLA}.')
            elif len(m) != gh * PANT_ALTO or any(len(f) != gw * PANT_ANCHO for f in m):
                e.append(f'{n}: el mapa no coincide con la rejilla de pantallas.')
            if not any(any(f) for f in g): e.append(f'{n}: no tiene ninguna pantalla.')
            if libre(p):
                W, H, k, d = mapa_libre(p, nv)
                if len(d) + 36 * len(p['tiles']) > 15000:
                    e.append(f'{n}: el mapa ocupa {len(d)} bytes (cada fila se guarda con {1 << k} tiles); con '
                             'los tiles no cabe en un banco. Usa menos pantallas, sobre todo a lo ancho.')
                if not 0 <= nv.get('relleno', 0) < len(p['tiles']):
                    e.append(f'{n}: el tile de relleno no existe.')
            gx, gy = inicio_rejilla(nv)
            for a in nv['apariciones']:
                if 0 <= a['f'] < len(m) and 0 <= a['c'] < len(m[0]) and not g[a['f'] // PANT_ALTO][a['c'] // PANT_ANCHO]:
                    e.append(f'{n}: hay enemigos colocados en una pantalla que no existe.'); break
        elif horizontal(p):
            if len(m) != MAPA_ALTO: e.append(f'{n}: el mapa horizontal debe tener {MAPA_ALTO} filas de tiles.')
            elif len(m[0]) < AREA_ANCHO // 2: e.append(f'{n}: el mapa necesita al menos {AREA_ANCHO // 2} columnas.')
            elif any(len(f) != len(m[0]) for f in m): e.append(f'{n}: las filas del mapa tienen distinto largo.')
        else:
            if len(m) < AREA_ALTO // 2: e.append(f'{n}: el mapa necesita al menos {AREA_ALTO // 2} filas.')
            elif any(len(f) != MAPA_ANCHO for f in m): e.append(f'{n}: cada fila del mapa debe tener {MAPA_ANCHO} tiles.')
        if any(t >= len(p['tiles']) for fila in m for t in fila): e.append(f'{n}: el mapa usa un tile que no existe.')
        if len(nv['apariciones']) > MAX_APARICIONES: e.append(f'{n}: máximo {MAX_APARICIONES} enemigos colocados.')
        alto, ancho = len(m), len(m[0]) if m else 0
        for a in nv['apariciones']:
            if not 0 <= a['tipo'] < len(p['enemigos']):
                e.append(f'{n}: hay enemigos colocados de un tipo que ya no existe.'); break
            if not (0 <= a['f'] < alto and 0 <= a['c'] < ancho):
                e.append(f'{n}: hay enemigos colocados fuera del mapa.'); break
    if not 1 <= sc['vel_auto'] <= 50: e.append('Velocidad del scroll automático: 1 a 50 fotogramas por paso.')
    if sc.get('paso', 8) not in (1, 2, 4, 8): e.append('El paso del scroll debe ser 1, 2, 4 u 8 píxeles.')
    elif modo_bloques(p) and all(len(nv['mapa']) == MAPA_ALTO for nv in p['niveles']):
        n = len(representantes(p, pares_proyecto(p))); por_par = 16 * 8 // sc['paso']
        limite = min(MAX_PARES, (max_pares_mem(p) // 2 if mezcla(p) else max_pares_mem(p)) // por_par)
        if n > limite:
            e.append(f'El scroll fino de {sc["paso"]} px admite {limite} combinaciones distintas de columnas vecinas '
                     f'y las fases tienen {n}. Usa un paso mayor, repite más los mismos tiles juntos o usa paso 8.')
        if len(p['tiles']) > 128: e.append('El scroll fino horizontal admite como máximo 128 tiles.')
        elif any(cambia(t) for t in p['tiles']) and len(pares_proyecto(p)) > 255:
            e.append('Demasiadas combinaciones de tiles que cambian (rompibles u objetos) junto a otros tiles: '
                     'usa menos variedad alrededor de ellos.')
    if multidir(p) and sc.get('modo') == 'auto': e.append('Pantalla a pantalla y scroll libre no tienen modo automático.')
    if sc.get('mezcla') and not modo_bloques(p):
        e.append('El modo mezcla necesita scroll horizontal (o de plataformas) con paso de 1, 2 o 4 píxeles.')
    if sc.get('color_sprites') and not (modo_bloques(p) or libre(p)):
        e.append('El color propio de los personajes necesita scroll horizontal fino (paso 1, 2 o 4) o libre.')
    if plataformas(p):
        fi = sc['fisica']
        if not 8 <= fi['altura'] <= 120: e.append('Altura de salto: de 8 a 120 píxeles.')
        if not 3 <= fi['subida'] <= 23: e.append('Tiempo de subida del salto: de 3 a 23 fotogramas.')
        if not 1 <= fi['caida_max'] <= 8: e.append('Velocidad máxima de caída: de 1 a 8 píxeles.')
    j = p['jugador']
    if not j['fotogramas']: e.append('El jugador no tiene fotogramas.')
    w, h = graficos.TAMANOS[j['tamano']]
    if not 0 <= j['x'] <= 192 - w: e.append(f'X inicial del jugador: 0 a {192 - w}.')
    if not 0 <= j['y'] <= 160 - h: e.append(f'Y inicial del jugador: 0 a {160 - h}.')
    if libre(p):
        if not 0 <= sc['umbral'] <= (192 - w) // 2 - 4:
            e.append(f'Margen horizontal del scroll libre: 0 a {(192 - w) // 2 - 4} con este tamaño de jugador.')
        if not 0 <= sc.get('umbral_v', 48) <= (160 - h) // 2 - 4:
            e.append(f'Margen vertical del scroll libre: 0 a {(160 - h) // 2 - 4} con este tamaño de jugador.')
    elif sc['modo'] == 'sigue' and not pantallas(p):
        lado = 192 - w if horizontal(p) else 160 - h       # recorrido del jugador en el eje del scroll
        if not 0 <= sc['umbral'] <= lado - 8:
            e.append(f'Umbral de avance: 0 a {lado - 8} con este tamaño de jugador.')
        if sc['retroceso'] and sc['umbral'] + sc['umbral_ret'] > lado - 16:
            e.append(f'Los umbrales de avance y retroceso suman demasiado (máx. {lado - 16}): '
                     'el jugador provocaría los dos scrolls a la vez.')
    if not 1 <= j['velocidad'] <= 4: e.append('Velocidad del jugador: 1 a 4.')
    if len(p['enemigos']) > MAX_TIPOS: e.append(f'Máximo {MAX_TIPOS} tipos de enemigo.')
    for en in p['enemigos']:
        n = en['nombre']
        if not en['fotogramas']: e.append(f'{n}: sin fotogramas.')
        if en['comportamiento'] not in COMPORTAMIENTOS: e.append(f'{n}: comportamiento desconocido.')
        if not 1 <= en['velocidad'] <= 4: e.append(f'{n}: velocidad de 1 a 4.')
        if not 1 <= en['energia'] <= 99: e.append(f'{n}: energía de 1 a 99.')
        if not 0 <= en['cadencia'] <= 250: e.append(f'{n}: cadencia de 0 (no dispara) a 250.')
        if not 0 <= en.get('puntos', 0) <= 990 or en.get('puntos', 0) % 10: e.append(f'{n}: puntos de 0 a 990, de 10 en 10.')
    if not 1 <= j.get('cadencia', 6) <= 50: e.append('Cadencia de disparo del jugador: 1 a 50.')
    for nombre, fr in (p['partida'].get('efectos_propios') or {}).items():
        if not 1 <= len(fr) <= sonido.MAX_FOTOGRAMAS:
            e.append(f'El efecto «{nombre}» tiene {len(fr)} fotogramas (de 1 a {sonido.MAX_FOTOGRAMAS}).')
    if not 0 <= int(j.get('inercia', 0) or 0) <= 10: e.append('Inercia del jugador: de 0 a 10.')
    if j.get('arma', 'disparo') not in ARMAS: e.append('Arma del jugador desconocida.')
    for quien in ('jugador', 'enemigo'):
        b = p['balas'][quien]
        if b.get('tamano', '8x8') not in graficos.TAMANOS_BALA: e.append(f'Bala del {quien}: tamaño 8x8, 8x16 o 16x8.')
        if not 1 <= b.get('velocidad', 4) <= 12: e.append(f'Velocidad de la bala del {quien}: de 1 a 12 píxeles.')
    la = j.get('laser') or {}
    if j.get('arma') == 'laser':
        if not 1 <= la.get('grosor', 1) <= 3: e.append('Láser: grosor de 1 a 3 líneas.')
        if not 1 <= la.get('duracion', 4) <= 50: e.append('Láser: se ve de 1 a 50 fotogramas.')
    if not modo_bloques(p) and not libre(p):
        svj, sve, svb, svbe = tamanos_a_la_vez(p)
        if svj + sve + svb + svbe > SAVE_TOTAL:
            e.append('Los sprites son demasiado grandes para este tipo de scroll (vertical u horizontal de 8 en 8): '
                     'no cabe ni un enemigo. Usa sprites más pequeños o el scroll horizontal fino.')
    for clave, txt in (('muerte', 'de muerte'),):
        k = j.get(clave)
        if k is not None and not 0 <= k < len(j['fotogramas']): e.append(f'Jugador: el fotograma {txt} no existe.')
    for lado, k in (j.get('agachado') or {}).items():
        if k is not None and not 0 <= k < len(j['fotogramas']): e.append(f'Jugador: el fotograma agachado ({lado}) no existe.')
    if sum(1 for en in p['enemigos'] if en.get('comportamiento') == 'personaje') > 15:
        e.append('Como mucho 15 tipos de personaje con los que se habla.')
    for en in p['enemigos']:
        k = en.get('muerte')
        if k is not None and not 0 <= k < min(8, len(en['fotogramas'])):
            e.append(f'{en["nombre"]}: el fotograma de muerte tiene que ser uno de los 8 primeros.')
        if en.get('comportamiento') == 'personaje' and not mensaje_valido(en.get('mensaje', '')):
            e.append(f'{en["nombre"]}: el mensaje tiene líneas de más de 20 letras.')
    pa = p['partida']
    if not 1 <= pa['vidas'] <= 9: e.append('Vidas: de 1 a 9.')
    if not 1 <= pa['energia'] <= 8: e.append('Energía por vida: de 1 a 8.')
    ancho_valor = {'puntos': 6, 'record': 6, 'vidas': 1, 'energia': pa['energia'], 'fase': 2}
    ar = p['area']
    for clave in HUD:
        h = pa['marcador'][clave]
        if not h['activo']: continue
        if len(h['etiqueta']) > 8: e.append(f'Marcador {clave}: la etiqueta tiene más de 8 letras.')
        fin = h['col'] + len(h['etiqueta']) + ancho_valor[clave]
        if not (0 <= h['fila'] <= 23 and 0 <= h['col'] and fin <= 32):
            e.append(f'Marcador {clave}: no cabe en la pantalla en esa posición.')
        elif ar['fila'] <= h['fila'] < ar['fila'] + AREA_ALTO and h['col'] < ar['col'] + AREA_ANCHO and fin > ar['col']:
            e.append(f'Marcador {clave}: está encima del área de juego.')
    for clave in ('fase', 'game_over', 'final'):
        if len(pa['mensajes'][clave]) > 20: e.append(f'El mensaje «{clave}» tiene más de 20 letras.')
    distintos = []
    tp = props_tiles(p)
    for i, t in enumerate(tp):
        if not cambia(t): continue
        if not 0 <= t.get('tras', 0) < len(tp):
            e.append(f'El tile {i} se convierte en un tile que no existe ({t.get("tras")}).')
        if t.get('objeto') and t.get('accion') == 'fase' and not 1 <= t.get('valor', 1) <= len(p['niveles']):
            e.append(f'El objeto del tile {i} lleva a la fase {t.get("valor")}, que no existe.')
        if not mensaje_valido(t.get('mensaje', '')): e.append(f'Tile {i}: el mensaje tiene líneas de más de 20 letras.')
        if es_puerta(t):
            if not 1 <= t.get('valor', 1) <= len(p['niveles']):
                e.append(f'La puerta del tile {i} lleva a la fase {t.get("valor")}, que no existe.')
            else:
                destino = p['niveles'][t.get('valor', 1) - 1]
                largo = largo_nivel(destino, horizontal(p))
                if horizontal(p) and t.get('columna', 0) > max(0, largo - AREA_ANCHO // 2):
                    e.append(f'La puerta del tile {i} entra por la columna {t.get("columna")}, pero la fase de '
                             f'destino solo tiene {largo} (máximo {max(0, largo - AREA_ANCHO // 2)}).')
            if t.get('llave', -1) >= len(estrategia(p)['elementos']):
                e.append(f'La puerta del tile {i} necesita un elemento que no existe.')
        if t.get('objeto') and t.get('mensaje') and t['mensaje'] not in distintos: distintos.append(t['mensaje'])
    es = estrategia(p); ne = len(es['elementos'])
    if ne > MAX_ELEMENTOS: e.append(f'Como mucho {MAX_ELEMENTOS} elementos de inventario.')
    if len(es['reglas']) > MAX_REGLAS: e.append(f'Como mucho {MAX_REGLAS} reglas de combinación.')
    for i, t in enumerate(tp):
        if t.get('objeto') and t.get('accion') == 'guardar' and not 0 <= t.get('valor', 0) < max(1, ne):
            e.append(f'El objeto del tile {i} guarda el elemento {t.get("valor")}, que no existe.')
        if t.get('objeto') and t.get('accion') in ('guardar', 'altar') and not ne:
            e.append(f'El objeto del tile {i} usa el inventario, pero no hay elementos definidos.')
    for k, r in enumerate(es['reglas']):
        if r.get('accion') not in ACCIONES_REGLA: e.append(f'Regla {k + 1}: acción no válida.')
        if not r.get('necesita') and r.get('cuando') == 'al_completar':
            e.append(f'Regla {k + 1}: una regla «al completar» necesita algún elemento.')
        if any(not 0 <= x < ne for x in r.get('necesita', [])): e.append(f'Regla {k + 1}: usa un elemento que no existe.')
        if r.get('accion') == 'guardar' and not 0 <= r.get('valor', 0) < ne:
            e.append(f'Regla {k + 1}: da un elemento que no existe.')
        if r.get('accion') == 'fase' and not 1 <= r.get('valor', 1) <= len(p['niveles']):
            e.append(f'Regla {k + 1}: lleva a la fase {r.get("valor")}, que no existe.')
        if not mensaje_valido(r.get('mensaje', '')): e.append(f'Regla {k + 1}: el mensaje tiene líneas de más de 20 letras.')
        if r.get('cuando') == 'personaje' and r.get('personaje', -1) not in personajes(p):
            e.append(f'Regla {k + 1}: el personaje con el que se habla no existe (o ya no es un personaje).')
    todos = set(m for m in [t.get('mensaje') for t in tp if t.get('objeto')] +
                [r.get('mensaje') for r in es['reglas']] + [es['falta']] if m)
    if len(todos) > SIN_MSG: e.append(f'Objetos, reglas y altar pueden usar como mucho {SIN_MSG} mensajes distintos.')
    if pa.get('fuente') is not None and len(pa['fuente']) != 768: e.append('La fuente debe tener 768 bytes.')
    for i, t in enumerate(tp):
        if not t.get('profundidad'): continue
        for clave, nombre in (('linea_tras', 'Tras'), ('linea_ante', 'Ante')):
            l = t.get(clave)
            if l and (len(l.get('p', [])) != 4 or not 0 <= l.get('borde', 0) <= 3 or
                      any(not -16 <= v <= 31 for v in l['p'])):
                e.append(f'Tile {i}: la línea {nombre} no es válida.')
    if sum(1 for t in tp if t.get('profundidad')) > 255: e.append('Como mucho 255 tiles de profundidad.')
    mus = pa.get('musica', {})
    for clave in ('menu', 'juego'):
        if mus.get(clave) and info_pt3(mus[clave]) is None: e.append(f'La música de {clave} no es un módulo PT3.')
    total = len(PT3PLAYER) + sum(len(m) for m in mus.values() if m)
    if total > 16384: e.append(f'Las dos melodías no caben juntas en el banco de música ({total - len(PT3PLAYER)} bytes; '
                               f'máximo {16384 - len(PT3PLAYER)}).')
    return e

def _anim(j, plat=False):
    """Ciclo de andar por dirección (hasta 8 índices). Diagonales vacías usan la vertical
    (en plataformas, arriba-dcha y arriba-izq vacías usan andar hacia ese lado)."""
    tabla = []
    for d in DIRECCIONES:
        lst = [k for k in j['anim'].get(d, []) if 0 <= k < len(j['fotogramas'])]
        if not lst and '-' in d:
            otra = d.split('-')[1] if plat else d.split('-')[0]
            if plat and d.startswith('abajo'):          # cayendo: si no hay, los del salto
                lst = [k for k in j['anim'].get('arriba-' + otra, []) if 0 <= k < len(j['fotogramas'])]
            if not lst:
                lst = [k for k in j['anim'].get(otra, []) if 0 <= k < len(j['fotogramas'])]
        tabla.append((lst or [0])[:8])
    return tabla

def _fijos(j, clave, ciclos):
    """Fotograma de reposo o de disparo por dirección (por defecto, el primero del ciclo de andar)."""
    res = []
    for i, d in enumerate(DIRECCIONES):
        k = j.get(clave, {}).get(d)
        if k is None or not 0 <= k < len(j['fotogramas']):
            k = ciclos[i][0] if clave == 'quieto' else None
        res.append(k)
    return res

def datos_nivel(p, n, base=0xC000, comunes=None):
    """Bloque de una fase colocado en la dirección base: cabecera, tiles, mapa, propiedades y apariciones.
    comunes: {datos: dirección} de lo ya guardado en el mismo banco por otras fases. Tiles, propiedades,
    reglas y lista de parejas son iguales en todas las fases (y el motor solo los lee): si ya están en
    el banco, la cabecera apunta a esa copia en lugar de repetirlos. Se actualiza con lo nuevo."""
    a, j, sc = p['area'], p['jugador'], p['scroll']
    nv = p['niveles'][n]; m = nv['mapa']
    # en el scroll fino por bloques el motor dibuja con los bloques pre-desplazados: no lee los tiles
    # (salvo para redibujar los tiles de profundidad que tapan a los personajes)
    tiles = b'' if modo_bloques(p) and not hay_profundidad(p) else b''.join(graficos.bytes_tile(t) for t in p['tiles'])
    tp = props_tiles(p)              # propiedades: de cada tile o, con 8x8, de cada carácter
    salas_d = None
    if pantallas(p):      # pantalla a pantalla: cada sala, por columnas como el horizontal (12 x 10)
        g = rejilla(nv)
        salas_d = [(x, y) for y in range(len(g)) for x in range(len(g[0])) if g[y][x]]
        largo = PANT_ANCHO
        mapa = b''
    elif libre(p):        # scroll libre: por filas de 2^k tiles
        W, H, k_libre, mapa = mapa_libre(p, nv)
        largo = H
    elif horizontal(p):     # por columnas: 10 tiles por columna, de izquierda a derecha
        largo = len(m[0])
        mapa = bytes(m[f][c] for c in range(largo) for f in range(MAPA_ALTO))
    else:                 # por filas: 12 tiles por fila, de arriba abajo
        largo = len(m)
        mapa = bytes(v for fila in m for v in fila)
    flags = bytes((1 if t.get('solido') else 0) | (2 if t.get('detiene') else 0) |
                  (4 if t.get('plataforma') else 0) | (8 if t.get('mortal') else 0) |
                  (16 if t.get('rompible') else 0) | (32 if t.get('fragil') else 0) |
                  (64 if t.get('objeto') else 0) | (128 if t.get('profundidad') else 0) for t in tp)
    mensajes = mensajes_objetos(p)
    tprop = bytearray()
    for t in tp:
        dec = min(99, t.get('puntos', 0) // 10)
        valor = t.get('valor', 0) if t.get('accion') == 'guardar' else max(1, t.get('valor', 1))
        if es_puerta(t):            # puerta: elemento necesario + 1, fase, mensaje, columna de entrada
            tprop += bytes([t.get('llave', -1) + 1, ACCIONES.index('puerta'), valor,
                            indice_mensaje(p, t.get('mensaje', '')), min(255, max(0, t.get('columna', 0)))])
            continue
        tprop += bytes([t.get('tras', 0), ACCIONES.index(t.get('accion', 'puntos')), valor,
                        indice_mensaje(p, t.get('mensaje', '')),
                        (dec // 10) << 4 | dec % 10])
    parlist = b''
    if modo_bloques(p) and any(cambia(t) for t in p['tiles']):
        # todas las combinaciones de medias columnas con su pareja (para cuando un tile cambia)
        parlist = b''.join(bytes([ta * 2 + ma, tb * 2 + mb, k])
                           for ((ta, ma), (tb, mb)), k in pares_proyecto(p).items())
    hay_obj = any(p['tiles'][v].get('objeto') for fila in m for v in fila)
    # (el motor copia 256 bytes, pero solo lee los de los tiles que existen: no hace falta rellenar)
    apar = b'' if pantallas(p) else datos_apariciones(p, n)
    parmap = mapa_pares(p, n, pares_proyecto(p)) if modo_bloques(p) else b''
    reglas = datos_reglas(p)                  # justo antes de las propiedades de los tiles
    comunes = {} if comunes is None else comunes
    prof, flg = tabla_profundidad(p)
    t8 = p.get('_t8')
    con_ext = bool(t8 or flg)                 # 8 bytes más tras la cabecera (bit 7 del ritmo)
    secciones, pos = [], base + (40 if con_ext else 32)
    def colocar(datos, compartible):
        nonlocal pos
        if compartible and datos in comunes: return comunes[datos]
        direccion = pos; secciones.append(datos); pos += len(datos)
        if pos > 0x10000: raise ValueError(f'{nv["nombre"]} no cabe en el banco a partir de 0x{base:04X}.')
        if compartible: comunes[datos] = direccion
        return direccion
    dir_tiles = colocar(tiles, True) if tiles else 0
    dir_salas = 0
    if salas_d is not None:
        gx0, gy0 = inicio_rejilla(nv)
        dirs_sala = []
        for (x, y) in salas_d:
            sala = bytes(m[y * PANT_ALTO + f][x * PANT_ANCHO + c] for c in range(PANT_ANCHO) for f in range(PANT_ALTO))
            dm = colocar(sala, False)
            da = colocar(apariciones_sala(p, nv, x, y), False)
            dirs_sala.append((dm, da))
        dir_mapa, dir_apar = dirs_sala[salas_d.index((gx0, gy0))]
        g = rejilla(nv); gw, gh = len(g[0]), len(g)
        dir_salas = pos
        tabla = dir_salas + 4 + gw * gh
        bloque = bytearray([gw, gh]) + tabla.to_bytes(2, 'little')
        bloque += bytes((salas_d.index((x, y)) + 1) if g[y][x] else 0 for y in range(gh) for x in range(gw))
        for dm, da in dirs_sala: bloque += dm.to_bytes(2, 'little') + da.to_bytes(2, 'little')
        assert colocar(bytes(bloque), False) == dir_salas
    else:
        dir_mapa = colocar(mapa, False)            # el mapa y el de parejas cambian en la partida: propios
    dir_flags = colocar(bytes(flags), True)
    if salas_d is None: dir_apar = colocar(apar, False)
    dir_parmap = colocar(parmap, False)
    dir_tprop = colocar(reglas + bytes(tprop), True) + len(reglas)
    dir_parlist = colocar(parlist, True)
    dir_meta = colocar(t8['meta'], True) if t8 else 0
    dir_trasm = colocar(t8['trasm'], True) if t8 else 0
    dir_prof = colocar(prof, True) if flg else 0
    ext = (dir_meta.to_bytes(2, 'little') + dir_trasm.to_bytes(2, 'little') + dir_prof.to_bytes(2, 'little') +
           bytes([1 if t8 else 0, flg]))
    if pos > 0x10000:
        raise ValueError(f'{nv["nombre"]} no cabe en el banco a partir de 0x{base:04X}.')
    cab = bytearray(32)
    cab[0:2] = largo.to_bytes(2, 'little')
    cab[2:4] = dir_tiles.to_bytes(2, 'little'); cab[4:6] = dir_mapa.to_bytes(2, 'little')
    cab[6], cab[7] = a['col'], a['fila']
    cab[8], cab[9], cab[10], cab[11] = j['x'], j['y'], j['velocidad'], sc['umbral']
    cab[12] = 1 if horizontal(p) or multidir(p) else 0
    cab[13] = 1 if sc['modo'] == 'auto' else 0
    cab[14] = 1 if sc['retroceso'] else 0
    cab[15] = sc['vel_auto']
    cab[16] = sc.get('umbral_v', 48) if libre(p) else sc['umbral_ret']
    cab[17:19] = dir_apar.to_bytes(2, 'little')
    cab[19:21] = dir_flags.to_bytes(2, 'little')
    cab[21] = j.get('cadencia', 6)
    cab[22] = sc.get('paso', 8)
    cab[23] = ritmo(p) | (0x80 if con_ext else 0)
    cab[24:26] = dir_parmap.to_bytes(2, 'little')
    cab[26:28] = dir_tprop.to_bytes(2, 'little')
    cab[28:30] = dir_parlist.to_bytes(2, 'little')
    cab[30] = len(parlist) // 3
    cab[31] = (len(reglas) // 6) << 1 | (1 if hay_obj else 0)
    if multidir(p):
        gx0, gy0 = inicio_rejilla(nv)
        cab[28], cab[29], cab[30] = gx0, gy0, 0
        if pantallas(p): cab[24:26] = dir_salas.to_bytes(2, 'little')
        else: cab[24], cab[25] = W, k_libre
        cab[13], cab[14] = 0, 0
    d = bytes(cab) + (ext if con_ext else b'') + b''.join(secciones)
    if len(d) > 16384:
        raise ValueError(f'{nv["nombre"]} ocupa {len(d)} bytes (máximo 16384). Reduce tiles o el largo del mapa.')
    return d

def mensajes_objetos(p):
    """Mensajes distintos de objetos, reglas y altar (máximo 15; la entrada 15 queda vacía)."""
    lista = []
    def anadir(m):
        if m and m not in lista: lista.append(m)
    for t in props_tiles(p):
        if t.get('objeto') and t.get('accion') in ('fase', 'ganar', 'perder', 'mensaje', 'puerta'):
            anadir(t.get('mensaje'))
    for en in p['enemigos']:
        if en.get('comportamiento') == 'personaje': anadir(en.get('mensaje'))
    e = estrategia(p)
    for r in e['reglas']: anadir(r.get('mensaje'))
    anadir(e['falta'])
    return lista[:SIN_MSG]

def indice_mensaje(p, m):
    lista = mensajes_objetos(p)
    return lista.index(m) if m in lista else SIN_MSG

def datos_reglas(p):
    """6 bytes por regla: elementos, opciones (bit0 exacta, bit1 al completar, bit2 gasta),
    acción, valor, mensaje, puntos (decenas en BCD)."""
    d = bytearray()
    for r in estrategia(p)['reglas'][:MAX_REGLAS]:
        mascara = sum(1 << i for i in r.get('necesita', []) if 0 <= i < MAX_ELEMENTOS)
        op = (1 if r.get('modo') == 'exacta' else 0) | (2 if r.get('cuando') == 'al_completar' else 0) | \
             (4 if r.get('gasta', True) else 0)
        if r.get('cuando') == 'personaje':              # bits 3-6: con qué personaje se habla
            op |= personajes(p).get(r.get('personaje', -1), 0) << 3
        dec = min(99, r.get('puntos', 0) // 10)
        valor = r.get('valor', 0) if r.get('accion') == 'guardar' else max(1, r.get('valor', 1))
        d += bytes([mascara, op, ACCIONES.index(r.get('accion', 'mensaje')), valor,
                    indice_mensaje(p, r.get('mensaje', '')), (dec // 10) << 4 | dec % 10])
    return bytes(d)

def datos_apariciones(p, n):
    """Lista ordenada por progreso: progreso, coordenada del mundo (caracteres) en el eje
    del scroll, coordenada transversal (px) y tipo. Termina en 0xFFFF."""
    lista = []
    if libre(p):
        # scroll libre: x e y del mundo en píxeles, tipo y estado (lo cambia el motor). Por x.
        nv = p['niveles'][n]; mapa = nv['mapa']
        for a in nv['apariciones']:
            en = p['enemigos'][a['tipo']]
            w, h = graficos.TAMANOS[en['tamano']]
            y = a['f'] * 16
            if plataformas(p) and en['comportamiento'] in ('patrulla', 'quieto', 'personaje'):
                y = _apoyar(p, mapa, a['f'], a['c'], h, y)
            lista.append((a['c'] * 16, y, a['tipo']))
        lista.sort()
        return b''.join(x.to_bytes(2, 'little') + y.to_bytes(2, 'little') + bytes([t, 0])
                        for x, y, t in lista) + b'\xff\xff'
    if horizontal(p):
        largo2 = len(p['niveles'][n]['mapa'][0]) * 2
        mapa = p['niveles'][n]['mapa']
        for a in p['niveles'][n]['apariciones']:
            en = p['enemigos'][a['tipo']]
            w, h = graficos.TAMANOS[en['tamano']]
            col = a['c'] * 2
            prog = min(max(0, col + w // 8 - AREA_ANCHO), largo2 - AREA_ANCHO)
            y = min(a['f'] * 16, 160 - h)
            if plataformas(p) and en['comportamiento'] in ('patrulla', 'quieto', 'personaje'):
                y = _apoyar(p, mapa, a['f'], a['c'], h, y)       # de pie sobre el suelo
            lista.append((prog, col, y, a['tipo']))
    else:
        largo2 = len(p['niveles'][n]['mapa']) * 2
        for a in p['niveles'][n]['apariciones']:
            w, h = graficos.TAMANOS[p['enemigos'][a['tipo']]['tamano']]
            fila = a['f'] * 2
            prog = max(0, largo2 - AREA_ALTO - fila) * 8          # en píxeles
            lista.append((prog, fila, min(a['c'] * 16, 192 - w), a['tipo']))
    lista.sort(key=lambda t: t[0])
    d = bytearray()
    for prog, mundo, trans, tipo in lista:
        d += prog.to_bytes(2, 'little') + mundo.to_bytes(2, 'little') + bytes([trans, tipo])
    return bytes(d) + b'\xff\xff'

def apariciones_sala(p, nv, x, y):
    """Pantalla a pantalla: lista de apariciones de una sala (todas a la vez al entrar)."""
    d = bytearray()
    m = nv['mapa']
    sala = [fila[x * PANT_ANCHO:(x + 1) * PANT_ANCHO] for fila in m[y * PANT_ALTO:(y + 1) * PANT_ALTO]]
    for a in nv['apariciones']:
        if a['f'] // PANT_ALTO != y or a['c'] // PANT_ANCHO != x: continue
        en = p['enemigos'][a['tipo']]
        w, h = graficos.TAMANOS[en['tamano']]
        f, c = a['f'] % PANT_ALTO, a['c'] % PANT_ANCHO
        col = min(c * 2, (192 - w) // 8)
        yy = min(f * 16, 160 - h)
        if plataformas(p) and en['comportamiento'] in ('patrulla', 'quieto', 'personaje'):
            yy = _apoyar(p, sala, f, c, h, yy)
        d += (0).to_bytes(2, 'little') + col.to_bytes(2, 'little') + bytes([yy, a['tipo']])
    return bytes(d) + b'\xff\xff'

def _apoyar(p, mapa, f, c, h, y):
    """Altura a la que un enemigo de alto h queda de pie sobre el primer suelo o plataforma
    desde la fila f hacia abajo, en la columna c."""
    for fila in range(f, len(mapa)):
        t = p['tiles'][mapa[fila][c]]
        if t.get('solido') or t.get('plataforma'):
            return max(0, fila * 16 - h)
    return y

def _codigo_comportamiento(p, en):
    """(código del motor, dirección) según el comportamiento elegido."""
    c = en['comportamiento']
    d = DIRECCIONES.index(en.get('direccion', 'abajo'))
    if c == 'quieto': return 0, 0
    if c == 'patrulla':
        if plataformas(p): return 4, 2                  # camina sobre el suelo
        return 1, (4 if horizontal(p) else 2)       # (en los modos 2D, en horizontal)
    if c == 'rebota': return 1, d
    if c == 'persigue': return 2, 0
    if c == 'personaje': return 5, 0                # quieto, se habla con él
    return 3, d                                     # cruza

BANCO7_LIBRE = 0xDB00                  # tras la pantalla oculta: 9472 bytes para sprites compilados
BANCO7_TAM = 0x10000 - BANCO7_LIBRE

def plan_compilados(p):
    """Qué personajes se compilan (en el banco 7) y sus descriptores. Solo en modo bloques.
    Orden: jugador, disparo del jugador, disparo enemigo y enemigos, mientras quepan.
    Devuelve (conjunto de claves compiladas, {clave de fotograma: dirección del descriptor}, bytes)."""
    if not modo_bloques(p) or not p['scroll'].get('compilar_sprites', True):
        return set(), {}, b''
    sin = p.get('_sin_balas', [])
    personajes = [('j', p['jugador'], False)]
    personajes += [(c, p['balas'][q], False) for c, q in (('bala_j', 'jugador'), ('bala_e', 'enemigo')) if q not in sin]
    personajes += [(n, en, en.get('voltear')) for n, en in enumerate(p['enemigos'][:MAX_TIPOS])]
    usado, dirs, salida, compilados = 0, {}, bytearray(), set()
    for clave, per, voltear in personajes:
        w, h = graficos.TAMANOS[per['tamano']]
        maximo = 1 if clave in ('bala_j', 'bala_e') else (8 if clave != 'j' else len(per['fotogramas']))
        frames = []
        for i, f in enumerate(per['fotogramas'][:maximo]):
            pix = graficos.redimensionar(f, w, h)
            frames.append((i, 'd', pix))
            if voltear: frames.append((i, 'i', [fila[::-1] for fila in pix]))
        codigos = [(i, lado, graficos.compilar_sprite(pix, SPRITE_NL)) for i, lado, pix in frames]
        tam = sum(8 + sum(len(v) for v in vers) for _, _, vers in codigos)
        if usado + tam > BANCO7_TAM: continue
        for i, lado, vers in codigos:
            base = BANCO7_LIBRE + len(salida)
            dirs_v, cuerpo = [], bytearray()
            for v in vers:
                dirs_v.append(base + 8 + len(cuerpo)); cuerpo += v
            salida += b''.join(a.to_bytes(2, 'little') for a in dirs_v) + cuerpo
            if clave in ('bala_j', 'bala_e'): dirs[clave] = base
            elif clave == 'j': dirs[('j', i)] = base
            else: dirs[(clave, lado, i)] = base
        usado = len(salida); compilados.add(clave)
    return compilados, dirs, bytes(salida)

def caja_pixeles(per):
    """(x, y, ancho, alto) de los píxeles no transparentes de todos sus fotogramas (y su espejo, si
    se voltea): es la caja con la que el láser le da justo donde empieza su dibujo."""
    w, h = graficos.TAMANOS[per['tamano']]
    xs, ys = [], []
    for f in per['fotogramas'][:8]:
        f = graficos.redimensionar(f, w, h)
        for y, fila in enumerate(f):
            for x, c in enumerate(fila):
                if c != '.':
                    ys.append(y); xs.append(x)
                    if per.get('voltear'): xs.append(w - 1 - x)
    if not xs: return (0, 0, w, h)
    return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

def datos_sprites(p, devolver_direcciones=False):
    """Banco 4: cabecera (jugador, animaciones, balas, 16 fichas de enemigo de 48 bytes) y fotogramas."""
    jg = p['jugador']
    jw, jh = graficos.TAMANOS[jg['tamano']]
    CAB = 0x407                                 # (0x3C7-0x406: caja de los píxeles de cada tipo de enemigo)
    compilados, dirs_c, _ = plan_compilados(p)
    frames, dirs = bytearray(), dict(dirs_c)
    def anadir(clave, pix, w, h):
        dirs[clave] = 0xC000 + CAB + len(frames)
        frames.extend(graficos.bytes_sprite(graficos.redimensionar(pix, w, h)))
    if 'j' not in compilados:
        for i, f in enumerate(jg['fotogramas']):
            anadir(('j', i), f, jw, jh)
    sin = p.get('_sin_balas', [])          # balas que nadie dispara: no hace falta su dibujo
    if 'bala_j' not in compilados and 'jugador' not in sin:
        anadir('bala_j', p['balas']['jugador']['fotogramas'][0], *graficos.TAMANOS[p['balas']['jugador'].get('tamano', '8x8')])
    if 'bala_e' not in compilados and 'enemigo' not in sin:
        anadir('bala_e', p['balas']['enemigo']['fotogramas'][0], *graficos.TAMANOS[p['balas']['enemigo'].get('tamano', '8x8')])
    dirs.setdefault('bala_j', 0xC000); dirs.setdefault('bala_e', 0xC000)
    for n, en in enumerate(p['enemigos'][:MAX_TIPOS]):
        if n in compilados: continue
        w, h = graficos.TAMANOS[en['tamano']]
        for i, f in enumerate(en['fotogramas'][:8]):
            anadir((n, 'd', i), f, w, h)
            if en.get('voltear'):
                anadir((n, 'i', i), [fila[::-1] for fila in f], w, h)
    if CAB + len(frames) > 16384:
        raise ValueError(f'Los sprites no caben en su banco (16 KB): sobran {CAB + len(frames) - 16384} bytes. '
                         'Usa menos fotogramas, sprites más pequeños o no voltees a algunos enemigos.')
    cab = bytearray(CAB)
    cab[0], cab[1], cab[2] = jw // 8, jh, max(1, min(15, jg.get('vel_anim', 4)))
    df = jg.get('disparo_fijo')
    cab[3] = DIRECCIONES.index(df) + 1 if df in DIRECCIONES else 0
    ciclos = _anim(jg, plataformas(p))
    for d, ciclo in enumerate(ciclos):
        for k in range(8):
            pos = 4 + (d * 8 + k) * 2
            cab[pos:pos + 2] = dirs[('j', ciclo[k % len(ciclo)])].to_bytes(2, 'little')
        cab[0x3A9 + d] = len(ciclo)
    quieto = _fijos(jg, 'quieto', ciclos)
    disparo = [k if k is not None else quieto[i] for i, k in enumerate(_fijos(jg, 'disparo', ciclos))]
    for d in range(8):
        cab[0x84 + d * 2:0x86 + d * 2] = dirs[('j', quieto[d])].to_bytes(2, 'little')
        cab[0x94 + d * 2:0x96 + d * 2] = dirs[('j', disparo[d])].to_bytes(2, 'little')
    cab[0xA4:0xA6] = dirs['bala_j'].to_bytes(2, 'little')
    cab[0xA6:0xA8] = dirs['bala_e'].to_bytes(2, 'little')
    cab[0xA8] = len(p['enemigos'])
    cab[0x3B1] = 1 if 'j' in compilados else 0
    cab[0x3B2] = 1 if 'bala_j' in compilados else 0
    cab[0x3B3] = 1 if 'bala_e' in compilados else 0
    cab[0x3B4] = atr_color(jg.get('color')) if color_sprites(p) else 0
    ag = jg.get('agachado') or {}                       # agachado (plataformas): dcha e izq
    for d, lado in ((2, 'dcha'), (6, 'izq')):
        k = ag.get(lado)
        if k is not None and 0 <= k < len(jg['fotogramas']):
            cab[0x3B5 + d * 2:0x3B7 + d * 2] = dirs[('j', k)].to_bytes(2, 'little')
    km = jg.get('muerte')
    if km is not None and 0 <= km < len(jg['fotogramas']):
        cab[0x3C5:0x3C7] = dirs[('j', km)].to_bytes(2, 'little')
    npcs = personajes(p)
    for n, en in enumerate(p['enemigos'][:MAX_TIPOS]):
        w, h = graficos.TAMANOS[en['tamano']]
        km = en.get('muerte')                           # fotograma de muerte: fuera del ciclo de andar
        if km is not None and not 0 <= km < min(8, len(en['fotogramas'])): km = None
        ciclo = [i for i in range(min(8, len(en['fotogramas']))) if i != km] or [0]
        nf = len(ciclo)
        codigo, direc = _codigo_comportamiento(p, en)
        dec = en.get('puntos', 0) // 10
        ficha = bytearray([w // 8, h, codigo, en['velocidad'], en['energia'], en['cadencia'], direc,
                           (dec // 10) << 4 | dec % 10, max(1, min(15, en.get('vel_anim', 4))), nf,
                           1 if n in compilados else 0,
                           atr_color(en.get('color')) if color_sprites(p) else 0])
        ficha += (dirs[(n, 'd', km)] if km is not None else 0).to_bytes(2, 'little')
        ficha += bytes([indice_mensaje(p, en.get('mensaje', '')) if n in npcs else SIN_MSG, npcs.get(n, 0)])
        lado_i = 'i' if en.get('voltear') else 'd'
        for lado in ('d', lado_i):
            for k in range(8):
                ficha += dirs[(n, lado, ciclo[k % nf])].to_bytes(2, 'little')
        o = 0xA9 + 48 * n
        cab[o:o + 48] = ficha
        cab[0x3C7 + 4 * n:0x3CB + 4 * n] = bytes(caja_pixeles(en))
    d = bytes(cab) + bytes(frames)
    if len(d) > 16384:
        raise ValueError(f'Los sprites ocupan {len(d)} bytes (máximo 16384). Reduce fotogramas '
                         '(o desactiva «voltear» en algún enemigo).')
    return dirs if devolver_direcciones else d

def _cadena(t, largo=None):
    b = a_ascii(t)
    if largo: b = b[:largo].ljust(largo, b' ')
    return b + b'\x00'

def _atr(d):
    return (0x40 if d.get('brillo') else 0) | (int(d['tinta']) & 7)

BANCOS_FASES = (0, 6, 3, 4, 1, 7)          # orden en el que se buscan huecos para las fases

def contenido_fijo(p, segmentos=None):
    """Lo que tiene sitio fijo en los bancos 1, 4 y 7: {banco: (dirección, bytes)}."""
    carga = p.get('pantalla_carga') or pantalla_vacia()
    titulo = p.get('pantalla_titulo') or carga
    marco = p.get('pantalla_marco') or marco_defecto(p['area']['col'], p['area']['fila'])
    sprites = datos_sprites(p)
    _, _, banco7 = plan_compilados(p)
    if segmentos is not None:
        segmentos += [(1, 0xC000, 6912, 'Presentación'), (1, 0xC000 + 6912, 6912, 'Marco'),
                      (4, 0xC000, len(sprites), 'Sprites'), (7, 0xC000, BANCO7_LIBRE - 0xC000, 'Pantalla oculta')]
        if banco7: segmentos.append((7, BANCO7_LIBRE, len(banco7), 'Sprites compilados'))
        if libre(p): segmentos.append((7, COPIAS_LIBRE[0], COPIAS_LIBRE[1] - COPIAS_LIBRE[0], 'Búferes del scroll libre'))
    if libre(p): return {1: (0xC000, titulo + marco), 4: (0xC000, sprites), 7: (COPIAS_LIBRE[1], b'')}
    return {1: (0xC000, titulo + marco), 4: (0xC000, sprites), 7: (BANCO7_LIBRE, banco7)}

def repartir_bancos(p, fijos=None, segmentos=None):
    """Coloca la configuración general en el banco 3 y reparte las fases en el primer hueco libre de los
    bancos 0, 6, 3, 4, 1 y 7 (detrás de lo que ya tenga cada uno: música, sprites, pantallas...).
    Devuelve {banco: (dirección, bytes)} listos para cargar. segmentos: lista a la que se añade
    (banco, dirección, tamaño, qué) para el mapa de memoria."""
    if fijos is None: fijos = contenido_fijo(p, segmentos)
    pa = p['partida']
    global _ESPANOL
    _ESPANOL = tipo_fuente(p) == 'espanola' or (tipo_fuente(p) == 'propia' and bool(pa.get('fuente_con_tildes')))
    instr = datos_textos(p.get('textos', []))
    menu = datos_textos(pa['menu'])
    ct = pa['controles']
    ancho_ct = max(len(ct['teclado']), len(ct['kempston']))
    cadenas = {'teclado': _cadena(ct['teclado'], ancho_ct), 'kempston': _cadena(ct['kempston'], ancho_ct),
               'fase': _cadena(pa['mensajes']['fase']), 'game_over': _cadena(pa['mensajes']['game_over']),
               'final': _cadena(pa['mensajes']['final'])}
    for i, msg in enumerate(mensajes_objetos(p)):
        cadenas[f'obj{i}'] = _cadena(msg)
    CONF = 288
    contenido3 = bytearray(CONF); dirs = {}
    for clave, datos in [('instr', instr), ('menu', menu)] + list(cadenas.items()):
        dirs[clave] = 0xC000 + len(contenido3); contenido3 += datos
    fuente = fuente_efectiva(p)
    if fuente:
        dirs['fuente'] = 0xC000 + len(contenido3); contenido3 += fuente
    if modo_bloques(p):
        pares = pares_proyecto(p)
        bloq, cols, compilados, largo_v, delta = bloques_memoria(p, pares)
        dirs['pares'] = 0xC000 + len(contenido3); contenido3 += bloq
        dirs['patr'] = 0xC000 + len(contenido3); contenido3 += cols
    # música: reproductor y módulos en el banco 6 (si hay alguna melodía)
    mus = pa.get('musica', {})
    hay_musica = any(mus.get(k) for k in ('menu', 'juego'))
    banco6 = bytearray(PT3PLAYER) if hay_musica else bytearray()
    dir_mus = {}
    for clave in ('menu', 'juego'):
        if mus.get(clave):
            if clave == 'juego' and mus.get('menu') == mus['juego']:
                dir_mus['juego'] = dir_mus['menu']            # la misma melodía: se guarda una vez
            else:
                dir_mus[clave] = 0xC000 + len(banco6); banco6 += mus[clave]
    # efectos de sonido (canal C): también en el banco 6
    datos_sfx, dirs_sfx = sonido.datos(pa.get('efectos', {}), 0xC000 + len(banco6), pa.get('efectos_propios'))
    banco6 += datos_sfx
    if segmentos is not None:
        segmentos.append((3, 0xC000, CONF, 'Configuración'))
        segmentos.append((3, 0xC000 + CONF, dirs.get('pares', 0xC000 + len(contenido3)) - 0xC000 - CONF,
                          'Textos y mensajes' + (' y fuente' if fuente else '')))
        if modo_bloques(p):
            segmentos.append((3, dirs['pares'], len(contenido3) - (dirs['pares'] - 0xC000), 'Bloques del scroll'))
        if hay_musica: segmentos.append((6, 0xC000, len(PT3PLAYER), 'Reproductor PT3'))
        for clave in ('menu', 'juego'):
            if clave in dir_mus and not (clave == 'juego' and dir_mus['juego'] == dir_mus.get('menu')):
                segmentos.append((6, dir_mus[clave], len(mus[clave]), f'Música {"del menú" if clave == "menu" else "de las fases"}'))
        if datos_sfx: segmentos.append((6, 0xC000 + len(banco6) - len(datos_sfx), len(datos_sfx), 'Efectos'))
    # fases: primer hueco libre de cada banco, en este orden. Una fase puede vivir en cualquier banco:
    # el motor pagina el suyo cada vez que lee el mapa (la interrupción de la música pagina el 6 y
    # devuelve el que hubiera; los sprites están en el 4 y el 7, y la fase puede compartirlos)
    bancos = {0: [0xC000, bytearray()], 6: [0xC000, banco6], 3: [0xC000, contenido3]}
    for b, (ini, datos) in fijos.items():
        bancos[b] = [ini, bytearray(datos)]
    # las fases, en el primer banco en el que quepan; si así no caben todas, de la más grande a la
    # más pequeña y cada una en el banco en el que quede menos hueco
    tam = {}
    def colocar_fases(orden, mejor):
        bk = {b: [ini, bytearray(c)] for b, (ini, c) in bancos.items()}
        ubic, comunes, segs = {}, {b: {} for b in BANCOS_FASES}, []
        for n in orden:
            opciones = []
            for b in BANCOS_FASES:
                ini, contenido = bk[b]
                base = ini + len(contenido)
                if base >= 0x10000: continue
                prueba = dict(comunes[b])
                try: d = datos_nivel(p, n, base, prueba)
                except ValueError: continue
                if base + len(d) <= 0x10000:
                    opciones.append((0x10000 - base - len(d), b, base, d, prueba))
                    if not mejor: break
            if not opciones: return None, n, bk
            _, b, base, d, prueba = min(opciones, key=lambda o: o[0]) if mejor else opciones[0]
            bk[b][1] += d; comunes[b] = prueba; ubic[n] = (b, base)
            segs.append((b, base, len(d), f'Fase {n + 1}'))
        return (bk, ubic, segs), None, bk
    res, fallo, bk = colocar_fases(range(len(p['niveles'])), False)
    if res is None:
        for n in range(len(p['niveles'])): tam[n] = len(datos_nivel(p, n))
        res2, _, _ = colocar_fases(sorted(tam, key=lambda n: -tam[n]), True)
        if res2 is None:
            libre_b = sum(0x10000 - ini - len(c) for ini, c in bk.values())
            raise ValueError(f'No cabe {p["niveles"][fallo]["nombre"]}: las fases ocupan demasiado (quedan unos '
                             f'{libre_b // 1024} KB libres repartidos entre los bancos y esta fase necesita '
                             f'{tam[fallo] // 1024 + 1} KB seguidos). Acorta mapas, quita tiles o '
                             'usa música más corta.')
        res = res2
    bk, ubic, segs = res
    for b in bancos: bancos[b] = bk[b]
    ubicacion = [ubic[n] for n in range(len(p['niveles']))]
    if segmentos is not None: segmentos += sorted(segs, key=lambda s_: int(s_[3].split()[1]))
    conf = bytearray(CONF)
    conf[0], conf[1], conf[2], conf[3] = pa['vidas'], pa['energia'], 1 if pa['kempston'] else 0, len(p['niveles'])
    conf[4:6] = dirs['instr'].to_bytes(2, 'little'); conf[6:8] = dirs['menu'].to_bytes(2, 'little')
    conf[8:10] = dirs.get('fuente', 0).to_bytes(2, 'little')
    conf[10], conf[11], conf[12] = ct['fila'], ct['col'], _atr(ct)
    for o, clave in ((13, 'teclado'), (15, 'kempston'), (17, 'fase'), (19, 'game_over'), (21, 'final')):
        conf[o:o + 2] = dirs[clave].to_bytes(2, 'little')
    conf[23] = _atr(pa['mensajes'])
    for n, (b, base) in enumerate(ubicacion):
        conf[24 + n * 3:27 + n * 3] = bytes([b]) + base.to_bytes(2, 'little')
    for k, clave in enumerate(HUD):
        h = pa['marcador'][clave]
        conf[72 + k * 13:72 + k * 13 + 13] = bytes([1 if h['activo'] else 0, h['fila'], h['col'], _atr(h)]) \
            + a_ascii(h['etiqueta'])[:8].ljust(8, b'\x00') + b'\x00'
    conf[137:139] = dir_mus.get('menu', 0).to_bytes(2, 'little')
    conf[139:141] = dir_mus.get('juego', 0).to_bytes(2, 'little')
    conf[141] = 1 if hay_musica else 0
    if plataformas(p):
        subida, caida = tablas_salto(p['scroll']['fisica'])
        conf[142] = 1
        conf[143:143 + len(subida) + 1] = bytes(subida) + b'\x00'
        conf[167:183] = bytes(caida)
    if modo_bloques(p):
        conf[183:185] = dirs['pares'].to_bytes(2, 'little')
        conf[185:187] = len(bloq).to_bytes(2, 'little')
        conf[187:189] = dirs['patr'].to_bytes(2, 'little')
        conf[189] = len(representantes(p, pares))
        conf[190] = 16 * 8 // p['scroll']['paso']
        conf[192] = 1 if compilados else 0
        conf[228] = largo_v if compilados else 0
        conf[243] = delta
        conf[245] = parejas_sin_pixeles(p, pares)
        conf[246] = 1 if any(c[0] != c[2] or c[1] != c[3] for c in
                             (_color_par(p, q) for q in representantes(p, pares) if q)) else 0
        conf[191] = 1 if len(set(cols)) <= 1 else 0          # monocromo: un solo color en todo
    for i in range(len(mensajes_objetos(p))):
        conf[196 + i * 2:198 + i * 2] = dirs[f'obj{i}'].to_bytes(2, 'little')
    e = estrategia(p)
    hud = e['hud']
    conf[229:233] = bytes([1 if hud.get('activo') and e['elementos'] else 0, hud.get('fila', 23),
                           hud.get('col', 22), hud.get('atr', 0x46)])
    simbolos = [(el.get('simbolo') or '?')[0] for el in e['elementos'][:MAX_ELEMENTOS]]
    conf[233:233 + len(simbolos)] = bytes(ord(c) if 32 <= ord(c) < 128 else 63 for c in simbolos)
    conf[241] = len(simbolos)
    for k, dsfx in enumerate(dirs_sfx):                 # efectos de sonido
        conf[247 + 2 * k:249 + 2 * k] = dsfx.to_bytes(2, 'little')
    conf[242] = indice_mensaje(p, e['falta']) if e['falta'] else 255
    jg = p['jugador']
    conf[193] = ARMAS.index(jg.get('arma', 'disparo')) if jg.get('arma', 'disparo') in ARMAS else 0
    conf[194] = max(4, min(32, jg.get('alcance', 12)))
    conf[195] = 1 if jg.get('pisar') else 0
    conf[263], conf[264] = valores_inercia(p)
    lim = limites_a_la_vez(p)['usar']
    conf[265:268] = bytes([lim['enemigos'], lim['balas_j'], lim['balas_e']])
    conf[268:272] = bytes(min(255, x) for x in tamanos_a_la_vez(p))
    bj, be = p['balas']['jugador'], p['balas']['enemigo']
    vmin = velocidad_minima_bala(p)
    conf[272] = max(vmin, min(12, bj.get('velocidad', 4))); conf[273] = max(vmin, min(12, be.get('velocidad', 2)))
    for o, b in ((274, bj), (276, be)):
        w, h = graficos.TAMANOS[b.get('tamano', '8x8')]
        conf[o], conf[o + 1] = w // 8, h
    la = jg.get('laser') or laser_defecto()
    conf[278] = (1 if la.get('para_enemigo', True) else 0) | (2 if la.get('para_tiles', True) else 0)
    conf[279] = max(1, min(3, la.get('grosor', 1))); conf[280] = max(1, min(50, la.get('duracion', 4)))
    conf[281] = max(0, min(255, la.get('alcance', 0)))
    pat = (list(la.get('patron') or [0xFF]) + [0xFF, 0xFF, 0xFF])[:3]
    conf[282:285] = bytes(x & 0xFF for x in pat)
    conf[285] = 1 if la.get('animar', True) else 0
    conf[286] = atr_libre(p)
    conf[244] = 1 if color_sprites(p) else 0
    bancos[3][1][0:CONF] = conf
    return {b: (ini, bytes(d)) for b, (ini, d) in bancos.items() if d}

def atr_libre(p):
    """Color del área en el scroll libre (dos colores: tinta y papel para todo el fondo)."""
    c = p['scroll'].get('colores', {'tinta': 7, 'papel': 0, 'brillo': 0})
    return (0x40 if c.get('brillo') else 0) | (c.get('papel', 0) & 7) << 3 | (c.get('tinta', 7) & 7)

def variante_motor(p):
    """Cada juego lleva solo la variante del motor de su tipo de scroll: V vertical, H horizontal o
    plataformas de 8 en 8, B horizontal o plataformas fino (bloques), D pantalla a pantalla y C scroll
    libre en 8 direcciones."""
    if pantallas(p): return 'D'
    if libre(p): return 'C'
    if not horizontal(p): return 'V'
    return 'B' if modo_bloques(p) else 'H'

def motor_de(p):
    return MOTORES[variante_motor(p)]

def aparte(p):
    """(dirección, bytes) del trozo del motor que va fuera de su sitio: en el scroll libre, siempre
    (0x8000); en el horizontal fino, solo si hay tiles de profundidad (va tras los bloques). (0, b'') si no."""
    v = variante_motor(p)
    if v in APARTES and (v == 'C' or hay_profundidad(p)): return APARTES[v]
    return 0, b''

def generar_tap(p, optimizar=None):
    """Cinta .tap del proyecto. Con optimizar (por defecto, lo que diga el proyecto, que es sí), antes
    se quita lo que no se usa (ver depurar)."""
    errores = comprobar(p)
    if errores:
        raise ValueError('\n'.join(errores))
    if optimizar is None: optimizar = p.get('optimizar', True)
    if optimizar: p, _ = depurar(p)
    p = expandir_t8(p)
    nombre = p.get('nombre') or 'JUEGO'
    carga = p.get('pantalla_carga') or pantalla_vacia()
    motor = motor_de(p)
    if len(motor) > MAX_MOTOR:
        raise ValueError('El motor no cabe en memoria')
    bancos = repartir_bancos(p)
    bloques = [(0, DIR_MOTOR, motor)] + [(0, ini, d) for ini, d in [aparte(p)] if d]
    bloques += [(b, ini, d) for b, (ini, d) in sorted(bancos.items())]
    tabla = bytearray([len(bloques)])
    for banco, dirc, datos in bloques:
        tabla += bytes([banco]) + dirc.to_bytes(2, 'little') + len(datos).to_bytes(2, 'little')
    tabla += DIR_MOTOR.to_bytes(2, 'little')
    salida = tap.bloque_programa(nombre, tap.programa_cargador(CLEAR, DIR_CARGADOR))
    salida += tap.bloque_codigo(nombre[:10], 16384, carga)
    salida += tap.bloque_codigo('cargador', DIR_CARGADOR, CARGADOR + bytes(tabla))
    for _, _, datos in bloques:
        salida += tap.bloque_sin_cabecera(datos)
    return salida

def mapa_memoria(p, optimizar=None):
    """Mapa de memoria del juego: (segmentos, informe). segmentos: [(banco, dirección, tamaño, qué)].
    informe: lo que ha quitado depurar (o None). Si algo no cabe, lanza ValueError."""
    if optimizar is None: optimizar = p.get('optimizar', True)
    informe = None
    if optimizar: p, informe = depurar(p)
    p = expandir_t8(p)
    seg = [(2, DIR_MOTOR, len(motor_de(p)), f'Motor {variante_motor(p)}')]
    ini, d = aparte(p)
    if d: seg.append((2 if ini >= 0x8000 else 5, ini, len(d), 'Motor: profundidad'))
    repartir_bancos(p, segmentos=seg)
    return seg, informe

def _usados_jugador(j, plat):
    ciclos = _anim(j, plat)
    usados = {k for c in ciclos for k in c}
    for clave in ('quieto', 'disparo'):
        usados |= {k for k in _fijos(j, clave, ciclos) if k is not None}
    usados |= {k for k in (j.get('agachado') or {}).values() if k is not None}
    if j.get('muerte') is not None: usados.add(j['muerte'])
    return {k for k in usados if 0 <= k < len(j['fotogramas'])} | {0}

def depurar(p):
    """Copia del proyecto sin lo que el juego no usa: tiles que no aparecen en ningún mapa (ni salen al
    romper o recoger otro), tipos de enemigo que no se colocan en ninguna fase (salvo los personajes de
    alguna regla) y fotogramas del jugador que no usa ninguna animación. Devuelve (copia, informe)."""
    import copy
    q = copy.deepcopy(p)
    inf = {'tiles': [], 'enemigos': [], 'fotogramas': [], 'balas': []}
    # --- tiles
    usados = {0}
    for nv in q['niveles']:
        for fila in nv['mapa']: usados.update(fila)
        if libre(q): usados.add(nv.get('relleno', 0))
    pendientes = list(usados)
    while pendientes:
        t = q['tiles'][pendientes.pop()] if pendientes[-1] < len(q['tiles']) else None
        if t and cambia(t) and t.get('tras', 0) not in usados and t.get('tras', 0) < len(q['tiles']):
            usados.add(t['tras']); pendientes.append(t['tras'])
    usados = {u for u in usados if u < len(q['tiles'])}
    if len(usados) < len(q['tiles']):
        nuevo = {v: k for k, v in enumerate(sorted(usados))}
        inf['tiles'] = [i for i in range(len(q['tiles'])) if i not in usados]
        q['tiles'] = [q['tiles'][i] for i in sorted(usados)]
        for t in q['tiles']:
            if 'tras' in t: t['tras'] = nuevo.get(t['tras'], 0)
        for nv in q['niveles']:
            nv['mapa'] = [[nuevo[v] for v in fila] for fila in nv['mapa']]
            if 'relleno' in nv: nv['relleno'] = nuevo.get(nv['relleno'], 0)
    # --- tipos de enemigo
    usados = {a['tipo'] for nv in q['niveles'] for a in nv['apariciones']}
    usados |= {r.get('personaje') for r in estrategia(q)['reglas'] if r.get('cuando') == 'personaje'}
    usados = {u for u in usados if u is not None and 0 <= u < len(q['enemigos'])}
    if len(usados) < len(q['enemigos']):
        nuevo = {v: k for k, v in enumerate(sorted(usados))}
        inf['enemigos'] = [q['enemigos'][i]['nombre'] for i in range(len(q['enemigos'])) if i not in usados]
        q['enemigos'] = [q['enemigos'][i] for i in sorted(usados)]
        for nv in q['niveles']:
            for a in nv['apariciones']: a['tipo'] = nuevo[a['tipo']]
        for r in estrategia(q)['reglas']:
            if r.get('cuando') == 'personaje': r['personaje'] = nuevo.get(r.get('personaje'), -1)
    # --- fotogramas del jugador
    j = q['jugador']
    usados = _usados_jugador(j, plataformas(q))
    if len(usados) < len(j['fotogramas']):
        nuevo = {v: k for k, v in enumerate(sorted(usados))}
        inf['fotogramas'] = [i for i in range(len(j['fotogramas'])) if i not in usados]
        j['fotogramas'] = [j['fotogramas'][i] for i in sorted(usados)]
        j['anim'] = {d: [nuevo[k] for k in lst if k in nuevo] for d, lst in j['anim'].items()}
        for clave in ('quieto', 'disparo', 'agachado'):
            if j.get(clave): j[clave] = {d: nuevo[k] for d, k in j[clave].items() if k in nuevo}
        if j.get('muerte') is not None: j['muerte'] = nuevo.get(j['muerte'])
    # --- balas que nadie dispara (se comparte el dibujo de la otra)
    if j.get('arma', 'disparo') != 'disparo': inf['balas'].append('jugador')
    if not any(en.get('cadencia', 0) for en in q['enemigos']): inf['balas'].append('enemigo')
    q['_sin_balas'] = list(inf['balas'])
    return q, inf

# ---------------- tramos del mapa ----------------
# Posiciones contadas desde el inicio de la fase (0 = la primera fila de abajo en vertical,
# la primera columna de la izquierda en horizontal). Los enemigos del tramo van con él.
def _cortes(nivel, horiz):
    m = nivel['mapa']
    if horiz:
        return [[m[f][c] for f in range(len(m))] for c in range(len(m[0]))]
    return [list(fila) for fila in reversed(m)]

def _desde_cortes(cortes, horiz):
    if horiz:
        return [[cortes[c][f] for c in range(len(cortes))] for f in range(len(cortes[0]))]
    return [list(fila) for fila in reversed(cortes)]

def _a_progreso(a, largo, horiz):
    return (a['c'], a['f']) if horiz else (largo - 1 - a['f'], a['c'])

def _de_progreso(pos, trans, tipo, largo, horiz):
    return {'tipo': tipo, 'f': trans, 'c': pos} if horiz else {'tipo': tipo, 'f': largo - 1 - pos, 'c': trans}

def largo_nivel(nivel, horiz):
    return len(nivel['mapa'][0]) if horiz else len(nivel['mapa'])

def _reconstruir(nivel, cortes, enemigos, horiz):
    nivel['mapa'] = _desde_cortes(cortes, horiz)
    n = len(cortes)
    nivel['apariciones'] = [_de_progreso(pos, tr, t, n, horiz) for pos, tr, t in enemigos if 0 <= pos < n]

def _enemigos(nivel, horiz):
    n = largo_nivel(nivel, horiz)
    return [(*_a_progreso(a, n, horiz), a['tipo']) for a in nivel['apariciones']]

def tramo_copiar(nivel, horiz, desde, hasta):
    cortes = _cortes(nivel, horiz)
    return {'cortes': [list(c) for c in cortes[desde:hasta + 1]],
            'enemigos': [(p - desde, tr, t) for p, tr, t in _enemigos(nivel, horiz) if desde <= p <= hasta]}

def tramo_insertar(nivel, horiz, pos, tramo, veces=1):
    cortes = _cortes(nivel, horiz); enem = _enemigos(nivel, horiz)
    n = len(tramo['cortes']) * veces
    enem = [(p + n if p >= pos else p, tr, t) for p, tr, t in enem]
    for k in range(veces):
        base = pos + k * len(tramo['cortes'])
        enem += [(base + p, tr, t) for p, tr, t in tramo['enemigos']]
    cortes[pos:pos] = [list(c) for _ in range(veces) for c in tramo['cortes']]
    _reconstruir(nivel, cortes, enem, horiz)

def tramo_borrar(nivel, horiz, desde, hasta):
    cortes = _cortes(nivel, horiz); enem = _enemigos(nivel, horiz)
    n = hasta - desde + 1
    enem = [(p - n if p > hasta else p, tr, t) for p, tr, t in enem if not desde <= p <= hasta]
    del cortes[desde:hasta + 1]
    _reconstruir(nivel, cortes, enem, horiz)

def fijar_largo(nivel, horiz, largo, tile=0):
    """Alarga o acorta la fase por su final (arriba en vertical, a la derecha en horizontal)."""
    cortes = _cortes(nivel, horiz); enem = _enemigos(nivel, horiz)
    ancho = len(cortes[0])
    cortes = cortes[:largo] + [[tile] * ancho for _ in range(largo - len(cortes))]
    _reconstruir(nivel, cortes, enem, horiz)
