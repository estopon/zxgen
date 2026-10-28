# Modo mezcla (estilo Super Mario Bros 128K)

## Qué hace output.tap (Super Mario Bros, CAFe 2019)

Lo he ejecutado en un Spectrum 128K emulado y he desmontado su código. Así presenta la imagen:

1. **Doble pantalla a 50 fps.** Dibuja cada fotograma en la pantalla oculta (banco 5 o 7) y las
   intercambia en todas las interrupciones.
2. **Tonos intermedios con las dos pantallas.** Las dos pantallas tienen los mismos atributos, pero
   los tiles usan patrones de píxeles distintos (damero en una y damero inverso en la otra). Al
   alternarlas a 50 Hz el ojo mezcla tinta y papel: así salen el «marrón» de los ladrillos y el rojo
   oscuro del suelo. Con la imagen quieta, las dos pantallas se diferencian en unos 700 bytes de
   píxeles y en ningún atributo.
3. **Cielo negro que no se dibuja**, con scroll horizontal fino. Tu motor de bloques ya lo hacía.
4. **Personajes con color propio.** Los enemigos pintan de su tinta las casillas de atributo que
   ocupan (el goomba sale en cian sobre el cielo negro).
5. Los datos van comprimidos con dzx7 y **la música no es PT3**. Son volcados de los registros
   del AY, comprimidos, que toca un reproductor propio. Al analizarlos he visto que todas las
   alturas coinciden al 100 % con una tabla de tonos de PT3: las melodías se compusieron en un
   tracker y luego se convirtieron.

## Lo que añade al generador

- **Pestaña Scroll → «Estilo Super Mario Bros 128K»** (solo con scroll horizontal o de
  plataformas con paso 1, 2 o 4):
  - *Modo mezcla*: el juego va siempre a 50 fps alternando las pantallas, y los tiles pueden
    tener un tercer tono.
  - *Color propio de los personajes*: cada personaje pinta su tinta (y brillo) en las casillas que
    ocupa y conserva el papel del fondo. El color se elige en la pestaña **Personajes**.
- **Pestaña Tiles**: nueva herramienta **Mezcla (tono medio)**. También se pinta con el botón
  central del ratón. La vista previa ya muestra el color mezclado. Fuera del modo mezcla esos
  píxeles se ven como un damero fijo.
- **Archivo → Ejemplo: modo mezcla (estilo SMB)**: «MEZCLA ZX», un juego de plataformas con
  suelo rojo oscuro, bloques naranja y enemigos de colores (el gráfico es propio, no de Nintendo).
- Mejora general del scroll fino: si media columna de un tile no tiene píxeles y comparte papel con
  su vecina, toma el color de esa vecina. Así no aparece la franja blanca en los bordes del suelo.

### Límites

- En el modo mezcla los bloques ocupan el doble (versión A para la pantalla 5 y B para la 7):
  caben la mitad de combinaciones de columnas vecinas.
- Si un fotograma no termina en una interrupción, la misma pantalla se ve dos veces y se nota un
  parpadeo. La pestaña Scroll avisa cuando el escenario es pesado. En el ejemplo se llega a 50 fps
  en unos 7 de cada 10 fotogramas mientras corre. Ayuda dejar mucho cielo vacío, como en el SMB.

## Motor (asm/motor.asm)

- `render_bloques`: en la pantalla 7 suma `C_MEZCLA` páginas a la dirección de cada bloque
  (versión B). Funciona con bloques de datos y con bloques compilados.
- `rest_atr` / `parchea`: cuando una casilla sucia se redibuja, recupera su color. Las llamadas se
  ponen o se quitan al empezar la fase, así que sin color propio el coste es casi nulo.
- `pintar_atrs` / `pintar_atr`: pinta los colores de los personajes después de dibujarlos.
- Ficha nueva `S_COLOR` en cada sprite (SLOT pasa de 26 a 27), `G_COLORJ` (0xC3B4) y la ficha del
  enemigo usa el byte 11. CONF_LEN pasa a 246: `C_MEZCLA` en conf+243 y `C_COLSPR` en conf+244.
