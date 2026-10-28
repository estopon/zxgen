"""Pestaña «Estrategia»: inventario, reglas escritas como frases, puertas y personajes que hablan.

Piezas del sistema:
  - Elementos: lo que el jugador lleva (hasta 8). Se consiguen con tiles «Guardar elemento» o como
    premio de una regla.
  - Altares (tiles «Altar»), personajes (comportamiento «personaje») y el propio inventario («al
    completar») disparan reglas.
  - Puertas (tiles «Puerta a otra fase»): llevan a otra fase; pueden necesitar un elemento.
  - Reglas: CUANDO <altar / hablar con X / completar> SI LLEVA <elementos> ENTONCES <resultado>.
    Se revisan en orden y se aplica la primera que se cumple."""
import tkinter as tk
from tkinter import ttk
import juego, estilo

RESULTADOS = {'Mostrar el mensaje y seguir': 'mensaje', 'Dar un elemento': 'guardar', 'Solo dar puntos': 'puntos',
              'Dar una vida': 'vida', 'Llenar la energía': 'energia', 'Ir a otra fase': 'fase',
              'Ganar el juego': 'ganar', 'Perder el juego': 'perder'}
MODOS = {'al menos estos': 'contiene', 'exactamente estos': 'exacta'}


def _clave(dic, valor, defecto):
    return next((k for k, v in dic.items() if v == valor), defecto)


