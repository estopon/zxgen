"""Aspecto común de la interfaz: tema ttk, tipos de letra, colores y algunos controles reutilizables."""
import sys
import tkinter as tk
from tkinter import ttk, font as tkfont

FONDO = '#eef0f4'        # fondo de las ventanas
PANEL = '#ffffff'        # cajas de texto y listas
BORDE = '#c5cad3'
TEXTO = '#1f2430'
SUAVE = '#6b7280'        # textos de ayuda
ACENTO = '#2f6fdd'       # botón principal y selección
ACENTO_OSCURO = '#2459b3'
AVISO = '#b45309'
COLORES = ['0 Negro', '1 Azul', '2 Rojo', '3 Magenta', '4 Verde', '5 Cian', '6 Amarillo', '7 Blanco']


def familia():
    disponibles = set(tkfont.families())
    for f in ('Segoe UI', 'Helvetica Neue', 'Ubuntu', 'Cantarell', 'DejaVu Sans', 'Arial'):
        if f in disponibles: return f
    return 'TkDefaultFont'


def aplicar(raiz):
    """Tema claro y uniforme para toda la aplicación."""
    fam = familia()
    tam = 10 if sys.platform.startswith('win') else 10
    for nombre in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
        try: tkfont.nametofont(nombre).configure(family=fam, size=tam)
        except tk.TclError: pass
    raiz.configure(bg=FONDO)
    raiz.option_add('*Listbox.background', PANEL)
    raiz.option_add('*Listbox.selectBackground', ACENTO)
    raiz.option_add('*Listbox.selectForeground', 'white')
    raiz.option_add('*Listbox.relief', 'flat')
    raiz.option_add('*Listbox.highlightThickness', 1)
    raiz.option_add('*Listbox.highlightColor', ACENTO)
    raiz.option_add('*Listbox.highlightBackground', BORDE)
    raiz.option_add('*Menu.font', (fam, tam))
    s = ttk.Style(raiz)
    try: s.theme_use('clam')
    except tk.TclError: pass
    s.configure('.', background=FONDO, foreground=TEXTO, font=(fam, tam), bordercolor=BORDE,
                lightcolor=FONDO, darkcolor=BORDE, troughcolor='#dde1e8', focuscolor=ACENTO)
    s.configure('TFrame', background=FONDO)
    s.configure('Panel.TFrame', background=PANEL)
    s.configure('Barra.TFrame', background='#e2e6ee')
    s.configure('TLabel', background=FONDO)
    s.configure('Barra.TLabel', background='#e2e6ee', foreground=SUAVE)
    s.configure('Ayuda.TLabel', foreground=SUAVE)
    s.configure('Aviso.TLabel', foreground=AVISO)
    s.configure('Titulo.TLabel', font=(fam, tam + 3, 'bold'))
    s.configure('Seccion.TLabel', font=(fam, tam, 'bold'))
    s.configure('Estado.TLabel', background='#e2e6ee', foreground=TEXTO, padding=(8, 3))
    s.configure('TLabelframe', background=FONDO, bordercolor=BORDE, relief='solid', borderwidth=1)
    s.configure('TLabelframe.Label', background=FONDO, foreground=ACENTO_OSCURO, font=(fam, tam, 'bold'))
    s.configure('TButton', padding=(10, 4), background='#f8f9fb')
    s.map('TButton', background=[('pressed', '#d6dbe4'), ('active', '#ffffff')])
    s.configure('Accent.TButton', background=ACENTO, foreground='white', font=(fam, tam, 'bold'),
                bordercolor=ACENTO_OSCURO, lightcolor=ACENTO, darkcolor=ACENTO_OSCURO)
    s.map('Accent.TButton', background=[('pressed', ACENTO_OSCURO), ('active', '#3d7cf0')],
          foreground=[('disabled', '#dddddd')])
    s.configure('Herr.TButton', padding=(8, 3), background='#e2e6ee', bordercolor='#e2e6ee')
    s.map('Herr.TButton', background=[('active', '#ffffff')])
    s.configure('Pequeno.TButton', padding=(4, 1))
    s.configure('TNotebook', background=FONDO, bordercolor=BORDE, tabmargins=(6, 6, 6, 0))
    s.configure('TNotebook.Tab', padding=(14, 6), background='#dfe3ea', foreground=SUAVE, bordercolor=BORDE)
    s.map('TNotebook.Tab', background=[('selected', FONDO), ('active', '#eef1f6')],
          foreground=[('selected', TEXTO)], expand=[('selected', (1, 2, 1, 0))])
    s.configure('Sub.TNotebook.Tab', padding=(10, 3))
    s.configure('TEntry', fieldbackground=PANEL, padding=3)
    s.configure('TSpinbox', fieldbackground=PANEL, padding=2, arrowsize=12)
    s.configure('TCombobox', fieldbackground=PANEL, padding=2, arrowsize=12)
    s.map('TCombobox', fieldbackground=[('readonly', PANEL)], selectbackground=[('readonly', PANEL)],
          selectforeground=[('readonly', TEXTO)])
    s.configure('TCheckbutton', background=FONDO)
    s.configure('TRadiobutton', background=FONDO)
    s.configure('Treeview', background=PANEL, fieldbackground=PANEL, rowheight=24, bordercolor=BORDE)
    s.map('Treeview', background=[('selected', ACENTO)], foreground=[('selected', 'white')])
    s.configure('Treeview.Heading', font=(fam, tam, 'bold'), background='#e2e6ee')
    return fam