- El motor termina en 0xBDEC: quedan 20 bytes antes de la tabla IM2.

**construir_motor_pyz80.py** reensambla el motor sin pasmo (`pip install pyz80`). Adapta antes el
fuente (rept/endm, equ, caracteres entre comillas). Lo he comprobado con el motor.asm original y
da un binario idéntico byte a byte al motor_bin.py que tenías. Si prefieres pasmo,
construir_motor.py sigue funcionando.

## Música (herramientas/)

- `extraer_musica_smb.py juego.tap`: descomprime el juego, ejecuta su reproductor en un Z80
  emulado, graba los registros del AY de cada melodía y los convierte a PT3 con `ay2pt3.py`.
  Después comprueba cada PT3 tocándolo con el reproductor de Bulba del generador. Necesita
  `pip install z80`.
- Las 5 melodías salen **idénticas, fotograma a fotograma y durante tres vueltas**, y ocupan entre
  2,1 y 5,2 KB. Se cargan en la pestaña Partida → Música. En el banco 6 caben unos 14 KB.
- Las melodías de Super Mario Bros son de Nintendo: úsalas para estudiar o en juegos que no
  distribuyas.

## TERRA ZX (ejemplo_terra.py)

TERRA ZX es un juego de plataformas con la estructura de un juego de este tipo para 128K, pero
con gráficos, personajes y fases propios. Tiene 8 fases de 132 columnas (unas 11 pantallas cada
una), que es lo más largo que cabe en memoria con las novedades de LEEME_NOVEDADES.md.

- **Fases:** se generan con una semilla fija por fase y son cada vez más difíciles. Tienen suelo
  con huecos, filas de ladrillos y bloques sorpresa que se rompen de un cabezazo, gemas,
  escalinatas, torres, pasarelas sobre fosos, pinchos y un muro al final.
- **Personajes:**
  - Jugadora: una exploradora con casco y capa. Salta con Q y aplasta a los enemigos cayéndoles
    encima.
  - Enemigos:
    - caracol y escarabajo, que patrullan;
    - abeja, que rebota;
    - murciélago, que persigue;
    - gólem, un guardián de tres golpes antes del final.
  - Cada personaje tiene su propio color.
- **Para abrirlo:**
  - En el generador: Archivo → Ejemplo: TERRA ZX.
  - Como proyecto ya guardado: `terra_zx.json`.
  - Para regenerar el JSON y el .tap: `python ejemplo_terra.py`.

### Para que vaya a 50 fps

Medido en el emulador, TERRA ZX llega a 50 fps en el 91 % de los fotogramas mientras corre. Lo
que hace falta para conseguirlo:

- **Suelo y tierra solo de color**, sin píxeles. Ahora el motor no dibuja las casillas cuyo par de
  tiles no tiene píxeles: solo pone su color.
- **Pocos tiles distintos**, con dibujos que se repiten cada 8 píxeles. Así hay pocas
  combinaciones de columnas vecinas (39 de las 52 que caben en modo mezcla).
- **La jugadora con pocos fotogramas** (6), para que quepa compilada en el banco 7.

## Mejoras de velocidad del motor (sirven en cualquier juego con scroll fino)

- Los pares de tiles sin píxeles no se dibujan ni cuentan como contenido. Las filas que solo
  tienen pares de este tipo se saltan enteras.
- El color de una columna ya no cambia a mitad de camino cuando ningún par lo necesita.
- Al repintar los colores se saltan las filas vacías que ya tenían el color del cielo, y el bucle
  de repintado es un 25 % más rápido.
- Una casilla solo recupera su color si la había pintado un personaje.
- Tres zonas de variables (`cabnivel`, `buf_msg` y `golpe_z`) pasan al hueco libre que hay tras la
  tabla IM2 (0xBF01). El motor acaba en 0xBDF8.
