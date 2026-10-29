"""Construcción de archivos .tap y del cargador BASIC tokenizado."""

def _bloque(flag, datos):
    cuerpo = bytes([flag]) + bytes(datos)
    chk = 0
    for b in cuerpo:
        chk ^= b
    cuerpo += bytes([chk])
    return len(cuerpo).to_bytes(2, 'little') + cuerpo

def _nombre(n):
    return n.encode('ascii', 'replace')[:10].ljust(10, b' ')

def cabecera(tipo, nombre, longitud, p1, p2):
    d = bytes([tipo]) + _nombre(nombre) + longitud.to_bytes(2, 'little') \
        + p1.to_bytes(2, 'little') + p2.to_bytes(2, 'little')
    return _bloque(0x00, d)

def bloque_codigo(nombre, direccion, datos):
    """Bloque CODE con cabecera (para LOAD ""CODE desde BASIC)."""
    return cabecera(3, nombre, len(datos), direccion, 32768) + _bloque(0xFF, datos)

def bloque_sin_cabecera(datos):
    return _bloque(0xFF, datos)

def bloque_programa(nombre, programa, linea_auto=10):
    return cabecera(0, nombre, len(programa), linea_auto, len(programa)) + _bloque(0xFF, programa)

# ---------------- BASIC ----------------
TOKENS = {'BORDER': 0xE7, 'PAPER': 0xDA, 'INK': 0xD9, 'CLEAR': 0xFD, 'LOAD': 0xEF,
          'SCREEN$': 0xAA, 'CODE': 0xAF, 'RANDOMIZE': 0xF9, 'USR': 0xC0, 'POKE': 0xF4}

def num(n):
    """Número BASIC: dígitos ASCII + forma oculta de 5 bytes (entero corto)."""
    return str(n).encode() + bytes([0x0E, 0, 0, n & 0xFF, (n >> 8) & 0xFF, 0])

def linea(numero, partes):
    """partes: lista de tokens (str en TOKENS), enteros (números) o bytes literales."""
    cuerpo = b''
    for p in partes:
        if isinstance(p, str):
            cuerpo += bytes([TOKENS[p]])
        elif isinstance(p, int):
            cuerpo += num(p)
        else:
            cuerpo += p
    cuerpo += b'\x0d'
    return numero.to_bytes(2, 'big') + len(cuerpo).to_bytes(2, 'little') + cuerpo

def programa_cargador(clear, dir_cargador):
    """10 BORDER 0:PAPER 0:INK 0:CLEAR c:LOAD ""SCREEN$:POKE 23739,111:LOAD ""CODE d:RANDOMIZE USR d"""
    sep = b':'
    return linea(10, ['BORDER', 0, sep, 'PAPER', 0, sep, 'INK', 0, sep, 'CLEAR', clear, sep,
                      'LOAD', b'""', 'SCREEN$', sep, 'POKE', 23739, b',', 111, sep,
                      'LOAD', b'""', 'CODE', dir_cargador, sep,
                      'RANDOMIZE', 'USR', dir_cargador])

def leer_tap(datos):
    """Devuelve la lista de bloques (flag + datos + checksum)."""
    bloques, i = [], 0
    while i + 2 <= len(datos):
        n = datos[i] | datos[i + 1] << 8
        bloques.append(bytes(datos[i + 2:i + 2 + n]))
        i += 2 + n
    return bloques
