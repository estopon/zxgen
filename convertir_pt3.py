"""Adapta mecánicamente pt3player.asm (sintaxis SjAsm) para pasmo:
convierte STRUCT CHP en constantes CHP_x y calcula los desplazamientos de (IX+...).
No cambia la lógica del reproductor de Sergey Bulba."""
import re, sys

def convertir(texto, org):
    lineas = texto.split('\n')
    salida, campos, en_struct, pos = [], {}, False, 0
    tam = {'DB': 1, 'DW': 2}
    for l in lineas:
        s = l.strip()
        if re.match(r'STRUCT\s+CHP', s, re.I):
            en_struct = True; continue
        if en_struct:
            if re.match(r'ENDS', s, re.I):
                en_struct = False
                salida.append(f'CHP_SIZE\tEQU {pos}')
                for k, v in campos.items(): salida.append(f'CHP_{k}\tEQU {v}')
                continue
            m = re.match(r'(\w+)\s+(DB|DW)\b', s, re.I)
            if m:
                campos[m.group(1)] = pos; pos += tam[m.group(2).upper()]
            continue
        salida.append(l)
    t = '\n'.join(salida)
    t = re.sub(r'CHP\.(\w+)', r'CHP_\1', t)
    t = re.sub(r'\bDS\s+CHP\b', 'DS CHP_SIZE', t, flags=re.I)
    def ix(m):      # (IX+expr) con números y CHP_x -> desplazamiento numérico
        expr = m.group(2)
        e = re.sub(r'CHP_(\w+)', lambda k: str(campos[k.group(1)]), expr)
        if re.fullmatch(r'[0-9+\-\s]+', e):
            v = eval(e)
            return f'({m.group(1)}{v:+d})'
        return m.group(0)
    t = re.sub(r'\((IX|IY)([+\-][^)]*)\)', ix, t, flags=re.I)
    t = re.sub(r'^Release\s+EQU\s+"7"', ';Release EQU "7"', t, flags=re.M)
    t = t.replace(',Release,', ',"7",')
    return f'\torg {org}\n' + t

if __name__ == '__main__':
    org = sys.argv[1] if len(sys.argv) > 1 else '0xC000'
    open('pt3player_pasmo.asm', 'w').write(convertir(open('pt3player.asm').read(), org))
