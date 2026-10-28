"""Editor del mapa.
Vertical:   12 tiles de ancho y tantas filas como se quiera; se empieza abajo.
Horizontal: 10 tiles de alto y tantas columnas como se quiera; se empieza a la izquierda."""
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
        f = ttk.LabelFrame(der, text='Longitud de la fase', padding=6); f.pack(fill='x', pady=8)
        self.info = ttk.Label(f, text='', wraplength=330, justify='left')
        self.info.grid(row=0, column=0, columnspan=4, sticky='w')
        self.l_largo = ttk.Label(f, text='Largo:'); self.l_largo.grid(row=1, column=0, sticky='w', pady=4)
        self.v_largo = tk.IntVar()
        ttk.Spinbox(f, from_=10, to=2000, textvariable=self.v_largo, width=6).grid(row=1, column=1, sticky='w')
        ttk.Button(f, text='Aplicar', command=self._aplicar_largo).grid(row=1, column=2, padx=4)
        ttk.Button(f, text='Rellenar todo con el tile elegido', command=self._rellenar).grid(row=2, column=0, columnspan=4, sticky='we')
        tr = ttk.LabelFrame(der, text='Tramos (posiciones desde el inicio de la fase)', padding=6); tr.pack(fill='x')
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
        self._fotos_tiles = [ImageTk.PhotoImage(graficos.imagen_tile(t, 2)) for t in self.app.proyecto['tiles']]
        if self.actual >= len(self._fotos_tiles):
            self.actual = 0
        if self.horizontal:
            self.lienzo.configure(width=640, height=10 * T)
            self.l_largo.configure(text='Columnas:')
            self.ayuda.configure(text='La línea roja marca la pantalla inicial: el jugador empieza a la izquierda '
                                      'y el scroll avanza hacia la derecha hasta la última columna.\n\n'
                                      'Cada columna del mapa son 16 píxeles; la vista muestra 12.')
        else:
            self.lienzo.configure(width=12 * T, height=480)
            self.l_largo.configure(text='Filas:')
            self.ayuda.configure(text='La línea roja marca la pantalla inicial: el jugador empieza abajo y el '
                                      'scroll sube hasta la fila superior del mapa.\n\n'
                                      'Cada fila del mapa son 16 píxeles; la vista muestra 10.')
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
            foto = ImageTk.PhotoImage(graficos.imagen_tile(t, 2))
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
        for y, fila in enumerate(self.mapa):
            items = []
            for x, v in enumerate(fila):
                foto = self._fotos_tiles[v] if v < len(self._fotos_tiles) else self._fotos_tiles[0]
                items.append(c.create_image(x * T, y * T, image=foto, anchor='nw'))
            self._celdas.append(items)
        if self.horizontal:
            x0 = 12 * T
            c.create_line(x0, 0, x0, alto * T, fill='red', width=2)
            for x in range(0, ancho, 10):
                c.create_text(x * T + 2, 2, text=str(x + 1), fill='white', anchor='nw')
            c.configure(scrollregion=(0, 0, ancho * T, alto * T))
            c.xview_moveto(0.0)
        else:
            y0 = (alto - 10) * T
            c.create_line(0, y0, ancho * T, y0, fill='red', width=2)
            for y in range(0, alto, 10):
                c.create_text(3, y * T + 2, text=str(alto - y), fill='white', anchor='nw')
            c.configure(scrollregion=(0, 0, ancho * T, alto * T))
            c.yview_moveto(1.0)
        self._dibujar_enemigos()
        self._info()
        self.v_largo.set(juego.largo_nivel(self.app.nivel(), self.horizontal))
        self._marcar_tramo()

    def _info(self):
        p = self.app.proyecto
        usado = 32 + 36 * len(p['tiles']) + len(self.mapa) * len(self.mapa[0])
        if self.horizontal:
            n = len(self.mapa[0]); txt = f'{n} columnas: {n * 16} píxeles, unas {n / 12:.0f} pantallas'
        else:
            n = len(self.mapa); txt = f'{n} filas: {n * 16} píxeles, unas {n / 10:.0f} pantallas'
        self.info.configure(text=f'{txt}\nBanco del nivel: {usado} de 16384 bytes')

    def _rueda(self, d):
        if self.horizontal: self.lienzo.xview_scroll(d, 'units')
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
            c.create_rectangle(0, y0, 12 * T, y1, outline='magenta', width=3, tags='tramo')

    def _aplicar_largo(self):
        try: n = int(self.v_largo.get())
        except (tk.TclError, ValueError): return
        minimo = 12 if self.horizontal else 10
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
        minimo = 12 if self.horizontal else 10
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
        if self.horizontal: mapa = [[self.actual] * 24 for _ in range(10)]
        else: mapa = [[self.actual] * 12 for _ in range(20)]
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
