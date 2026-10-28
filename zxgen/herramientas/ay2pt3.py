"""Convierte un volcado de registros del AY (un fotograma por fila) en un módulo PT3 equivalente.
Pensado para músicas que salieron de un tracker: las alturas coinciden con una tabla de tonos de PT3,
y cada nota es un 'instrumento' (secuencia por fotograma de volumen, mezclador, desplazamiento de tono
y ruido) que se convierte en una muestra de PT3. Las notas suenan exactas; el resultado se verifica
reproduciéndolo con el reproductor de Bulba."""

def canal(r, c):
    p = r[2 * c] | (r[2 * c + 1] & 15) << 8
    v = r[8 + c]
    t = not (r[7] >> c) & 1
    n = not (r[7] >> (3 + c)) & 1
    env = bool(v & 16)
    vol = 15 if env else v & 15
    aud = (env or vol > 0) and (t or n)
    return p, vol, env, t, n, aud

def nota_cercana(p, tabla):
    return min(range(96), key=lambda k: abs(tabla[k] - p))

def segmentar(frames, c, estable=3):
    """Lista de notas: (frame inicial, [estados por fotograma]). Estado = (p, vol, env, t, n, aud, ruido)."""
    est = [canal(r, c) + (r[6] & 31,) for r in frames]
    notas, actual = [], None
    for i, e in enumerate(est):
        p, vol, env, t, n, aud, ns = e
        inicio = False
        if aud:
            if actual is None: inicio = True
            else:
                pe = est[i - 1]
                if not pe[5]: inicio = True
                elif vol > pe[1]: inicio = True
                elif t and p != pe[0]:
                    antes = all(est[k][0] == pe[0] for k in range(max(0, i - estable), i))
                    despues = all(est[k][0] == p for k in range(i, min(len(est), i + estable)))
                    if antes and despues: inicio = True
        if inicio:
            actual = [i, []]; notas.append(actual)
        if actual is not None:
            actual[1].append(e)
    return notas

FILAS = 64

def _linea(e, tabla, nota):
    p, vol, env, t, n, aud, ns = e
    if not aud:
        return (0x01, 0x90, 0)                         # silencio: sin tono, sin ruido, volumen 0
    b = (vol if not env else 15) | (0 if t else 0x10) | (0 if n else 0x80)
    c = (0 if env else 1) | ((ns & 31) << 1 if n else 0)
    tono = (p - tabla[nota]) if t else 0
    return (c, b, tono & 0xFFFF)

