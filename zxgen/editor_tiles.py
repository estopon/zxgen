"""Editor de tiles de 16x16 con un atributo por cuadro de 8x8."""
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

import graficos, pantalla, juego, estilo
from graficos import atributo, partes_atr

ACCIONES_TXT = {'Solo puntos': 'puntos', 'Vida extra': 'vida', 'Recuperar energía': 'energia',
                'Ir a otra fase': 'fase', 'Ganar el juego': 'ganar', 'Perder el juego': 'perder',
                'Mensaje y seguir': 'mensaje', 'Guardar elemento (inventario)': 'guardar',
                'Altar (comprueba las reglas)': 'altar', 'Puerta a otra fase': 'puerta'}
COLORES = ['0 Negro', '1 Azul', '2 Rojo', '3 Magenta', '4 Verde', '5 Cian', '6 Amarillo', '7 Blanco']
CELDA = 20          # tamaño de un píxel en el editor
MINI = 32           # tamaño de las miniaturas
POR_FILA = 6
CUADROS = ['Arriba izquierda', 'Arriba derecha', 'Abajo izquierda', 'Abajo derecha']


class EditorTiles(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        self.actual = 0
        self._fotos = []
        self._construir()

    @property
    def tiles(self):
        return self.app.proyecto['tiles']

    # ---------------- interfaz ----------------
    def _construir(self):
        izq = ttk.LabelFrame(self, text='Tiles', padding=4)
        izq.grid(row=0, column=0, rowspan=2, sticky='ns')
        self.paleta = tk.Canvas(izq, width=POR_FILA * (MINI + 4), height=420, bg='#333', highlightthickness=0)
        barra = ttk.Scrollbar(izq, orient='vertical', command=self.paleta.yview)
        self.paleta.configure(yscrollcommand=barra.set)
        self.paleta.grid(row=0, column=0); barra.grid(row=0, column=1, sticky='ns')
        self.paleta.bind('<Button-1>', self._clic_paleta)
        b = ttk.Frame(izq); b.grid(row=1, column=0, columnspan=2, pady=4)
        for txt, fn in (('Nuevo', self.nuevo), ('Duplicar', self.duplicar), ('Borrar', self.borrar)):
            ttk.Button(b, text=txt, command=fn, width=9).pack(side='left', padx=1)
        ttk.Button(izq, text='Importar PNG de tiles…', command=self.importar).grid(row=2, column=0, columnspan=2, sticky='we')
        self.info = ttk.Label(izq, text='')
        self.info.grid(row=3, column=0, columnspan=2, pady=4)

        centro = ttk.LabelFrame(self, text='Píxeles', padding=4)
        centro.grid(row=0, column=1, padx=8, sticky='nwe')
        herr = ttk.Frame(centro); herr.pack()
        self.v_herr = tk.StringVar(value='X')
        ttk.Radiobutton(herr, text='Tinta', value='X', variable=self.v_herr).pack(side='left', padx=4)
        ttk.Radiobutton(herr, text='Mezcla (tono medio)', value='m', variable=self.v_herr).pack(side='left', padx=4)
        self.lienzo = tk.Canvas(centro, width=16 * CELDA, height=16 * CELDA, highlightthickness=0)
        self.lienzo.pack()
        for ev in ('<Button-1>', '<B1-Motion>'):
            self.lienzo.bind(ev, lambda e: self._pintar(e, self.v_herr.get()))
        for ev, val in (('<Button-2>', 'm'), ('<B2-Motion>', 'm'), ('<Button-3>', '.'), ('<B3-Motion>', '.')):
            self.lienzo.bind(ev, lambda e, v=val: self._pintar(e, v))
        ttk.Label(centro, text='Clic izq.: herramienta · central: mezcla · dcho.: papel', style='Ayuda.TLabel').pack()
        b = ttk.Frame(centro); b.pack(pady=6)
        for k, (txt, fn) in enumerate((('Limpiar', self.limpiar), ('Invertir', self.invertir),
                                       ('Espejo ↔', lambda: self._transformar(lambda p: [f[::-1] for f in p])),
                                       ('Espejo ↕', lambda: self._transformar(lambda p: p[::-1])))):
            ttk.Button(b, text=txt, command=fn, width=10).grid(row=k // 2, column=k % 2, padx=1, pady=1)

        der = ttk.LabelFrame(self, text='Color por cuadro de 8×8', padding=8)
        der.grid(row=1, column=1, sticky='nwe', padx=8, pady=(8, 0))
        self.v_cuadro = tk.IntVar(value=0)
        cu = ttk.Frame(der); cu.grid(row=0, column=0, sticky='nw')
        for i, n in enumerate(CUADROS):
            ttk.Radiobutton(cu, text=n, value=i, variable=self.v_cuadro,
                            command=self._mostrar_atr).grid(row=i // 2, column=i % 2, sticky='w', padx=(0, 6))
        self.v_tinta = tk.StringVar(); self.v_papel = tk.StringVar(); self.v_brillo = tk.BooleanVar()
        co = ttk.Frame(der); co.grid(row=1, column=0, sticky='nw', pady=(6, 0))
        ttk.Label(co, text='Tinta').grid(row=0, column=0, sticky='w')
        ttk.Combobox(co, values=COLORES, textvariable=self.v_tinta, state='readonly', width=11).grid(row=0, column=1, padx=4)
        ttk.Label(co, text='Papel').grid(row=1, column=0, sticky='w')
        ttk.Combobox(co, values=COLORES, textvariable=self.v_papel, state='readonly', width=11).grid(row=1, column=1, padx=4, pady=2)
        ttk.Checkbutton(co, text='Brillo', variable=self.v_brillo).grid(row=0, column=2, sticky='w')
        bb = ttk.Frame(der); bb.grid(row=2, column=0, sticky='w', pady=(6, 0))
        ttk.Button(bb, text='Aplicar al cuadro', command=self._aplicar_atr).pack(side='left')
        ttk.Button(bb, text='A los 4', command=lambda: self._aplicar_atr(True)).pack(side='left', padx=4)
        ttk.Label(der, style='Ayuda.TLabel', wraplength=330, justify='left', text=(
            'Cada cuadro de 8×8 tiene dos colores (tinta y papel) y un brillo, como en el Spectrum. '
            'Mezcla = un tercer tono entre tinta y papel (solo en modo mezcla; si no, se ve como un damero).'
        )).grid(row=3, column=0, columnspan=2, sticky='w', pady=(6, 0))
        caja = ttk.LabelFrame(self, text='Propiedades en el juego', padding=8)
        caja.grid(row=0, column=2, rowspan=2, sticky='nsew')
        self.columnconfigure(2, weight=1)
        pr = ttk.Frame(caja); pr.pack(anchor='w', fill='x')
        prd = ttk.Frame(caja); prd.pack(anchor='w', fill='x', pady=(10, 0))
        self.v_solido = tk.BooleanVar(); self.v_detiene = tk.BooleanVar()
        ttk.Checkbutton(pr, text='Sólido (no se puede atravesar)', variable=self.v_solido,
                        command=self._propiedades).pack(anchor='w')
        ttk.Checkbutton(pr, text='Detiene los disparos', variable=self.v_detiene,
                        command=self._propiedades).pack(anchor='w')
        self.v_plataforma = tk.BooleanVar(); self.v_mortal = tk.BooleanVar()
        ttk.Checkbutton(pr, text='Plataforma (se pisa desde arriba)', variable=self.v_plataforma,
                        command=self._propiedades).pack(anchor='w')
        ttk.Checkbutton(pr, text='Mortal (quita energía al tocarla)', variable=self.v_mortal,
                        command=self._propiedades).pack(anchor='w')
        self.v_rompible = tk.BooleanVar(); self.v_fragil = tk.BooleanVar(); self.v_objeto = tk.BooleanVar()
        ttk.Checkbutton(pr, text='Rompible (golpes, disparos, cabezazo)', variable=self.v_rompible,
                        command=self._propiedades).pack(anchor='w')
        ttk.Checkbutton(pr, text='Frágil (se rompe al caer sobre él)', variable=self.v_fragil,
                        command=self._propiedades).pack(anchor='w')
        ttk.Checkbutton(pr, text='Objeto (se recoge o se usa al tocarlo)', variable=self.v_objeto,
                        command=lambda: (self._propiedades(), self._campos_accion())).pack(anchor='w')
        cam = ttk.Frame(prd); cam.pack(anchor='w')
        ttk.Label(cam, text='Después se cambia por el tile').grid(row=0, column=0, sticky='w')
        self.v_tras = tk.StringVar(value='0')
        ttk.Spinbox(cam, from_=0, to=255, textvariable=self.v_tras, width=5,
                    command=self._propiedades).grid(row=0, column=1, padx=4, sticky='w')
        ttk.Label(cam, text='Puntos').grid(row=1, column=0, sticky='w')
        self.v_puntos_t = tk.StringVar(value='0')
        ttk.Spinbox(cam, from_=0, to=990, increment=10, textvariable=self.v_puntos_t, width=5,
                    command=self._propiedades).grid(row=1, column=1, padx=4, sticky='w')
        ttk.Label(cam, text='Si es objeto, al tocarlo').grid(row=2, column=0, sticky='w')
        self.v_accion = tk.StringVar()
        cb = ttk.Combobox(cam, values=list(ACCIONES_TXT), textvariable=self.v_accion, state='readonly', width=27)
        cb.grid(row=2, column=1, padx=4, sticky='w'); cb.bind('<<ComboboxSelected>>', lambda e: self._cambio_accion())
        for w in cam.winfo_children():
            if isinstance(w, (ttk.Spinbox, ttk.Entry)): w.bind('<FocusOut>', lambda ev: self._propiedades())
        # campos que dependen de la respuesta (solo se ven los que hacen falta)
        self.f_acc = ttk.Frame(prd); self.f_acc.pack(anchor='w', fill='x', pady=(4, 0))
        self.v_valor = tk.StringVar(value='1'); self.v_columna = tk.StringVar(value='0')
        self.v_elem = tk.StringVar(); self.v_llave = tk.StringVar()
        self.w_fase = ttk.Spinbox(self.f_acc, from_=1, to=16, textvariable=self.v_valor, width=5, command=self._propiedades)
        self.w_col = ttk.Spinbox(self.f_acc, from_=0, to=255, textvariable=self.v_columna, width=5, command=self._propiedades)
        self.w_elem = ttk.Combobox(self.f_acc, textvariable=self.v_elem, state='readonly', width=18)
        self.w_llave = ttk.Combobox(self.f_acc, textvariable=self.v_llave, state='readonly', width=18)
        for w in (self.w_fase, self.w_col): w.bind('<FocusOut>', lambda ev: self._propiedades())
        for w in (self.w_elem, self.w_llave): w.bind('<<ComboboxSelected>>', lambda ev: self._propiedades())
        self.w_msg = estilo.CampoMensaje(self.f_acc, al_cambiar=self._propiedades)
        self.l_acc = ttk.Label(self.f_acc, style='Ayuda.TLabel', wraplength=380, justify='left')
        ttk.Label(caja, style='Ayuda.TLabel', justify='left', wraplength=380, text='En la paleta: esquina roja = sólido, azul = detiene disparos, amarilla = plataforma, magenta = mortal; borde naranja = rompible o frágil, verde = objeto.').pack(anchor='w', side='bottom', pady=(6, 0))

    # ---------------- dibujo ----------------
    def refrescar(self):
        if self.actual >= len(self.tiles):
            self.actual = len(self.tiles) - 1
        self._dibujar_paleta()
        self._dibujar_tile()
        self._mostrar_atr()

    def _dibujar_paleta(self):
        c = self.paleta; c.delete('all'); self._fotos = []; self._items = []
        for i, t in enumerate(self.tiles):
            x = (i % POR_FILA) * (MINI + 4) + 2; y = (i // POR_FILA) * (MINI + 4) + 2
            foto = ImageTk.PhotoImage(graficos.imagen_tile(t, MINI // 16))
            self._fotos.append(foto)
            self._items.append(c.create_image(x, y, image=foto, anchor='nw'))
            if t.get('solido'):
                c.create_polygon(x, y, x + 9, y, x, y + 9, fill='red', outline='white')
            if t.get('detiene'):
                c.create_polygon(x + MINI, y, x + MINI - 9, y, x + MINI, y + 9, fill='#3070ff', outline='white')
            if t.get('plataforma'):
                c.create_polygon(x, y + MINI, x + 9, y + MINI, x, y + MINI - 9, fill='yellow', outline='white')
            if t.get('mortal'):
                c.create_polygon(x + MINI, y + MINI, x + MINI - 9, y + MINI, x + MINI, y + MINI - 9, fill='magenta', outline='white')
            if t.get('rompible') or t.get('fragil'):
                c.create_rectangle(x + 2, y + 2, x + MINI - 2, y + MINI - 2, outline='orange', width=2)
            if t.get('objeto'):
                c.create_rectangle(x + 5, y + 5, x + MINI - 5, y + MINI - 5, outline='#40ff40', width=2)
            if i == self.actual:
                c.create_rectangle(x - 2, y - 2, x + MINI + 1, y + MINI + 1, outline='white', width=2)
        filas = (len(self.tiles) + POR_FILA - 1) // POR_FILA
        c.configure(scrollregion=(0, 0, POR_FILA * (MINI + 4), filas * (MINI + 4) + 4))
        self.info.configure(text=f'Tile {self.actual} de {len(self.tiles)}  ·  máx. 256')

    def _dibujar_tile(self):
        c = self.lienzo; c.delete('all')
        t = self.tiles[self.actual]
        img = graficos.imagen_tile(t, CELDA)
        self._foto_grande = ImageTk.PhotoImage(img)
        c.create_image(0, 0, image=self._foto_grande, anchor='nw')
        for k in range(17):
            ancho = 2 if k in (0, 8, 16) else 1
            col = '#888' if ancho == 2 else '#555'
            c.create_line(k * CELDA, 0, k * CELDA, 16 * CELDA, fill=col, width=ancho)
            c.create_line(0, k * CELDA, 16 * CELDA, k * CELDA, fill=col, width=ancho)

    def _propiedades(self):
        t = self.tiles[self.actual]
        t['solido'] = bool(self.v_solido.get()); t['detiene'] = bool(self.v_detiene.get())
        t['plataforma'] = bool(self.v_plataforma.get()); t['mortal'] = bool(self.v_mortal.get())
        t['rompible'] = bool(self.v_rompible.get()); t['fragil'] = bool(self.v_fragil.get())
        t['objeto'] = bool(self.v_objeto.get())
        def entero(v, defecto):
            try: return int(v.get())
            except ValueError: return defecto
        t['tras'] = max(0, min(len(self.tiles) - 1, entero(self.v_tras, 0)))
        t['puntos'] = max(0, min(990, entero(self.v_puntos_t, 0)))
        if getattr(self, '_cargando', False): return
        t['accion'] = ACCIONES_TXT.get(self.v_accion.get(), 'puntos')
        els = [e['nombre'] for e in juego.estrategia(self.app.proyecto)['elementos']]
        if t['accion'] == 'guardar':                           # elementos: por su nombre
            t['valor'] = els.index(self.v_elem.get()) if self.v_elem.get() in els else 0
        else:
            t['valor'] = max(1, min(16, entero(self.v_valor, 1)))
        if t['accion'] == 'puerta':
            t['columna'] = max(0, min(255, entero(self.v_columna, 0)))
            t['llave'] = els.index(self.v_llave.get()) if self.v_llave.get() in els else -1
        else:
            t.pop('columna', None); t.pop('llave', None)
        t['mensaje'] = self.w_msg.get()
        self._dibujar_paleta(); self.app.marcar_cambio('tiles')

    def _cambio_accion(self):
        if ACCIONES_TXT.get(self.v_accion.get()) in ('puerta', 'guardar', 'altar') and not self.v_objeto.get():
            self.v_objeto.set(True)
        self._propiedades(); self._campos_accion()

    def _campos_accion(self):
        """Muestra solo los campos que usa la respuesta elegida."""
        for w in self.f_acc.winfo_children(): w.grid_forget()
        acc = ACCIONES_TXT.get(self.v_accion.get(), 'puntos')
        if not self.v_objeto.get():
            self.l_acc.configure(text='Marca «Objeto» para que haga algo al tocarlo.')
            self.l_acc.grid(row=0, column=0, columnspan=2, sticky='w'); return
        els = [e['nombre'] for e in juego.estrategia(self.app.proyecto)['elementos']]
        self.w_elem.configure(values=els); self.w_llave.configure(values=['(no hace falta nada)'] + els)
        fila = 0
        def poner(texto, w):
            nonlocal fila
            ttk.Label(self.f_acc, text=texto).grid(row=fila, column=0, sticky='nw', pady=1)
            w.grid(row=fila, column=1, sticky='w', padx=4, pady=1); fila += 1
        ayuda = {'puntos': 'Se recoge y da los puntos.', 'vida': 'Se recoge y da una vida.',
                 'energia': 'Se recoge y llena la energía.',
                 'fase': 'Se recoge y lleva a esa fase (con el mensaje, si lo hay).',
                 'ganar': 'Termina el juego con éxito.', 'perder': 'Termina la partida.',
                 'mensaje': 'Se recoge y muestra el mensaje; la partida sigue.',
                 'guardar': 'Se recoge y mete el elemento en el inventario (pestaña Estrategia).',
                 'altar': 'No se recoge: al tocarlo se comprueban las reglas «al tocar un altar».',
                 'puerta': 'No se recoge: al tocarla (en plataformas, con abajo) lleva a la fase y columna '
                           'indicadas. Si necesita un elemento y no se lleva, muestra el mensaje.'}[acc]
        if acc in ('fase', 'puerta'): poner('Fase de destino', self.w_fase)
        if acc == 'puerta': poner('Entrar por la columna', self.w_col)
        if acc == 'puerta': poner('Necesita llevar', self.w_llave)
        if acc == 'guardar':
            if els: poner('Elemento', self.w_elem)
            else: ayuda += ' Antes crea algún elemento en la pestaña Estrategia.'
        if acc in ('fase', 'ganar', 'perder', 'mensaje', 'puerta'):
            poner('Mensaje si está cerrada' if acc == 'puerta' else 'Mensaje', self.w_msg)
        self.l_acc.configure(text=ayuda)
        self.l_acc.grid(row=fila, column=0, columnspan=2, sticky='w', pady=(4, 0))

    def _mostrar_atr(self):
        if not self.tiles: return
        t = self.tiles[self.actual]
        self.v_solido.set(bool(t.get('solido'))); self.v_detiene.set(bool(t.get('detiene')))
        self.v_plataforma.set(bool(t.get('plataforma'))); self.v_mortal.set(bool(t.get('mortal')))
        self.v_rompible.set(bool(t.get('rompible'))); self.v_fragil.set(bool(t.get('fragil')))
        self.v_objeto.set(bool(t.get('objeto')))
        self.v_tras.set(str(t.get('tras', 0))); self.v_puntos_t.set(str(t.get('puntos', 0)))
        self._cargando = True
        els = [e['nombre'] for e in juego.estrategia(self.app.proyecto)['elementos']]
        self.v_valor.set(str(t.get('valor', 1)) if t.get('accion') != 'guardar' else '1')
        self.v_elem.set(els[t.get('valor', 0)] if t.get('accion') == 'guardar' and 0 <= t.get('valor', 0) < len(els) else '')
        self.v_columna.set(str(t.get('columna', 0)))
        k = t.get('llave', -1)
        self.v_llave.set(els[k] if 0 <= k < len(els) else '(no hace falta nada)')
        self.w_msg.set(t.get('mensaje', ''))
        self.v_accion.set([k for k, v in ACCIONES_TXT.items() if v == t.get('accion', 'puntos')][0])
        self._cargando = False
        self._campos_accion()
        a = self.tiles[self.actual]['atr'][self.v_cuadro.get()]
        tinta, papel, br = partes_atr(a)
        self.v_tinta.set(COLORES[tinta]); self.v_papel.set(COLORES[papel]); self.v_brillo.set(bool(br))

    # ---------------- acciones ----------------
    def _clic_paleta(self, e):
        x = self.paleta.canvasx(e.x); y = self.paleta.canvasy(e.y)
        i = int(y // (MINI + 4)) * POR_FILA + int(x // (MINI + 4))
        if 0 <= i < len(self.tiles) and x < POR_FILA * (MINI + 4):
            self.actual = i; self.refrescar()

    def _pintar(self, e, valor):
        x, y = e.x // CELDA, e.y // CELDA
        if not (0 <= x < 16 and 0 <= y < 16): return
        t = self.tiles[self.actual]
        fila = t['pix'][y]
        if fila[x] == valor: return
        t['pix'][y] = fila[:x] + valor + fila[x + 1:]
        self._dibujar_tile()
        self._cambio(solo_tile=True)

    def _aplicar_atr(self, todos=False):
        a = atributo(int(self.v_tinta.get()[0]), int(self.v_papel.get()[0]), self.v_brillo.get())
        t = self.tiles[self.actual]
        for q in (range(4) if todos else [self.v_cuadro.get()]):
            t['atr'][q] = a
        self._dibujar_tile(); self._cambio()

    def _transformar(self, f):
        t = self.tiles[self.actual]
        t['pix'] = f(t['pix'])
        self._dibujar_tile(); self._cambio()

    def limpiar(self):
        self._transformar(lambda p: ['.' * 16] * 16)

    def invertir(self):
        self._transformar(lambda p: [f.translate(str.maketrans('X.', '.X')) for f in p])

    def nuevo(self):
        if len(self.tiles) >= 256: return
        self.tiles.append(graficos.tile_vacio())
        self.actual = len(self.tiles) - 1; self._cambio(); self.refrescar()

    def duplicar(self):
        if len(self.tiles) >= 256: return
        self.tiles.insert(self.actual + 1, copy.deepcopy(self.tiles[self.actual]))
        self._renumerar(lambda v: v + 1 if v > self.actual else v)
        self.actual += 1; self._cambio(); self.refrescar()

    def borrar(self):
        if len(self.tiles) <= 1:
            messagebox.showinfo('Tiles', 'Tiene que quedar al menos un tile.'); return
        usos = sum(f.count(self.actual) for nv in self.app.proyecto['niveles'] for f in nv['mapa'])
        if usos and not messagebox.askyesno('Borrar tile',
                                            f'El tile se usa {usos} veces en el mapa; esas casillas pasarán al tile 0. ¿Seguir?'):
            return
        i = self.actual
        del self.tiles[i]
        self._renumerar(lambda v: 0 if v == i else (v - 1 if v > i else v))
        self._cambio(); self.refrescar()

    def _renumerar(self, f):
        for nv in self.app.proyecto['niveles']:
            m = nv['mapa']
            for y, fila in enumerate(m):
                m[y] = [f(v) for v in fila]

    def importar(self):
        """Lee una imagen con tiles de 16x16 en rejilla y los añade al final."""
        ruta = filedialog.askopenfilename(filetypes=[('Imágenes', '*.png *.gif *.bmp'), ('Todos', '*.*')])
        if not ruta: return
        img = Image.open(ruta).convert('RGB'); px = img.load()
        nx, ny = img.width // 16, img.height // 16
        if nx * ny == 0:
            messagebox.showerror('Importar', 'La imagen debe medir al menos 16×16.'); return
        nuevos = 0
        for ty in range(ny):
            for tx in range(nx):
                if len(self.tiles) >= 256: break
                pix = [['.'] * 16 for _ in range(16)]; atr = []
                for q in range(4):
                    ox, oy = tx * 16 + (q % 2) * 8, ty * 16 + (q // 2) * 8
                    filas, a = pantalla.convertir_celda([px[ox + x, oy + y] for y in range(8) for x in range(8)])
                    atr.append(a)
                    for y in range(8):
                        for x in range(8):
                            if filas[y] & (0x80 >> x):
                                pix[(q // 2) * 8 + y][(q % 2) * 8 + x] = 'X'
                self.tiles.append({'pix': [''.join(f) for f in pix], 'atr': atr}); nuevos += 1
        self._cambio(); self.refrescar()
        messagebox.showinfo('Importar', f'{nuevos} tiles añadidos.')

    def _cambio(self, solo_tile=False):
        if not solo_tile:
            self._dibujar_paleta()
        else:
            # actualizar solo la miniatura del tile actual
            i = self.actual
            if i < len(self._items):
                self._fotos[i] = ImageTk.PhotoImage(graficos.imagen_tile(self.tiles[i], MINI // 16))
                self.paleta.itemconfigure(self._items[i], image=self._fotos[i])
        self.app.marcar_cambio('tiles')
