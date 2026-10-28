"""Editor de personajes: jugador, enemigos y balas. Personajes de 8x8 a 32x32 (16 tamaños)."""
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk

import graficos
import juego
import estilo
from juego import DIRECCIONES, MAX_TIPOS, COMPORTAMIENTOS

CELDA = 14
HERRAMIENTAS = [('Tinta', 'X'), ('Contorno', 'o'), ('Transparente', '.')]
COLOR_EDITOR = {'X': '#ffffff', 'o': '#202020', '.': None}


AYUDA_COMP = {
    'quieto': 'Se queda donde aparece (se mueve con el escenario).',
    'patrulla': 'Va y viene en horizontal (en juegos horizontales, en vertical); da la vuelta en muros y bordes. '
                'En plataformas camina sobre el suelo y da la vuelta en los bordes.',
    'persigue': 'Camina hacia el jugador; los tiles sólidos le cortan el paso.',
    'rebota': 'Avanza en la dirección indicada y rebota en muros y bordes.',
    'cruza': 'Avanza en la dirección indicada atravesando todo y desaparece al salir.',
    'personaje': 'No ataca ni se puede destruir: se queda quieto mirando al jugador y habla con él '
                 '(pestaña «Habla»). Con las reglas de Estrategia puede dar objetos o pedirlos.',
}