def ayuda(padre, texto, ancho=420, **grid):
    """Texto de ayuda en gris."""
    return ttk.Label(padre, text=texto, style='Ayuda.TLabel', wraplength=ancho, justify='left')


class CampoMensaje(ttk.Frame):
    """Mensaje de una o dos líneas (máx. 20 letras cada una). Se guarda como «LINEA 1|LINEA 2»."""
    def __init__(self, padre, al_cambiar=None, ancho=22):
        super().__init__(padre)
        self._al_cambiar = al_cambiar
        self._cargando = False
        self.v1, self.v2 = tk.StringVar(), tk.StringVar()
        self.l1 = ttk.Label(self, text='', style='Ayuda.TLabel', width=5)
        self.l2 = ttk.Label(self, text='', style='Ayuda.TLabel', width=5)
        ttk.Entry(self, textvariable=self.v1, width=ancho).grid(row=0, column=0, sticky='w')
        self.l1.grid(row=0, column=1, padx=4)
        ttk.Entry(self, textvariable=self.v2, width=ancho).grid(row=1, column=0, sticky='w', pady=(2, 0))
        self.l2.grid(row=1, column=1, padx=4)
        for v in (self.v1, self.v2): v.trace_add('write', lambda *a: self._cambio())
        self._contar()

    def _contar(self):
        for v, l in ((self.v1, self.l1), (self.v2, self.l2)):
            n = len(v.get())
            l.configure(text=f'{n}/20', style='Aviso.TLabel' if n > 20 else 'Ayuda.TLabel')

    def _cambio(self):
        self._contar()
        if not self._cargando and self._al_cambiar: self._al_cambiar()

    def get(self):
        a = self.v1.get().strip().upper()[:20].replace('|', ' ')
        b = self.v2.get().strip().upper()[:20].replace('|', ' ')
        return f'{a}|{b}' if b else a

    def set(self, texto):
        self._cargando = True
        partes = (texto or '').split('|')
        self.v1.set(partes[0]); self.v2.set(partes[1] if len(partes) > 1 else '')
        self._cargando = False
        self._contar()


class Desplazable(ttk.Frame):
    """Marco con barra de desplazamiento vertical (para paneles que pueden no caber)."""
    def __init__(self, padre, ancho=None, **kw):
        super().__init__(padre, **kw)
        self.lienzo = tk.Canvas(self, highlightthickness=0, bg=FONDO, width=ancho or 300)
        barra = ttk.Scrollbar(self, orient='vertical', command=self.lienzo.yview)
        self.interior = ttk.Frame(self.lienzo)
        self._id = self.lienzo.create_window(0, 0, window=self.interior, anchor='nw')
        self.lienzo.configure(yscrollcommand=barra.set)
        self.lienzo.pack(side='left', fill='both', expand=True)
        barra.pack(side='right', fill='y')
        self.interior.bind('<Configure>', lambda e: self._ajustar())
        self.lienzo.bind('<Configure>', lambda e: self.lienzo.itemconfigure(self._id, width=e.width))
        for w in (self.lienzo, self.interior):
            w.bind('<Enter>', lambda e: self._rueda(True)); w.bind('<Leave>', lambda e: self._rueda(False))

    def _ajustar(self):
        self.lienzo.configure(scrollregion=self.lienzo.bbox('all'))
        if not ancho_fijo(self.lienzo):
            self.lienzo.configure(width=self.interior.winfo_reqwidth())

    def _rueda(self, activar):
        if activar:
            self.lienzo.bind_all('<MouseWheel>', lambda e: self.lienzo.yview_scroll(-1 if e.delta > 0 else 1, 'units'))
            self.lienzo.bind_all('<Button-4>', lambda e: self.lienzo.yview_scroll(-1, 'units'))
            self.lienzo.bind_all('<Button-5>', lambda e: self.lienzo.yview_scroll(1, 'units'))
        else:
            for ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'): self.lienzo.unbind_all(ev)


def ancho_fijo(_lienzo):
    return False


def color_combo(padre, var_tinta, var_brillo, al_cambiar):
    """Tinta (lista de colores) + brillo, en una fila."""
    f = ttk.Frame(padre)
    cb = ttk.Combobox(f, values=COLORES, textvariable=var_tinta, state='readonly', width=10)
    cb.pack(side='left'); cb.bind('<<ComboboxSelected>>', lambda e: al_cambiar())
    ttk.Checkbutton(f, text='brillo', variable=var_brillo, command=al_cambiar).pack(side='left', padx=6)
    return f
