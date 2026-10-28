"""Efectos de sonido para el canal C del AY.

El motor los toca en la interrupción, después del reproductor PT3: solo cambia el canal C durante
lo que dura el efecto y la música sigue en los canales A y B (y vuelve al C al acabar).
Cada efecto es una lista de fotogramas (50 por segundo): (volumen 0-15, tono sí/no, ruido sí/no,
periodo del tono 1-4095, periodo del ruido 0-31). Aquí hay una colección de efectos ya hechos;
el generador los empaqueta (4 bytes por fotograma) en el banco 6.

Además de los efectos hechos, cada proyecto puede tener sus propios efectos («efectos_propios» en la
partida: {nombre: lista de fotogramas}), importados de:
  - .afx: un efecto de AYFX Editor (el editor de efectos para el AY más usado en el Spectrum);
  - .afb: un banco de efectos de AYFX Editor (se importan todos);
  - .wav: un sonido grabado (golpe, grito...). Se convierte de forma aproximada: el volumen sigue
    la intensidad, el tono la nota principal y el ruido la parte sin nota. El AY no puede tocar
    muestras sin parar el juego, así que el resultado recuerda al original pero no es una grabación.
Límite: MAX_FOTOGRAMAS fotogramas (2 segundos). Lo recomendable son 5-25 (0,1-0,5 s): un efecto
largo tapa la música del canal C y ocupa 4 bytes por fotograma."""
import math

RELOJ = 1773400                                  # reloj del AY en el Spectrum 128K
MAX_FOTOGRAMAS = 100                             # 2 segundos
RECOMENDADO = 25

EVENTOS = [('salto', 'Salto'), ('golpe', 'Golpe a un enemigo'), ('disparo', 'Disparo'),
           ('enemigo', 'Enemigo destruido'), ('herido', 'Jugador herido o muerto'),
           ('objeto', 'Coger un objeto'), ('romper', 'Romper un bloque'),
           ('puerta', 'Puerta o hablar con un personaje')]


def periodo(hz):
    return max(1, min(4095, round(RELOJ / 16 / hz)))


def _barrido(f0, f1, n, v0=14, v1=8, ruido=False, np=0):
    """Glissando exponencial de f0 a f1 Hz en n fotogramas, con volumen de v0 a v1."""
    res = []
    for k in range(n):
        t = k / max(1, n - 1)
        f = f0 * (f1 / f0) ** t
        res.append((round(v0 + (v1 - v0) * t), True, ruido, periodo(f), np))
    return res


def _ruido(n, v0=15, v1=2, np0=2, np1=20, tono=None):
    res = []
    for k in range(n):
        t = k / max(1, n - 1)
        res.append((round(v0 + (v1 - v0) * t), tono is not None, True,
                    periodo(tono) if tono else 0, round(np0 + (np1 - np0) * t)))
    return res


def _vibrato(f0, f1, n, v0=14, v1=4, ruido=False, np=0, prof=0.06, vel=3):
    """Voz: barrido de f0 a f1 con un temblor de tono (prof) cada vel fotogramas."""
    res = []
    for k in range(n):
        t = k / max(1, n - 1)
        f = f0 * (f1 / f0) ** t * (1 + prof * math.sin(2 * math.pi * k / vel))
        res.append((round(v0 + (v1 - v0) * t), True, ruido, periodo(f), np))
    return res


