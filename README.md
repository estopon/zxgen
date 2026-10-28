# zxgen — Generador de juegos para ZX Spectrum 128K

Editor de escritorio en Python (Tkinter) para crear juegos de acción para el **ZX Spectrum 128K**
sin escribir código. Diseñas tiles, personajes, mapas, reglas, música y pantallas, y el generador
monta un archivo **`.tap`** listo para cargar en un emulador o en un Spectrum real. El juego corre
sobre un motor propio escrito en **ensamblador Z80**.

## Características

- **Varios tipos de juego**: scroll vertical, horizontal o de plataformas, de 8 en 8 o fino (1, 2
  o 4 píxeles), para matamarcianos, plataformas o beat 'em up.
- **Editores integrados**, en pestañas por orden de trabajo: Proyecto, Tiles, Personajes, Mapa,
  Scroll, Estrategia, Partida, Sonido, Pantallas y Textos.
- **Tiles** de 16×16 con un atributo por cuadro de 8×8 y propiedades (sólido, detiene disparos,
  puntos, vidas, puertas, altares, inventario…).
- **Personajes** de 8×8 a 32×32 (16 tamaños), animaciones por dirección, agacharse, muerte y
  comportamientos: quieto, patrulla, persigue, rebota, cruza y personaje que habla.
- **Armas**: balas configurables (tamaño y velocidad) y láser con patrón, grosor y alcance.
- **Estrategia**: inventario de hasta 8 elementos, puertas entre fases y reglas escritas como
  frases (*CUANDO hable con Sabio · SI LLEVA Amuleto · ENTONCES dar Llave*).
- **Música PT3** (reproductor de Sergey Bulba) y **efectos de sonido** en el canal C del AY que no
  cortan la música. Importa efectos `.afx`/`.afb` (AYFX Editor) y `.wav`.
- **Modo mezcla** (estilo *Super Mario Bros 128K*): doble pantalla a 50 fps para obtener tonos
  intermedios y personajes con color propio.
- **Pantallas** de carga, título y marco convertidas desde PNG al formato del Spectrum.
- **Memoria dinámica**: las fases se reparten por los bancos libres del 128K y la pestaña Proyecto
  muestra el mapa de memoria. *Comprobar* (F7) avisa de lo que no cabe.

## Requisitos