class EditorSprites(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        self.sel = 0              # 0 = jugador, 1.. = enemigo n-1
        self.celda = CELDA
        self.fot = 0
        self._construir()

    # ---------------- datos ----------------
    # sel: 0 = jugador, 1..n = enemigos, n+1 = disparo del jugador, n+2 = disparo enemigo
    def _tipo_sel(self):
        n = len(self.app.proyecto['enemigos'])
        if self.sel == 0: return 'jugador'
        if self.sel <= n: return 'enemigo'
        return 'bala'

    @property
    def personaje(self):
        p = self.app.proyecto; n = len(p['enemigos'])
        if self.sel == 0: return p['jugador']
        if self.sel <= n: return p['enemigos'][self.sel - 1]
        return p['balas']['jugador' if self.sel == n + 1 else 'enemigo']

    @property
    def frames(self):
        return self.personaje['fotogramas']

    def _tam(self):
        return graficos.TAMANOS[self.personaje['tamano']]

    # ---------------- interfaz ----------------
    def _construir(self):
        arriba = ttk.Frame(self); arriba.grid(row=0, column=0, columnspan=3, sticky='we', pady=(0, 6))
        ttk.Label(arriba, text='Personaje:').pack(side='left')
        self.v_pers = tk.StringVar()
        self.c_pers = ttk.Combobox(arriba, textvariable=self.v_pers, state='readonly', width=18)
        self.c_pers.pack(side='left', padx=4)
        self.c_pers.bind('<<ComboboxSelected>>', self._elegir_personaje)
        for txt, fn in (('Nuevo enemigo', self.nuevo_enemigo), ('Renombrar', self.renombrar),
                        ('Borrar enemigo', self.borrar_enemigo)):
            ttk.Button(arriba, text=txt, command=fn).pack(side='left', padx=2)
        ttk.Label(arriba, text='   Tamaño:').pack(side='left')
        self.v_tam = tk.StringVar()
        self.c_tam = ttk.Button(arriba, text='16x16 ▾', width=9, command=self._abrir_tamanos)
        self.c_tam.pack(side='left', padx=4)
        self.l_motor = ttk.Label(self, text='', style='Ayuda.TLabel', justify='left', wraplength=900)
        self.l_motor.grid(row=2, column=0, columnspan=3, sticky='w', pady=(6, 0))

        # fotogramas
        izq = ttk.LabelFrame(self, text='Fotogramas', padding=4); izq.grid(row=1, column=0, sticky='ns')
        self.lista = tk.Canvas(izq, width=110, height=400, bg='#333', highlightthickness=0)
        barra = ttk.Scrollbar(izq, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.grid(row=0, column=0); barra.grid(row=0, column=1, sticky='ns')
        self.lista.bind('<Button-1>', self._clic_lista)
        b = ttk.Frame(izq); b.grid(row=1, column=0, columnspan=2)
        for i, (txt, fn) in enumerate((('Nuevo', self.nuevo_fot), ('Duplicar', self.duplicar_fot),
                                       ('Borrar', self.borrar_fot), ('Importar…', self.importar))):
            ttk.Button(b, text=txt, command=fn, width=8).grid(row=i // 2, column=i % 2)

        # rejilla
        centro = ttk.LabelFrame(self, text='Dibujo  (clic izq.: herramienta · clic dcho.: transparente)', padding=4)
        centro.grid(row=1, column=1, padx=8, sticky='n')
        self.v_herr = tk.StringVar(value='X')
        h = ttk.Frame(centro); h.pack()
        for txt, val in HERRAMIENTAS:
            ttk.Radiobutton(h, text=txt, value=val, variable=self.v_herr).pack(side='left', padx=4)
        self.rejilla = tk.Canvas(centro, width=24 * CELDA, height=24 * CELDA, bg='#4a6a4a', highlightthickness=0)
        self.rejilla.pack(pady=4)
        self.rejilla.bind('<Button-1>', lambda e: self._pintar(e, self.v_herr.get()))
        self.rejilla.bind('<B1-Motion>', lambda e: self._pintar(e, self.v_herr.get()))
        self.rejilla.bind('<Button-3>', lambda e: self._pintar(e, '.'))
        self.rejilla.bind('<B3-Motion>', lambda e: self._pintar(e, '.'))
        b = ttk.Frame(centro); b.pack()
        for k, (txt, fn) in enumerate((('Contorno auto.', lambda: self._transformar(graficos.contorno_auto)),
                                       ('Limpiar', lambda: self._transformar(lambda p: ['.' * len(p[0])] * len(p))),
                                       ('Girar 90°', self._girar),
                                       ('Espejo ↔', lambda: self._transformar(lambda p: [f[::-1] for f in p])),
                                       ('Espejo ↕', lambda: self._transformar(lambda p: p[::-1])))):
            ttk.Button(b, text=txt, command=fn, width=13).grid(row=k // 3, column=k % 3, padx=1, pady=1)
        ttk.Label(centro, justify='left', wraplength=330, style='Ayuda.TLabel', text=(
            'Tinta = píxeles encendidos. Contorno = píxeles opacos apagados (tapan el fondo). '
            'En el juego el sprite toma los colores de la casilla del fondo que pisa.')).pack(pady=4)

        # propiedades
        self.der = ttk.Frame(self); self.der.grid(row=1, column=2, sticky='nsew')
        self.columnconfigure(2, weight=1); self.rowconfigure(1, weight=1)
        arriba_der = ttk.Frame(self.der); arriba_der.pack(pady=(0, 8))
        self.vista = tk.Canvas(arriba_der, width=100, height=100, bg='black', highlightthickness=0)
        self.vista.grid(row=0, column=0, padx=(0, 8))
        self.animada = tk.Canvas(arriba_der, width=100, height=100, bg='black', highlightthickness=0)
        self.animada.grid(row=0, column=1)
        ttk.Label(arriba_der, text='Fotograma', style='Ayuda.TLabel').grid(row=1, column=0)
        self.v_dir_prev = tk.StringVar(value='arriba')
        self.c_dir_prev = ttk.Combobox(arriba_der, values=DIRECCIONES, textvariable=self.v_dir_prev,
                                       state='readonly', width=11)
        self.c_dir_prev.grid(row=1, column=1)
        self._paso_prev = 0; self._id_anim = None
        self._animar()
        self.marco_props = ttk.Frame(self.der)
        self.marco_props.pack(fill='both', expand=True)

    # ---------------- refresco ----------------
    def refrescar(self):
        p = self.app.proyecto
        nombres = ['Jugador'] + [f'Enemigo: {e["nombre"]}' for e in p['enemigos']] + \
                  ['Disparo del jugador', 'Disparo enemigo']
        self.c_pers.configure(values=nombres)
        if self.sel >= len(nombres): self.sel = 0
        self.v_pers.set(nombres[self.sel])
        self.v_tam.set(self.personaje['tamano'])
        self.c_tam.configure(text=self.personaje['tamano'] + ' ▾',
                             state='disabled' if self._tipo_sel() == 'bala' else 'normal')
        self._info_motor()
        if self.fot >= len(self.frames): self.fot = max(0, len(self.frames) - 1)
        self._dibujar_lista(); self._dibujar_rejilla(); self._propiedades()
        self._paso_prev = 0; self._pintar_animada()

    def _dibujar_lista(self):
        c = self.lista; c.delete('all'); self._minis = []
        y = 4
        for i, f in enumerate(self.frames):
            img = graficos.imagen_sprite(f, 3, fondo=(60, 90, 60), contorno=(20, 20, 20))
            foto = ImageTk.PhotoImage(img); self._minis.append(foto)
            c.create_text(4, y, text=str(i), fill='white', anchor='nw')
            c.create_image(24, y, image=foto, anchor='nw')
            if i == self.fot:
                c.create_rectangle(22, y - 2, 24 + img.width + 1, y + img.height + 1, outline='yellow', width=2)
            y += img.height + 8
        c.configure(scrollregion=(0, 0, 110, y))
        self._altura_item = img.height + 8 if self.frames else 80

    def _dibujar_rejilla(self):
        c = self.rejilla; c.delete('all')
        if not self.frames: return
        pix = self.frames[self.fot]
        w, h = len(pix[0]), len(pix)
        self.celda = CELDA if h <= 24 else 12
        CEL = self.celda
        c.configure(width=w * CEL, height=h * CEL)
        self._rects = []
        for y in range(h):
            fila = []
            for x in range(w):
                col = COLOR_EDITOR[pix[y][x]] or ('#4a6a4a' if (x // 8 + y // 8) % 2 == 0 else '#557755')
                fila.append(c.create_rectangle(x * CEL, y * CEL, (x + 1) * CEL, (y + 1) * CEL,
                                               fill=col, outline='#3a4a3a'))
            self._rects.append(fila)
        for k in range(0, w + 1, 8):
            c.create_line(k * CEL, 0, k * CEL, h * CEL, fill='#99aa99', width=2)
        for k in range(0, h + 1, 8):
            c.create_line(0, k * CEL, w * CEL, k * CEL, fill='#99aa99', width=2)
        self._vista()

    def _componer(self, pix):
        """El fotograma sobre el primer tile del mapa, con sus colores reales, a escala x3."""
        p = self.app.proyecto
        fondo = Image.new('RGB', (40, 40))           # cabe un sprite de hasta 32 de alto
        t = graficos.imagen_tile(p['tiles'][0])
        for ox in (0, 16, 32):
            for oy in (0, 16, 32):
                fondo.paste(t, (ox, oy))
        tinta, papel, br = graficos.partes_atr(p['tiles'][0]['atr'][0])
        col = self.personaje.get('color', 0) if self._tipo_sel() != 'bala' else 0
        if col and p['scroll'].get('color_sprites'):
            tinta, br = col & 7, 1 if col & 0x40 else 0
        from pantalla import PALETA
        px = fondo.load()
        for y, fila in enumerate(pix):
            for x, ch in enumerate(fila):
                if ch == 'X': px[x + 4, y + 4] = PALETA[tinta + 8 * br]
                elif ch == 'o': px[x + 4, y + 4] = PALETA[papel + 8 * br]
        return fondo.resize((100, 100), Image.NEAREST)

    def _ciclo(self):
        """Índices de fotograma de la animación que se previsualiza."""
        per = self.personaje; n = len(self.frames)
        if self._tipo_sel() == 'jugador':
            d = self.v_dir_prev.get()
            lst = [k for k in per['anim'].get(d, []) if 0 <= k < n]
            if not lst and '-' in d:
                lst = [k for k in per['anim'].get(d.split('-')[0], []) if 0 <= k < n]
            return (lst or [0])[:8]
        return list(range(min(8, n))) or [0]

    def _animar(self):
        """Vista previa animada a la velocidad del juego (25 fotogramas por segundo)."""
        vel = self._pintar_animada(avanzar=True)
        self._id_anim = self.after(max(1, vel) * 40, self._animar)

    def _pintar_animada(self, avanzar=False):
        try:
            if self.frames:
                ciclo = self._ciclo()
                self._paso_prev = (self._paso_prev + (1 if avanzar else 0)) % len(ciclo)
                k = ciclo[self._paso_prev]
                pix = self.frames[k]
                if self._tipo_sel() == 'enemigo' and self.personaje.get('voltear') and (self._paso_prev // len(ciclo)) % 2:
                    pix = [f[::-1] for f in pix]
                self._foto_anim = ImageTk.PhotoImage(self._componer(pix))
                self.animada.delete('all'); self.animada.create_image(0, 0, image=self._foto_anim, anchor='nw')
                self.animada.create_text(3, 3, text=str(k), fill='yellow', anchor='nw')
            return self.personaje.get('vel_anim', 4) if self._tipo_sel() != 'bala' else 4
        except Exception:
            return 4

    def _vista(self):
        """Vista previa sobre el primer tile del mapa, con sus colores reales."""
        c = self.vista; c.delete('all')
        if not self.frames: return
        self._foto_vista = ImageTk.PhotoImage(self._componer(self.frames[self.fot]))
        c.create_image(0, 0, image=self._foto_vista, anchor='nw')

    def _propiedades(self):
        for w in self.marco_props.winfo_children(): w.destroy()
        per = self.personaje
        self._vars = {}
        tipo = self._tipo_sel()
        nb = ttk.Notebook(self.marco_props, style='Sub.TNotebook')
        nb.pack(fill='both', expand=True)
        def hoja(texto):
            h = ttk.Frame(nb, padding=8); nb.add(h, text=texto); return h
        def campo(f, fila, texto, clave, dic, desde, hasta, inc=1):
            ttk.Label(f, text=texto).grid(row=fila, column=0, sticky='w', pady=1)
            v = tk.IntVar(value=dic.get(clave, 0)); self._vars[(id(dic), clave)] = (v, dic, clave)
            s = ttk.Spinbox(f, from_=desde, to=hasta, increment=inc, textvariable=v, width=6,
                            command=lambda: self._guardar_vars())
            s.grid(row=fila, column=1, sticky='w', pady=1); s.bind('<FocusOut>', lambda e: self._guardar_vars())
        def combo(f, fila, texto, valores, actual, al_elegir, ancho=18):
            ttk.Label(f, text=texto).grid(row=fila, column=0, sticky='w', pady=1)
            v = tk.StringVar(value=actual)
            c = ttk.Combobox(f, values=valores, textvariable=v, state='readonly', width=ancho)
            c.grid(row=fila, column=1, sticky='w', pady=1)
            c.bind('<<ComboboxSelected>>', lambda e: al_elegir(v.get()))
            return v, c
        nfot = len(self.frames)
        opciones_fot = ['(ninguno)'] + [str(k) for k in range(nfot)]
        def txt_fot(k): return '(ninguno)' if k is None or not 0 <= k < nfot else str(k)
        def num_fot(t): return None if t == '(ninguno)' else int(t)
        w, h = self._tam()
        if tipo == 'jugador':
            self._mov = hoja('Movimiento')
            f = self._mov
            campo(f, 0, 'Velocidad (px)', 'velocidad', per, 1, 4)
            campo(f, 1, 'X inicial', 'x', per, 0, 192 - w)
            campo(f, 2, 'Y inicial', 'y', per, 0, 160 - h)
            per.setdefault('arma', 'disparo'); per.setdefault('alcance', 12); per.setdefault('pisar', False)
            armas = {'disparo': 'Disparo', 'laser': 'Láser', 'golpe': 'Golpe (puñetazo/patada)', 'ninguna': 'Ninguna'}
            per.setdefault('laser', juego.laser_defecto())
            def cambio_arma(t):
                per['arma'] = {v: k for k, v in armas.items()}[t]; self.app.marcar_cambio('sprites')
                self._propiedades(); self._info_motor()
            combo(f, 3, 'Arma', list(armas.values()), armas[per['arma']], cambio_arma, 22)
            campo(f, 4, 'Cadencia de disparo', 'cadencia', per, 1, 50)
            def cambio_df(t):
                per['disparo_fijo'] = None if t == 'hacia donde mira' else t; self.app.marcar_cambio('sprites')
            combo(f, 5, 'Dirección del disparo', ['hacia donde mira'] + DIRECCIONES,
                  per.get('disparo_fijo') or 'hacia donde mira', cambio_df, 16)
            campo(f, 6, 'Alcance del golpe (px)', 'alcance', per, 4, 32)
            vpis = tk.BooleanVar(value=per['pisar'])
            def cambio_pisar():
                per['pisar'] = bool(vpis.get()); self.app.marcar_cambio('sprites')
            ttk.Checkbutton(f, text='Pisar enemigos: caerles encima los daña (plataformas)',
                            variable=vpis, command=cambio_pisar).grid(row=7, column=0, columnspan=2, sticky='w', pady=(6, 0))
            self._campo_color(f, 8)
            if juego.plataformas(self.app.proyecto):
                per.setdefault('inercia', 0)
                ttk.Label(f, text='Inercia (0 = ninguna)').grid(row=9, column=0, sticky='w', pady=(8, 1))
                vi = tk.IntVar(value=per['inercia'])
                li = ttk.Label(f, style='Ayuda.TLabel')
                def cambio_inercia(_=None):
                    k = int(float(vi.get())); vi.set(k)
                    if per.get('inercia') != k:
                        per['inercia'] = k; self.app.marcar_cambio('sprites')
                    a, _f = juego.valores_inercia(self.app.proyecto)
                    li.configure(text='Se mueve en seco, como siempre.' if not k else
                                 f'Tarda unos {-(-per.get("velocidad", 2) * 16 // a)} fotogramas en arrancar '
                                 'y otros tantos en pararse (resbala).')
                fi = ttk.Frame(f); fi.grid(row=9, column=1, sticky='w', pady=(8, 1))
                ttk.Scale(fi, from_=0, to=10, variable=vi, orient='horizontal', length=130,
                          command=cambio_inercia).pack(side='left')
                ttk.Label(fi, textvariable=vi, width=3).pack(side='left', padx=4)
                li.grid(row=10, column=0, columnspan=2, sticky='w')
                cambio_inercia()
            if per['arma'] == 'laser': self._hoja_laser(hoja('Láser'), per['laser'])
            # animación por direcciones
            a = hoja('Animación')
            campo(a, 0, 'Velocidad de animación', 'vel_anim', per, 1, 15)
            t = ttk.Frame(a); t.grid(row=1, column=0, columnspan=2, sticky='w', pady=(6, 0))
            for c_, txt in enumerate(('Dirección', 'Andar (hasta 8)', 'Reposo', 'Disparo')):
                ttk.Label(t, text=txt, style='Seccion.TLabel').grid(row=0, column=c_, sticky='w', padx=2)
            self._anim = {}; self._fijos = {}
            plat = juego.plataformas(self.app.proyecto)
            nombres_plat = {'arriba-dcha': 'salto ↗ (sube)', 'arriba-izq': 'salto ↖ (sube)',
                            'abajo-dcha': 'cae ↘', 'abajo-izq': 'cae ↙', 'dcha': 'derecha', 'izq': 'izquierda'}
            for i, d in enumerate(DIRECCIONES):
                ttk.Label(t, text=nombres_plat.get(d, d) if plat else d).grid(row=1 + i, column=0, sticky='w')
                v = tk.StringVar(value=','.join(map(str, per['anim'].get(d, []))))
                e = ttk.Entry(t, textvariable=v, width=13); e.grid(row=1 + i, column=1, sticky='w', padx=2, pady=1)
                self._anim[d] = v
                for c_, clave in ((2, 'quieto'), (3, 'disparo')):
                    k = per.get(clave, {}).get(d)
                    vf = tk.StringVar(value='' if k is None else str(k))
                    ef = ttk.Entry(t, textvariable=vf, width=4); ef.grid(row=1 + i, column=c_, padx=2)
                    self._fijos[(clave, d)] = vf
                    ef.bind('<FocusOut>', lambda ev: self._guardar_anim()); ef.bind('<Return>', lambda ev: self._guardar_anim())
                e.bind('<FocusOut>', lambda ev: self._guardar_anim()); e.bind('<Return>', lambda ev: self._guardar_anim())
            ttk.Label(a, style='Ayuda.TLabel', wraplength=300, justify='left', text=(
                'Números de fotograma separados por comas. Diagonal vacía = usa la vertical. Reposo y disparo '
                'vacíos = primer fotograma de andar. Con golpe, el fotograma de «Disparo» es el del ataque.' +
                (' En plataformas, «salto» se ve mientras sube y «cae» mientras baja (vacío = el de salto).'
                 if plat else ''))).grid(row=2, column=0, columnspan=2, sticky='w', pady=(6, 0))
            # fotogramas especiales
            e = hoja('Agacharse · morir')
            ag = per.get('agachado') or {}
            def cambio_ag(lado, t):
                per.setdefault('agachado', {})[lado] = num_fot(t)
                if per['agachado'][lado] is None: del per['agachado'][lado]
                self.app.marcar_cambio('sprites')
            combo(e, 0, 'Agachado (derecha)', opciones_fot, txt_fot(ag.get('dcha')),
                  lambda t: cambio_ag('dcha', t), 10)
            combo(e, 1, 'Agachado (izquierda)', opciones_fot, txt_fot(ag.get('izq')),
                  lambda t: cambio_ag('izq', t), 10)
            def cambio_muerte(t):
                per['muerte'] = num_fot(t); self.app.marcar_cambio('sprites')
            combo(e, 2, 'Al morir', opciones_fot, txt_fot(per.get('muerte')), cambio_muerte, 10)
            ttk.Label(e, style='Ayuda.TLabel', wraplength=300, justify='left', text=(
                'Agacharse (solo en plataformas): con la tecla abajo, quieto en el suelo. La misma tecla '
                'sirve para entrar en las puertas y hablar con los personajes.\n\n'
                'Al morir: el personaje salta hacia arriba con ese dibujo y cae fuera de la pantalla, '
                'como en los clásicos de plataformas. Sin fotograma, el aviso es solo el borde rojo.\n\n'
                'Los fotogramas especiales no tienen que estar en ninguna animación de andar.'
            )).grid(row=3, column=0, columnspan=2, sticky='w', pady=(8, 0))
        elif tipo == 'enemigo':
            self._anim = None
            f = hoja('Conducta')
            vd = tk.StringVar(value=per.get('direccion', 'abajo'))
            def cambio_comp(t=None, marcar=True):
                if t is not None: per['comportamiento'] = t
                per['direccion'] = vd.get()
                cd.configure(state='readonly' if per['comportamiento'] in ('rebota', 'cruza') else 'disabled')
                self.l_comp.configure(text=AYUDA_COMP[per['comportamiento']])
                if marcar: self.app.marcar_cambio('sprites')
                if t is not None: self._propiedades()
            combo(f, 0, 'Comportamiento', COMPORTAMIENTOS, per['comportamiento'], cambio_comp, 12)
            ttk.Label(f, text='Dirección').grid(row=1, column=0, sticky='w')
            cd = ttk.Combobox(f, values=DIRECCIONES, textvariable=vd, state='readonly', width=12)
            cd.grid(row=1, column=1, sticky='w'); cd.bind('<<ComboboxSelected>>', lambda e: cambio_comp())
            self.l_comp = ttk.Label(f, text='', style='Ayuda.TLabel', wraplength=280, justify='left')
            self.l_comp.grid(row=2, column=0, columnspan=2, sticky='w', pady=(4, 8))
            npc = per['comportamiento'] == 'personaje'
            if not npc:
                campo(f, 3, 'Velocidad (px)', 'velocidad', per, 1, 4)
                campo(f, 4, 'Energía (impactos)', 'energia', per, 1, 99)
                campo(f, 5, 'Cadencia (0 = no dispara)', 'cadencia', per, 0, 250)
                campo(f, 6, 'Puntos (de 10 en 10)', 'puntos', per, 0, 990, 10)
            self._campo_color(f, 7)
            a = hoja('Animación')
            campo(a, 0, 'Velocidad de animación', 'vel_anim', per, 1, 15)
            vv = tk.BooleanVar(value=per.get('voltear', False))
            def cambio_voltear():
                per['voltear'] = bool(vv.get()); self.app.marcar_cambio('sprites')
            ttk.Checkbutton(a, text='Voltear al ir hacia la izquierda', variable=vv,
                            command=cambio_voltear).grid(row=1, column=0, columnspan=2, sticky='w')
            def cambio_muerte(t):
                per['muerte'] = num_fot(t); self.app.marcar_cambio('sprites')
            if not npc:
                combo(a, 2, 'Fotograma al morir', ['(ninguno)'] + [str(k) for k in range(min(8, nfot))],
                      txt_fot(per.get('muerte')), cambio_muerte, 10)
            ttk.Label(a, style='Ayuda.TLabel', wraplength=280, justify='left', text=(
                'Se usan hasta 8 fotogramas, en orden. El fotograma al morir (aplastado, boca abajo…) se '
                'quita de la animación de andar y se ve un momento al destruir al enemigo.')).grid(
                row=3, column=0, columnspan=2, sticky='w', pady=(8, 0))
            if npc:
                hb = hoja('Habla')
                ttk.Label(hb, text='Lo que dice (2 líneas de 20 letras)').grid(row=0, column=0, sticky='w')
                self.m_npc = estilo.CampoMensaje(hb, al_cambiar=lambda: self._guardar_msg_npc())
                self.m_npc.grid(row=1, column=0, sticky='w', pady=4)
                self.m_npc.set(per.get('mensaje', ''))
                ttk.Label(hb, style='Ayuda.TLabel', wraplength=280, justify='left', text=(
                    'Se habla con él tocándolo (en plataformas, tocándolo y pulsando abajo). Si una regla de '
                    'la pestaña Estrategia es «al hablar con» este personaje y se cumple, pasa lo que diga la '
                    'regla (dar un elemento, abrir el camino a otra fase…); si no, dice este mensaje.')).grid(
                    row=2, column=0, sticky='w', pady=(6, 0))
                if nb.index('end') > 2: nb.select(2)
            cambio_comp(marcar=False)
        else:
            self._anim = None
            f = hoja('Bala')
            pj = self.app.proyecto
            def cambio_tam_bala(t):
                self.v_tam.set(t); self._cambiar_tamano(None)
            combo(f, 0, 'Tamaño', list(graficos.TAMANOS_BALA), per.get('tamano', '8x8'), cambio_tam_bala, 7)
            per.setdefault('velocidad', 4)
            vmin = juego.velocidad_minima_bala(pj)
            ttk.Label(f, text='Velocidad (px por fotograma)').grid(row=1, column=0, sticky='w', pady=1)
            vv = tk.IntVar(value=per['velocidad'])
            lv = ttk.Label(f, style='Ayuda.TLabel', wraplength=300, justify='left')
            def cambio_vel(_=None):
                try: k = max(1, min(12, int(vv.get())))
                except (tk.TclError, ValueError): return
                if per.get('velocidad') != k:
                    per['velocidad'] = k; self.app.marcar_cambio('sprites')
                txt = (f'El scroll avanza unos {juego.velocidad_scroll(pj)} px por fotograma: la bala tiene que ir '
                       f'al menos a {vmin}. ')
                if k < vmin:
                    lv.configure(style='Aviso.TLabel', text=txt + f'⚠ Con {k} el motor la sube a {vmin}.')
                else:
                    lv.configure(style='Ayuda.TLabel', text=txt + (
                        f'Con {k} px avanza a saltos de {k} píxeles, pero no atraviesa a nadie: el motor '
                        'comprueba todo el tramo recorrido en cada salto y daña igual.' if k > 4 else
                        'Movimiento suave.'))
            sp = ttk.Spinbox(f, from_=1, to=12, textvariable=vv, width=5, command=cambio_vel)
            sp.grid(row=1, column=1, sticky='w'); sp.bind('<FocusOut>', cambio_vel); sp.bind('<Return>', cambio_vel)
            lv.grid(row=2, column=0, columnspan=2, sticky='w', pady=(2, 8))
            cambio_vel()
            ttk.Label(f, style='Ayuda.TLabel', wraplength=300, justify='left',
                      text='Tamaños: 8×8, 8×16 (alta) o 16×8 (alargada). Se usa el primer fotograma. '
                           'El daño se calcula con la caja entera de la bala; cuanto más pequeña, más '
                           'balas a la vez caben en los scroll de 8 en 8.').grid(row=3, column=0, columnspan=2, sticky='w')

    # ---------------- láser ----------------
    def _hoja_laser(self, f, la):
        """Dibujo (patrón de 8 píxeles por línea), grosor, duración, alcance y a qué se para."""
        def marcar(): self.app.marcar_cambio('sprites'); dibujar()
        ttk.Label(f, text='Dibujo').grid(row=0, column=0, sticky='w')
        nombres = list(juego.PATRONES_LASER)
        def actual():
            for n, pt in juego.PATRONES_LASER.items():
                if list(pt[:la['grosor']]) == list(la['patron'][:la['grosor']]): return n
            return '(propio)'
        vp = tk.StringVar(value=actual())
        cp = ttk.Combobox(f, values=nombres, textvariable=vp, state='readonly', width=16)
        cp.grid(row=0, column=1, sticky='w')
        def cambio_patron(_=None):
            la['patron'] = list(juego.PATRONES_LASER[vp.get()]); marcar()
        cp.bind('<<ComboboxSelected>>', cambio_patron)
        ttk.Label(f, text='Patrón (clic en cada píxel)').grid(row=1, column=0, sticky='nw', pady=(4, 0))
        C = 16
        rej = tk.Canvas(f, width=8 * C + 1, height=3 * C + 1, bg='#222', highlightthickness=0)
        rej.grid(row=1, column=1, sticky='w', pady=(4, 0))
        prev = tk.Canvas(f, width=260, height=76, bg='black', highlightthickness=0)
        prev.grid(row=2, column=0, columnspan=2, sticky='w', pady=4)
        def dibujar():
            rej.delete('all'); prev.delete('all')
            for r in range(3):
                b = la['patron'][r] if r < len(la['patron']) else 0
                for c in range(8):
                    on = b & (0x80 >> c)
                    activo = r < la['grosor']
                    col = ('#ff5050' if on else '#552222') if activo else ('#666' if on else '#333')
                    rej.create_rectangle(c * C, r * C, c * C + C - 1, r * C + C - 1, fill=col, outline='')
            # vista: horizontal y diagonal, a doble tamaño
            for k in range(la['grosor']):
                b = la['patron'][k]
                for i in range(110):
                    if b & (0x80 >> (i & 7)):
                        x, y = 6 + i * 2, 8 + (k - (la['grosor'] - 1) // 2) * 2
                        prev.create_rectangle(x, y, x + 1, y + 1, fill='#ff6060', outline='')
                for i in range(28):
                    if b & (0x80 >> (i & 7)):
                        x, y = 6 + i * 2 - (k - (la['grosor'] - 1) // 2) * 2, 18 + i * 2 + (k - (la['grosor'] - 1) // 2) * 2
                        prev.create_rectangle(x, y, x + 1, y + 1, fill='#ff6060', outline='')
                for i in range(28):
                    if b & (0x80 >> (i & 7)):
                        x, y = 100 + (k - (la['grosor'] - 1) // 2) * 2, 18 + i * 2
                        prev.create_rectangle(x, y, x + 1, y + 1, fill='#ff6060', outline='')
            prev.create_text(130, 50, anchor='w', fill='#aaaaaa', font=('TkDefaultFont', 8),
                             text='horizontal, diagonal\ny vertical (×2)')
            vp.set(actual())
        def clic(e):
            c, r = e.x // C, e.y // C
            if 0 <= c < 8 and 0 <= r < la['grosor']:
                pt = (list(la['patron']) + [0xFF, 0xFF, 0xFF])[:3]
                pt[r] ^= 0x80 >> c; la['patron'] = pt; marcar()
        rej.bind('<Button-1>', clic)
        def num(fila, texto, clave, desde, hasta, ayuda=''):
            ttk.Label(f, text=texto).grid(row=fila, column=0, sticky='w', pady=1)
            v = tk.IntVar(value=la.get(clave, desde))
            def cambio(_=None):
                try: k = max(desde, min(hasta, int(v.get())))
                except (tk.TclError, ValueError): return
                if la.get(clave) != k: la[clave] = k; marcar()
            s = ttk.Spinbox(f, from_=desde, to=hasta, textvariable=v, width=5, command=cambio)
            s.grid(row=fila, column=1, sticky='w', pady=1); s.bind('<FocusOut>', cambio); s.bind('<Return>', cambio)
            if ayuda: ttk.Label(f, text=ayuda, style='Ayuda.TLabel').grid(row=fila, column=1, sticky='w', padx=(70, 0))
        num(3, 'Grosor (líneas)', 'grosor', 1, 3)
        num(4, 'Se ve durante', 'duracion', 1, 50, 'fotogramas')
        num(5, 'Alcance (px)', 'alcance', 0, 255, '0 = hasta el borde')
        fila = 6
        for clave, texto in (('para_enemigo', 'Se detiene en el enemigo al que da (si no, los atraviesa a todos)'),
                             ('para_tiles', 'Se detiene en los tiles que paran las balas'),
                             ('animar', 'Animar el dibujo (se desplaza a lo largo del rayo)')):
            v = tk.BooleanVar(value=la.get(clave, True))
            def cambio(v=v, clave=clave):
                la[clave] = bool(v.get()); marcar()
            ttk.Checkbutton(f, text=texto, variable=v, command=cambio).grid(row=fila, column=0, columnspan=2, sticky='w')
            fila += 1
        ttk.Label(f, style='Ayuda.TLabel', wraplength=420, justify='left', text=(
            'Sale hacia donde se mira o camina (también en diagonal) y daña «al píxel»: justo donde '
            'empieza el dibujo del enemigo. Rompe los tiles rompibles.')).grid(
            row=fila, column=0, columnspan=2, sticky='w', pady=(6, 0))
        dibujar()

    # ---------------- tamaños y capacidad del motor ----------------
    def _clave_motor(self):
        n = len(self.app.proyecto['enemigos'])
        if self.sel == 0: return 'j'
        if self.sel <= n: return self.sel - 1
        return 'bala_j' if self.sel == n + 1 else 'bala_e'

    def _texto_motor(self, fondo=None):
        p = self.app.proyecto
        lim = juego.limites_a_la_vez(p)
        fps, _, _ = juego.estimacion_fps(p, fondo)
        m, u = lim['max'], lim['usar']
        return lim, fps, (f'El motor mueve a la vez hasta {m["enemigos"]} enemigos, {m["balas_j"]} balas tuyas y '
                          f'{m["balas_e"]} enemigas con estos tamaños (límite: {lim["motivo"]}). Usando ahora '
                          f'{u["enemigos"]}/{u["balas_j"]}/{u["balas_e"]} (pestaña Partida) · unos {fps:g} fps con '
                          'todo en pantalla.')

    def _info_motor(self):
        try:
            _, _, txt = self._texto_motor()
            _, _, _, comp = juego.info_compilado(self.app.proyecto, self._clave_motor())
            if not juego.modo_bloques(self.app.proyecto): comp = ''
            self.l_motor.configure(text=txt + ('\n' + comp if comp else ''),
                                   style='Aviso.TLabel' if comp.startswith('⚠') else 'Ayuda.TLabel')
        except Exception as ex:          # nunca debe impedir editar
            self.l_motor.configure(text=f'(no se pudo calcular la capacidad del motor: {ex})')

    def _abrir_tamanos(self):
        """Rejilla 4×4 de tamaños; en negrita los más usados. Cada casilla dice cuántos enemigos caben
        a la vez y si se compilaría el sprite con ese tamaño."""
        p = self.app.proyecto; per = self.personaje; clave = self._clave_motor()
        win = tk.Toplevel(self); win.title('Tamaño del personaje'); win.transient(self.winfo_toplevel())
        win.configure(bg=estilo.FONDO); win.resizable(False, False)
        fam = estilo.familia()
        ttk.Label(win, text='Ancho →  /  Alto ↓', style='Seccion.TLabel').grid(row=0, column=0, padx=8, pady=6)
        anchos = (8, 16, 24, 32)
        for c, w in enumerate(anchos):
            ttk.Label(win, text=f'{w} px', style='Seccion.TLabel').grid(row=0, column=c + 1)
        fondo = juego.coste_fondo(p) if juego.modo_bloques(p) else 70000
        original = per['tamano']
        for r, h in enumerate(anchos):
            ttk.Label(win, text=f'{h} px', style='Seccion.TLabel').grid(row=r + 1, column=0, padx=8)
            for c, w in enumerate(anchos):
                t = f'{w}x{h}'
                per['tamano'] = t
                pa = p['partida']; vez_orig = pa.get('a_la_vez')
                try:
                    lim = juego.limites_a_la_vez(p)
                    pa['a_la_vez'] = dict(lim['max'])          # fps con el máximo en pantalla
                    fps = juego.estimacion_fps(p, fondo)[0]
                    if juego.modo_bloques(p):
                        comp = juego.info_compilado(p, clave)[0] if p['scroll'].get('compilar_sprites', True) else True
                    else:
                        comp = True
                    sv = juego.tamanos_a_la_vez(p)
                    cabe = juego.modo_bloques(p) or sum(sv) <= juego.SAVE_TOTAL
                finally:
                    per['tamano'] = original
                    if vez_orig is None: pa.pop('a_la_vez', None)
                    else: pa['a_la_vez'] = vez_orig
                frec = t in graficos.TAMANOS_FRECUENTES
                txt = f'{w}×{h}\nhasta {lim["max"]["enemigos"]} · {fps:g} fps' if cabe else f'{w}×{h}\nno cabe'
                if not comp: txt += '\n⚠ sin compilar'
                bg = estilo.ACENTO if t == original else ('#ffffff' if cabe else '#f3d6d6')
                b = tk.Button(win, text=txt, width=15, height=3, relief='groove', bg=bg,
                              fg='white' if t == original else (estilo.TEXTO if comp else estilo.AVISO),
                              font=(fam, 9, 'bold' if frec else 'normal'),
                              state='normal' if cabe else 'disabled',
                              command=lambda t=t: (win.destroy(), self.v_tam.set(t), self._cambiar_tamano(None)))
                b.grid(row=r + 1, column=c + 1, padx=2, pady=2)
        ttk.Label(win, style='Ayuda.TLabel', wraplength=560, justify='left', text=(
            'En negrita, los tamaños más usados (8×8, 16×16, 16×24, 16×32, 24×24 y 32×32). «hasta N» es el '
            'máximo de enemigos que el motor puede mover a la vez si este personaje tiene ese tamaño, y los fps '
            'una estimación con ese máximo (y el máximo de balas) en pantalla. ' + (
                '«⚠ sin compilar»: con ese tamaño ya no cabe en el banco 7 de sprites compilados y se dibujaría '
                'unas 3 veces más despacio.' if juego.modo_bloques(p) else
                'En este tipo de scroll cada sprite guarda el fondo que tapa en una zona de 1024 bytes: cuanto más '
                'pequeños, más enemigos y balas a la vez. En rojo, los que no caben.'))).grid(
            row=6, column=0, columnspan=5, sticky='w', padx=8, pady=8)
        win.update_idletasks()
        raiz = self.winfo_toplevel()
        win.geometry(f'+{raiz.winfo_rootx() + 60}+{raiz.winfo_rooty() + 80}')
        win.grab_set()

    def _guardar_msg_npc(self):
        if self._tipo_sel() == 'enemigo':
            self.personaje['mensaje'] = self.m_npc.get(); self.app.marcar_cambio('sprites')

    def _campo_color(self, f, fila):
        """Color propio del personaje (solo con «color propio» en la pestaña Scroll)."""
        per = self.personaje
        nombres = ['Del fondo'] + [f'{k} {n}' for k, n in enumerate(
            ('Negro', 'Azul', 'Rojo', 'Magenta', 'Verde', 'Cian', 'Amarillo', 'Blanco')) if k]
        c = per.get('color', 0)
        ttk.Label(f, text='Color propio').grid(row=fila, column=0, sticky='w')
        caja = ttk.Frame(f); caja.grid(row=fila, column=1, sticky='w')
        vc = tk.StringVar(value=nombres[c & 7] if c else nombres[0])
        vb = tk.BooleanVar(value=bool(c & 0x40))
        cb = ttk.Combobox(caja, values=nombres, textvariable=vc, state='readonly', width=10)
        cb.pack(side='left')
        def cambio(_=None):
            k = nombres.index(vc.get())
            per['color'] = graficos.atributo(k, 0, vb.get()) if k else 0
            self.app.marcar_cambio('sprites')
        cb.bind('<<ComboboxSelected>>', cambio)
        ttk.Checkbutton(caja, text='brillo', variable=vb, command=cambio).pack(side='left', padx=4)

    def _guardar_vars(self):
        for v, dic, clave in self._vars.values():
            try: dic[clave] = int(v.get())
            except (tk.TclError, ValueError): pass
        self.app.marcar_cambio('sprites')

    def _guardar_anim(self):
        per = self.personaje
        for d, v in self._anim.items():
            try:
                lst = [int(x) for x in v.get().replace(' ', '').split(',') if x != '']
            except ValueError:
                continue
            per['anim'][d] = [k for k in lst if 0 <= k < len(self.frames)][:8]
        for (clave, d), v in getattr(self, '_fijos', {}).items():
            txt = v.get().strip()
            if txt == '':
                per.setdefault(clave, {}).pop(d, None)
            elif txt.isdigit() and int(txt) < len(self.frames):
                per.setdefault(clave, {})[d] = int(txt)
        self.app.marcar_cambio('sprites')

    # ---------------- acciones ----------------
    def _elegir_personaje(self, _):
        self.sel = self.c_pers.current(); self.fot = 0; self.refrescar()

    def _cambiar_tamano(self, _):
        nuevo = self.v_tam.get()
        if nuevo == self.personaje['tamano']: return
        w, h = graficos.TAMANOS[nuevo]
        self.personaje['tamano'] = nuevo
        self.personaje['fotogramas'] = [graficos.redimensionar(f, w, h) for f in self.frames]
        if self.sel == 0:
            j = self.personaje
            j['x'] = min(j['x'], 192 - w); j['y'] = min(j['y'], 160 - h)
        self.app.marcar_cambio('sprites'); self.refrescar()

    def _clic_lista(self, e):
        y = self.lista.canvasy(e.y)
        i = int(y // self._altura_item) if self.frames else -1
        if 0 <= i < len(self.frames):
            self.fot = i; self._dibujar_lista(); self._dibujar_rejilla()

    def _pintar(self, e, valor):
        if not self.frames: return
        pix = self.frames[self.fot]
        x, y = e.x // self.celda, e.y // self.celda
        if not (0 <= y < len(pix) and 0 <= x < len(pix[0])) or pix[y][x] == valor: return
        pix[y] = pix[y][:x] + valor + pix[y][x + 1:]
        col = COLOR_EDITOR[valor] or ('#4a6a4a' if (x // 8 + y // 8) % 2 == 0 else '#557755')
        self.rejilla.itemconfigure(self._rects[y][x], fill=col)
        self._vista(); self.app.marcar_cambio('sprites')

    def _transformar(self, f):
        if not self.frames: return
        self.frames[self.fot] = f(self.frames[self.fot])
        self._dibujar_rejilla(); self._dibujar_lista(); self.app.marcar_cambio('sprites')

    def _girar(self):
        w, h = self._tam()
        if w != h:
            messagebox.showinfo('Girar', 'Solo se pueden girar sprites cuadrados.'); return
        self._transformar(lambda p: [''.join(p[h - 1 - x][y] for x in range(h)) for y in range(w)])

    def nuevo_fot(self):
        w, h = self._tam()
        self.frames.append(graficos.sprite_vacio(w, h)); self.fot = len(self.frames) - 1
        self.app.marcar_cambio('sprites'); self.refrescar()

    def duplicar_fot(self):
        if not self.frames: return
        self.frames.insert(self.fot + 1, list(self.frames[self.fot])); self.fot += 1
        self.app.marcar_cambio('sprites'); self.refrescar()

    def borrar_fot(self):
        if len(self.frames) <= 1:
            messagebox.showinfo('Fotogramas', 'Tiene que quedar al menos un fotograma.'); return
        i = self.fot
        del self.frames[i]
        per = self.personaje
        mover = lambda k: None if k is None or k == i else (k - 1 if k > i else k)
        if self._tipo_sel() == 'jugador':   # reajustar animaciones y fotogramas especiales
            for d, lst in per['anim'].items():
                per['anim'][d] = [k - 1 if k > i else k for k in lst if k != i]
            for clave in ('quieto', 'disparo', 'agachado'):
                dic = per.get(clave) or {}
                for d in list(dic):
                    dic[d] = mover(dic[d])
                    if dic[d] is None: del dic[d]
        if self._tipo_sel() in ('jugador', 'enemigo') and per.get('muerte') is not None:
            per['muerte'] = mover(per['muerte'])
        self.fot = max(0, i - 1); self.app.marcar_cambio('sprites'); self.refrescar()

    def importar(self):
        """Importa una imagen. Si es más ancha que el sprite, se corta en varios fotogramas.
        Color de la esquina superior izquierda = transparente; negro = contorno; resto = tinta."""
        ruta = filedialog.askopenfilename(filetypes=[('Imágenes', '*.png *.gif *.bmp'), ('Todos', '*.*')])
        if not ruta: return
        img = Image.open(ruta).convert('RGB'); px = img.load()
        w, h = self._tam()
        transp = px[0, 0]
        n = 0
        for oy in range(0, max(1, img.height - h + 1), h):
            for ox in range(0, max(1, img.width - w + 1), w):
                filas = []
                for y in range(h):
                    f = ''
                    for x in range(w):
                        if ox + x >= img.width or oy + y >= img.height:
                            f += '.'; continue
                        c = px[ox + x, oy + y]
                        f += '.' if c == transp else ('o' if sum(c) < 90 else 'X')
                    filas.append(f)
                self.frames.append(filas); n += 1
        self.fot = len(self.frames) - 1
        self.app.marcar_cambio('sprites'); self.refrescar()
        messagebox.showinfo('Importar', f'{n} fotogramas añadidos.')

    def nuevo_enemigo(self):
        p = self.app.proyecto
        if len(p['enemigos']) >= MAX_TIPOS:
            messagebox.showinfo('Enemigos', f'Máximo {MAX_TIPOS} tipos de enemigo.'); return
        nombre = simpledialog.askstring('Nuevo enemigo', 'Nombre:', parent=self) or f'Enemigo {len(p["enemigos"]) + 1}'
        p['enemigos'].append(juego.enemigo_defecto(nombre))
        self.sel = len(p['enemigos']); self.fot = 0
        self.app.marcar_cambio('sprites'); self.refrescar()

    def renombrar(self):
        if self._tipo_sel() != 'enemigo': return
        n = simpledialog.askstring('Renombrar', 'Nombre:', initialvalue=self.personaje['nombre'], parent=self)
        if n:
            self.personaje['nombre'] = n; self.app.marcar_cambio('sprites'); self.refrescar()

    def borrar_enemigo(self):
        if self._tipo_sel() != 'enemigo': return
        p = self.app.proyecto; i = self.sel - 1
        usos = sum(1 for nv in p['niveles'] for a in nv['apariciones'] if a['tipo'] == i)
        aviso = f'\nSe quitarán también sus {usos} apariciones en el mapa.' if usos else ''
        if messagebox.askyesno('Borrar', f'¿Borrar «{self.personaje["nombre"]}»?{aviso}'):
            del p['enemigos'][i]; self.sel = 0
            for nv in p['niveles']:
                nv['apariciones'] = [dict(a, tipo=a['tipo'] - (1 if a['tipo'] > i else 0))
                                     for a in nv['apariciones'] if a['tipo'] != i]
            self.app.marcar_cambio('sprites'); self.refrescar()