def _notas(notas, por_nota=3, v0=13, caida=1):
    """Arpegio: lista de frecuencias, cada una por_nota fotogramas, con un poco de caída."""
    res = []
    for i, f in enumerate(notas):
        for k in range(por_nota):
            res.append((max(1, v0 - caida * k - i // 2), True, False, periodo(f), 0))
    return res


NOTA = lambda n: 440 * 2 ** ((n - 69) / 12)      # número MIDI -> Hz

PRESETS = {
    'Salto (sube)':           lambda: _barrido(260, 900, 10, 13, 9),
    'Salto corto':            lambda: _barrido(330, 700, 6, 12, 8),
    'Salto «boing»':          lambda: _barrido(180, 520, 5, 14, 12) + _barrido(520, 260, 5, 11, 6),
    'Golpe seco':             lambda: _ruido(5, 15, 6, 6, 12, tono=110),
    'Golpe metálico':         lambda: _barrido(1400, 500, 6, 14, 6, ruido=True, np=3),
    'Disparo láser':          lambda: _barrido(1800, 300, 8, 13, 5),
    'Disparo corto':          lambda: _ruido(4, 13, 7, 1, 4),
    'Explosión':              lambda: _ruido(22, 15, 1, 6, 31),
    'Aplastar':               lambda: _barrido(400, 120, 6, 13, 7) + _ruido(3, 8, 3, 15, 25),
    'Enemigo cae':            lambda: _barrido(900, 150, 14, 12, 4),
    'Herido':                 lambda: _barrido(220, 90, 10, 14, 7, ruido=True, np=18),
    'Muerte (melodía)':       lambda: _notas([NOTA(n) for n in (72, 67, 64, 60, 55, 52, 48)], 4, 13, 2),
    'Moneda':                 lambda: _notas([NOTA(83), NOTA(88)], 3, 13, 0) + _notas([NOTA(88)], 8, 12, 1),
    'Objeto (arpegio)':       lambda: _notas([NOTA(n) for n in (60, 64, 67, 72, 76)], 2, 13, 1),
    'Vida extra':             lambda: _notas([NOTA(n) for n in (64, 67, 76, 72, 74, 79)], 3, 13, 1),
    'Romper ladrillo':        lambda: _ruido(10, 14, 2, 3, 12, tono=180),
    'Puerta':                 lambda: _barrido(150, 300, 8, 12, 10) + _barrido(300, 150, 8, 10, 4),
    'Hablar (blip)':          lambda: _notas([NOTA(79), NOTA(84), NOTA(79)], 2, 11, 2),
    'Campanilla':             lambda: _notas([NOTA(96)], 12, 13, 1),
    'Puñetazo':               lambda: _ruido(3, 15, 9, 10, 14, tono=90) + _ruido(3, 8, 3, 16, 24),
    'Patada':                 lambda: _barrido(160, 70, 4, 15, 10) + _ruido(4, 10, 2, 8, 20),
    'Golpe fuerte':           lambda: _ruido(2, 15, 15, 2, 4) + _ruido(10, 14, 1, 8, 31, tono=55),
    'Grito':                  lambda: _vibrato(620, 380, 18, 14, 6, ruido=True, np=6),
    'Quejido':                lambda: _vibrato(300, 160, 14, 13, 4),
    'Risa malvada':           lambda: sum(([(13, True, True, periodo(f), 4)] * 3 + [(3, False, False, 1, 0)] * 2
                                           for f in (330, 300, 270, 240)), []),
    'Rugido':                 lambda: _vibrato(90, 60, 22, 15, 5, ruido=True, np=20),
    'Ladrido':                lambda: _barrido(500, 300, 3, 14, 12, ruido=True, np=8) + [(0, False, False, 1, 0)] * 3 +
                                      _barrido(500, 300, 3, 14, 10, ruido=True, np=8),
    'Alarma':                 lambda: (_notas([NOTA(81)], 4, 13, 0) + _notas([NOTA(76)], 4, 13, 0)) * 3,
    'Teletransporte':         lambda: _barrido(100, 2000, 16, 12, 12) + _barrido(2000, 100, 8, 12, 4),
}

POR_DEFECTO = {'salto': 'Salto (sube)', 'golpe': 'Golpe seco', 'disparo': 'Disparo láser',
               'enemigo': 'Aplastar', 'herido': 'Herido', 'objeto': 'Moneda', 'romper': 'Romper ladrillo',
               'puerta': 'Puerta'}


def efecto(nombre, propios=None):
    """Fotogramas del efecto: uno hecho (PRESETS) o uno propio del proyecto."""
    if propios and nombre in propios: return [tuple(f) for f in propios[nombre]]
    return PRESETS[nombre]() if nombre in PRESETS else []


def existe(nombre, propios=None):
    return bool(nombre) and (nombre in PRESETS or bool(propios and nombre in propios))


def bytes_efecto(fotogramas):
    d = bytearray()
    for vol, tono, ruido, per, np in fotogramas[:MAX_FOTOGRAMAS]:
        d += bytes([(vol & 15) | (16 if tono else 0) | (32 if ruido else 0), per & 255, (per >> 8) & 15, np & 31])
    return bytes(d) + b'\xff'


def datos(efectos, base, propios=None):
    """efectos: {evento: nombre o None}. Devuelve (bytes, [8 direcciones o 0]) colocados en base."""
    d, dirs, hechos = bytearray(), [], {}
    for clave, _ in EVENTOS:
        nombre = efectos.get(clave)
        if not existe(nombre, propios):
            dirs.append(0); continue
        if nombre not in hechos:
            hechos[nombre] = base + len(d); d += bytes_efecto(efecto(nombre, propios))
        dirs.append(hechos[nombre])
    return bytes(d), dirs


# ---------------- importar y exportar ----------------
def leer_afx(datos, inicio=0, fin=None):
    """Un efecto en formato AYFX (de AYFX Editor). Cada fotograma: byte de información (bits 0-3
    volumen, bit 4 tono apagado, bit 5 sigue el periodo del tono en 2 bytes, bit 6 sigue el del ruido
    en 1 byte, bit 7 ruido apagado). Fin: bit 6 con ruido 0x20 o más. Devuelve la lista de fotogramas."""
    res, i, per, np = [], inicio, 0, 0
    while i < len(datos) and len(res) < 1000:
        info = datos[i]; i += 1
        if info & 0x20:
            if i + 1 >= len(datos): break
            per = (datos[i] | datos[i + 1] << 8) & 0xFFF; i += 2
        if info & 0x40:
            if i >= len(datos): break
            n = datos[i]; i += 1
            if n >= 0x20: break
            np = n
        res.append((info & 15, not info & 0x10, not info & 0x80, max(1, per), np))
    if fin is not None: fin.append(i)
    return res


def leer_afb(datos):
    """Banco de AYFX Editor: número de efectos, tabla de desplazamientos (cada efecto empieza en la
    dirección del byte alto de su desplazamiento + el desplazamiento) y, al final, los nombres
    (si los hay). Devuelve [(nombre o None, fotogramas)]."""
    n = datos[0]
    res = []
    for k in range(n):
        pos = 1 + 2 * k
        ini = pos + 1 + (datos[pos] | datos[pos + 1] << 8)
        res.append([None, leer_afx(datos, ini)])
    # nombres: cadenas terminadas en 0 detrás del último efecto (versiones nuevas de AYFX Editor)
    try:
        finales = []
        for k in range(n):
            leer_afx(datos, 2 + 2 * k + (datos[1 + 2 * k] | datos[2 + 2 * k] << 8), finales)
        cola = datos[max(finales):]
        partes = [c.decode('latin-1').strip() for c in cola.split(b'\x00')]
        nombres = [c for c in partes if c and all(32 <= ord(x) < 127 for x in c)]
        if len(nombres) >= n:
            for k in range(n): res[k][0] = nombres[-n + k]
    except Exception:
        pass
    return [tuple(r) for r in res]


def escribir_afx(fotogramas):
    """Fotogramas -> .afx (para abrirlo y retocarlo en AYFX Editor)."""
    d, per0, np0 = bytearray(), None, None
    for vol, tono, ruido, per, np in fotogramas:
        info = (vol & 15) | (0 if tono else 0x10) | (0 if ruido else 0x80)
        extra = bytearray()
        if per != per0: info |= 0x20; extra += bytes([per & 255, per >> 8]); per0 = per
        if np != np0: info |= 0x40; extra += bytes([np & 31]); np0 = np
        d += bytes([info]) + extra
    return bytes(d) + b'\xd0\x20'


def leer_wav(ruta, maximo=MAX_FOTOGRAMAS):
    """Convierte un .wav (PCM de 8 o 16 bits, mono o estéreo) en fotogramas del AY, de forma
    aproximada: por cada 1/50 s, volumen según la intensidad, tono según la nota principal
    (autocorrelación) y ruido si el sonido no tiene una nota clara."""
    import wave, struct
    with wave.open(ruta, 'rb') as w:
        nc, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        crudo = w.readframes(min(n, sr * maximo // 50 + sr))
    if sw == 2:
        mu = struct.unpack(f'<{len(crudo) // 2}h', crudo[:len(crudo) // 2 * 2])
    elif sw == 1:
        mu = [b - 128 for b in crudo]
    else:
        raise ValueError('Solo WAV PCM de 8 o 16 bits.')
    if nc > 1: mu = [sum(mu[i:i + nc]) / nc for i in range(0, len(mu) - nc + 1, nc)]
    paso = max(1, sr // 8000)                       # a unos 8 kHz para ir rápido
    mu = [sum(mu[i:i + paso]) / paso for i in range(0, len(mu) - paso + 1, paso)]
    sr8 = sr / paso; tam = int(sr8 / 50)
    trozos = [mu[i:i + tam] for i in range(0, len(mu) - tam + 1, tam)][:maximo]
    rms = [math.sqrt(sum(x * x for x in t) / len(t)) for t in trozos]
    pico = max(rms) or 1
    res = []
    for t, r in zip(trozos, rms):
        vol = 0 if r < pico * 0.02 else max(1, min(15, round(15 + 2 * math.log2(r / pico))))
        if vol == 0:
            res.append((0, False, False, 1, 0)); continue
        media = sum(t) / len(t); t = [x - media for x in t]
        e0 = sum(x * x for x in t) or 1
        mejor, lag_m = 0, 0
        for lag in range(max(2, int(sr8 / 1500)), min(len(t) - 2, int(sr8 / 60))):
            c = sum(t[i] * t[i + lag] for i in range(0, len(t) - lag, 2)) * 2 / e0
            if c > mejor: mejor, lag_m = c, lag
        cruces = sum(1 for i in range(1, len(t)) if (t[i - 1] < 0) != (t[i] < 0)) * 50 / 2
        tono = mejor > 0.45 and lag_m
        ruido = mejor < 0.7
        per = periodo(sr8 / lag_m) if tono else periodo(max(60, min(4000, cruces or 200)))
        np = max(0, min(31, round(31 - min(1.0, cruces / 3000) * 30)))
        res.append((vol, bool(tono), ruido or not tono, per, np))
    while res and res[-1][0] == 0: res.pop()
    return res or [(0, False, False, 1, 0)]


def duracion(fotogramas):
    return len(fotogramas) / 50


def wav(nombre, ruta, sr=22050, propios=None):
    """Guarda el efecto como .wav (para escucharlo desde el generador)."""
    import struct, wave, random
    fr = efecto(nombre, propios)
    VOL = [0, .0137, .0205, .0291, .0423, .0618, .0847, .1369, .1691, .2647, .3527, .4499, .5704, .6873, .8482, 1]
    muestras, fase, lfsr = [], 0.0, 1
    rnd = random.Random(1)
    for vol, tono, ruido, per, np in fr + [(0, False, False, 1, 0)] * 3:
        f = RELOJ / 16 / per if tono else 0
        nr = RELOJ / 16 / max(1, np) if ruido else 0
        bit = 1
        for i in range(sr // 50):
            fase = (fase + f / sr) % 1.0
            t = 1 if not tono or fase < .5 else 0
            if ruido and rnd.random() < nr / sr: bit = rnd.randint(0, 1)
            n = bit if ruido else 1
            muestras.append(int((t * n * VOL[vol] - 0.25 * VOL[vol]) * 26000))
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(struct.pack(f'<{len(muestras)}h', *muestras))


def escuchar(nombre, propios=None):
    """Toca el efecto en el ordenador (Windows: winsound; otros: aplay/afplay si existen)."""
    import os, tempfile, subprocess, sys
    ruta = os.path.join(tempfile.gettempdir(), 'zxgen_efecto.wav')
    wav(nombre, ruta, propios=propios)
    if sys.platform.startswith('win'):
        import winsound
        winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    for orden in (['afplay', ruta], ['aplay', '-q', ruta], ['paplay', ruta]):
        try:
            subprocess.Popen(orden, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return True
        except OSError:
            continue
    return False
