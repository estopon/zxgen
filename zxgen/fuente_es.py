"""Fuente de 8x8 propia del generador, con las letras del español (por defecto en todos los juegos).
Mayúsculas de 6 x 7 píxeles con trazos verticales dobles (se leen bien en una tele), minúsculas
con altura de x de 5 píxeles y las letras con tilde: la tilde va en la fila de arriba.
Como el motor solo tiene los caracteres 32 a 127, las letras españolas ocupan el sitio de símbolos
que casi no se usan en un juego (ver ESPANOL). La «ü» se escribe como «u»."""

# letra española -> carácter cuyo dibujo ocupa
ESPANOL = {'Á': '#', 'É': '$', 'Í': '%', 'Ó': '&', 'Ú': '@', 'Ñ': '[',
           'á': '\\', 'é': ']', 'í': '^', 'ó': '_', 'ú': '`', 'ñ': '{', '¿': '}', '¡': '~'}
SIMBOLOS_PERDIDOS = '#$%&@[\\]^_`{}~'

# cada carácter: 8 filas de 6 columnas (las columnas 0 y 7 de la celda quedan vacías: separación)
_ = '......'
G = {}

def _m(c, *filas, desde=0):
    """Carácter c con las filas dadas a partir de la fila 'desde'."""
    f = [_] * 8
    for i, fila in enumerate(filas): f[desde + i] = fila
    G[c] = f

