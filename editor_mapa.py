"""Editor del mapa.
Vertical:   12 tiles de ancho y tantas filas como se quiera; se empieza abajo.
Horizontal: 10 tiles de alto y tantas columnas como se quiera; se empieza a la izquierda.
Pantalla a pantalla y scroll libre: rejilla de pantallas de 12 x 10 tiles (hasta 16 x 16); las que
no existen no se pueden visitar (en el scroll libre se ven con el tile de relleno)."""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

import copy
from tkinter import simpledialog
import graficos, juego, estilo

T = 32            # tamaño de un tile en pantalla (x2)
MINI = 32


class EditorMapa(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        self.actual = 0
        self._fotos_tiles = []
        self._celdas = []
        self._construir()

    @property
    def mapa(self):
        return self.app.nivel()['mapa']

    @property
    def apariciones(self):
        return self.app.nivel()['apariciones']

    @property
    def horizontal(self):
        return juego.horizontal(self.app.proyecto)

    @property
    def dosd(self):
        return juego.multidir(self.app.proyecto)

    @property
    def f(self):
        """Celdas del mapa por tile de 16 píxeles (2 con tiles de 8x8)."""
        return juego.factor(self.app.proyecto)

    def _construir(self):
        fases = ttk.Frame(self); fases.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 6))
        ttk.Label(fases, text='Fase:').pack(side='left')
        self.v_fase = tk.StringVar()
        self.c_fase = ttk.Combobox(fases, textvariable=self.v_fase, state='readonly', width=18)
        self.c_fase.pack(side='left', padx=4)
        self.c_fase.bind('<<ComboboxSelected>>', lambda e: self._elegir_fase(self.c_fase.current()))
        for txt, fn in (('Nueva', self._nueva_fase), ('Duplicar', self._duplicar_fase), ('Borrar', self._borrar_fase),
                        ('Renombrar', self._renombrar_fase), ('↑', lambda: self._mover_fase(-1)), ('↓', lambda: self._mover_fase(1))):
            ttk.Button(fases, text=txt, command=fn, width=len(txt) + 2).pack(side='left', padx=1)
        ttk.Label(fases, text='  Las fases se juegan en este orden; todas comparten tiles y enemigos.',
                  style='Ayuda.TLabel').pack(side='left')
        izq = ttk.Frame(self); izq.grid(row=1, column=0, sticky='nsew')
        self.lienzo = tk.Canvas(izq, width=12 * T, height=480, bg='black', highlightthickness=0)
        self.barra_v = ttk.Scrollbar(izq, orient='vertical', command=self.lienzo.yview)
        self.barra_h = ttk.Scrollbar(izq, orient='horizontal', command=self.lienzo.xview)
        self.lienzo.configure(yscrollcommand=self.barra_v.set, xscrollcommand=self.barra_h.set)
        self.lienzo.grid(row=0, column=0, sticky='nsew')
        self.barra_v.grid(row=0, column=1, sticky='ns'); self.barra_h.grid(row=1, column=0, sticky='we')
        self.lienzo.bind('<Button-1>', lambda e: self._pintar(e, False))
        self.lienzo.bind('<B1-Motion>', lambda e: self._pintar(e, True))
        self.lienzo.bind('<Button-3>', self._cuentagotas)
        for ev, d in (('<Button-4>', -1), ('<Button-5>', 1)):
            self.lienzo.bind(ev, lambda e, d=d: self._rueda(d))
        self.lienzo.bind('<MouseWheel>', lambda e: self._rueda(-1 if e.delta > 0 else 1))

        marco_der = estilo.Desplazable(self); marco_der.grid(row=1, column=1, sticky='ns', padx=(10, 0))
        der = marco_der.interior
        self.rowconfigure(1, weight=1)
        modo = ttk.LabelFrame(der, text='Qué se edita', padding=6); modo.pack(fill='x', pady=(0, 8))
        self.v_modo = tk.StringVar(value='tiles')
        ttk.Radiobutton(modo, text='Tiles', value='tiles', variable=self.v_modo).grid(row=0, column=0, sticky='w')
        self.r_pant = ttk.Radiobutton(modo, text='Pantallas', value='pantallas', variable=self.v_modo,
                                      command=self._dibujar_rejilla)
        self.r_pant.grid(row=2, column=0, sticky='w')
        ttk.Radiobutton(modo, text='Enemigos:', value='enemigos', variable=self.v_modo).grid(row=0, column=1, sticky='w', padx=(12, 0))
        self.v_tipo = tk.StringVar()
        self.c_tipo = ttk.Combobox(modo, textvariable=self.v_tipo, state='readonly', width=16)
        self.c_tipo.grid(row=0, column=2, padx=4)
        self.c_tipo.bind('<<ComboboxSelected>>', lambda e: self.v_modo.set('enemigos'))
        self.l_enem = ttk.Label(modo, text='', style='Ayuda.TLabel')
        self.l_enem.grid(row=1, column=0, columnspan=3, sticky='w')
        ttk.Label(der, text='Tile para pintar  (clic dcho. en el mapa lo copia)').pack(anchor='w')
        self.paleta = tk.Canvas(der, width=8 * (MINI + 4), height=180, bg='#333', highlightthickness=0)
        self.paleta.pack(anchor='w')
        self.paleta.bind('<Button-1>', self._clic_paleta)
        self.f_rej = ttk.LabelFrame(der, text='Rejilla de pantallas (12 x 10 tiles cada una)', padding=6)
        self.f_rej.pack(fill='x', pady=8)
        rj = self.f_rej
        self.v_gw = tk.IntVar(value=3); self.v_gh = tk.IntVar(value=2)
        ttk.Label(rj, text='Ancho').grid(row=0, column=0, sticky='w')
        ttk.Spinbox(rj, from_=1, to=juego.MAX_REJILLA, textvariable=self.v_gw, width=4).grid(row=0, column=1, sticky='w')
        ttk.Label(rj, text='Alto').grid(row=0, column=2, sticky='w', padx=(8, 0))
        ttk.Spinbox(rj, from_=1, to=juego.MAX_REJILLA, textvariable=self.v_gh, width=4).grid(row=0, column=3, sticky='w')
        ttk.Button(rj, text='Aplicar', command=self._aplicar_rejilla).grid(row=0, column=4, padx=4)
        self.l_sel = ttk.Label(rj, text='', style='Ayuda.TLabel', wraplength=330, justify='left')
        self.l_sel.grid(row=1, column=0, columnspan=5, sticky='w', pady=(4, 2))
        bb = ttk.Frame(rj); bb.grid(row=2, column=0, columnspan=5, sticky='w')
        for i, (txt, fn) in enumerate((('Quitar / poner', self._alternar_pantalla), ('Empezar aquí', self._inicio_aqui),
                                       ('Copiar', self._copiar_pantalla), ('Pegar', self._pegar_pantalla))):
            ttk.Button(bb, text=txt, command=fn).grid(row=i // 2, column=i % 2, sticky='we', padx=1, pady=1)
        self.f_rell = ttk.Frame(rj); self.f_rell.grid(row=3, column=0, columnspan=5, sticky='w', pady=(4, 0))
        ttk.Button(self.f_rell, text='Relleno = tile elegido', command=self._fijar_relleno).pack(side='left')
        self.l_rell = ttk.Label(self.f_rell, text='', style='Ayuda.TLabel'); self.l_rell.pack(side='left', padx=6)
        zf = ttk.Frame(rj); zf.grid(row=4, column=0, columnspan=5, sticky='w', pady=(4, 0))
        ttk.Label(zf, text='Zoom').pack(side='left')
        self.v_zoom = tk.StringVar(value='x1')
        cz = ttk.Combobox(zf, values=['x1', 'x2'], textvariable=self.v_zoom, state='readonly', width=4)
        cz.pack(side='left', padx=4); cz.bind('<<ComboboxSelected>>', lambda e: self._dibujar_mapa())
        self.sel_pant = (0, 0); self.porta_pant = None
        f = ttk.LabelFrame(der, text='Longitud de la fase', padding=6); f.pack(fill='x', pady=8)
        self.f_largo = f
        self.info = ttk.Label(f, text='', wraplength=330, justify='left')
        self.info.grid(row=0, column=0, columnspan=4, sticky='w')
        self.l_largo = ttk.Label(f, text='Largo:'); self.l_largo.grid(row=1, column=0, sticky='w', pady=4)
        self.v_largo = tk.IntVar()
        ttk.Spinbox(f, from_=10, to=2000, textvariable=self.v_largo, width=6).grid(row=1, column=1, sticky='w')
        ttk.Button(f, text='Aplicar', command=self._aplicar_largo).grid(row=1, column=2, padx=4)
        ttk.Button(f, text='Rellenar todo con el tile elegido', command=self._rellenar).grid(row=2, column=0, columnspan=4, sticky='we')
        tr = ttk.LabelFrame(der, text='Tramos (posiciones desde el inicio de la fase)', padding=6); tr.pack(fill='x')
        self.f_tramos = tr
        self.v_desde = tk.IntVar(value=1); self.v_hasta = tk.IntVar(value=10)
        self.v_pos = tk.IntVar(value=1); self.v_veces = tk.IntVar(value=1)
        ttk.Label(tr, text='Desde').grid(row=0, column=0, sticky='w')
        ttk.Spinbox(tr, from_=1, to=2000, textvariable=self.v_desde, width=5, command=self._marcar_tramo).grid(row=0, column=1)
        ttk.Label(tr, text='hasta').grid(row=0, column=2)
        ttk.Spinbox(tr, from_=1, to=2000, textvariable=self.v_hasta, width=5, command=self._marcar_tramo).grid(row=0, column=3)
        ttk.Button(tr, text='Copiar', command=self._copiar_tramo).grid(row=1, column=0, columnspan=2, sticky='we', pady=2)
        ttk.Button(tr, text='Borrar', command=self._borrar_tramo).grid(row=1, column=2, columnspan=2, sticky='we', padx=2)
        ttk.Label(tr, text='Repetir detrás').grid(row=2, column=0, columnspan=2, sticky='w')
        ttk.Spinbox(tr, from_=1, to=50, textvariable=self.v_veces, width=4).grid(row=2, column=2, sticky='w')
        ttk.Button(tr, text='veces', command=self._repetir_tramo).grid(row=2, column=3, sticky='we', padx=2)
        ttk.Label(tr, text='Pegar lo copiado en').grid(row=3, column=0, columnspan=2, sticky='w')
        ttk.Spinbox(tr, from_=1, to=2001, textvariable=self.v_pos, width=5).grid(row=3, column=2, sticky='w')
        ttk.Button(tr, text='Pegar', command=self._pegar_tramo).grid(row=3, column=3, sticky='we', padx=2)
        self.l_porta = ttk.Label(tr, text='(nada copiado)', style='Ayuda.TLabel')
        self.l_porta.grid(row=4, column=0, columnspan=4, sticky='w')
        self.portapapeles = None
        self.ayuda = ttk.Label(der, justify='left', wraplength=300)
        self.ayuda.pack(anchor='w')

    # ---------------- dibujo ----------------
    def refrescar(self):
        niveles = self.app.proyecto['niveles']
        self.c_fase.configure(values=[f'{i + 1}. {n["nombre"]}' for i, n in enumerate(niveles)])
        self.c_fase.current(self.app.nivel_sel)
        global T
        T = (16 if (self.dosd and self.v_zoom.get() == 'x1') else 32) // self.f
        self._fotos_tiles = [ImageTk.PhotoImage(graficos.imagen_tile(t, max(1, T // len(t['pix']))))
                             for t in self.app.proyecto['tiles']]
        if self.actual >= len(self._fotos_tiles):
            self.actual = 0
        for w_, ver in ((self.f_rej, self.dosd), (self.f_largo, not self.dosd), (self.f_tramos, not self.dosd)):
            if ver and not w_.winfo_ismapped(): w_.pack(fill='x', pady=8, before=self.ayuda)
            if not ver and w_.winfo_ismapped(): w_.pack_forget()
        self.r_pant.configure(state='normal' if self.dosd else 'disabled')
        if not self.dosd and self.v_modo.get() == 'pantallas': self.v_modo.set('tiles')
        if self.dosd:
            self.lienzo.configure(width=640, height=480)
            libre = juego.libre(self.app.proyecto)
            if libre: self.f_rell.grid()
            else: self.f_rell.grid_remove()
            self.ayuda.configure(text=(
                'Cada recuadro blanco es una pantalla (12 x 10 tiles, el área entera). Las tachadas no existen: ' +
                ('el scroll no deja salir del rectángulo y se ven con el tile de relleno (ponlo sólido). '
                 if libre else 'no se puede pasar a ellas. ') +
                'La verde es la de inicio (el jugador empieza en su X e Y iniciales).\n\n'
                'Con «Qué se edita: Pantallas», un clic elige pantalla para los botones de la rejilla.'))
        elif self.horizontal:
            self.lienzo.configure(width=640, height=10 * self.f * T)
            self.l_largo.configure(text='Columnas:')
            self.ayuda.configure(text='La línea roja marca la pantalla inicial: el jugador empieza a la izquierda '
                                      'y el scroll avanza hacia la derecha hasta la última columna.\n\n'
                                      f'Cada columna del mapa son {16 // self.f} píxeles; la vista muestra {12 * self.f}.')
        else:
            self.lienzo.configure(width=12 * self.f * T, height=480)
            self.l_largo.configure(text='Filas:')
            self.ayuda.configure(text='La línea roja marca la pantalla inicial: el jugador empieza abajo y el '
                                      'scroll sube hasta la fila superior del mapa.\n\n'
                                      f'Cada fila del mapa son {16 // self.f} píxeles; la vista muestra {10 * self.f}.')
        nombres = [f'{i}: {e["nombre"]}' for i, e in enumerate(self.app.proyecto['enemigos'])]
        self.c_tipo.configure(values=nombres)
        if nombres and self.c_tipo.current() < 0: self.c_tipo.current(0)
        if not nombres: self.v_tipo.set('')
        self._fotos_enem = []
        for e in self.app.proyecto['enemigos']:
            self._fotos_enem.append(ImageTk.PhotoImage(self._imagen_enemigo(e)))
        self._dibujar_paleta()
        self._dibujar_mapa()

    def _imagen_enemigo(self, e):
        """Primer fotograma con transparencia, a escala x2."""
        pix = e['fotogramas'][0] if e['fotogramas'] else ['.']
        h, w = len(pix), len(pix[0])
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = img.load()
        for y in range(h):
            for x in range(w):
                if pix[y][x] == 'X': px[x, y] = (255, 255, 255, 255)
                elif pix[y][x] == 'o': px[x, y] = (0, 0, 0, 255)
        return img.resize((w * 2, h * 2), Image.NEAREST)

    def _dibujar_enemigos(self):
        c = self.lienzo; c.delete('enemigo')
        p = self.app.proyecto
        for a in self.apariciones:
            if not 0 <= a['tipo'] < len(self._fotos_enem): continue
            x, y = a['c'] * T, a['f'] * T
            c.create_image(x, y, image=self._fotos_enem[a['tipo']], anchor='nw', tags='enemigo')
            w, h = graficos.TAMANOS[p['enemigos'][a['tipo']]['tamano']]
            c.create_rectangle(x, y, x + w * 2, y + h * 2, outline='yellow', tags='enemigo')
            c.create_text(x + 2, y + 1, text=str(a['tipo']), fill='yellow', anchor='nw', tags='enemigo')
        self.l_enem.configure(text=f'{len(self.apariciones)} enemigos colocados · clic izq. coloca, clic dcho. quita')

    def _dibujar_paleta(self):
        c = self.paleta; c.delete('all')
        self._mini = []
        for i, t in enumerate(self.app.proyecto['tiles']):
            foto = ImageTk.PhotoImage(graficos.imagen_tile(t, MINI // len(t['pix'])))
            self._mini.append(foto)
            x = (i % 8) * (MINI + 4) + 2; y = (i // 8) * (MINI + 4) + 2
            c.create_image(x, y, image=foto, anchor='nw')
            if i == self.actual:
                c.create_rectangle(x - 2, y - 2, x + MINI + 1, y + MINI + 1, outline='white', width=2)
        filas = (len(self._mini) + 7) // 8
        c.configure(height=min(300, max(40, filas * (MINI + 4) + 4)))

    def _dibujar_mapa(self):
        c = self.lienzo; c.delete('all'); self._celdas = []
        alto, ancho = len(self.mapa), len(self.mapa[0]) if self.mapa else 0
        if self.dosd:
            self._fotos_tiles = [ImageTk.PhotoImage(graficos.imagen_tile(t, max(1, T // len(t['pix']))))
                                 for t in self.app.proyecto['tiles']]
        for y, fila in enumerate(self.mapa):
            items = []
            for x, v in enumerate(fila):
                foto = self._fotos_tiles[v] if v < len(self._fotos_tiles) else self._fotos_tiles[0]
                items.append(c.create_image(x * T, y * T, image=foto, anchor='nw'))
            self._celdas.append(items)
        if self.dosd:
            c.configure(scrollregion=(0, 0, ancho * T, alto * T))
            self._dibujar_rejilla()
            g = juego.rejilla(self.app.nivel(), self.f); gx0, gy0 = juego.inicio_rejilla(self.app.nivel(), self.f)
            c.xview_moveto(max(0.0, (gx0 - 0.5) / len(g[0]))); c.yview_moveto(max(0.0, (gy0 - 0.5) / len(g)))
        elif self.horizontal:
            x0 = 12 * self.f * T
            c.create_line(x0, 0, x0, alto * T, fill='red', width=2)
            for x in range(0, ancho, 10):
                c.create_text(x * T + 2, 2, text=str(x + 1), fill='white', anchor='nw')
            c.configure(scrollregion=(0, 0, ancho * T, alto * T))
            c.xview_moveto(0.0)
        else:
            y0 = (alto - 10 * self.f) * T
            c.create_line(0, y0, ancho * T, y0, fill='red', width=2)
            for y in range(0, alto, 10):
                c.create_text(3, y * T + 2, text=str(alto - y), fill='white', anchor='nw')
            c.configure(scrollregion=(0, 0, ancho * T, alto * T))
            c.yview_moveto(1.0)
        self._dibujar_enemigos()
        self._info()
        if not self.dosd:
            self.v_largo.set(juego.largo_nivel(self.app.nivel(), self.horizontal))
            self._marcar_tramo()

    def _dibujar_rejilla(self):
        """Bordes de las pantallas, las que no existen tachadas, la de inicio en verde y la elegida."""
        c = self.lienzo; c.delete('rejilla')
        if not self.dosd: return
        nv = self.app.nivel(); g = juego.rejilla(nv, self.f); gx0, gy0 = juego.inicio_rejilla(nv, self.f)
        PW, PH = juego.PANT_ANCHO * self.f * T, juego.PANT_ALTO * self.f * T
        for y, fila in enumerate(g):
            for x, hay in enumerate(fila):
                x0, y0 = x * PW, y * PH
                if not hay:
                    c.create_rectangle(x0, y0, x0 + PW, y0 + PH, fill='#202020', stipple='gray75', outline='', tags='rejilla')
                    c.create_line(x0, y0, x0 + PW, y0 + PH, fill='#ff6060', width=2, tags='rejilla')
                    c.create_line(x0 + PW, y0, x0, y0 + PH, fill='#ff6060', width=2, tags='rejilla')
                c.create_rectangle(x0, y0, x0 + PW, y0 + PH, outline='white', tags='rejilla')
        c.create_rectangle(gx0 * PW + 2, gy0 * PH + 2, (gx0 + 1) * PW - 2, (gy0 + 1) * PH - 2, outline='#40ff40',
                           width=3, tags='rejilla')
        if self.v_modo.get() == 'pantallas':
            sx, sy = self.sel_pant
            c.create_rectangle(sx * PW + 5, sy * PH + 5, (sx + 1) * PW - 5, (sy + 1) * PH - 5, outline='yellow',
                               width=3, dash=(6, 3), tags='rejilla')
        c.tag_raise('enemigo')
        self.v_gw.set(len(g[0])); self.v_gh.set(len(g))
        rell = nv.get('relleno', 0)
        self.l_rell.configure(text=f'tile {rell}' + ('' if rell < len(self.app.proyecto['tiles']) and
                                                     self.app.proyecto['tiles'][rell].get('solido') else ' (no es sólido)'))
        n = sum(sum(1 for v in f if v) for f in g)
        self.l_sel.configure(text=f'{n} pantallas de {len(g[0]) * len(g)}. Elegida: columna {self.sel_pant[0] + 1}, '
                                  f'fila {self.sel_pant[1] + 1}' + (f' · copiada: {self.porta_pant[0]}' if self.porta_pant else ''))

    def _aplicar_rejilla(self):
        try: gw, gh = int(self.v_gw.get()), int(self.v_gh.get())
        except (tk.TclError, ValueError): return
        gw, gh = max(1, min(juego.MAX_REJILLA, gw)), max(1, min(juego.MAX_REJILLA, gh))
        g = juego.rejilla(self.app.nivel(), self.f)
        if (gw < len(g[0]) or gh < len(g)) and not messagebox.askyesno(
                'Rejilla', 'Se quitarán las pantallas de la derecha o de abajo que no caben (con sus enemigos). ¿Seguir?'):
            return
        juego.fijar_rejilla(self.app.nivel(), gw, gh, self.actual, self.f)
        self.sel_pant = (min(self.sel_pant[0], gw - 1), min(self.sel_pant[1], gh - 1))
        self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _alternar_pantalla(self):
        nv = self.app.nivel(); g = juego.rejilla(nv, self.f); x, y = self.sel_pant
        if g[y][x] and sum(sum(1 for v in f if v) for f in g) <= 1:
            messagebox.showinfo('Pantallas', 'Tiene que quedar al menos una pantalla.'); return
        g[y][x] = not g[y][x]
        if not g[y][x]:
            nv['apariciones'] = [a for a in nv['apariciones']
                                 if (a['c'] // (juego.PANT_ANCHO * self.f), a['f'] // (juego.PANT_ALTO * self.f)) != (x, y)]
        nv['inicio'] = list(juego.inicio_rejilla(nv, self.f))
        self._dibujar_rejilla(); self._dibujar_enemigos(); self.app.marcar_cambio('mapa')

    def _inicio_aqui(self):
        nv = self.app.nivel(); g = juego.rejilla(nv, self.f); x, y = self.sel_pant
        if not g[y][x]:
            messagebox.showinfo('Pantallas', 'Esa pantalla no existe.'); return
        nv['inicio'] = [x, y]; self._dibujar_rejilla(); self.app.marcar_cambio('mapa')

    def _copiar_pantalla(self):
        x, y = self.sel_pant; PW, PH = juego.PANT_ANCHO * self.f, juego.PANT_ALTO * self.f
        nv = self.app.nivel()
        tiles = [fila[x * PW:(x + 1) * PW] for fila in self.mapa[y * PH:(y + 1) * PH]]
        enem = [(a['tipo'], a['f'] - y * PH, a['c'] - x * PW) for a in nv['apariciones']
                if (a['c'] // PW, a['f'] // PH) == (x, y)]
        self.porta_pant = (f'columna {x + 1}, fila {y + 1}', tiles, enem); self._dibujar_rejilla()

    def _pegar_pantalla(self):
        if not self.porta_pant:
            messagebox.showinfo('Pantallas', 'Primero copia una pantalla.'); return
        x, y = self.sel_pant; PW, PH = juego.PANT_ANCHO * self.f, juego.PANT_ALTO * self.f
        nv = self.app.nivel(); _, tiles, enem = self.porta_pant
        for f in range(PH):
            self.mapa[y * PH + f][x * PW:(x + 1) * PW] = list(tiles[f])
        nv['apariciones'] = [a for a in nv['apariciones'] if (a['c'] // PW, a['f'] // PH) != (x, y)]
        nv['apariciones'] += [{'tipo': t, 'f': f + y * PH, 'c': c + x * PW} for t, f, c in enem]
        juego.rejilla(nv, self.f)[y][x] = True
        self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _fijar_relleno(self):
        self.app.nivel()['relleno'] = self.actual; self._dibujar_rejilla(); self.app.marcar_cambio('mapa')

    def _info(self):
        p = self.app.proyecto
        if self.dosd:
            g = juego.rejilla(self.app.nivel(), self.f); n = sum(sum(1 for v in f if v) for f in g)
            q = juego.expandir_t8(p)
            if juego.libre(p):
                W, H, k, d = juego.mapa_libre(q, q['niveles'][self.app.nivel_sel])
                usado = 32 + 36 * len(q['tiles']) + len(d)
                txt = f'{n} pantallas en una rejilla de {len(g[0])} x {len(g)} ({W} x {H} tiles; cada fila se guarda con {1 << k})'
            else:
                usado = 32 + 36 * len(q['tiles']) + n * 126 + len(g) * len(g[0]) + 4
                txt = f'{n} pantallas en una rejilla de {len(g[0])} x {len(g)}'
            self.info.configure(text=f'{txt}\nBanco del nivel: unos {usado} de 16384 bytes')
            return
        q = juego.expandir_t8(p)
        usado = 32 + 36 * len(q['tiles']) + len(self.mapa) * len(self.mapa[0]) // (self.f * self.f)
        lado = 16 // self.f
        if self.horizontal:
            n = len(self.mapa[0]); txt = f'{n} columnas: {n * lado} píxeles, unas {n / (12 * self.f):.0f} pantallas'
        else:
            n = len(self.mapa); txt = f'{n} filas: {n * lado} píxeles, unas {n / (10 * self.f):.0f} pantallas'
        if self.f == 2: txt += f'\n{len(q["tiles"])} grupos distintos de 2×2 tiles (máx. {128 if juego.modo_bloques(p) else 256})'
        self.info.configure(text=f'{txt}\nBanco del nivel: {usado} de 16384 bytes')

    def _rueda(self, d):
        if self.dosd: self.lienzo.yview_scroll(d, 'units')
        elif self.horizontal: self.lienzo.xview_scroll(d, 'units')
        else: self.lienzo.yview_scroll(d, 'units')

    # ---------------- acciones ----------------
    def _posicion(self, e):
        x = int(self.lienzo.canvasx(e.x) // T); y = int(self.lienzo.canvasy(e.y) // T)
        if 0 <= y < len(self.mapa) and 0 <= x < len(self.mapa[0]):
            return x, y
        return None

    def _pintar(self, e, arrastre=False):
        pos = self._posicion(e)
        if not pos: return
        x, y = pos
        if self.v_modo.get() == 'pantallas':
            if arrastre: return
            self.sel_pant = (x // (juego.PANT_ANCHO * self.f), y // (juego.PANT_ALTO * self.f)); self._dibujar_rejilla(); return
        if self.dosd and not juego.rejilla(self.app.nivel(), self.f)[y // (juego.PANT_ALTO * self.f)][x // (juego.PANT_ANCHO * self.f)]:
            return                          # pantalla que no existe
        if self.v_modo.get() == 'enemigos':
            if arrastre: return            # los enemigos se colocan de uno en uno
            tipo = self.c_tipo.current()
            if tipo < 0: return
            ap = self.apariciones
            ap[:] = [a for a in ap if (a['f'], a['c']) != (y, x)]
            ap.append({'tipo': tipo, 'f': y, 'c': x})
            self._dibujar_enemigos(); self.app.marcar_cambio('enemigos'); return
        if self.mapa[y][x] == self.actual: return
        self.mapa[y][x] = self.actual
        self.lienzo.itemconfigure(self._celdas[y][x], image=self._fotos_tiles[self.actual])
        self.app.marcar_cambio('mapa')

    def _cuentagotas(self, e):
        pos = self._posicion(e)
        if pos and self.v_modo.get() == 'enemigos':
            ap = self.apariciones
            ap[:] = [a for a in ap if (a['f'], a['c']) != (pos[1], pos[0])]
            self._dibujar_enemigos(); self.app.marcar_cambio('enemigos'); return
        if pos:
            self.actual = self.mapa[pos[1]][pos[0]]; self._dibujar_paleta()

    def _clic_paleta(self, e):
        i = int(e.y // (MINI + 4)) * 8 + int(e.x // (MINI + 4))
        if 0 <= i < len(self._fotos_tiles):
            self.actual = i; self._dibujar_paleta()

    # ---------------- longitud y tramos ----------------
    def _rango(self):
        n = juego.largo_nivel(self.app.nivel(), self.horizontal)
        try: d, h = int(self.v_desde.get()), int(self.v_hasta.get())
        except (tk.TclError, ValueError): return None
        d, h = min(d, h), max(d, h)
        if not (1 <= d and h <= n):
            messagebox.showinfo('Tramos', f'El tramo debe estar entre 1 y {n}.'); return None
        return d - 1, h - 1

    def _marcar_tramo(self):
        """Resalta el tramo elegido sobre el mapa."""
        c = self.lienzo; c.delete('tramo')
        n = juego.largo_nivel(self.app.nivel(), self.horizontal)
        try: d, h = sorted((int(self.v_desde.get()) - 1, int(self.v_hasta.get()) - 1))
        except (tk.TclError, ValueError): return
        d, h = max(0, d), min(n - 1, h)
        if d > h: return
        if self.horizontal:
            c.create_rectangle(d * T, 0, (h + 1) * T, len(self.mapa) * T, outline='magenta', width=3, tags='tramo')
        else:
            y0, y1 = (n - 1 - h) * T, (n - d) * T
            c.create_rectangle(0, y0, 12 * self.f * T, y1, outline='magenta', width=3, tags='tramo')

    def _aplicar_largo(self):
        try: n = int(self.v_largo.get())
        except (tk.TclError, ValueError): return
        minimo = (12 if self.horizontal else 10) * self.f
        if n < minimo:
            messagebox.showinfo('Mapa', f'La fase necesita al menos {minimo}.'); return
        actual = juego.largo_nivel(self.app.nivel(), self.horizontal)
        if n < actual and not messagebox.askyesno('Acortar', f'Se quitarán {actual - n} del final de la fase '
                                                  '(y los enemigos que haya en ellas). ¿Seguir?'):
            return
        juego.fijar_largo(self.app.nivel(), self.horizontal, n, self.actual)
        self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _copiar_tramo(self):
        r = self._rango()
        if not r: return
        self.portapapeles = juego.tramo_copiar(self.app.nivel(), self.horizontal, *r)
        self.l_porta.configure(text=f'Copiado: {r[1] - r[0] + 1} de largo, {len(self.portapapeles["enemigos"])} enemigos')

    def _pegar_tramo(self):
        if not self.portapapeles:
            messagebox.showinfo('Tramos', 'Primero copia un tramo.'); return
        n = juego.largo_nivel(self.app.nivel(), self.horizontal)
        try: pos = int(self.v_pos.get()) - 1
        except (tk.TclError, ValueError): return
        if not 0 <= pos <= n:
            messagebox.showinfo('Tramos', f'La posición debe estar entre 1 y {n + 1} (al final).'); return
        juego.tramo_insertar(self.app.nivel(), self.horizontal, pos, self.portapapeles)
        self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _repetir_tramo(self):
        r = self._rango()
        if not r: return
        try: veces = max(1, int(self.v_veces.get()))
        except (tk.TclError, ValueError): return
        t = juego.tramo_copiar(self.app.nivel(), self.horizontal, *r)
        juego.tramo_insertar(self.app.nivel(), self.horizontal, r[1] + 1, t, veces)
        self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _borrar_tramo(self):
        r = self._rango()
        if not r: return
        n = juego.largo_nivel(self.app.nivel(), self.horizontal)
        minimo = (12 if self.horizontal else 10) * self.f
        if n - (r[1] - r[0] + 1) < minimo:
            messagebox.showinfo('Tramos', f'La fase quedaría con menos de {minimo}.'); return
        if messagebox.askyesno('Borrar tramo', f'¿Borrar las posiciones {r[0] + 1} a {r[1] + 1} y sus enemigos?'):
            juego.tramo_borrar(self.app.nivel(), self.horizontal, *r)
            self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    def _rellenar(self):
        if messagebox.askyesno('Rellenar', f'¿Rellenar todo el mapa con el tile {self.actual}?'):
            for fila in self.mapa:
                fila[:] = [self.actual] * len(fila)
            self._dibujar_mapa(); self.app.marcar_cambio('mapa')

    # ---------------- fases ----------------
    def _elegir_fase(self, i):
        self.app.nivel_sel = i; self.refrescar()

    def _nueva_fase(self):
        niveles = self.app.proyecto['niveles']
        if len(niveles) >= juego.MAX_NIVELES:
            messagebox.showinfo('Fases', f'Máximo {juego.MAX_NIVELES} fases.'); return
        if self.dosd:
            niveles.append(juego.nivel_2d(f'Fase {len(niveles) + 1}', 3, 2, self.actual, f=self.f))
            self.app.marcar_cambio('fases'); self._elegir_fase(len(niveles) - 1); return
        k = self.f
        if self.horizontal: mapa = [[self.actual] * 24 * k for _ in range(10 * k)]
        else: mapa = [[self.actual] * 12 * k for _ in range(20 * k)]
        niveles.append({'nombre': f'Fase {len(niveles) + 1}', 'mapa': mapa, 'apariciones': []})
        self.app.marcar_cambio('fases'); self._elegir_fase(len(niveles) - 1)

    def _duplicar_fase(self):
        niveles = self.app.proyecto['niveles']
        if len(niveles) >= juego.MAX_NIVELES: return
        nueva = copy.deepcopy(self.app.nivel()); nueva['nombre'] += ' (copia)'
        niveles.insert(self.app.nivel_sel + 1, nueva)
        self.app.marcar_cambio('fases'); self._elegir_fase(self.app.nivel_sel + 1)

    def _borrar_fase(self):
        niveles = self.app.proyecto['niveles']
        if len(niveles) <= 1:
            messagebox.showinfo('Fases', 'Tiene que quedar al menos una fase.'); return
        if messagebox.askyesno('Borrar fase', f'¿Borrar «{self.app.nivel()["nombre"]}» con su mapa y sus enemigos?'):
            del niveles[self.app.nivel_sel]
            self.app.marcar_cambio('fases'); self._elegir_fase(max(0, self.app.nivel_sel - 1))

    def _renombrar_fase(self):
        n = simpledialog.askstring('Renombrar', 'Nombre de la fase:', initialvalue=self.app.nivel()['nombre'], parent=self)
        if n:
            self.app.nivel()['nombre'] = n; self.app.marcar_cambio('fases'); self.refrescar()

    def _mover_fase(self, d):
        niveles = self.app.proyecto['niveles']; i = self.app.nivel_sel; k = i + d
        if 0 <= k < len(niveles):
            niveles[i], niveles[k] = niveles[k], niveles[i]
            self.app.marcar_cambio('fases'); self._elegir_fase(k)
