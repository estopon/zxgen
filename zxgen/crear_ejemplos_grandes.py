"""Crea los cinco juegos de ejemplo grandes buscando la mayor longitud de fase que cabe en memoria.
Uso:  python crear_ejemplos_grandes.py [juego ...]   (sin argumentos, los cinco)
Escribe ejemplos/<juego>.json y juegos/<juego>.tap, y muestra cuánto ocupa cada banco."""
import json, os, sys
import juego, ejemplos_grandes as eg

# en el paquete, ejemplos/ y juegos/ están junto a zxgen/; si no, dentro
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI) if os.path.isdir(os.path.join(os.path.dirname(AQUI), 'ejemplos')) else AQUI
EJ, JU = os.path.join(RAIZ, 'ejemplos'), os.path.join(RAIZ, 'juegos')

RANGOS = {'asalto': (20, 1600), 'comando': (20, 1600), 'nebulosa': (20, 700), 'templo': (20, 700), 'punos': (20, 700)}
NOMBRES = {'asalto': 'asalto_vertical', 'comando': 'comando_vertical', 'nebulosa': 'nebulosa_horizontal',
           'templo': 'templo_plataformas', 'punos': 'punos_beat_em_up'}

def guardar_json(p, ruta):
    d = dict(p)
    for k in ('pantalla_carga', 'pantalla_titulo', 'pantalla_marco'):
        if d.get(k): d[k] = d[k].hex()
    d['partida'] = dict(d['partida'])
    if d['partida'].get('fuente'): d['partida']['fuente'] = bytes(d['partida']['fuente']).hex()
    d['partida']['musica'] = {k: (v.hex() if v else None) for k, v in d['partida']['musica'].items()}
    json.dump(d, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def ocupacion(p):
    seg, _ = juego.mapa_memoria(p)
    usado = {}
    for b, _, tam, _ in seg: usado[b] = usado.get(b, 0) + tam
    return ' · '.join(f'banco {b}: {u * 100 // 16384}%' for b, u in sorted(usado.items()) if b != 2)

if __name__ == '__main__':
    os.makedirs(EJ, exist_ok=True); os.makedirs(JU, exist_ok=True)
    for clave in [a for a in sys.argv[1:] if not a.startswith('--')] or list(RANGOS):
        guardadas = json.load(open(os.path.join(EJ, 'longitudes.json'))) if os.path.exists(os.path.join(EJ, 'longitudes.json')) else {}
        if clave in guardadas and '--maximizar' not in sys.argv:      # ya se buscó: se comprueba que sigue cabiendo
            r = eg.cabe_con_todo(clave, guardadas[clave])
            largo, (p, tap) = guardadas[clave], r if r else (None, None)
            if not r: largo, p, tap = eg.maximizar(clave, *RANGOS[clave])
        else:
            largo, p, tap = eg.maximizar(clave, *RANGOS[clave])
        guardadas[clave] = largo
        json.dump(guardadas, open(os.path.join(EJ, 'longitudes.json'), 'w'), indent=1)
        guardar_json(p, os.path.join(EJ, f'{NOMBRES[clave]}.json'))
        open(os.path.join(JU, f'{NOMBRES[clave]}.tap'), 'wb').write(tap)
        print(f'   {NOMBRES[clave]}.tap: {len(tap)} bytes · 16 fases · {ocupacion(p)}', flush=True)