class EditorEstrategia(ttk.Frame):
    def __init__(self, padre, app):
        super().__init__(padre, padding=10)
        self.app = app
        self.regla_sel = None
        self._cargando = False
        self._construir()

    @property
    def est(self):
        return juego.estrategia(self.app.proyecto)

    def _elementos(self):
        return [e.get('nombre', '') for e in self.est['elementos']]

    def _personajes(self):
        """[(índice de enemigo, nombre)] de los personajes con los que se habla."""
        return [(i, en['nombre']) for i, en in enumerate(self.app.proyecto['enemigos'])
                if en.get('comportamiento') == 'personaje']

    # ---------------- interfaz ----------------
    def _construir(self):
        guia = ttk.Frame(self); guia.pack(fill='x', pady=(0, 8))
        pasos = (('1  Inventario', 'Crea aquí los elementos (llave, amuleto…).'),
                 ('2  Colócalos', 'Tiles: objeto «Guardar elemento», «Altar» o «Puerta a otra fase». '
                                  'Personajes: comportamiento «personaje».'),
                 ('3  Reglas', 'Escribe qué pasa: cuando… si lleva… entonces…'))
        for k, (t, d) in enumerate(pasos):
            c = ttk.Frame(guia, padding=(0, 0, 18, 0)); c.grid(row=0, column=k, sticky='nw')
            ttk.Label(c, text=t, style='Seccion.TLabel').pack(anchor='w')
            ttk.Label(c, text=d, style='Ayuda.TLabel', wraplength=330, justify='left').pack(anchor='w')
        cuerpo = ttk.Frame(self); cuerpo.pack(fill='both', expand=True)
        cuerpo.columnconfigure(1, weight=1); cuerpo.rowconfigure(0, weight=1)

        # ---- columna izquierda: inventario y marcador
        izq = ttk.Frame(cuerpo); izq.grid(row=0, column=0, sticky='nsw')
        el = ttk.LabelFrame(izq, text=f'Inventario (máx. {juego.MAX_ELEMENTOS})', padding=8)
        el.pack(fill='x')
        self.l_elem = tk.Listbox(el, height=5, width=20, exportselection=False, activestyle='none')
        self.l_elem.pack(fill='x'); self.l_elem.bind('<<ListboxSelect>>', lambda e: self._elem_cargar())
        f = ttk.Frame(el); f.pack(fill='x', pady=(6, 2))
        ttk.Label(f, text='Nombre').grid(row=0, column=0, sticky='w')
        self.v_enom = tk.StringVar(); ttk.Entry(f, textvariable=self.v_enom, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(f, text='Símbolo').grid(row=1, column=0, sticky='w')
        self.v_esim = tk.StringVar(); ttk.Entry(f, textvariable=self.v_esim, width=3).grid(row=1, column=1, padx=4, sticky='w')
        b = ttk.Frame(el); b.pack(fill='x', pady=(4, 0))
        ttk.Button(b, text='Añadir', width=8, command=self._elem_anadir).pack(side='left')
        ttk.Button(b, text='Cambiar', width=8, command=self._elem_aplicar).pack(side='left', padx=4)
        ttk.Button(b, text='Borrar', width=8, command=self._elem_borrar).pack(side='left')
        ttk.Label(el, text='El símbolo es la letra que sale en el marcador.', style='Ayuda.TLabel',
                  wraplength=230).pack(anchor='w', pady=(6, 0))
        hud = ttk.LabelFrame(izq, text='En el marcador', padding=8); hud.pack(fill='x', pady=(10, 0))
        self.v_hud = tk.BooleanVar()
        ttk.Checkbutton(hud, text='Mostrar el inventario', variable=self.v_hud,
                        command=self._hud_aplicar).grid(row=0, column=0, columnspan=2, sticky='w')
        self.v_hfila, self.v_hcol = tk.StringVar(), tk.StringVar()
        self.v_htinta, self.v_hbrillo = tk.StringVar(), tk.BooleanVar()
        for k, (txt, var, a, z) in enumerate((('Fila', self.v_hfila, 0, 23), ('Columna', self.v_hcol, 0, 31))):
            ttk.Label(hud, text=txt).grid(row=1 + k, column=0, sticky='w')
            sp = ttk.Spinbox(hud, from_=a, to=z, textvariable=var, width=5, command=self._hud_aplicar)
            sp.grid(row=1 + k, column=1, sticky='w', pady=1); sp.bind('<FocusOut>', lambda e: self._hud_aplicar())
        ttk.Label(hud, text='Color').grid(row=3, column=0, sticky='w')
        estilo.color_combo(hud, self.v_htinta, self.v_hbrillo, self._hud_aplicar).grid(row=3, column=1, sticky='w')
        fa = ttk.LabelFrame(izq, text='Altar sin ninguna regla que se cumpla', padding=8)
        fa.pack(fill='x', pady=(10, 0))
        self.m_falta = estilo.CampoMensaje(fa, al_cambiar=self._falta_aplicar, ancho=20)
        self.m_falta.pack(anchor='w')
        ttk.Label(fa, text='Vacío = no dice nada.', style='Ayuda.TLabel').pack(anchor='w')

        # ---- centro: reglas
        rg = ttk.LabelFrame(cuerpo, text=f'Reglas (máx. {juego.MAX_REGLAS}): se aplica la primera que se cumple',
                            padding=8)
        rg.grid(row=0, column=1, sticky='nsew', padx=10)
        rg.columnconfigure(0, weight=1)
        self.l_reg = tk.Listbox(rg, height=7, exportselection=False, activestyle='none')
        self.l_reg.grid(row=0, column=0, sticky='we'); self.l_reg.bind('<<ListboxSelect>>', lambda e: self._regla_cargar())
        b = ttk.Frame(rg); b.grid(row=1, column=0, sticky='w', pady=6)
        for txt, cmd in (('+ Nueva regla', self._regla_nueva), ('Borrar', self._regla_borrar),
                         ('↑', lambda: self._regla_mover(-1)), ('↓', lambda: self._regla_mover(1))):
            ttk.Button(b, text=txt, command=cmd, width=len(txt) + 3 if len(txt) > 2 else 3).pack(side='left', padx=(0, 4))
        self.ed = ttk.Frame(rg); self.ed.grid(row=2, column=0, sticky='nwe')
        ed = self.ed
        self.l_reg.bind('<Configure>', lambda e: self.l_regla.configure(wraplength=max(300, e.width - 10)))
        self.v_cuando = tk.StringVar(); self.v_pers = tk.StringVar(); self.v_modo = tk.StringVar()
        self.v_accion = tk.StringVar(); self.v_valor = tk.StringVar(value='1'); self.v_dar = tk.StringVar()
        self.v_puntos = tk.StringVar(value='0'); self.v_gasta = tk.BooleanVar(value=True)
        def titulo(fila, txt):
            ttk.Label(ed, text=txt, style='Seccion.TLabel', width=10).grid(row=fila, column=0, sticky='nw', pady=(6, 0))
        # CUANDO
        titulo(0, 'CUANDO')
        cu = ttk.Frame(ed); cu.grid(row=0, column=1, sticky='w', pady=(6, 0))
        self.c_cuando = ttk.Combobox(cu, textvariable=self.v_cuando, state='readonly', width=28,
                                     values=['toque un altar', 'hable con un personaje',
                                             'complete el conjunto (al recoger)'])
        self.c_cuando.pack(side='left'); self.c_cuando.bind('<<ComboboxSelected>>', lambda e: self._editado())
        self.c_pers = ttk.Combobox(cu, textvariable=self.v_pers, state='readonly', width=16)
        self.c_pers.bind('<<ComboboxSelected>>', lambda e: self._editado())
        # SI LLEVA
        titulo(1, 'SI LLEVA')
        si = ttk.Frame(ed); si.grid(row=1, column=1, sticky='w', pady=(6, 0))
        self.c_modo = ttk.Combobox(si, values=list(MODOS), textvariable=self.v_modo, state='readonly', width=16)
        self.c_modo.grid(row=0, column=0, sticky='nw'); self.c_modo.bind('<<ComboboxSelected>>', lambda e: self._editado())
        self.f_nec = ttk.Frame(si); self.f_nec.grid(row=0, column=1, sticky='w', padx=8)
        self.v_nec = [tk.BooleanVar() for _ in range(juego.MAX_ELEMENTOS)]
        # ENTONCES
        titulo(2, 'ENTONCES')
        en = ttk.Frame(ed); en.grid(row=2, column=1, sticky='w', pady=(6, 0))
        self.c_accion = ttk.Combobox(en, values=list(RESULTADOS), textvariable=self.v_accion, state='readonly', width=24)
        self.c_accion.pack(side='left'); self.c_accion.bind('<<ComboboxSelected>>', lambda e: self._editado())
        self.c_dar = ttk.Combobox(en, textvariable=self.v_dar, state='readonly', width=16)
        self.c_dar.bind('<<ComboboxSelected>>', lambda e: self._editado())
        self.s_fase = ttk.Spinbox(en, from_=1, to=16, textvariable=self.v_valor, width=5, command=self._editado)
        self.s_fase.bind('<FocusOut>', lambda e: self._editado())
        # Y ADEMÁS
        titulo(3, 'Y ADEMÁS')
        ya = ttk.Frame(ed); ya.grid(row=3, column=1, sticky='w', pady=(6, 0))
        ttk.Label(ya, text='suma').pack(side='left')
        sp = ttk.Spinbox(ya, from_=0, to=990, increment=10, textvariable=self.v_puntos, width=6, command=self._editado)
        sp.pack(side='left', padx=4); sp.bind('<FocusOut>', lambda e: self._editado())
        ttk.Label(ya, text='puntos').pack(side='left')
        ttk.Checkbutton(ed, text='Se gastan los elementos que pide',
                        variable=self.v_gasta, command=self._editado).grid(row=5, column=1, sticky='w', pady=(4, 0))
        titulo(4, 'Y DICE')
        self.m_msg = estilo.CampoMensaje(ed, al_cambiar=self._editado)
        self.m_msg.grid(row=4, column=1, sticky='w', pady=(6, 0))
        self.l_regla = ttk.Label(rg, style='Ayuda.TLabel', wraplength=480, justify='left')
        self.l_regla.grid(row=3, column=0, sticky='w', pady=(10, 0))

        # ---- derecha: resumen de la estrategia (qué hay y dónde)
        der = ttk.LabelFrame(cuerpo, text='Resumen del juego', padding=8)
        der.grid(row=0, column=2, sticky='nse')
        self.t_res = tk.Text(der, width=32, height=20, wrap='word', relief='flat', bg=estilo.PANEL,
                             font=(estilo.familia(), 9), padx=6, pady=6)
        self.t_res.pack(fill='both', expand=True)
        self.t_res.tag_configure('t', font=(estilo.familia(), 9, 'bold'), foreground=estilo.ACENTO_OSCURO)
        self.t_res.tag_configure('aviso', foreground=estilo.AVISO)
        self.t_res.tag_configure('suave', foreground=estilo.SUAVE)

    # ---------------- elementos ----------------
    def _elem_cargar(self):
        s = self.l_elem.curselection()
        if not s: return
        el = self.est['elementos'][s[0]]
        self.v_enom.set(el.get('nombre', '')); self.v_esim.set(el.get('simbolo', ''))

    def _elem_anadir(self):
        els = self.est['elementos']
        if len(els) >= juego.MAX_ELEMENTOS: return
        els.append({'nombre': self.v_enom.get().strip() or f'Elemento {len(els) + 1}',
                    'simbolo': (self.v_esim.get().strip() or str(len(els) + 1))[:1].upper()})
        self.app.marcar_cambio('elementos'); self.refrescar()

    def _elem_aplicar(self):
        s = self.l_elem.curselection()
        if not s: return
        el = self.est['elementos'][s[0]]
        el['nombre'] = self.v_enom.get().strip() or el['nombre']
        el['simbolo'] = (self.v_esim.get().strip() or el['simbolo'])[:1].upper()
        self.app.marcar_cambio('elementos'); self.refrescar()

    def _elem_borrar(self):
        s = self.l_elem.curselection()
        if not s: return
        k = s[0]; del self.est['elementos'][k]
        for r in self.est['reglas']:                     # los índices posteriores bajan uno
            r['necesita'] = [x - (x > k) for x in r.get('necesita', []) if x != k]
            if r.get('accion') == 'guardar' and r.get('valor', 0) >= k: r['valor'] = max(0, r.get('valor', 0) - 1)
        for t in self.app.proyecto['tiles']:
            if t.get('accion') == 'guardar' and t.get('valor', 0) >= k: t['valor'] = max(0, t.get('valor', 0) - 1)
            if t.get('accion') == 'puerta' and t.get('llave', -1) >= k:
                t['llave'] = -1 if t['llave'] == k else t['llave'] - 1
        self.app.marcar_cambio('elementos'); self.refrescar()

    def _hud_aplicar(self):
        if self._cargando: return
        def n(v, d):
            try: return int(v.get())
            except (ValueError, tk.TclError): return d
        tinta = int((self.v_htinta.get() or '6')[0])
        self.est['hud'] = {'activo': bool(self.v_hud.get()), 'fila': max(0, min(23, n(self.v_hfila, 23))),
                           'col': max(0, min(31, n(self.v_hcol, 22))),
                           'atr': tinta | (0x40 if self.v_hbrillo.get() else 0)}
        self.app.marcar_cambio('marcador')

    def _falta_aplicar(self):
        if self._cargando: return
        self.est['falta'] = self.m_falta.get()
        self.app.marcar_cambio('altar'); self._resumen_juego()

    # ---------------- reglas ----------------
    def _frase(self, r):
        els = self._elementos()
        nombres = [els[i] for i in r.get('necesita', []) if i < len(els)]
        c = r.get('cuando', 'altar')
        if c == 'personaje':
            en = self.app.proyecto['enemigos']
            k = r.get('personaje', -1)
            cuando = f'al hablar con {en[k]["nombre"] if 0 <= k < len(en) else "?"}'
        elif c == 'al_completar': cuando = 'al completar'
        else: cuando = 'en un altar'
        si = (' + '.join(nombres) if nombres else 'nada') + (' (exacto)' if r.get('modo') == 'exacta' and nombres else '')
        acc = r.get('accion', 'mensaje')
        res = _clave(RESULTADOS, acc, '?').lower()
        if acc == 'guardar':
            v = r.get('valor', 0); res = f'dar {els[v] if 0 <= v < len(els) else "?"}'
        elif acc == 'fase': res = f'ir a la fase {r.get("valor", 1)}'
        if r.get('puntos'): res += f', +{r["puntos"]}'
        return f'{cuando[0].upper() + cuando[1:]}, si lleva {si} → {res}'

    def _regla_cargar(self):
        s = self.l_reg.curselection()
        if not s: return
        self.regla_sel = s[0]; r = self.est['reglas'][s[0]]
        self._cargando = True
        for i, v in enumerate(self.v_nec): v.set(i in r.get('necesita', []))
        self.v_modo.set(_clave(MODOS, r.get('modo', 'contiene'), 'al menos estos'))
        c = r.get('cuando', 'altar')
        self.v_cuando.set({'altar': 'toque un altar', 'personaje': 'hable con un personaje'}.get(
            c, 'complete el conjunto (al recoger)'))
        en = self.app.proyecto['enemigos']; k = r.get('personaje', -1)
        self.v_pers.set(en[k]['nombre'] if 0 <= k < len(en) else '')
        self.v_accion.set(_clave(RESULTADOS, r.get('accion', 'mensaje'), 'Mostrar el mensaje y seguir'))
        els = self._elementos(); v = r.get('valor', 0)
        self.v_dar.set(els[v] if r.get('accion') == 'guardar' and 0 <= v < len(els) else '')
        self.v_valor.set(str(r.get('valor', 1)) if r.get('accion') == 'fase' else '1')
        self.v_puntos.set(str(r.get('puntos', 0))); self.v_gasta.set(r.get('gasta', True))
        self.m_msg.set(r.get('mensaje', ''))
        self._cargando = False
        self._mostrar_campos()

    def _mostrar_campos(self):
        """Solo se ven los campos que tienen sentido para la regla."""
        hay = self.regla_sel is not None and self.regla_sel < len(self.est['reglas'])
        if not hay:
            self.ed.grid_remove()
            self.l_regla.configure(text='Pulsa «+ Nueva regla» o elige una de la lista para editarla.')
            return
        self.ed.grid()
        if self.v_cuando.get() == 'hable con un personaje':
            self.c_pers.pack(side='left', padx=6)
        else:
            self.c_pers.pack_forget()
        acc = RESULTADOS.get(self.v_accion.get(), 'mensaje')
        self.c_dar.pack_forget(); self.s_fase.pack_forget()
        if acc == 'guardar': self.c_dar.pack(side='left', padx=6)
        if acc == 'fase': self.s_fase.pack(side='left', padx=6)
        r = self.est['reglas'][self.regla_sel]
        ayuda = []
        if r.get('cuando') == 'personaje':
            ayuda.append('Si esta regla no se cumple, el personaje dice su propio mensaje (pestaña Personajes).')
            if not self._personajes():
                ayuda.append('Todavía no hay ningún personaje: en la pestaña Personajes pon a un enemigo el '
                             'comportamiento «personaje».')
        if r.get('cuando') == 'al_completar':
            ayuda.append('Se comprueba cada vez que se recoge un elemento: sirve para «cuando tengas las tres '
                         'gemas, pasa…».')
        if r.get('cuando') == 'altar':
            ayuda.append('Se comprueba al tocar un tile con la respuesta «Altar».')
        if not r.get('necesita'):
            ayuda.append('Sin elementos marcados la regla se cumple siempre (salvo «al completar»).')
        self.l_regla.configure(text='  '.join(ayuda))

    def _editado(self):
        if self._cargando or self.regla_sel is None or self.regla_sel >= len(self.est['reglas']): return
        def n(v, d):
            try: return int(v.get())
            except (ValueError, tk.TclError): return d
        r = self.est['reglas'][self.regla_sel]
        r['necesita'] = [i for i, v in enumerate(self.v_nec) if v.get() and i < len(self.est['elementos'])]
        r['modo'] = MODOS.get(self.v_modo.get(), 'contiene')
        r['cuando'] = {'toque un altar': 'altar', 'hable con un personaje': 'personaje'}.get(
            self.v_cuando.get(), 'al_completar')
        if r['cuando'] == 'personaje':
            nombres = {nom: i for i, nom in self._personajes()}
            if self.v_pers.get() not in nombres and nombres:
                self.v_pers.set(next(iter(nombres)))
            r['personaje'] = nombres.get(self.v_pers.get(), -1)
        else:
            r.pop('personaje', None)
        r['accion'] = RESULTADOS.get(self.v_accion.get(), 'mensaje')
        if r['accion'] == 'guardar':
            els = self._elementos()
            if self.v_dar.get() not in els and els: self.v_dar.set(els[0])
            r['valor'] = els.index(self.v_dar.get()) if self.v_dar.get() in els else 0
        else:
            r['valor'] = max(1, min(16, n(self.v_valor, 1)))
        r['puntos'] = max(0, min(990, n(self.v_puntos, 0)) // 10 * 10)
        r['mensaje'] = self.m_msg.get(); r['gasta'] = bool(self.v_gasta.get())
        self.app.marcar_cambio('reglas')
        k = self.regla_sel
        self.l_reg.delete(k); self.l_reg.insert(k, f'{k + 1}. ' + self._frase(r)); self.l_reg.selection_set(k)
        self._mostrar_campos(); self._resumen_juego()

    def _regla_nueva(self):
        if len(self.est['reglas']) >= juego.MAX_REGLAS: return
        pers = self._personajes()
        r = {'necesita': [], 'modo': 'contiene', 'cuando': 'personaje' if pers else 'altar', 'accion': 'mensaje',
             'valor': 1, 'puntos': 0, 'mensaje': '', 'gasta': True}
        if pers: r['personaje'] = pers[0][0]
        self.est['reglas'].append(r)
        self.regla_sel = len(self.est['reglas']) - 1
        self.app.marcar_cambio('reglas'); self.refrescar()

    def _regla_borrar(self):
        s = self.l_reg.curselection()
        if not s: return
        del self.est['reglas'][s[0]]; self.regla_sel = None
        self.app.marcar_cambio('reglas'); self.refrescar()

    def _regla_mover(self, d):
        s = self.l_reg.curselection()
        if not s: return
        k = s[0]; rs = self.est['reglas']
        if not 0 <= k + d < len(rs): return
        rs[k], rs[k + d] = rs[k + d], rs[k]
        self.regla_sel = k + d
        self.app.marcar_cambio('reglas'); self.refrescar()

    # ---------------- resumen ----------------
    def _resumen_juego(self):
        p = self.app.proyecto; els = self._elementos(); t = self.t_res
        t.configure(state='normal'); t.delete('1.0', 'end')
        nfases = len(p['niveles'])
        def donde(idx_tile):
            fs = [str(n + 1) for n, nv in enumerate(p['niveles'])
                  if any(idx_tile in fila for fila in nv['mapa'])]
            return ('fase ' + ', '.join(fs)) if fs else 'sin colocar en el mapa'
        def tipo_en(i):
            fs = [str(n + 1) for n, nv in enumerate(p['niveles']) if any(a['tipo'] == i for a in nv['apariciones'])]
            return ('fase ' + ', '.join(fs)) if fs else 'sin colocar en el mapa'
        consigue = {k: [] for k in range(len(els))}
        piden = {k: [] for k in range(len(els))}
        t.insert('end', 'Objetos que dan elementos\n', 't')
        hay = False
        for i, tl in enumerate(p['tiles']):
            if tl.get('objeto') and tl.get('accion') == 'guardar':
                v = tl.get('valor', 0); hay = True
                nombre = els[v] if 0 <= v < len(els) else '?'
                consigue.setdefault(v, []).append(f'tile {i}')
                t.insert('end', f'• Tile {i} → {nombre}  ({donde(i)})\n')
        if not hay: t.insert('end', '  (ninguno)\n', 'suave')
        t.insert('end', '\nPuertas\n', 't'); hay = False
        for i, tl in enumerate(p['tiles']):
            if juego.es_puerta(tl):
                hay = True; k = tl.get('llave', -1)
                if 0 <= k < len(els): piden[k].append(f'puerta {i}')
                nec = f', necesita {els[k]}' if 0 <= k < len(els) else ''
                t.insert('end', f'• Tile {i} → fase {tl.get("valor", 1)}, columna {tl.get("columna", 0)}{nec}'
                                f'  ({donde(i)})\n')
                if not 1 <= tl.get('valor', 1) <= nfases: t.insert('end', '   ¡esa fase no existe!\n', 'aviso')
        if not hay: t.insert('end', '  (ninguna)\n', 'suave')
        t.insert('end', '\nPersonajes que hablan\n', 't'); hay = False
        for i, nom in self._personajes():
            hay = True
            t.insert('end', f'• {nom}  ({tipo_en(i)})\n')
            msg = p['enemigos'][i].get('mensaje', '')
            if msg: t.insert('end', f'   «{msg.replace("|", " / ")}»\n', 'suave')
        if not hay: t.insert('end', '  (ninguno)\n', 'suave')
        t.insert('end', '\nAltares\n', 't'); hay = False
        for i, tl in enumerate(p['tiles']):
            if tl.get('objeto') and tl.get('accion') == 'altar':
                hay = True; t.insert('end', f'• Tile {i}  ({donde(i)})\n')
        if not hay: t.insert('end', '  (ninguno)\n', 'suave')
        for r in self.est['reglas']:
            if r.get('accion') == 'guardar': consigue.setdefault(r.get('valor', 0), []).append('regla')
            for k in r.get('necesita', []): piden.setdefault(k, []).append('regla')
        avisos = []
        for k, nom in enumerate(els):
            if piden.get(k) and not consigue.get(k):
                avisos.append(f'«{nom}» se pide pero nada lo da.')
            if consigue.get(k) and not piden.get(k):
                avisos.append(f'«{nom}» se consigue pero nada lo pide (solo adorna el inventario).')
        for r in self.est['reglas']:
            if r.get('cuando') == 'personaje' and r.get('personaje', -1) not in dict(self._personajes()):
                avisos.append('Una regla habla con un personaje que ya no existe.')
        t.insert('end', '\nComprobación\n', 't')
        if avisos:
            for a in avisos: t.insert('end', f'• {a}\n', 'aviso')
        else:
            t.insert('end', '  Todo encaja.\n', 'suave')
        t.configure(state='disabled')

    # ---------------- refresco ----------------
    def refrescar(self):
        e = self.est
        self._cargando = True
        self.l_elem.delete(0, 'end')
        for i, el in enumerate(e['elementos']):
            self.l_elem.insert('end', f' [{el.get("simbolo", "?")}]  {el.get("nombre", "")}')
        for w in self.f_nec.winfo_children(): w.destroy()
        for i, el in enumerate(e['elementos']):
            ttk.Checkbutton(self.f_nec, text=el.get('nombre', ''), variable=self.v_nec[i],
                            command=self._editado).grid(row=i // 4, column=i % 4, sticky='w', padx=(0, 8))
        if not e['elementos']:
            ttk.Label(self.f_nec, text='(crea elementos en el inventario)', style='Ayuda.TLabel').grid(row=0, column=0)
        self.c_pers.configure(values=[n for _, n in self._personajes()])
        self.c_dar.configure(values=self._elementos())
        self.l_reg.delete(0, 'end')
        for k, r in enumerate(e['reglas']): self.l_reg.insert('end', f'{k + 1}. ' + self._frase(r))
        h = e['hud']
        self.v_hud.set(h.get('activo', False)); self.v_hfila.set(str(h.get('fila', 23)))
        self.v_hcol.set(str(h.get('col', 22)))
        atr = h.get('atr', 0x46)
        self.v_htinta.set(estilo.COLORES[atr & 7]); self.v_hbrillo.set(bool(atr & 0x40))
        self.m_falta.set(e.get('falta', ''))
        self._cargando = False
        if self.regla_sel is not None and self.regla_sel < len(e['reglas']):
            self.l_reg.selection_set(self.regla_sel); self._regla_cargar()
        else:
            self.regla_sel = None; self._mostrar_campos()
        self._resumen_juego()