- Python 3 con Tkinter
- [Pillow](https://pypi.org/project/pillow/) para el editor
- Opcionales:
  - [pyz80](https://pypi.org/project/pyz80/) o [pasmo](https://pasmo.speccy.org/) para reensamblar el motor
  - [z80](https://pypi.org/project/z80/) para las herramientas de música
- Un emulador de Spectrum 128K (Fuse, ZEsarUX, Spectaculator…) para probar los juegos

```bash
pip install pillow
```

## Uso

```bash
cd zxgen
python generador.py
```

- **Archivo → Abrir** carga un proyecto `.json` (por ejemplo, los de `ejemplos/`).
- **Archivo → Ejemplos** crea uno de los juegos de ejemplo.
- **Generar .tap** crea la cinta; **Probar en emulador** la abre directamente.
- Las cintas se cargan en el emulador en modo **128K** (*Tape Loader*).

## Ejecutable sin Python

### Descargar

En la página [Releases](https://github.com/estopon/zxgen/releases/latest) hay un ejecutable para
cada sistema que no necesita Python:

| Sistema | Archivo | Cómo abrirlo |
|---|---|---|
| Windows | `zxgen-windows.exe` | Doble clic |
| Linux | `zxgen-linux.tar.gz` | Descomprimir y ejecutar `./zxgen` |
| macOS | `zxgen-macos.zip` | Descomprimir y abrir `zxgen.app` |

Los ejecutables no van firmados, así que el sistema avisa la primera vez que se abren:

- **Windows**: si aparece *Windows protegió su PC*, pulsa **Más información → Ejecutar de todas
  formas**. Si el navegador dice que el archivo *no se descarga habitualmente*, elige
  **Conservar** en el menú de la descarga.
- **macOS**: si dice que no se puede abrir porque no se puede verificar el desarrollador, haz clic
  derecho sobre `zxgen.app` y elige **Abrir**, o permítelo en **Ajustes del Sistema → Privacidad y
  seguridad**.

### Construir

El generador se puede empaquetar con [PyInstaller](https://pyinstaller.org/) en un único
ejecutable que no necesita Python instalado:

```bash
cd zxgen
pip install pyinstaller pillow
python construir_exe.py
```

Deja `zxgen/dist/zxgen.exe` (`zxgen` en Linux, `zxgen.app` en macOS). PyInstaller no compila de forma cruzada:
el ejecutable de cada sistema se construye en ese sistema.

### Publicar una versión

El workflow `.github/workflows/release.yml` construye los ejecutables de Windows, Linux y macOS
y los publica en una release de GitHub al subir una etiqueta `v*`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Las descargas quedan en la página *Releases* del repositorio. También se puede lanzar a mano
desde la pestaña *Actions* para construir los ejecutables sin publicar nada; quedan como
artefactos de la ejecución.

El workflow ya incluye el paso para firmar el ejecutable de Windows con
[SignPath](https://about.signpath.io/), pero solo actúa si el repositorio tiene configurados la
variable `SIGNPATH_ORGANIZATION_ID` y el secreto `SIGNPATH_API_TOKEN`; sin ellos se publica sin
firmar. La configuración del artefacto para SignPath está en `.signpath/configuracion-artefacto.xml`.

## Estructura del repositorio

```
.
├── LEEME.txt                          Guía rápida
├── LICENSE                            Licencia MIT
├── Manual_Generador_ZX_Spectrum.docx  Manual completo
├── ejemplos/                          Proyectos .json de ejemplo
│   ├── musica/                        Módulos .pt3
│   └── pantallas/                     Pantallas de carga y título (.png / .scr)
├── juegos/                            Cintas .tap generadas de cada ejemplo
└── zxgen/                             Generador y motor
    ├── generador.py                   Aplicación principal (ventana y pestañas)
    ├── editor_tiles.py                Editor de tiles
    ├── editor_sprites.py              Editor de personajes y balas
    ├── editor_mapa.py                 Editor de mapas
    ├── editor_estrategia.py           Inventario, reglas, puertas y diálogos
    ├── juego.py                       Montaje del proyecto en un .tap
    ├── graficos.py / pantalla.py      Formatos de tiles, sprites y pantallas
    ├── sonido.py                      Efectos de sonido del AY
    ├── tap.py                         Bloques .tap y cargador BASIC
    ├── estilo.py                      Tema de la interfaz
    ├── arte.py, ejemplo*.py           Generación del contenido de ejemplo
    ├── crear_ejemplos_grandes.py      Regenera los ejemplos grandes (.json y .tap)
    ├── motor_bin.py                   Motor ensamblado (generado, no editar)
    ├── construir_motor_pyz80.py       Reensambla el motor con pyz80
    ├── construir_motor.py             Reensambla el motor con pasmo
    ├── construir_exe.py               Empaqueta el generador en un ejecutable (PyInstaller)
    ├── asm/                           Fuentes Z80: motor, cargador y reproductor PT3
    ├── herramientas/                  Conversor AY → PT3 y extractor de música
    ├── LEEME_NOVEDADES.md             Novedades por versión
    └── LEEME_MODO_MEZCLA.md           Modo mezcla y ejemplo TERRA ZX
```

## Juegos de ejemplo

| Proyecto | Tipo |
|---|---|
| `terra_zx` | Plataformas en modo mezcla: amuleto, sabio que habla y puerta con llave |
| `mezcla_zx` | Demo del modo mezcla |
| `templo_plataformas`, `saltamontes_plataformas`, `patrulla_plataformas` | Plataformas |
| `nebulosa_horizontal`, `patrulla_horizontal`, `estrella_naves` | Scroll horizontal |
| `asalto_vertical`, `comando_vertical`, `patrulla_vertical` | Scroll vertical |
| `punos_beat_em_up` | Beat 'em up |

Sus cintas están en `juegos/`. Para regenerarlas:

```bash
cd zxgen
python crear_ejemplos_grandes.py   # asalto, comando, nebulosa, templo y puños
python ejemplo_terra.py            # TERRA ZX
```

## Motor Z80

El motor (`zxgen/asm/motor.asm`) se carga en `0x8C00` y tiene tres variantes, una por tipo de
scroll (vertical, horizontal de 8 en 8 y fino por bloques); cada juego lleva solo la suya. El
ensamblado ya está incluido en `motor_bin.py`, así que solo hay que reensamblar si se modifica el
código Z80:

```bash
cd zxgen
pip install pyz80
python construir_motor_pyz80.py
```

## Herramientas de música

En `zxgen/herramientas/` (requieren `pip install z80`):

- `ay2pt3.py`: convierte un volcado de registros del AY en un módulo PT3.
- `pt3emu.py`: toca un PT3 con el reproductor del generador en un Z80 emulado.
- `extraer_musica_smb.py juego.tap`: extrae a PT3 las melodías de un `.tap` con música en
  volcados del AY.

## Documentación

- [`LEEME.txt`](LEEME.txt): guía rápida.
- [`Manual_Generador_ZX_Spectrum.docx`](Manual_Generador_ZX_Spectrum.docx): manual completo.
- [`zxgen/LEEME_NOVEDADES.md`](zxgen/LEEME_NOVEDADES.md): animaciones, efectos, puertas,
  personajes que hablan, láser y memoria dinámica.
- [`zxgen/LEEME_MODO_MEZCLA.md`](zxgen/LEEME_MODO_MEZCLA.md): modo mezcla y TERRA ZX.

## Autor

**Manuel Rico**

## Licencias y créditos

- El generador y el motor tienen licencia [MIT](LICENSE).
- El reproductor PT3 es obra de **Sergey Bulba**.
- La música de `ejemplos/musica/` tiene licencia MIT (© 2026 Miguel Ángel Esteve Marco); ver
  [`LICENCIA_spectrumizer.txt`](ejemplos/musica/LICENCIA_spectrumizer.txt).
- Las melodías de *Super Mario Bros* que se pueden extraer con las herramientas son de Nintendo:
  úsalas solo para estudiar o en juegos que no distribuyas. Los gráficos de los ejemplos son
  propios.