# ---------------- mayúsculas: filas 0-6 ----------------
MAY = {
    'A': [".XXXX.", "XX..XX", "XX..XX", "XXXXXX", "XX..XX", "XX..XX", "XX..XX"],
    'B': ["XXXXX.", "XX..XX", "XX..XX", "XXXXX.", "XX..XX", "XX..XX", "XXXXX."],
    'C': [".XXXX.", "XX..XX", "XX....", "XX....", "XX....", "XX..XX", ".XXXX."],
    'D': ["XXXX..", "XX.XX.", "XX..XX", "XX..XX", "XX..XX", "XX.XX.", "XXXX.."],
    'E': ["XXXXXX", "XX....", "XX....", "XXXXX.", "XX....", "XX....", "XXXXXX"],
    'F': ["XXXXXX", "XX....", "XX....", "XXXXX.", "XX....", "XX....", "XX...."],
    'G': [".XXXX.", "XX..XX", "XX....", "XX.XXX", "XX..XX", "XX..XX", ".XXXXX"],
    'H': ["XX..XX", "XX..XX", "XX..XX", "XXXXXX", "XX..XX", "XX..XX", "XX..XX"],
    'I': ["XXXXXX", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "XXXXXX"],
    'J': ["..XXXX", "....XX", "....XX", "....XX", "XX..XX", "XX..XX", ".XXXX."],
    'K': ["XX..XX", "XX.XX.", "XXXX..", "XXX...", "XXXX..", "XX.XX.", "XX..XX"],
    'L': ["XX....", "XX....", "XX....", "XX....", "XX....", "XX....", "XXXXXX"],
    'M': ["XX..XX", "XXXXXX", "XXXXXX", "XX..XX", "XX..XX", "XX..XX", "XX..XX"],
    'N': ["XX..XX", "XXX.XX", "XXXXXX", "XX.XXX", "XX..XX", "XX..XX", "XX..XX"],
    'O': [".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    'P': ["XXXXX.", "XX..XX", "XX..XX", "XXXXX.", "XX....", "XX....", "XX...."],
    'Q': [".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX.XXX", "XX..XX", ".XXX.X"],
    'R': ["XXXXX.", "XX..XX", "XX..XX", "XXXXX.", "XX.XX.", "XX..XX", "XX..XX"],
    'S': [".XXXX.", "XX..XX", "XX....", ".XXXX.", "....XX", "XX..XX", ".XXXX."],
    'T': ["XXXXXX", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX.."],
    'U': ["XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    'V': ["XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX.", "..XX.."],
    'W': ["XX..XX", "XX..XX", "XX..XX", "XX..XX", "XXXXXX", "XXXXXX", "XX..XX"],
    'X': ["XX..XX", "XX..XX", ".XXXX.", "..XX..", ".XXXX.", "XX..XX", "XX..XX"],
    'Y': ["XX..XX", "XX..XX", "XX..XX", ".XXXX.", "..XX..", "..XX..", "..XX.."],
    'Z': ["XXXXXX", "....XX", "...XX.", "..XX..", ".XX...", "XX....", "XXXXXX"],
}
for c, f in MAY.items(): _m(c, *f)

# mayúsculas con tilde: la tilde en la fila 0 y la letra en 6 filas (2-7, un píxel más baja)
MAY5 = {
    'A': [".XXXX.", "XX..XX", "XXXXXX", "XX..XX", "XX..XX", "XX..XX"],
    'E': ["XXXXXX", "XX....", "XXXXX.", "XX....", "XX....", "XXXXXX"],
    'I': ["XXXXXX", "..XX..", "..XX..", "..XX..", "..XX..", "XXXXXX"],
    'O': [".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    'U': ["XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    'N': ["XX..XX", "XXX.XX", "XXXXXX", "XX.XXX", "XX..XX", "XX..XX"],
}
TILDE, VIRGULILLA = "...XX.", ".XXXXX"

# ---------------- minúsculas: altura de x en las filas 2-6 ----------------
MIN = {
    'a': [_, _, ".XXXX.", "....XX", ".XXXXX", "XX..XX", ".XXXXX", _],
    'b': ["XX....", "XX....", "XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XXXXX.", _],
    'c': [_, _, ".XXXX.", "XX....", "XX....", "XX....", ".XXXX.", _],
    'd': ["....XX", "....XX", ".XXXXX", "XX..XX", "XX..XX", "XX..XX", ".XXXXX", _],
    'e': [_, _, ".XXXX.", "XX..XX", "XXXXXX", "XX....", ".XXXX.", _],
    'f': ["..XXX.", ".XX...", ".XX...", "XXXXX.", ".XX...", ".XX...", ".XX...", _],
    'g': [_, _, ".XXXXX", "XX..XX", "XX..XX", ".XXXXX", "....XX", ".XXXX."],
    'h': ["XX....", "XX....", "XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", _],
    'i': ["..XX..", _, ".XXX..", "..XX..", "..XX..", "..XX..", ".XXXX.", _],
    'j': ["...XX.", _, "..XXX.", "...XX.", "...XX.", "...XX.", "XX.XX.", ".XXX.."],
    'k': ["XX....", "XX....", "XX..XX", "XX.XX.", "XXXX..", "XX.XX.", "XX..XX", _],
    'l': [".XXX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", ".XXXX.", _],
    'm': [_, _, "XXXXX.", "XX.X.X", "XX.X.X", "XX.X.X", "XX.X.X", _],
    'n': [_, _, "XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", _],
    'o': [_, _, ".XXXX.", "XX..XX", "XX..XX", "XX..XX", ".XXXX.", _],
    'p': [_, _, "XXXXX.", "XX..XX", "XX..XX", "XXXXX.", "XX....", "XX...."],
    'q': [_, _, ".XXXXX", "XX..XX", "XX..XX", ".XXXXX", "....XX", "....XX"],
    'r': [_, _, "XX.XXX", "XXXX..", "XX....", "XX....", "XX....", _],
    's': [_, _, ".XXXXX", "XX....", ".XXXX.", "....XX", "XXXXX.", _],
    't': [_, ".XX...", "XXXXX.", ".XX...", ".XX...", ".XX...", "..XXX.", _],
    'u': [_, _, "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXXX", _],
    'v': [_, _, "XX..XX", "XX..XX", "XX..XX", ".XXXX.", "..XX..", _],
    'w': [_, _, "XX..XX", "XX..XX", "XXXXXX", "XXXXXX", ".X..X.", _],
    'x': [_, _, "XX..XX", ".XXXX.", "..XX..", ".XXXX.", "XX..XX", _],
    'y': [_, _, "XX..XX", "XX..XX", "XX..XX", ".XXXXX", "....XX", ".XXXX."],
    'z': [_, _, "XXXXXX", "...XX.", "..XX..", ".XX...", "XXXXXX", _],
}
for c, f in MIN.items(): G[c] = list(f)

# ---------------- cifras: filas 0-6 ----------------
CIF = {
    '0': [".XXXX.", "XX..XX", "XX.XXX", "XXXXXX", "XXX.XX", "XX..XX", ".XXXX."],
    '1': ["..XX..", ".XXX..", "XXXX..", "..XX..", "..XX..", "..XX..", "XXXXXX"],
    '2': [".XXXX.", "XX..XX", "....XX", "...XX.", "..XX..", ".XX...", "XXXXXX"],
    '3': [".XXXX.", "XX..XX", "....XX", "..XXX.", "....XX", "XX..XX", ".XXXX."],
    '4': ["...XX.", "..XXX.", ".XXXX.", "XX.XX.", "XXXXXX", "...XX.", "...XX."],
    '5': ["XXXXXX", "XX....", "XXXXX.", "....XX", "....XX", "XX..XX", ".XXXX."],
    '6': [".XXXX.", "XX....", "XX....", "XXXXX.", "XX..XX", "XX..XX", ".XXXX."],
    '7': ["XXXXXX", "....XX", "...XX.", "..XX..", "..XX..", "..XX..", "..XX.."],
    '8': [".XXXX.", "XX..XX", "XX..XX", ".XXXX.", "XX..XX", "XX..XX", ".XXXX."],
    '9': [".XXXX.", "XX..XX", "XX..XX", ".XXXXX", "....XX", "....XX", ".XXXX."],
}
for c, f in CIF.items(): _m(c, *f)

# ---------------- signos ----------------
_m(' ')
_m('!', "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", _, "..XX..")
_m('"', "XX.XX.", "XX.XX.", ".X..X.")
_m("'", "..XX..", "..XX..", ".XX...")
_m('(', "...XX.", "..XX..", ".XX...", ".XX...", ".XX...", "..XX..", "...XX.")
_m(')', ".XX...", "..XX..", "...XX.", "...XX.", "...XX.", "..XX..", ".XX...")
_m('*', _, ".X..X.", "..XX..", "XXXXXX", "..XX..", ".X..X.", _)
_m('+', _, "..XX..", "..XX..", "XXXXXX", "..XX..", "..XX..", _)
_m(',', "..XX..", "..XX..", ".XX...", desde=5)
_m('-', ".XXXX.", desde=3)
_m('.', "..XX..", "..XX..", desde=5)
_m('/', "....XX", "....XX", "...XX.", "..XX..", ".XX...", "XX....", "XX....")
_m(':', _, "..XX..", "..XX..", _, "..XX..", "..XX..", _)
_m(';', _, "..XX..", "..XX..", _, "..XX..", "..XX..", ".XX...")
_m('<', "...XX.", "..XX..", ".XX...", "XX....", ".XX...", "..XX..", "...XX.")
_m('=', _, _, "XXXXXX", _, "XXXXXX", _, _)
_m('>', ".XX...", "..XX..", "...XX.", "....XX", "...XX.", "..XX..", ".XX...")
_m('?', ".XXXX.", "XX..XX", "....XX", "...XX.", "..XX..", _, "..XX..")
_m('|', "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..")
_m(chr(127), *(["XXXXXX"] * 8))             # (el motor lo usa como bloque de la barra de energía)

# ---------------- letras españolas, en el sitio de los símbolos ----------------
for may, c in (('A', 'Á'), ('E', 'É'), ('I', 'Í'), ('O', 'Ó'), ('U', 'Ú')):
    _m(ESPANOL[c], TILDE, _, *MAY5[may])
_m(ESPANOL['Ñ'], VIRGULILLA, _, *MAY5['N'])
for c, base in (('á', 'a'), ('é', 'e'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')):
    f = list(MIN[base]); f[0] = VIRGULILLA if c == 'ñ' else TILDE
    G[ESPANOL[c]] = f
G[ESPANOL['í']] = [TILDE, _, ".XXX..", "..XX..", "..XX..", "..XX..", ".XXXX.", _]
_m(ESPANOL['¿'], "..XX..", _, "..XX..", ".XX...", "XX....", "XX..XX", ".XXXX.", desde=1)
_m(ESPANOL['¡'], "..XX..", _, "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", desde=1)


def datos():
    """Los 768 bytes de la fuente (caracteres 32 a 127)."""
    d = bytearray()
    for n in range(32, 128):
        filas = G[chr(n)]
        assert len(filas) == 8 and all(len(f) == 6 for f in filas), chr(n)
        for f in filas:
            b = 0
            for x, ch in enumerate(f):
                if ch == 'X': b |= 0x80 >> (x + 1)
            d.append(b)
    return bytes(d)


def codificar(texto, espanol=True):
    """Texto -> bytes para el motor. Con la fuente española, las tildes, la ñ, ¿ y ¡ van a su sitio;
    sin ella (fuente de la ROM o una propia) se quitan las tildes."""
    import unicodedata
    salida = bytearray()
    for c in texto:
        if espanol and c in ESPANOL: salida.append(ord(ESPANOL[c])); continue
        if espanol and c in SIMBOLOS_PERDIDOS: salida.append(ord(' ')); continue
        if c in 'üÜ': c = c.translate(str.maketrans('üÜ', 'uU'))
        if c in '¿¡': c = {'¿': '?', '¡': '!'}[c]
        base = ''.join(x for x in unicodedata.normalize('NFKD', c) if not unicodedata.combining(x)) or '?'
        for x in base: salida.append(ord(x) if 32 <= ord(x) < 127 else ord('?'))
    return bytes(salida)
