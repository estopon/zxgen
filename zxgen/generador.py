"""GENERADOR DE JUEGOS PARA ZX SPECTRUM 128K  -  Fase 7
Ejecutar:  python generador.py      (requiere Pillow:  pip install pillow)"""
import json, os, shlex, subprocess, tempfile, traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk

import juego, pantalla, graficos, sonido, estilo
from editor_tiles import EditorTiles
from editor_mapa import EditorMapa
from editor_estrategia import EditorEstrategia
from editor_sprites import EditorSprites

CONFIG = os.path.join(os.path.expanduser("~"), ".zxgen_config.json")
PANTALLAS = ("pantalla_carga", "pantalla_titulo", "pantalla_marco")

RITMOS = {'Automática (25 fps constantes)': None, '50 fps (escenas despejadas y pocos sprites)': 1,
          '25 fps': 2, '16,7 fps (escenas muy cargadas)': 3}
COLORES = ['0 Negro', '1 Azul', '2 Rojo', '3 Magenta', '4 Verde', '5 Cian', '6 Amarillo', '7 Blanco']

class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Generador ZX Spectrum 128K')
        estilo.aplicar(self)
        # tamaño adaptado a la pantalla, para que nada quede fuera de la vista
        ancho = min(1280, self.winfo_screenwidth() - 40)
        alto = min(820, self.winfo_screenheight() - 80)
        self.geometry(f'{ancho}x{alto}+10+10')
        self.minsize(1000, 620)
        self.ruta_proyecto = None
        self.proyecto = juego.proyecto_nuevo()
        self.nivel_sel = 0
        self._fotos = {}
        self.estado = tk.StringVar(value='Proyecto nuevo')
        self._menu()
        # barra de herramientas: lo que se usa a menudo (el resto, en el menú Archivo)
        arriba = ttk.Frame(self, style='Barra.TFrame', padding=(8, 6)); arriba.pack(side='top', fill='x')
        self.l_titulo = ttk.Label(arriba, text='', style='Barra.TLabel', font=(estilo.familia(), 12, 'bold'))
        self.l_titulo.pack(side='left', padx=(2, 16))
        ttk.Button(arriba, text='▶  Generar .tap', style='Accent.TButton', command=self.generar).pack(side='right')
        ttk.Button(arriba, text='Probar en emulador', style='Herr.TButton', command=self.probar).pack(side='right', padx=6)
        ttk.Button(arriba, text='Comprobar', style='Herr.TButton', command=self.comprobar).pack(side='right')
        ttk.Label(arriba, text='Ctrl+S guardar · Ctrl+G generar · F5 probar', style='Barra.TLabel').pack(side='right', padx=12)
        # barra de estado abajo (se coloca antes que las pestañas para que nunca quede fuera)
        abajo = ttk.Frame(self, style='Barra.TFrame'); abajo.pack(side='bottom', fill='x')
        ttk.Label(abajo, textvariable=self.estado, style='Estado.TLabel').pack(side='left')
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill='both', expand=True, padx=8, pady=(4, 6))
        # orden de trabajo: proyecto, gráficos, personajes, mapa, scroll, estrategia, partida, sonido, pantallas
        self._pestana_general()
        self.ed_tiles = EditorTiles(self.pestanas, self); self.pestanas.add(self.ed_tiles, text='Tiles')
        self.ed_sprites = EditorSprites(self.pestanas, self); self.pestanas.add(self.ed_sprites, text='Personajes')
        self.ed_mapa = EditorMapa(self.pestanas, self); self.pestanas.add(self.ed_mapa, text='Mapa')
        self._pestana_scroll()
        self.ed_estrategia = EditorEstrategia(self.pestanas, self); self.pestanas.add(self.ed_estrategia, text='Estrategia')
        self._pestana_partida()
        self._pestana_sonido()
        self._pestana_pantallas()
        self._pestana_textos()
        self.pestanas.bind('<<NotebookTabChanged>>', self._cambio_pestana)
        self.refrescar()

    def nivel(self):
        """Fase que se está editando."""
        n = self.proyecto['niveles']
        self.nivel_sel = max(0, min(self.nivel_sel, len(n) - 1))
        return n[self.nivel_sel]

    # ---------- menú y proyecto ----------
    def _menu(self):
        m = tk.Menu(self)
        a = tk.Menu(m, tearoff=0)
        a.add_command(label='Nuevo', command=self.nuevo, accelerator='Ctrl+N')
        a.add_command(label='Abrir…', command=self.abrir, accelerator='Ctrl+O')
        ej = tk.Menu(a, tearoff=0)
        ej.add_command(label='TERRA ZX (plataformas, 8 fases, puertas y personajes)', command=self.ejemplo_terra)
        ej.add_command(label='MEZCLA ZX (modo mezcla, estilo SMB)', command=self.ejemplo_mezcla)
        a.add_cascade(label='Ejemplos', menu=ej)
        a.add_separator()
        a.add_command(label='Guardar', command=self.guardar, accelerator='Ctrl+S')
        a.add_command(label='Guardar como…', command=lambda: self.guardar(True), accelerator='Ctrl+Mayús+S')
        a.add_separator(); a.add_command(label='Salir', command=self.destroy)
        m.add_cascade(label='Archivo', menu=a)
        y = tk.Menu(m, tearoff=0)
        y.add_command(label='Atajos de teclado', command=lambda: messagebox.showinfo('Atajos', (
            'Ctrl+N  nuevo proyecto\nCtrl+O  abrir\nCtrl+S  guardar\nCtrl+Mayús+S  guardar como\n'
            'Ctrl+G  generar la cinta .tap\nF5  probar en el emulador\nF7  comprobar errores')))
        y.add_command(label='Acerca de', command=lambda: messagebox.showinfo('Generador ZX Spectrum 128K', (
            'Crea juegos de scroll para ZX Spectrum 128K: tiles, personajes, mapas, scroll fino, '
            'estrategia (inventario, puertas, personajes que hablan), música PT3 y efectos de sonido.')))
        m.add_cascade(label='Ayuda', menu=y)
        self.config(menu=m)
        self.bind_all('<Control-g>', lambda e: self.generar())
        self.bind_all('<Control-G>', lambda e: self.generar())
        self.bind_all('<F5>', lambda e: self.probar())
        self.bind_all('<Control-s>', lambda e: self.guardar())
        self.bind_all('<Control-o>', lambda e: self.abrir())
        self.bind_all('<Control-n>', lambda e: self.nuevo())
        self.bind_all('<Control-S>', lambda e: self.guardar(True))
        self.bind_all('<F7>', lambda e: self.comprobar())

    def nuevo(self):
        if messagebox.askyesno('Nuevo', '¿Descartar el proyecto actual?'):
            self.proyecto = juego.proyecto_nuevo(); self.ruta_proyecto = None; self.nivel_sel = 0; self.refrescar()

    def ejemplo_mezcla(self):
        if messagebox.askyesno('Ejemplo', '¿Descartar el proyecto actual y abrir el ejemplo del modo mezcla?'):
            import ejemplo
            self.proyecto = ejemplo.proyecto_mezcla(juego.proyecto_nuevo())
            self.ruta_proyecto = None; self.nivel_sel = 0; self.refrescar()

    def ejemplo_terra(self):
        if messagebox.askyesno('Ejemplo', '¿Descartar el proyecto actual y abrir TERRA ZX?'):
            import ejemplo_terra
            self.config(cursor='watch'); self.update()
            try:
                self.proyecto = ejemplo_terra.proyecto(ejemplo_terra.LARGO)
            finally:
                self.config(cursor='')
            self.ruta_proyecto = None; self.nivel_sel = 0; self.refrescar()

    def abrir(self):
        ruta = filedialog.askopenfilename(filetypes=[('Proyecto', '*.json')])
        if not ruta: return
        try:
            with open(ruta, encoding='utf-8') as f: d = json.load(f)
            for k in PANTALLAS:
                if d.get(k): d[k] = bytes.fromhex(d[k])
            d = juego.actualizar(d)
            if d['partida'].get('fuente'): d['partida']['fuente'] = bytes.fromhex(d['partida']['fuente'])
            mus = d['partida']['musica']
            for k in ('menu', 'juego'):
                if mus.get(k): mus[k] = bytes.fromhex(mus[k])
            p = juego.proyecto_nuevo(); p.update(d); self.nivel_sel = 0
            self.proyecto = p; self.ruta_proyecto = ruta; self.refrescar()
            self.estado.set(f'Abierto: {ruta}')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo abrir:\n{e}')

    def guardar(self, como=False):
        self.recoger()
        if como or not self.ruta_proyecto:
            ruta = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Proyecto', '*.json')])
            if not ruta: return
            self.ruta_proyecto = ruta
        d = dict(self.proyecto)
        for k in PANTALLAS:
            if d.get(k): d[k] = d[k].hex()
        d['partida'] = dict(d['partida'])
        if d['partida'].get('fuente'): d['partida']['fuente'] = bytes(d['partida']['fuente']).hex()
        d['partida']['musica'] = {k: (v.hex() if v else None) for k, v in d['partida']['musica'].items()}
        with open(self.ruta_proyecto, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        self.estado.set(f'Guardado: {self.ruta_proyecto}')

    # ---------- pestaña General ----------
    def _pestana_general(self):
        f = ttk.Frame(self.pestanas, padding=16); self.pestanas.add(f, text='Proyecto')
        ttk.Label(f, text='Nombre del juego (máx. 10 caracteres en la cinta):').grid(row=0, column=0, sticky='w')
        self.v_nombre = tk.StringVar()
        ttk.Entry(f, textvariable=self.v_nombre, width=20).grid(row=0, column=1, sticky='w', padx=6)
        ttk.Label(f, text='Posición del área de juego (24×20 caracteres):').grid(row=1, column=0, sticky='w', pady=(12, 0))
        a = ttk.Frame(f); a.grid(row=1, column=1, sticky='w', pady=(12, 0))
        self.v_acol = tk.IntVar(); self.v_afila = tk.IntVar()
        ttk.Label(a, text='columna').pack(side='left')
        ttk.Spinbox(a, from_=0, to=7, textvariable=self.v_acol, width=4, command=self._area_cambiada).pack(side='left', padx=4)
        ttk.Label(a, text='fila').pack(side='left')
        ttk.Spinbox(a, from_=0, to=4, textvariable=self.v_afila, width=4, command=self._area_cambiada).pack(side='left', padx=4)
        ttk.Label(f, text='Emulador para «Probar» ({tap} = archivo):').grid(row=2, column=0, sticky='w', pady=(12, 0))
        self.v_emu = tk.StringVar(value=self._config().get('emulador', ''))
        e = ttk.Frame(f); e.grid(row=2, column=1, sticky='w', pady=(12, 0))
        ttk.Entry(e, textvariable=self.v_emu, width=50).pack(side='left')
        ttk.Button(e, text='Buscar…', command=self._buscar_emu).pack(side='left', padx=4)
        ttk.Label(f, style='Ayuda.TLabel', text='Ejemplos:  fuse --machine 128 {tap}    ·    "C:\\ZEsarUX\\zesarux.exe" --machine 128k {tap}').grid(row=3, column=1, sticky='w')
        self.v_optim = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text='Meter en la cinta solo lo que se usa (tiles, enemigos, fotogramas y balas sin usar se quedan fuera)',
                        variable=self.v_optim, command=self._optim_cambiado).grid(row=4, column=0, columnspan=2, sticky='w', pady=(12, 0))
        mm = ttk.LabelFrame(f, text='Mapa de memoria del Spectrum 128K (cada barra es un banco de 16 KB)', padding=8)
        mm.grid(row=5, column=0, columnspan=2, sticky='we', pady=(10, 0))
        self.c_mem = tk.Canvas(mm, width=900, height=7 * 30 + 10, bg=estilo.PANEL, highlightthickness=0)
        self.c_mem.pack(anchor='w')
        self.l_memoria = ttk.Label(mm, text='', justify='left', wraplength=900)
        self.l_memoria.pack(anchor='w', pady=(6, 0))
        info = ('Máquina: ZX Spectrum 128K (+2 / +2A / +3 con cinta). Controles: Q A O P o joystick Sinclair '
                '(6 7 8 9); disparo con ESPACIO o 0. En plataformas: Q salta, A se agacha y entra en puertas.\n\n'
                'Orden de trabajo sugerido (las pestañas van en este orden): dibuja los tiles, crea los '
                'personajes, pinta el mapa de cada fase, elige el scroll, prepara la estrategia (inventario, '
                'puertas y personajes que hablan), ajusta la partida y el sonido, y añade las pantallas.')
        ttk.Label(f, text=info, wraplength=900, justify='left', style='Ayuda.TLabel').grid(row=6, column=0, columnspan=2, sticky='w', pady=(10, 0))

    # ---------- pestaña Scroll ----------
    def _pestana_scroll(self):
        f = ttk.Frame(self.pestanas, padding=12); self.pestanas.add(f, text='Scroll')
        marco_izq = estilo.Desplazable(f); marco_izq.grid(row=0, column=0, sticky='nsw')
        f.rowconfigure(0, weight=1)
        izq = marco_izq.interior
        self.v_dir = tk.StringVar(); self.v_modo = tk.StringVar(); self.v_retro = tk.BooleanVar()
        self.v_vauto = tk.IntVar(); self.v_umb = tk.IntVar(); self.v_umbr = tk.IntVar()
        d = ttk.LabelFrame(izq, text='Dirección (una por juego)', padding=8); d.pack(fill='x')
        ttk.Radiobutton(d, text='Vertical: avanza hacia arriba', value='vertical', variable=self.v_dir,
                        command=self._cambiar_direccion).pack(anchor='w')
        ttk.Radiobutton(d, text='Horizontal: avanza hacia la derecha', value='horizontal', variable=self.v_dir,
                        command=self._cambiar_direccion).pack(anchor='w')
        ttk.Radiobutton(d, text='Plataformas: horizontal con gravedad y saltos', value='plataformas',
                        variable=self.v_dir, command=self._cambiar_direccion).pack(anchor='w')
        pf = ttk.Frame(d); pf.pack(anchor='w', pady=(6, 0))
        ttk.Label(pf, text='Paso del scroll:').pack(side='left')
        self.v_paso = tk.StringVar(value='8')
        self.c_paso = ttk.Combobox(pf, values=['1', '2', '4', '8'], textvariable=self.v_paso, state='readonly', width=3)
        self.c_paso.pack(side='left', padx=4); self.c_paso.bind('<<ComboboxSelected>>', lambda e: self._scroll_cambiado())
        ttk.Label(pf, text='píxeles', style='Ayuda.TLabel').pack(side='left')
        cf = ttk.Frame(d); cf.pack(anchor='w', pady=(4, 0))
        ttk.Label(cf, text='Cadencia:').pack(side='left')
        self.v_ritmo = tk.StringVar()
        self.c_ritmo = ttk.Combobox(cf, values=list(RITMOS), textvariable=self.v_ritmo, state='readonly', width=34)
        self.c_ritmo.pack(side='left', padx=4); self.c_ritmo.bind('<<ComboboxSelected>>', lambda e: self._scroll_cambiado())
        self.v_compilar = tk.BooleanVar(value=True)
        ttk.Checkbutton(d, text='Compilar sprites (código Z80 en el banco 7; solo con scroll horizontal fino)',
                        variable=self.v_compilar, command=self._scroll_cambiado).pack(anchor='w', pady=(4, 0))
        smb = ttk.LabelFrame(d, text='Estilo Super Mario Bros 128K (solo scroll horizontal fino)', padding=6)
        smb.pack(fill='x', pady=(6, 0))
        self.v_mezcla = tk.BooleanVar(value=False); self.v_colspr = tk.BooleanVar(value=False)
        ttk.Checkbutton(smb, text='Modo mezcla: dos pantallas alternadas a 50 Hz (tono medio en los tiles)',
                        variable=self.v_mezcla, command=self._scroll_cambiado).pack(anchor='w')
        ttk.Checkbutton(smb, text='Color propio de los personajes (pintan sus casillas de su color)',
                        variable=self.v_colspr, command=self._scroll_cambiado).pack(anchor='w')
        self.l_smb = ttk.Label(smb, style='Ayuda.TLabel', wraplength=420, justify='left')
        self.l_smb.pack(anchor='w')
        self.l_paso = ttk.Label(d, style='Ayuda.TLabel', wraplength=430, justify='left')
        self.l_paso.pack(anchor='w')
        m = ttk.LabelFrame(izq, text='Modo', padding=8); m.pack(fill='x', pady=8)
        ttk.Radiobutton(m, text='Sigue al jugador (avanza cuando se acerca al borde)', value='sigue',
                        variable=self.v_modo, command=self._scroll_cambiado).grid(row=0, column=0, columnspan=3, sticky='w')
        self.c_retro = ttk.Checkbutton(m, text='Permitir retroceso', variable=self.v_retro, command=self._scroll_cambiado)
        self.c_retro.grid(row=1, column=0, columnspan=3, sticky='w', padx=(20, 0))
        ttk.Radiobutton(m, text='Automático (avanza solo a velocidad fija)', value='auto',
                        variable=self.v_modo, command=self._scroll_cambiado).grid(row=2, column=0, columnspan=3, sticky='w', pady=(8, 0))
        ttk.Label(m, text='Un paso cada').grid(row=3, column=0, sticky='w', padx=(20, 0))
        self.s_vauto = ttk.Spinbox(m, from_=1, to=50, textvariable=self.v_vauto, width=4, command=self._scroll_cambiado)
        self.s_vauto.grid(row=3, column=1, padx=4)
        self.l_vauto = ttk.Label(m, text=''); self.l_vauto.grid(row=3, column=2, sticky='w')
        u = ttk.LabelFrame(izq, text='Umbrales (en píxeles, modo «sigue»)', padding=8); u.pack(fill='x')
        ttk.Label(u, text='Distancia al borde de avance:').grid(row=0, column=0, sticky='w')
        self.s_umb = ttk.Spinbox(u, from_=0, to=184, textvariable=self.v_umb, width=5, command=self._scroll_cambiado)
        self.s_umb.grid(row=0, column=1, padx=4)
        ttk.Label(u, text='Distancia al borde de retroceso:').grid(row=1, column=0, sticky='w')
        self.s_umbr = ttk.Spinbox(u, from_=0, to=184, textvariable=self.v_umbr, width=5, command=self._scroll_cambiado)
        self.s_umbr.grid(row=1, column=1, padx=4)
        for w in (self.s_vauto, self.s_umb, self.s_umbr):
            w.bind('<FocusOut>', lambda e: self._scroll_cambiado()); w.bind('<Return>', lambda e: self._scroll_cambiado())
        self.f_fisica = ttk.LabelFrame(izq, text='Salto (modo plataformas)', padding=8); self.f_fisica.pack(fill='x', pady=(8, 0))
        self.v_alt = tk.IntVar(); self.v_sub = tk.IntVar(); self.v_cmax = tk.IntVar()
        for r, (txt, var, a, b) in enumerate((('Altura del salto (px)', self.v_alt, 8, 120),
                                              ('Tiempo de subida (fotogramas)', self.v_sub, 3, 23),
                                              ('Velocidad máxima de caída (px)', self.v_cmax, 1, 8))):
            ttk.Label(self.f_fisica, text=txt).grid(row=r, column=0, sticky='w')
            sp = ttk.Spinbox(self.f_fisica, from_=a, to=b, textvariable=var, width=5, command=self._scroll_cambiado)
            sp.grid(row=r, column=1, padx=4)
            sp.bind('<FocusOut>', lambda e: self._scroll_cambiado()); sp.bind('<Return>', lambda e: self._scroll_cambiado())
        self.l_fisica = ttk.Label(self.f_fisica, style='Ayuda.TLabel', wraplength=400, justify='left')
        self.l_fisica.grid(row=3, column=0, columnspan=2, sticky='w', pady=(4, 0))
        ttk.Label(izq, wraplength=420, justify='left', style='Ayuda.TLabel', text=(
            'El scroll avanza de paso en paso (8 píxeles o menos). En modo «sigue», cuando el jugador cruza '
            'la línea roja el escenario avanza; con retroceso, al cruzar la línea azul vuelve atrás, '
            'pero nunca más allá del inicio del mapa. En modo automático el jugador se mueve libremente '
            'dentro del área mientras el escenario avanza.')).pack(anchor='w', pady=8)
        der = ttk.LabelFrame(f, text='Área de juego (posición inicial del jugador)', padding=8)
        der.grid(row=0, column=1, sticky='n', padx=16)
        self.esquema = tk.Canvas(der, width=192 * 2, height=160 * 2, bg='#103010', highlightthickness=0)
        self.esquema.pack()

    def _refrescar_scroll(self):
        sc = self.proyecto['scroll']
        self.v_dir.set(sc['direccion']); self.v_modo.set(sc['modo']); self.v_retro.set(sc['retroceso'])
        self.v_vauto.set(sc['vel_auto']); self.v_umb.set(sc['umbral']); self.v_umbr.set(sc['umbral_ret'])
        fi = sc['fisica']; self.v_alt.set(fi['altura']); self.v_sub.set(fi['subida']); self.v_cmax.set(fi['caida_max'])
        self.v_paso.set(str(sc.get('paso', 8)))
        self.v_compilar.set(sc.get('compilar_sprites', True))
        self.v_mezcla.set(sc.get('mezcla', False)); self.v_colspr.set(sc.get('color_sprites', False))
        self.v_ritmo.set([k for k, v in RITMOS.items() if v == sc.get('ritmo')][0])
        self._dibujar_esquema()

    def _scroll_cambiado(self, marcar=True):
        sc = self.proyecto['scroll']
        sc['modo'] = self.v_modo.get(); sc['retroceso'] = bool(self.v_retro.get())
        for clave, v in (('vel_auto', self.v_vauto), ('umbral', self.v_umb), ('umbral_ret', self.v_umbr)):
            try: sc[clave] = int(v.get())
            except (tk.TclError, ValueError): pass
        sc['paso'] = int(self.v_paso.get() or 8)
        sc['compilar_sprites'] = bool(self.v_compilar.get())
        sc['mezcla'] = bool(self.v_mezcla.get()); sc['color_sprites'] = bool(self.v_colspr.get())
        if self.v_ritmo.get() in RITMOS: sc['ritmo'] = RITMOS[self.v_ritmo.get()]
        for clave, v in (('altura', self.v_alt), ('subida', self.v_sub), ('caida_max', self.v_cmax)):
            try: sc['fisica'][clave] = int(v.get())
            except (tk.TclError, ValueError): pass
        if marcar: self.marcar_cambio('scroll')
        self._dibujar_esquema()

    def _cambiar_direccion(self):
        nueva = self.v_dir.get(); sc = self.proyecto['scroll']
        if nueva == sc['direccion']: return
        mismo_mapa = {nueva, sc['direccion']} == {'horizontal', 'plataformas'}
        if mismo_mapa:
            sc['direccion'] = nueva
            self.marcar_cambio('dirección'); self.refrescar(); return
        if not messagebox.askyesno('Cambiar dirección',
                                   'El mapa y los enemigos colocados se girarán para la nueva dirección (el inicio '
                                   'de abajo pasa a la izquierda, o al revés) y el jugador volverá a su posición de salida. '
                                   'Los tiles no se giran. Al pasar a horizontal, las dos últimas columnas '
                                   'del mapa vertical (y sus enemigos) no caben y se pierden. ¿Seguir?'):
            self.v_dir.set(sc['direccion']); return
        for nv in self.proyecto['niveles']:
            nv['apariciones'] = juego.convertir_apariciones(nv['apariciones'], nv['mapa'], nueva != 'vertical')
            nv['mapa'] = juego.convertir_mapa(nv['mapa'], nueva != 'vertical')
        sc['direccion'] = nueva
        j = self.proyecto['jugador']; w, h = graficos.TAMANOS[j['tamano']]
        if nueva != 'vertical': j['x'], j['y'] = 16, (160 - h) // 2
        else: j['x'], j['y'] = (192 - w) // 2 // 2 * 2, 160 - h - 16
        self.marcar_cambio('dirección'); self.refrescar()

    def _dibujar_esquema(self):
        c = self.esquema; c.delete('all')
        sc = self.proyecto['scroll']; j = self.proyecto['jugador']
        w, h = graficos.TAMANOS[j['tamano']]; E = 2
        hor = sc['direccion'] != 'vertical'
        plat = sc['direccion'] == 'plataformas'
        for w_ in self.f_fisica.winfo_children():
            try: w_.configure(state='normal' if plat else 'disabled')
            except tk.TclError: pass
        if plat:
            subida, caida = juego.tablas_salto(sc['fisica'])
            self.l_fisica.configure(text=f'Altura real: {sum(subida)} px en {len(subida)} fotogramas. Salta con '
                                         'arriba (Q, 9 o Kempston); soltando pronto, salta menos. Caer al vacío '
                                         'cuesta una vida.')
        auto = sc['modo'] == 'auto'
        self.c_retro.configure(state='disabled' if auto else 'normal')
        self.s_vauto.configure(state='normal' if auto else 'disabled')
        self.s_umb.configure(state='disabled' if auto else 'normal')
        self.s_umbr.configure(state='normal' if (not auto and sc['retroceso']) else 'disabled')
        n = max(1, sc['vel_auto'])
        paso = sc.get('paso', 8)
        if paso == 8:
            nota = 'De 8 en 8: 25 fps, pero el escenario avanza a saltos y el jugador retrocede de golpe al avanzar.'
        elif not hor:
            nota = 'Vertical fino: tan rápido como de 8 en 8; los colores se mueven de 8 en 8.'
        else:
            try:
                n = len(juego.pares_proyecto(self.proyecto)) if all(len(nv['mapa']) == juego.MAPA_ALTO
                                                                   for nv in self.proyecto['niveles']) else 0
            except Exception:
                n = 0
            limite = min(juego.MAX_PARES, juego.MAX_PARES_MEM // (128 // paso))
            comp = 'compilados' if juego.usa_compilados(self.proyecto) else 'de datos'
            nota = (f'Horizontal fino por bloques pre-desplazados ({comp}), al estilo de Cobra o del Mario de '
                    f'Smirnov: solo se dibujan las casillas con contenido, así que un cielo liso (tile sin píxeles) '
                    f'sale casi gratis. Cadencia constante y el escenario sigue al jugador píxel a píxel. '
                    f'Combinaciones de columnas vecinas: {n} de {limite} posibles.')
            try:
                comp, _, b7 = juego.plan_compilados(self.proyecto)
                if sc.get('compilar_sprites', True):
                    nombres = {'j': 'jugador', 'bala_j': 'disparo', 'bala_e': 'disparo enemigo'}
                    lista = [nombres.get(k) or self.proyecto['enemigos'][k]['nombre'] for k in
                             sorted(comp, key=lambda k: (isinstance(k, int), str(k)))]
                    nota += (f' Sprites compilados: {", ".join(lista) if lista else "ninguno (no caben)"} '
                             f'({len(b7)} de {juego.BANCO7_TAM} bytes); el resto usa la rutina normal.')
            except Exception:
                pass
            vel = self.proyecto['jugador'].get('velocidad', 2)
            if sc['modo'] == 'sigue' and paso > vel:
                nota += f' Aviso: el paso ({paso}) es mayor que la velocidad del jugador ({vel}): oscilará {paso - vel} px.'
        self.l_paso.configure(text=nota)
        if (sc.get('mezcla') or sc.get('color_sprites')) and not juego.modo_bloques(self.proyecto):
            self.l_smb.configure(text='Necesita dirección horizontal o plataformas y paso 1, 2 o 4.', foreground='red')
        elif sc.get('mezcla'):
            try: coste = juego.coste_fondo(self.proyecto)
            except Exception: coste = 0
            aviso = (' El escenario más cargado cuesta unos {:,} ciclos: '.format(coste).replace(',', '.') +
                     ('cabe en 50 fps.' if coste < 45000 else
                      'a veces no llegará a 50 fps y se notará el parpadeo; usa más cielo vacío.'))
            self.l_smb.configure(style='Ayuda.TLabel', text=(
                'Como el Super Mario Bros de 128K: cada fotograma se dibuja en una pantalla y se muestra '
                'la otra, y se alternan 50 veces por segundo. Los píxeles «mezcla» de los tiles se '
                'encienden en una y se apagan en la otra, en damero, y se ve el tono intermedio entre tinta '
                'y papel (rojo oscuro, naranja...). Va siempre a 50 fps; deja mucho cielo vacío (tile sin '
                'píxeles), que no se dibuja.' + aviso))
        else:
            self.l_smb.configure(style='Ayuda.TLabel', text='Color propio: elige el color de cada personaje en '
                                 'la pestaña Personajes. Queda mejor sobre cielo negro.' if sc.get('color_sprites') else '')
        self.c_ritmo.configure(state='disabled' if sc.get('mezcla') else 'readonly')
        self.l_vauto.configure(text=f'fotogramas  (paso de {paso} px: ≈ {paso * 25 / n:.0f} px/s)')
        flecha = (192 * E - 30, 80 * E, 192 * E - 6, 80 * E) if hor else (96 * E, 30, 96 * E, 6)
        c.create_line(*flecha, arrow='last', fill='white', width=3)
        if not auto:
            if hor:
                xu = (192 - sc['umbral']) * E
                c.create_line(xu, 0, xu, 160 * E, fill='red', width=2, dash=(6, 3))
                if sc['retroceso']:
                    xr = sc['umbral_ret'] * E
                    c.create_line(xr, 0, xr, 160 * E, fill='#4080ff', width=2, dash=(6, 3))
            else:
                yu = sc['umbral'] * E
                c.create_line(0, yu, 192 * E, yu, fill='red', width=2, dash=(6, 3))
                if sc['retroceso']:
                    yr = (160 - sc['umbral_ret']) * E
                    c.create_line(0, yr, 192 * E, yr, fill='#4080ff', width=2, dash=(6, 3))
        if j['fotogramas']:
            img = graficos.imagen_sprite(j['fotogramas'][0], E, fondo=(16, 48, 16), tinta=(255, 255, 255), contorno=(0, 0, 0))
            self._foto_esquema = ImageTk.PhotoImage(img)
            c.create_image(j['x'] * E, j['y'] * E, image=self._foto_esquema, anchor='nw')
        c.create_rectangle(j['x'] * E, j['y'] * E, (j['x'] + w) * E, (j['y'] + h) * E, outline='yellow')

    def _area_cambiada(self):
        self.recoger()
        if not self.proyecto.get('pantalla_marco'):
            self.dibujar_pantalla('pantalla_marco')

    def _config(self):
        try:
            with open(CONFIG, encoding='utf-8') as f: return json.load(f)
        except (OSError, ValueError):
            return {}

    def _buscar_emu(self):
        r = filedialog.askopenfilename(title='Ejecutable del emulador')
        if r: self.v_emu.set(f'"{r}" {{tap}}')

    COLORES_MEM = (('Fase', '#58b368'), ('Sprites', '#8e6cc9'), ('Música', '#e8a23a'), ('Reproductor', '#e8a23a'),
                   ('Efectos', '#f0c060'), ('Configuración', '#4f7fd1'), ('Textos', '#7fa4e0'), ('Bloques', '#3bb3c3'),
                   ('Presentación', '#9aa3ae'), ('Marco', '#b5bcc5'), ('Pantalla', '#9aa3ae'), ('Motor', '#2a3f66'),
                   ('Búferes', '#c9ced6'), ('Sistema', '#c9ced6'))

    def _optim_cambiado(self):
        self.proyecto['optimizar'] = bool(self.v_optim.get()); self.marcar_cambio('optimización'); self._memoria()

    def _memoria(self):
        c = self.c_mem; c.delete('all')
        try:
            seg, inf = juego.mapa_memoria(self.proyecto)
        except Exception as e:
            self.l_memoria.configure(text=f'No cabe todo: {e}', style='Aviso.TLabel'); return
        fijos = [(2, 0x8000, 0xC00, 'Búferes del fondo'), (2, 0xBE00, 0x200, 'Sistema (interrupciones)')]
        filas = [(0, 'Banco 0'), (1, 'Banco 1'), (2, 'Banco 2 (motor)'), (3, 'Banco 3'), (4, 'Banco 4'),
                 (6, 'Banco 6'), (7, 'Banco 7')]
        X0, W = 120, 690
        libre_total, mayor = 0, 0
        for r, (b, nombre) in enumerate(filas):
            y = 6 + r * 30
            c.create_text(4, y + 11, text=nombre, anchor='w', fill=estilo.TEXTO)
            c.create_rectangle(X0, y, X0 + W, y + 22, fill='#ffffff', outline=estilo.BORDE)
            base = 0x8000 if b == 2 else 0xC000
            usado = 0; ocupado = []
            for (bb, ini, tam, que) in seg + (fijos if b == 2 else []):
                if bb != b or tam <= 0: continue
                x1 = X0 + (ini - base) * W / 16384; x2 = X0 + (ini - base + tam) * W / 16384
                col = next((cc for k, cc in self.COLORES_MEM if que.startswith(k)), '#cccccc')
                c.create_rectangle(x1, y + 1, max(x1 + 1, x2), y + 21, fill=col, outline='white')
                if x2 - x1 > 46:
                    c.create_text((x1 + x2) / 2, y + 11, text=que, fill='white', font=(estilo.familia(), 8))
                ocupado.append((ini, ini + tam))
            if b != 2:
                ocupado.sort(); fin = max([o[1] for o in ocupado] + [base])
                libre = 0x10000 - fin
                libre_total += libre; mayor = max(mayor, libre)
                c.create_text(X0 + W + 6, y + 11, text=f'{libre // 1024} KB libres' if libre >= 1024 else f'{libre} B libres',
                              anchor='w', fill=estilo.SUAVE, font=(estilo.familia(), 8))
        partes = [f'Libre en total: {libre_total // 1024} KB (el hueco más grande, {mayor // 1024} KB). '
                  'Las fases se colocan en el primer hueco donde caben, en cualquier banco: si añades fases, '
                  'tiles o música, el reparto se ajusta solo.']
        if inf:
            quitado = []
            if inf['tiles']: quitado.append(f'{len(inf["tiles"])} tiles ({", ".join(map(str, inf["tiles"][:12]))}{"…" if len(inf["tiles"]) > 12 else ""})')
            if inf['enemigos']: quitado.append(f'{len(inf["enemigos"])} tipos de enemigo ({", ".join(inf["enemigos"])})')
            if inf['fotogramas']: quitado.append(f'{len(inf["fotogramas"])} fotogramas del jugador')
            if inf['balas']: quitado.append('el disparo ' + ' y el '.join({'jugador': 'del jugador', 'enemigo': 'enemigo'}[x] for x in inf['balas']))
            partes.append('Se quedan fuera de la cinta porque no se usan: ' + ('; '.join(quitado) if quitado else 'nada (todo se usa)') + '.')
        self.l_memoria.configure(text='\n'.join(partes), style='TLabel')

    # ---------- pestaña Pantallas ----------
    def _pestana_pantallas(self):
        f = ttk.Frame(self.pestanas, padding=12); self.pestanas.add(f, text='Pantallas')
        self.lienzos = {}
        for col, (clave, titulo) in enumerate([('pantalla_carga', 'Pantalla de carga'),
                                               ('pantalla_titulo', 'Pantalla de presentación'),
                                               ('pantalla_marco', 'Marco del juego')]):
            marco = ttk.LabelFrame(f, text=titulo, padding=8)
            marco.grid(row=0, column=col, padx=6, sticky='n')
            c = tk.Canvas(marco, width=288, height=224, bg='black', highlightthickness=0)
            c.pack(); self.lienzos[clave] = c
            b = ttk.Frame(marco); b.pack(pady=6)
            ttk.Button(b, text='Importar…', command=lambda k=clave: self.importar(k)).pack(side='left')
            ttk.Button(b, text='Exportar .scr…', command=lambda k=clave: self.exportar(k)).pack(side='left', padx=4)
            ttk.Button(b, text='Quitar', command=lambda k=clave: self.quitar(k)).pack(side='left')
        ttk.Label(f, text='Las imágenes se ajustan a 256×192 y se convierten a la paleta del Spectrum '
                          '(2 colores por cuadro de 8×8). Para mejor resultado, prepara la imagen ya a 256×192. '
                          'Si no hay presentación, se reutiliza la de carga. El marco se muestra durante la partida: '
                          'el rectángulo amarillo es el área de juego, que el motor tapa. Sin marco se usa uno sencillo.',
                  wraplength=900).grid(row=1, column=0, columnspan=3, pady=8)

    def importar(self, clave):
        ruta = filedialog.askopenfilename(filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.gif *.bmp *.scr'), ('Todos', '*.*')])
        if not ruta: return
        self.config(cursor='watch'); self.update()
        try:
            self.proyecto[clave] = pantalla.cargar_pantalla(ruta)
            self.dibujar_pantalla(clave)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo convertir la imagen:\n{e}')
        finally:
            self.config(cursor='')

    def exportar(self, clave):
        if not self.proyecto.get(clave): return
        ruta = filedialog.asksaveasfilename(defaultextension='.scr', filetypes=[('Pantalla', '*.scr')])
        if ruta:
            with open(ruta, 'wb') as f: f.write(self.proyecto[clave])

    def quitar(self, clave):
        self.proyecto[clave] = None; self.dibujar_pantalla(clave)

    def dibujar_pantalla(self, clave):
        c = self.lienzos[clave]; c.delete('all')
        scr = self.proyecto.get(clave)
        if not scr and clave == 'pantalla_marco':
            a = self.proyecto['area']; scr = juego.marco_defecto(a['col'], a['fila'])
        if not scr:
            c.create_text(144, 112, text='(sin imagen)', fill='gray'); return
        img = pantalla.scr_a_imagen(scr, escala=1, borde=0)
        self._fotos[clave] = ImageTk.PhotoImage(img)
        c.create_image(0, 0, image=self._fotos[clave], anchor='nw')
        if clave == 'pantalla_marco':
            a = self.proyecto['area']
            x0, y0 = 16 + a['col'] * 8, 16 + a['fila'] * 8
            c.create_rectangle(x0, y0, x0 + 192, y0 + 160, outline='yellow', dash=(3, 3))

    # ---------- pestaña Textos ----------
    def _pestana_textos(self):
        marco = ttk.Frame(self.pestanas, padding=12); self.pestanas.add(marco, text='Textos')
        sel = ttk.Frame(marco); sel.pack(fill='x', pady=(0, 8))
        ttk.Label(sel, text='Pantalla:').pack(side='left')
        self.v_lista = tk.StringVar(value='Instrucciones')
        c = ttk.Combobox(sel, values=['Instrucciones', 'Menú (sobre la presentación)'], textvariable=self.v_lista,
                         state='readonly', width=28)
        c.pack(side='left', padx=6); c.bind('<<ComboboxSelected>>', lambda e: self.refrescar_textos())
        f = ttk.Frame(marco); f.pack(fill='both', expand=True)
        cols = ('fila', 'col', 'tinta', 'brillo', 'texto')
        self.tabla = ttk.Treeview(f, columns=cols, show='headings', height=10)
        for c, w in zip(cols, (50, 50, 90, 60, 420)):
            self.tabla.heading(c, text=c.capitalize()); self.tabla.column(c, width=w)
        self.tabla.grid(row=0, column=0, columnspan=8, sticky='nsew')
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar_texto)
        self.e_fila = tk.IntVar(value=0); self.e_col = tk.IntVar(value=0)
        self.e_tinta = tk.StringVar(value=COLORES[7]); self.e_brillo = tk.BooleanVar()
        self.e_texto = tk.StringVar()
        fila = 1
        ttk.Label(f, text='Fila (0-23)').grid(row=fila, column=0, pady=8)
        ttk.Spinbox(f, from_=0, to=23, textvariable=self.e_fila, width=4).grid(row=fila, column=1)
        ttk.Label(f, text='Columna (0-31)').grid(row=fila, column=2)
        ttk.Spinbox(f, from_=0, to=31, textvariable=self.e_col, width=4).grid(row=fila, column=3)
        ttk.Combobox(f, values=COLORES, textvariable=self.e_tinta, width=11, state='readonly').grid(row=fila, column=4)
        ttk.Checkbutton(f, text='Brillo', variable=self.e_brillo).grid(row=fila, column=5)
        ttk.Entry(f, textvariable=self.e_texto, width=40).grid(row=2, column=0, columnspan=5, sticky='we')
        ttk.Button(f, text='Añadir', command=self.anadir_texto).grid(row=2, column=5)
        ttk.Button(f, text='Modificar', command=self.modificar_texto).grid(row=2, column=6)
        ttk.Button(f, text='Borrar', command=self.borrar_texto).grid(row=2, column=7)
        ttk.Label(f, text='Instrucciones: pantalla que se abre con la tecla 2 del menú. Menú: textos que se escriben '
                          'sobre la pantalla de presentación (la línea de controles se configura en la pestaña Partida). '
                          'Las tildes y la ñ se convierten a letras sin acento (la fuente de la ROM no las tiene; '
                          'en la fase 5 el juego tendrá su propia fuente editable).',
                  wraplength=820).grid(row=3, column=0, columnspan=8, pady=10, sticky='w')
        f.columnconfigure(4, weight=1)

    def _textos(self):
        if self.v_lista.get().startswith('Men'):
            return self.proyecto['partida']['menu']
        return self.proyecto['textos']

    def _texto_desde_campos(self):
        return {'fila': self.e_fila.get(), 'col': self.e_col.get(), 'tinta': int(self.e_tinta.get()[0]),
                'brillo': int(self.e_brillo.get()), 'texto': self.e_texto.get()}

    def anadir_texto(self):
        self._textos().append(self._texto_desde_campos()); self.refrescar_textos()

    def modificar_texto(self):
        sel = self.tabla.selection()
        if sel:
            self._textos()[int(sel[0])] = self._texto_desde_campos(); self.refrescar_textos()

    def borrar_texto(self):
        sel = self.tabla.selection()
        if sel:
            del self._textos()[int(sel[0])]; self.refrescar_textos()

    def seleccionar_texto(self, _):
        sel = self.tabla.selection()
        if not sel: return
        t = self._textos()[int(sel[0])]
        self.e_fila.set(t['fila']); self.e_col.set(t['col']); self.e_tinta.set(COLORES[t['tinta']])
        self.e_brillo.set(bool(t['brillo'])); self.e_texto.set(t['texto'])

    def refrescar_textos(self):
        self.tabla.delete(*self.tabla.get_children())
        for i, t in enumerate(self._textos()):
            self.tabla.insert('', 'end', iid=str(i), values=(t['fila'], t['col'], COLORES[t['tinta']],
                                                             'sí' if t['brillo'] else 'no', t['texto']))

    # ---------- pestaña Sonido ----------
    def _pestana_sonido(self):
        f = ttk.Frame(self.pestanas, padding=12); self.pestanas.add(f, text='Sonido')
        mu = ttk.LabelFrame(f, text='Música (módulos PT3 para el chip AY)', padding=8); mu.grid(row=0, column=0, sticky='nwe')
        self.l_musica = {}
        for r, (clave, texto) in enumerate((('menu', 'Menú'), ('juego', 'Fases (todas)'))):
            ttk.Label(mu, text=texto, width=12).grid(row=r, column=0, sticky='w')
            ttk.Button(mu, text='Cargar .pt3…', command=lambda k=clave: self._cargar_musica(k)).grid(row=r, column=1, padx=2)
            ttk.Button(mu, text='Quitar', command=lambda k=clave: self._quitar_musica(k)).grid(row=r, column=2, padx=2)
            self.l_musica[clave] = ttk.Label(mu, text='', width=28); self.l_musica[clave].grid(row=r, column=3, sticky='w', padx=4)
        self.l_musica_total = ttk.Label(mu, style='Ayuda.TLabel', wraplength=430, justify='left')
        self.l_musica_total.grid(row=2, column=0, columnspan=4, sticky='w', pady=(6, 0))
        ef = ttk.LabelFrame(f, text='Efectos de sonido (canal C del AY, sin cortar la música)', padding=8)
        ef.grid(row=1, column=0, sticky='nwe', pady=(10, 0))
        ttk.Label(ef, text='Cuándo suena', style='Seccion.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(ef, text='Efecto', style='Seccion.TLabel').grid(row=0, column=1, sticky='w', padx=6)
        self.v_sfx = {}; self.c_sfx = []
        for r, (clave, texto) in enumerate(sonido.EVENTOS, start=1):
            ttk.Label(ef, text=texto).grid(row=r, column=0, sticky='w', pady=1)
            v = tk.StringVar(); self.v_sfx[clave] = v
            cb = ttk.Combobox(ef, textvariable=v, state='readonly', width=24); self.c_sfx.append(cb)
            cb.grid(row=r, column=1, padx=6, pady=1, sticky='w')
            cb.bind('<<ComboboxSelected>>', lambda e, k=clave: self._sfx_cambiado(k))
            ttk.Button(ef, text='▶ Escuchar', style='Pequeno.TButton',
                       command=lambda k=clave: self._sfx_escuchar(k)).grid(row=r, column=2, pady=1)
        ttk.Button(ef, text='Volver a los efectos por defecto', command=self._sfx_defecto).grid(
            row=len(sonido.EVENTOS) + 1, column=0, columnspan=3, sticky='w', pady=(8, 0))
        self.l_sfx = ttk.Label(ef, style='Ayuda.TLabel', wraplength=560, justify='left')
        self.l_sfx.grid(row=len(sonido.EVENTOS) + 2, column=0, columnspan=3, sticky='w', pady=(6, 0))
        pr = ttk.LabelFrame(f, text='Mis efectos (importados)', padding=8)
        f.columnconfigure(1, weight=1)
        pr.grid(row=0, column=1, rowspan=2, sticky='nwe', padx=(16, 0))
        self.l_propios = tk.Listbox(pr, height=8, width=40, exportselection=False, activestyle='none')
        self.l_propios.grid(row=0, column=0, columnspan=2, sticky='we')
        for k, (txt, fn) in enumerate((('Importar…', self._sfx_importar), ('▶ Escuchar', self._sfx_escuchar_propio),
                                       ('Exportar .afx…', self._sfx_exportar), ('Borrar', self._sfx_borrar))):
            ttk.Button(pr, text=txt, command=fn).grid(row=1 + k // 2, column=k % 2, sticky='we', padx=1, pady=2)
        ttk.Label(pr, style='Ayuda.TLabel', wraplength=360, justify='left', text=(
            'Formatos: .afx (un efecto) y .afb (banco de efectos) de AYFX Editor, el editor de efectos para el '
            'chip AY más usado en el Spectrum; y .wav (golpes, gritos, voces...), que se convierte de forma '
            'aproximada a tono, ruido y volumen del AY. Duración: máximo 2 s (100 fotogramas); lo ideal es '
            f'0,1-0,5 s (5-{sonido.RECOMENDADO} fotogramas), unos 4 bytes por fotograma. Exportar .afx te deja '
            'retocar cualquier efecto (también los convertidos de .wav) en AYFX Editor y volver a importarlo.'
        )).grid(row=3, column=0, columnspan=2, sticky='w', pady=(4, 0))
        ttk.Label(f, style='Ayuda.TLabel', wraplength=420, justify='left', text=(
            'Los efectos se tocan en la interrupción, después de la música: mientras dura un efecto, el '
            'canal C del chip AY hace el efecto y los canales A y B siguen con la melodía. Al acabar, el '
            'canal C vuelve a la música. Si no hay música, los efectos suenan igual.\n\n'
            'Cada efecto ocupa unos 20-90 bytes en el banco 6 (si un mismo efecto se usa para varios '
            'momentos, se guarda una vez). «▶ Escuchar» lo toca en el ordenador con un sonido parecido '
            'al del AY.')).grid(row=2, column=1, sticky='nw', padx=(16, 0), pady=(10, 0))

    def _propios(self):
        return self.proyecto['partida'].setdefault('efectos_propios', {})

    def _refrescar_sonido(self):
        ef = self.proyecto['partida'].setdefault('efectos', dict(sonido.POR_DEFECTO))
        propios = self._propios()
        opciones = ['(ninguno)'] + list(propios) + list(sonido.PRESETS)
        for cb in self.c_sfx: cb.configure(values=opciones)
        for clave, v in self.v_sfx.items():
            v.set(ef.get(clave) if sonido.existe(ef.get(clave), propios) else '(ninguno)')
        total = len(sonido.datos(ef, 0, propios)[0])
        self.l_sfx.configure(text=f'Efectos: {total} bytes en el banco 6. Los tuyos salen al principio de la lista.')
        self.l_propios.delete(0, 'end')
        for nombre, fr in propios.items():
            aviso = '  ⚠ largo' if len(fr) > sonido.RECOMENDADO else ''
            self.l_propios.insert('end', f'{nombre}  ·  {len(fr) / 50:.2f} s  ·  {len(fr) * 4 + 1} bytes{aviso}')

    def _sfx_importar(self):
        rutas = filedialog.askopenfilenames(filetypes=[('Efectos', '*.afx *.afb *.wav'), ('AYFX', '*.afx *.afb'),
                                                       ('Sonido WAV', '*.wav'), ('Todos', '*.*')])
        if not rutas: return
        propios = self._propios(); nuevos, avisos = 0, []
        def nombre_libre(base):
            base = (base or 'Efecto').strip()[:24]; n, k = base, 2
            while n in propios or n in sonido.PRESETS: n = f'{base} {k}'; k += 1
            return n
        for ruta in rutas:
            base = os.path.splitext(os.path.basename(ruta))[0]
            try:
                ext = ruta.lower().rsplit('.', 1)[-1]
                if ext == 'wav':
                    lista = [(base, sonido.leer_wav(ruta))]
                elif ext == 'afb':
                    lista = [(n or f'{base} {k + 1}', fr) for k, (n, fr) in enumerate(sonido.leer_afb(open(ruta, 'rb').read()))]
                else:
                    lista = [(base, sonido.leer_afx(open(ruta, 'rb').read()))]
            except Exception as e:
                avisos.append(f'{os.path.basename(ruta)}: {e}'); continue
            for n, fr in lista:
                if not fr: continue
                if len(fr) > sonido.MAX_FOTOGRAMAS:
                    avisos.append(f'{n}: dura {len(fr) / 50:.1f} s; se recorta a 2 s.'); fr = fr[:sonido.MAX_FOTOGRAMAS]
                propios[nombre_libre(n)] = [list(x) for x in fr]; nuevos += 1
        self.marcar_cambio('efectos'); self._refrescar_sonido()
        messagebox.showinfo('Importar efectos', f'{nuevos} efectos importados.' + ('\n\n' + '\n'.join(avisos) if avisos else ''))

    def _sfx_sel(self):
        s = self.l_propios.curselection()
        return list(self._propios())[s[0]] if s else None

    def _sfx_escuchar_propio(self):
        n = self._sfx_sel()
        if n and not sonido.escuchar(n, self._propios()):
            self.estado.set('No se encontró cómo reproducir sonido en este ordenador.')

    def _sfx_exportar(self):
        n = self._sfx_sel()
        if not n: return
        ruta = filedialog.asksaveasfilename(defaultextension='.afx', initialfile=n + '.afx', filetypes=[('AYFX', '*.afx')])
        if ruta:
            with open(ruta, 'wb') as fh: fh.write(sonido.escribir_afx(sonido.efecto(n, self._propios())))

    def _sfx_borrar(self):
        n = self._sfx_sel()
        if not n: return
        del self._propios()[n]
        ef = self.proyecto['partida'].get('efectos', {})
        for k, v in list(ef.items()):
            if v == n: ef[k] = None
        self.marcar_cambio('efectos'); self._refrescar_sonido()

    def _sfx_cambiado(self, clave):
        nombre = self.v_sfx[clave].get()
        self.proyecto['partida'].setdefault('efectos', {})[clave] = None if nombre == '(ninguno)' else nombre
        self.marcar_cambio('efectos'); self._refrescar_sonido()

    def _sfx_escuchar(self, clave):
        nombre = self.v_sfx[clave].get()
        if sonido.existe(nombre, self._propios()) and not sonido.escuchar(nombre, self._propios()):
            self.estado.set('No se encontró cómo reproducir sonido en este ordenador.')

    def _sfx_defecto(self):
        self.proyecto['partida']['efectos'] = dict(sonido.POR_DEFECTO)
        self.marcar_cambio('efectos'); self._refrescar_sonido()

    # ---------- pestaña Partida ----------
    def _pestana_partida(self):
        f = ttk.Frame(self.pestanas, padding=12); self.pestanas.add(f, text='Partida')
        self.vp = {}
        def var(clave, tipo=tk.IntVar):
            v = tipo(); self.vp[clave] = v; return v
        izq = ttk.Frame(f); izq.grid(row=0, column=0, sticky='nw')
        der = ttk.Frame(f); der.grid(row=0, column=1, sticky='nw', padx=16)
        v = ttk.LabelFrame(izq, text='Vidas y energía', padding=8); v.pack(fill='x')
        ttk.Label(v, text='Vidas').grid(row=0, column=0, sticky='w')
        ttk.Spinbox(v, from_=1, to=9, textvariable=var('vidas'), width=4).grid(row=0, column=1, padx=4)
        ttk.Label(v, text='Energía por vida (golpes)').grid(row=0, column=2, sticky='w', padx=(12, 0))
        ttk.Spinbox(v, from_=1, to=8, textvariable=var('energia'), width=4).grid(row=0, column=3, padx=4)
        ttk.Checkbutton(v, text='Empezar con Kempston (se cambia con la tecla 3 del menú)',
                        variable=var('kempston', tk.BooleanVar)).grid(row=1, column=0, columnspan=4, sticky='w', pady=(6, 0))
        ttk.Label(v, style='Ayuda.TLabel', wraplength=430, justify='left', text=(
            'Cada golpe quita una unidad de energía; sin energía se pierde una vida y el jugador reaparece '
            'en el mismo sitio, invulnerable 2 segundos. Con energía 1, cada golpe es una vida.')).grid(
            row=2, column=0, columnspan=4, sticky='w', pady=(6, 0))
        av = ttk.LabelFrame(izq, text='A la vez en pantalla', padding=8); av.pack(fill='x', pady=(8, 0))
        self.sp_vez = {}
        for c, (clave, texto) in enumerate((('enemigos', 'Enemigos'), ('balas_j', 'Balas tuyas'),
                                             ('balas_e', 'Balas enemigas'))):
            ttk.Label(av, text=texto).grid(row=0, column=2 * c, sticky='w', padx=(0 if not c else 12, 0))
            sp = ttk.Spinbox(av, from_=1, to=juego.MAX_A_LA_VEZ[clave], textvariable=var(f'v_{clave}'), width=4)
            sp.grid(row=0, column=2 * c + 1, padx=4); self.sp_vez[clave] = sp
        self.l_vez = ttk.Label(av, style='Ayuda.TLabel', wraplength=430, justify='left')
        self.l_vez.grid(row=1, column=0, columnspan=6, sticky='w', pady=(6, 0))
        m = ttk.LabelFrame(izq, text='Marcador (se escribe sobre el marco, fuera del área de juego)', padding=8)
        m.pack(fill='x', pady=8)
        for c, t in enumerate(('Ver', 'Elemento', 'Etiqueta', 'Fila', 'Col.', 'Tinta', 'Brillo')):
            ttk.Label(m, text=t).grid(row=0, column=c, sticky='w', padx=2)
        nombres = {'puntos': 'Puntos', 'record': 'Récord', 'vidas': 'Vidas', 'energia': 'Energía', 'fase': 'Fase'}
        for r, clave in enumerate(juego.HUD, start=1):
            ttk.Checkbutton(m, variable=var(f'h_{clave}_activo', tk.BooleanVar)).grid(row=r, column=0)
            ttk.Label(m, text=nombres[clave]).grid(row=r, column=1, sticky='w')
            ttk.Entry(m, textvariable=var(f'h_{clave}_etiqueta', tk.StringVar), width=10).grid(row=r, column=2, padx=2)
            ttk.Spinbox(m, from_=0, to=23, textvariable=var(f'h_{clave}_fila'), width=4).grid(row=r, column=3)
            ttk.Spinbox(m, from_=0, to=31, textvariable=var(f'h_{clave}_col'), width=4).grid(row=r, column=4)
            ttk.Combobox(m, values=COLORES, textvariable=var(f'h_{clave}_tinta', tk.StringVar), state='readonly',
                         width=10).grid(row=r, column=5, padx=2)
            ttk.Checkbutton(m, variable=var(f'h_{clave}_brillo', tk.BooleanVar)).grid(row=r, column=6)
        ttk.Label(m, style='Ayuda.TLabel', wraplength=430, justify='left', text=(
            'El valor se escribe justo después de la etiqueta (máx. 8 letras). Puntos y récord ocupan 6 cifras, '
            'vidas 1, fase 2 y la barra de energía un carácter por unidad.')).grid(row=6, column=0, columnspan=7, sticky='w', pady=(6, 0))
        c = ttk.LabelFrame(der, text='Línea de controles del menú (tecla 3)', padding=8); c.pack(fill='x')
        ttk.Label(c, text='Texto con teclado').grid(row=0, column=0, sticky='w')
        ttk.Entry(c, textvariable=var('c_teclado', tk.StringVar), width=24).grid(row=0, column=1, columnspan=3, sticky='w')
        ttk.Label(c, text='Texto con Kempston').grid(row=1, column=0, sticky='w')
        ttk.Entry(c, textvariable=var('c_kempston', tk.StringVar), width=24).grid(row=1, column=1, columnspan=3, sticky='w')
        ttk.Label(c, text='Fila / columna').grid(row=2, column=0, sticky='w')
        ttk.Spinbox(c, from_=0, to=23, textvariable=var('c_fila'), width=4).grid(row=2, column=1, sticky='w')
        ttk.Spinbox(c, from_=0, to=31, textvariable=var('c_col'), width=4).grid(row=2, column=2, sticky='w')
        ttk.Label(c, text='Tinta / brillo').grid(row=3, column=0, sticky='w')
        ttk.Combobox(c, values=COLORES, textvariable=var('c_tinta', tk.StringVar), state='readonly', width=10).grid(row=3, column=1, columnspan=2, sticky='w')
        ttk.Checkbutton(c, variable=var('c_brillo', tk.BooleanVar)).grid(row=3, column=3, sticky='w')
        ms = ttk.LabelFrame(der, text='Mensajes (máx. 20 letras, centrados)', padding=8)
        ms.pack(fill='x', pady=8)
        for r, (clave, texto) in enumerate((('fase', 'Inicio de fase (+ número)'), ('game_over', 'Sin vidas'),
                                            ('final', 'Juego terminado'))):
            ttk.Label(ms, text=texto).grid(row=r, column=0, sticky='w')
            ttk.Entry(ms, textvariable=var(f'm_{clave}', tk.StringVar), width=22).grid(row=r, column=1, columnspan=2, sticky='w')
        ttk.Label(ms, text='Tinta / brillo').grid(row=3, column=0, sticky='w')
        ttk.Combobox(ms, values=COLORES, textvariable=var('m_tinta', tk.StringVar), state='readonly', width=10).grid(row=3, column=1, sticky='w')
        ttk.Checkbutton(ms, variable=var('m_brillo', tk.BooleanVar)).grid(row=3, column=2, sticky='w')
        fu = ttk.LabelFrame(der, text='Fuente', padding=8); fu.pack(fill='x')
        b = ttk.Frame(fu); b.pack(anchor='w')
        ttk.Button(b, text='Importar…', command=self._importar_fuente).pack(side='left')
        ttk.Button(b, text='Usar la de la ROM', command=self._quitar_fuente).pack(side='left', padx=4)
        self.l_fuente = ttk.Label(fu, text=''); self.l_fuente.pack(anchor='w', pady=4)
        self.c_fuente = tk.Canvas(fu, width=256 * 2 // 2 * 1, height=48, bg='black', highlightthickness=0)
        self.c_fuente.pack(anchor='w')
        ttk.Label(fu, style='Ayuda.TLabel', wraplength=360, justify='left', text=(
            'Archivo de 768 bytes (.ch8, .fnt, .bin: caracteres 32 a 127) o imagen con los 96 caracteres en '
            'una rejilla de 8×8 (32×3 o 16×6). El carácter 127 se usa como bloque de la barra de energía.')).pack(anchor='w')
        for v_ in self.vp.values():
            v_.trace_add('write', lambda *a: self._leer_partida(marcar=True))

    def _refrescar_partida(self):
        pa = self.proyecto['partida']
        self._cargando = True
        self.vp['vidas'].set(pa['vidas']); self.vp['energia'].set(pa['energia']); self.vp['kempston'].set(pa['kempston'])
        vez = dict(juego.A_LA_VEZ); vez.update(pa.get('a_la_vez') or {})
        for k in juego.A_LA_VEZ: self.vp[f'v_{k}'].set(vez[k])
        for clave in juego.HUD:
            h = pa['marcador'][clave]
            for k in ('activo', 'etiqueta', 'fila', 'col', 'brillo'):
                self.vp[f'h_{clave}_{k}'].set(h[k])
            self.vp[f'h_{clave}_tinta'].set(COLORES[h['tinta']])
        ct = pa['controles']
        for k in ('teclado', 'kempston', 'fila', 'col', 'brillo'): self.vp[f'c_{k}'].set(ct[k])
        self.vp['c_tinta'].set(COLORES[ct['tinta']])
        ms = pa['mensajes']
        for k in ('fase', 'game_over', 'final', 'brillo'): self.vp[f'm_{k}'].set(ms[k])
        self.vp['m_tinta'].set(COLORES[ms['tinta']])
        self._cargando = False
        self._dibujar_fuente()
        self._mostrar_musica()
        self._mostrar_a_la_vez()

    def _mostrar_a_la_vez(self):
        """Máximo de personajes y balas a la vez con los tamaños actuales, y fps estimados."""
        if not hasattr(self, 'l_vez'): return
        p = self.proyecto
        try:
            lim = juego.limites_a_la_vez(p)
            fps, usado, disp = juego.estimacion_fps(p)
        except Exception as ex:
            self.l_vez.configure(text=f'(no se pudo calcular: {ex})'); return
        m, u = lim['max'], lim['usar']
        for k, sp in self.sp_vez.items(): sp.configure(to=m[k])
        recorte = [k for k in u if u[k] < max(1, int((p['partida'].get('a_la_vez') or {}).get(k, u[k])))]
        txt = (f'Con los tamaños actuales el motor admite hasta {m["enemigos"]} enemigos, {m["balas_j"]} balas '
               f'tuyas y {m["balas_e"]} enemigas a la vez (límite: {lim["motivo"]}). '
               f'Con {u["enemigos"]}/{u["balas_j"]}/{u["balas_e"]}: unos {fps:g} fps con todo en pantalla. '
               'Más a la vez = más lento cuando se juntan muchos; los sprites pequeños dejan meter más.')
        if recorte: txt += ' ⚠ Se ha recortado al máximo: ' + ', '.join(recorte) + '.'
        self.l_vez.configure(text=txt, style='Aviso.TLabel' if recorte else 'Ayuda.TLabel')

    def _leer_partida(self, marcar=False):
        if getattr(self, '_cargando', False) or not hasattr(self, 'vp'): return
        pa = self.proyecto['partida']
        def g(k, defecto):
            try: return self.vp[k].get()
            except (tk.TclError, ValueError): return defecto
        pa['vidas'] = g('vidas', pa['vidas']); pa['energia'] = g('energia', pa['energia'])
        pa['kempston'] = bool(g('kempston', pa['kempston']))
        vez = pa.setdefault('a_la_vez', dict(juego.A_LA_VEZ))
        antes = dict(vez)
        for k in juego.A_LA_VEZ:
            try: vez[k] = max(1, min(juego.MAX_A_LA_VEZ[k], int(g(f'v_{k}', vez.get(k, juego.A_LA_VEZ[k])))))
            except (TypeError, ValueError): pass
        for clave in juego.HUD:
            h = pa['marcador'][clave]
            h['activo'] = bool(g(f'h_{clave}_activo', h['activo'])); h['etiqueta'] = g(f'h_{clave}_etiqueta', h['etiqueta'])
            h['fila'] = g(f'h_{clave}_fila', h['fila']); h['col'] = g(f'h_{clave}_col', h['col'])
            h['tinta'] = int(g(f'h_{clave}_tinta', COLORES[h['tinta']])[0]); h['brillo'] = int(bool(g(f'h_{clave}_brillo', h['brillo'])))
        ct = pa['controles']
        for k in ('teclado', 'kempston'): ct[k] = g(f'c_{k}', ct[k])
        ct['fila'] = g('c_fila', ct['fila']); ct['col'] = g('c_col', ct['col'])
        ct['tinta'] = int(g('c_tinta', COLORES[ct['tinta']])[0]); ct['brillo'] = int(bool(g('c_brillo', ct['brillo'])))
        ms = pa['mensajes']
        for k in ('fase', 'game_over', 'final'): ms[k] = g(f'm_{k}', ms[k])
        ms['tinta'] = int(g('m_tinta', COLORES[ms['tinta']])[0]); ms['brillo'] = int(bool(g('m_brillo', ms['brillo'])))
        if marcar:
            self.marcar_cambio('partida')
            if vez != antes: self.after_idle(self._mostrar_a_la_vez)

    def _cargar_musica(self, clave):
        ruta = filedialog.askopenfilename(filetypes=[('Módulos PT3', '*.pt3'), ('Todos', '*.*')])
        if not ruta: return
        try:
            self.proyecto['partida']['musica'][clave] = juego.cargar_pt3(ruta)
            self.marcar_cambio('música'); self._mostrar_musica()
        except Exception as e:
            messagebox.showerror('Música', f'No se pudo cargar el módulo:\n{e}')

    def _quitar_musica(self, clave):
        self.proyecto['partida']['musica'][clave] = None; self.marcar_cambio('música'); self._mostrar_musica()

    def _mostrar_musica(self):
        mus = self.proyecto['partida']['musica']
        for clave, etiqueta in self.l_musica.items():
            m = mus.get(clave)
            if m:
                formato, titulo, autor = juego.info_pt3(m)
                txt = f'«{titulo or "sin título"}» · {len(m)} bytes'
            else:
                txt = '(sin música)'
            etiqueta.configure(text=txt[:48])
        libre = 16384 - len(juego.PT3PLAYER) - sum(len(m) for m in mus.values() if m)
        self.l_musica_total.configure(text=(
            f'Reproductor de Sergey Bulba (Vortex Tracker II) y módulos en el banco 6: quedan {libre} bytes. '
            'La melodía de fases sigue sonando al pasar de una fase a otra. Si solo hay melodía de fases, '
            'el menú queda en silencio, y al revés.'))

    def _importar_fuente(self):
        ruta = filedialog.askopenfilename(filetypes=[('Fuentes', '*.ch8 *.fnt *.bin *.png *.gif *.bmp'), ('Todos', '*.*')])
        if not ruta: return
        try:
            self.proyecto['partida']['fuente'] = pantalla.cargar_fuente(ruta)
            self.marcar_cambio('fuente'); self._dibujar_fuente()
        except Exception as e:
            messagebox.showerror('Fuente', f'No se pudo importar la fuente:\n{e}')

    def _quitar_fuente(self):
        self.proyecto['partida']['fuente'] = None; self.marcar_cambio('fuente'); self._dibujar_fuente()

    def _dibujar_fuente(self):
        c = self.c_fuente; c.delete('all')
        fuente = self.proyecto['partida'].get('fuente')
        if not fuente:
            self.l_fuente.configure(text='Se usa la fuente de la ROM del Spectrum.')
            c.configure(height=1); return
        self.l_fuente.configure(text='Fuente propia (caracteres 32 a 127):')
        img = pantalla.imagen_fuente(fuente)
        self._foto_fuente = ImageTk.PhotoImage(img.resize((img.width * 2, img.height * 2)))
        c.configure(width=img.width * 2, height=img.height * 2)
        c.create_image(0, 0, image=self._foto_fuente, anchor='nw')

    # ---------- general ----------
    def refrescar(self):
        self.v_nombre.set(self.proyecto.get('nombre', ''))
        self.v_acol.set(self.proyecto['area']['col']); self.v_afila.set(self.proyecto['area']['fila'])
        for k in self.lienzos: self.dibujar_pantalla(k)
        self.refrescar_textos()
        self._refrescar_scroll()
        self._refrescar_partida()
        self._refrescar_sonido()
        self.l_titulo.configure(text=self.proyecto.get('nombre', '') or 'JUEGO')
        self.v_optim.set(self.proyecto.get('optimizar', True))
        for ed in (self.ed_tiles, self.ed_mapa, self.ed_sprites, self.ed_estrategia):
            ed.refrescar()
        self._memoria()

    def _cambio_pestana(self, _):
        actual = self.pestanas.nametowidget(self.pestanas.select())
        if actual in (self.ed_tiles, self.ed_mapa, self.ed_sprites, self.ed_estrategia):
            actual.refrescar()
        else:
            if self.pestanas.index('current') == 0: self._memoria()
            if self.pestanas.tab('current', 'text') == 'Partida': self._mostrar_a_la_vez()
            self._dibujar_esquema()

    def marcar_cambio(self, que):
        self.estado.set(f'Modificado ({que})')

    def recoger(self):
        self.proyecto['nombre'] = self.v_nombre.get().strip()[:10] or 'JUEGO'
        try:
            self.proyecto['area'] = {'col': int(self.v_acol.get()), 'fila': int(self.v_afila.get())}
        except (tk.TclError, ValueError):
            pass
        self._scroll_cambiado(marcar=False)
        self._leer_partida()
        if hasattr(self.ed_sprites, '_vars'):
            self.ed_sprites._guardar_vars()
        if getattr(self.ed_sprites, '_anim', None) and self.ed_sprites.sel == 0:
            self.ed_sprites._guardar_anim()

    def comprobar(self):
        self.recoger()
        errores = juego.comprobar(self.proyecto)
        if errores:
            messagebox.showwarning('Comprobar', 'Hay que corregir:\n\n• ' + '\n• '.join(errores))
        else:
            try:
                datos = juego.generar_tap(self.proyecto)
                _, inf = juego.mapa_memoria(self.proyecto)
                extra = ''
                if inf and any(inf.values()):
                    extra = (f'\n\nSe quedan fuera porque no se usan: {len(inf["tiles"])} tiles, '
                             f'{len(inf["enemigos"])} tipos de enemigo, {len(inf["fotogramas"])} fotogramas del jugador'
                             + (' y el dibujo de ' + ' y '.join('las balas del ' + x for x in inf['balas']) if inf['balas'] else '') + '.')
                messagebox.showinfo('Comprobar', f'Todo correcto. La cinta ocupará {len(datos)} bytes.' + extra)
            except Exception as e:
                messagebox.showwarning('Comprobar', str(e))

    def _montar(self):
        self.recoger()
        errores = juego.comprobar(self.proyecto)
        if errores:
            messagebox.showerror('Hay que corregir', '\n'.join(errores)); return None
        return juego.generar_tap(self.proyecto)

    def generar(self):
        try:
            datos = self._montar()
            if datos is None: return
            ruta = filedialog.asksaveasfilename(defaultextension='.tap', filetypes=[('Cinta', '*.tap')],
                                                initialfile=self.proyecto['nombre'] + '.tap')
            if not ruta: return
            with open(ruta, 'wb') as f: f.write(datos)
            self.estado.set(f'Generado {os.path.basename(ruta)} ({len(datos)} bytes)')
            messagebox.showinfo('Listo', f'Cinta generada:\n{ruta}\n\nCárgala en un emulador en modo 128K '
                                         '(opción «Tape Loader» del menú).')
        except Exception as e:
            traceback.print_exc(); messagebox.showerror('Error', str(e))

    def probar(self):
        orden = self.v_emu.get().strip()
        if not orden:
            messagebox.showinfo('Probar', 'Indica primero el emulador en la pestaña General.')
            self.pestanas.select(0); return
        cfg = self._config(); cfg['emulador'] = orden
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f: json.dump(cfg, f)
        except OSError:
            pass
        try:
            datos = self._montar()
            if datos is None: return
            ruta = os.path.join(tempfile.gettempdir(), 'zxgen_prueba.tap')
            with open(ruta, 'wb') as f: f.write(datos)
            if '{tap}' not in orden: orden += ' {tap}'
            partes = [p.replace('{tap}', ruta) for p in shlex.split(orden, posix=(os.name != 'nt'))]
            partes = [p.strip('"') for p in partes]
            subprocess.Popen(partes)
            self.estado.set('Emulador lanzado')
        except Exception as e:
            traceback.print_exc(); messagebox.showerror('Error', f'No se pudo lanzar el emulador:\n{e}')

if __name__ == '__main__':
    Aplicacion().mainloop()