def convertir(frames, tabla, num_tabla, titulo='', autor='', bucle_frame=0):
    """frames: lista de [R0..R13, r13_escrito]. Devuelve los bytes del módulo PT3."""
    n_frames = len(frames)
    # ---- notas e instrumentos ----
    eventos = [dict() for _ in range(3)]               # fila -> datos de la nota que empieza
    cuerpos = []
    for c in range(3):
        for ini, body in segmentar(frames, c):
            base = next((e[0] for e in body if e[5] and e[3]), None)
            nota = nota_cercana(base, tabla) if base is not None else 48
            lineas = [_linea(e, tabla, nota) for e in body]
            while len(lineas) > 1 and lineas[-1] == lineas[-2] and lineas[-1][1] & 15 == 0:
                lineas.pop()
            env = None
            if body[0][2]:
                r = frames[ini]; env = (r[13] & 15, r[11] | r[12] << 8)
            eventos[c][ini] = {'nota': nota, 'lineas': tuple(lineas), 'env': env}
            cuerpos.append(tuple(lineas))
    # muestras: se agrupan las que son prefijo de otra
    reps = []
    for s in sorted(set(cuerpos), key=len, reverse=True):
        if not any(r[:len(s)] == s for r in reps): reps.append(s)
    if len(reps) > 31:
        raise ValueError(f'Hacen falta {len(reps)} muestras (PT3 admite 31).')
    def muestra_de(lineas):
        for k, r in enumerate(reps):
            if r[:len(lineas)] == lineas: return k + 1
    # ---- envolvente: redisparos o cambios de periodo a mitad de nota ----
    env_extra = {}                                       # fila -> (canal, forma, periodo)
    prev_per = None
    for i, r in enumerate(frames):
        per = r[11] | r[12] << 8
        usa = [c for c in range(3) if canal(r, c)[2] and canal(r, c)[5]]
        if usa and (r[14] or per != prev_per):
            c = usa[0]
            ev = eventos[c].get(i)
            if ev is not None and ev['env'] is not None: pass
            elif ev is not None: ev['env'] = (r[13] & 15, per)
            else: env_extra[i] = (c, r[13] & 15, per)
        if usa: prev_per = per
    # ---- patrones ----
    n_pat = (n_frames + FILAS - 1) // FILAS
    patrones, posiciones, vistos = [], [], {}
    skip = [None, None, None]; muestra_act = [None, None, None]
    for pnum in range(n_pat):
        f0, f1 = pnum * FILAS, min(n_frames, (pnum + 1) * FILAS)
        flujos = []
        for c in range(3):
            filas = sorted(set([f0] + [f for f in eventos[c] if f0 <= f < f1] +
                               [f for f, v in env_extra.items() if v[0] == c and f0 <= f < f1]))
            d = bytearray()
            for k, f in enumerate(filas):
                n = (filas[k + 1] if k + 1 < len(filas) else f1) - f
                if skip[c] != n:
                    d += bytes([0xB1, n]); skip[c] = n
                ev = eventos[c].get(f)
                ex = env_extra.get(f)
                if ev is not None:
                    if ev['env'] is not None:
                        forma, per = ev['env']; d += bytes([0xB1 + forma, per >> 8, per & 255])
                    s = muestra_de(ev['lineas'])
                    if s != muestra_act[c]:
                        d += bytes([0xD0 + s]); muestra_act[c] = s
                    d += bytes([0x50 + ev['nota']])
                else:
                    if ex is not None and ex[0] == c:
                        d += bytes([0xB1 + ex[1], ex[2] >> 8, ex[2] & 255])
                    if f == bucle_frame and not canal(frames[f], c)[5]:
                        d += bytes([0xC0])             # punto de bucle: el canal empieza callado
                    else:
                        d += bytes([0xD0])
            d.append(0x00)
            flujos.append(bytes(d))
        clave = tuple(flujos)
        if clave in vistos and False:
            posiciones.append(vistos[clave])
        else:
            vistos[clave] = len(patrones); posiciones.append(len(patrones)); patrones.append(flujos)
    return montar(patrones, posiciones, reps, num_tabla, titulo, autor, bucle_frame // FILAS)

def montar(patrones, posiciones, muestras, num_tabla, titulo, autor, bucle):
    def texto(s, n): return s.encode('latin-1', 'replace')[:n].ljust(n, b' ')
    h = bytearray(b'ProTracker 3.6 compilation of ' + texto(titulo, 32) + b' by ' + texto(autor, 32))
    h += bytes([0x20, num_tabla, 1, len(posiciones), bucle])
    h += bytes(2)                                          # 0x67: tabla de patrones (se rellena)
    h += bytes(64) + bytes(32)                             # 0x69 muestras, 0xA9 ornamentos
    h += bytes(p * 3 for p in posiciones) + b'\xff'
    tabla_pat = len(h); h[0x67:0x69] = tabla_pat.to_bytes(2, 'little')
    h += bytes(6 * len(patrones))
    for k, flujos in enumerate(patrones):
        for c in range(3):
            pos = len(h); h[tabla_pat + k * 6 + c * 2:tabla_pat + k * 6 + c * 2 + 2] = pos.to_bytes(2, 'little')
            h += flujos[c]
    for k, lineas in enumerate(muestras):
        pos = len(h); h[0x69 + (k + 1) * 2:0x69 + (k + 1) * 2 + 2] = pos.to_bytes(2, 'little')
        h += bytes([len(lineas) - 1, len(lineas)])         # bucle en la última línea
        for c, b, tono in lineas:
            h += bytes([c, b, tono & 255, tono >> 8])
    pos = len(h); h[0xA9:0xAB] = pos.to_bytes(2, 'little'); h += bytes([0, 1, 0])
    return bytes(h)
