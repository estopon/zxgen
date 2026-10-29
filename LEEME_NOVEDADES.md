# Novedades: animaciones, efectos de sonido, puertas, personajes que hablan e interfaz nueva

## Animaciones

- **Agacharse** (modo plataformas): con la tecla abajo (A), quieto en el suelo. Se elige el
  fotograma en **Personajes → Jugador → Agacharse · morir** (uno para cada lado o el mismo).
  La misma tecla sirve para entrar en las puertas y para hablar con los personajes.
- **Salto en dos partes**: en plataformas, las direcciones *arriba-dcha / arriba-izq* son el
  salto mientras sube, y *abajo-dcha / abajo-izq* la caída. Si la caída está vacía, se usa el
  fotograma del salto.
- **Muerte de la protagonista**: con un fotograma «Al morir», salta hacia arriba y cae fuera de
  la pantalla. Después reaparece como siempre.
- **Muerte de los enemigos**: con un «Fotograma al morir» (pestaña Animación del enemigo), al
  destruirlo se ve ese dibujo un momento (aplastado, boca abajo…) antes de desaparecer. Ese
  fotograma no entra en la animación de andar.

## Efectos de sonido (pestaña Sonido)

- Ocho momentos: salto, golpe a un enemigo, disparo, enemigo destruido, jugador herido o muerto,
  coger un objeto, romper un bloque y puerta o hablar.
- Hay 19 efectos hechos. No son copias de los del .tap de Super Mario, pero siguen su estilo:
  barridos de tono para el salto, ruido para los golpes y arpegios para las monedas. «▶ Escuchar»
  los toca en el ordenador.
- **No cortan la música.** El motor toca el efecto en el canal C del AY después del reproductor
  PT3. Mientras dura el efecto, la melodía sigue en los canales A y B, y luego el canal C vuelve a
  la música. Lo he comprobado en el emulador con una melodía sonando.
- Cada efecto ocupa entre 20 y 90 bytes en el banco 6. Si un efecto se usa en varios momentos,
  se guarda una sola vez.

## Estrategia más fácil y con más elementos

- **Puertas**: tile «Puerta a otra fase» en la pestaña Tiles. Se indican:
  - la fase de destino;
  - la columna por la que se entra;
  - si hace falta llevar algún elemento;
  - el mensaje que sale si está cerrada.
  En plataformas se entra pulsando abajo delante de la puerta. Al entrar por una puerta no sale
  el aviso «FASE nn» y el inventario se conserva.
- **Personajes que hablan**: un enemigo con el comportamiento «personaje» no ataca y no se puede
  destruir. Mira hacia la jugadora, se apoya en el suelo y, al tocarlo (en plataformas, tocarlo y
  pulsar abajo), dice su mensaje. Se escribe en la pestaña **Habla** y puede tener dos líneas.
- **Reglas escritas como frases**, en la pestaña Estrategia:
  > CUANDO *hable con Sabio* · SI LLEVA *Amuleto* · ENTONCES *dar Llave* · Y ADEMÁS *+200
  > puntos* · Y DICE *«TOMA ESTA LLAVE / ABRE LA PUERTA»*
  - Los campos se guardan solos y solo aparecen los que hacen falta.
  - Los resultados nuevos son «Dar un elemento» y «al hablar con un personaje».
- **Resumen del juego** a la derecha de la pestaña Estrategia:
  - dónde está cada objeto, puerta, personaje y altar;
  - avisos como «la Llave se pide pero nada la da».
- **Mensajes de dos líneas** (20 letras cada una) en objetos, puertas, personajes y reglas. Cada
  línea lleva un contador de letras.

## TERRA ZX con todo esto

1. En la Tierra 1-2 hay un **amuleto** en lo alto, al principio.
2. En la 1-3, el **sabio** pide el amuleto y, a cambio, da una **llave**.
3. En la 1-4, la **puerta** sin la llave dice «PUERTA CERRADA / FALTA UNA LLAVE». Con la llave,
   lleva directamente a la Tierra 2-2.

Además:
- la exploradora se agacha y tiene animación de muerte;
- los bichos tienen su fotograma de muerte (aplastados o boca abajo);
- el inventario se ve en el marcador;
- todos los efectos de sonido están puestos.

Para que quepa todo, las fases tienen ahora 132 columnas, y el juego sigue a 50 fps en el 91 % de
los fotogramas.

## Interfaz

- **Sin duplicados**:
  - la barra de menú tiene Archivo (con el submenú Ejemplos) y Ayuda;
  - la barra de herramientas tiene Comprobar, Probar en emulador y Generar .tap.
- **Pestañas en orden de trabajo**: Proyecto, Tiles, Personajes, Mapa, Scroll, Estrategia,
  Partida, Sonido, Pantallas y Textos.
- **Aspecto nuevo**:
  - tema claro uniforme y tipos de letra del sistema;
  - botón principal en azul;
  - títulos de sección y textos de ayuda en gris;
  - la ventana se ajusta a la pantalla (hasta 1280×820).
- **Personajes**: las propiedades van en subpestañas (Movimiento, Animación y Agacharse · morir
  para la jugadora; Conducta, Animación y Habla para los enemigos), así ya no se salen de la
  ventana.
- **Tiles**: las propiedades van en una columna propia y solo se ven los campos de la respuesta
  elegida.
- **Mapa y Scroll**: el panel lateral tiene barra de desplazamiento si no cabe.
- **Comprobar (F7)**: revisa el proyecto y dice cuánto ocupará la cinta sin pedir dónde
  guardarla.

## Motor (asm/motor.asm)

- La configuración pasa a 0x5B00 y la fuente a 0x5D00, en la memoria que dejaba libre el
  cargador. BANKM es ahora una variable propia (0x5C08), porque la de la ROM (0x5B5C) cae dentro
  de la configuración. El motor ocupa de 0x8C00 a 0xBD24: quedan 220 bytes.
- Rutinas nuevas:
  - `sonido` y `sfx_cuadro`: efectos en la interrupción;
  - `morir`: animación de muerte de la jugadora;
  - `puerta` y `hablar`;
  - estado 6 de los enemigos: muriendo.
- Las reglas tienen una clave más: el número de personaje con el que se habla. Si una regla da un
  elemento o puntos, también se ve su mensaje.
- Se reensambla con `python construir_motor_pyz80.py` (pip install pyz80).

# Versión 8: cinta optimizada, memoria dinámica y efectos propios

## Solo lo que se usa
Con «Meter en la cinta solo lo que se usa» (pestaña Proyecto, activado por defecto) no entran en la
cinta los tiles que no aparecen en ningún mapa, los tipos de enemigo que no se colocan, los
fotogramas del jugador que no usa ninguna animación ni los dibujos de balas que nadie dispara.
En scroll horizontal fino tampoco se guardan los dibujos de los tiles con las fases (el motor
dibuja con los bloques), y las propiedades de los tiles ya no se rellenan hasta 256 bytes.

## Memoria dinámica
Las fases van al primer hueco libre de los bancos 0, 6, 3, 4, 1 y 7 (detrás de música, sprites,
pantallas o sprites compilados). La pestaña Proyecto dibuja el mapa de memoria. TERRA ZX pasa de
132 a 171 columnas por fase; asalto, comando y puños vuelven a llevar todos los efectos.

## Efectos propios
Pestaña Sonido → Mis efectos: importar .afx y .afb (AYFX Editor) y .wav (conversión aproximada),
escuchar, exportar a .afx y borrar. Máximo 2 s por efecto; lo ideal, 0,1-0,5 s. Hay 10 efectos
hechos nuevos: Puñetazo, Patada, Golpe fuerte, Grito, Quejido, Risa malvada, Rugido, Ladrido,
Alarma y Teletransporte.

# Versión 9: láser, balas configurables y personajes de 8×8 a 32×32

## Personajes de 16 tamaños
El botón **Tamaño** (Personajes) abre una rejilla 4×4 con todos los tamaños de 8 a 32 píxeles. En
negrita, los más usados: 8×8, 16×16, 16×24, 16×32, 24×24 y 32×32. Cada casilla dice cuántos enemigos
caben a la vez con ese tamaño y los fps estimados, y avisa si el personaje deja de caber entre los
sprites compilados. Debajo del editor hay una línea con la capacidad del motor en cada momento.

## ¿Cuántos a la vez?
Pestaña Partida → **A la vez en pantalla**: enemigos (hasta 10), balas tuyas (hasta 6) y enemigas
(hasta 8). En scroll horizontal fino el máximo es fijo y el tamaño solo cambia la velocidad. En
vertical y horizontal de 8 en 8, cada sprite guarda el fondo que tapa en 1024 bytes, así que el
máximo baja con el tamaño: 10 enemigos de 16×16, 9 de 24×24, 6 de 24×32 y 5 de 32×32.

## Balas
Disparo del jugador y Disparo enemigo: tamaño 8×8, 8×16 o 16×8 y velocidad de 1 a 12 píxeles por
fotograma. Como mínimo van un píxel más rápido que el scroll; si se pone menos, el motor sube la
velocidad a ese mínimo. Las balas rápidas avanzan a saltos, pero el motor comprueba todo el tramo
recorrido, así que no atraviesan a nadie sin dañarlo.

## Láser
Nueva arma «Láser» con subpestaña propia:
- dibujo: continua, discontinua, punteada, estrellas, onda… o un patrón propio de 8 píxeles por línea;
- grosor de 1 a 3 líneas, duración y alcance;
- se detiene en el enemigo al que da (por defecto sí) y en los tiles que paran los disparos (por defecto sí);
- daña «al píxel»: usa la caja de los píxeles dibujados del enemigo;
- sale en horizontal, vertical o diagonal según hacia dónde se camina.

## Correcciones
- Al recibir una bala enemiga, el bucle de colisiones perdía su contador y podía escribir fuera de
  la tabla de sprites. Con sprites grandes dejaba el juego sin enemigos tras perder una vida.
- El aviso de «los sprites no caben en el banco 4» dice ahora cuántos bytes sobran en total.

# Versión 10: pantalla a pantalla y scroll libre en 8 direcciones

## Dos tipos de scroll nuevos (pestaña Scroll)
- **Pantalla a pantalla (sin scroll)**: al llegar a un borde se pasa a la pantalla de al lado.
  - Cenital: por los cuatro bordes.
  - Con gravedad y saltos: hacia arriba saltando por un hueco del techo y hacia abajo cayendo.
  - Al entrar en una pantalla salen sus enemigos; al volver, otra vez.
  - Va a 25 fps. Dibujar la pantalla nueva tarda unas décimas.
  - Usa la variante D del motor.
- **Libre en 8 direcciones**: la cámara sigue al jugador cuando sale del recuadro de márgenes.
  - Se mueve píxel a píxel en vertical y de 2 en 2 en horizontal, como los sprites.
  - El fondo es de dos colores (tinta, papel y brillo en la pestaña Scroll), así que no hay choque de
    atributos.
  - Puede ser cenital o con gravedad y saltos.
  - Va a unos 16,7 fps constantes.
  - Usa la variante C del motor: 4 copias del fondo ya desplazadas, y solo se dibuja lo que entra.

## Mapa en rejilla (pestaña Mapa)
En los dos modos, cada fase es una rejilla de pantallas de 12 x 10 tiles, de 1 x 1 a 16 x 16. No
tiene por qué ser rectangular: las pantallas se pueden quitar.
- Con «Qué se edita: Pantallas», un clic elige pantalla y los botones sirven para quitarla o ponerla,
  empezar aquí, copiar y pegar.
- En el scroll libre, las pantallas quitadas se ven con el tile de relleno: elige uno sólido.
- Al cambiar a estos modos, las fases de un scroll de una dirección se cortan en pantallas sin perder
  nada.

## Ejemplos nuevos
- **CASTILLO** (castillo_zx): plataformas pantalla a pantalla con 9 salas en una rejilla de 4 x 3.
- **SELVA ZX** (selva_zx): acción cenital con scroll libre, rejilla de 4 x 3 con dos pantallas quitadas
  y fondo negro sobre verde.

Se generan con `python ejemplos_2d.py`.

## Motor
- Variantes D y C nuevas. Los bloques «;@ SOLO» se pueden anidar.
- Las variantes V, H y B no cambian (el binario es idéntico).

# Versión 11: fuente española, tiles de 8×8 y tiles de profundidad

## Fuente española de serie

- El motor trae una fuente de letras gruesas con **á é í ó ú ñ Á É Í Ó Ú Ñ ¿ ¡**. Los textos se
  escriben con sus tildes y salen tal cual.
- Esas letras ocupan el sitio de `# $ % & @ [ \ ] ^ _ ` { } ~`, que con esta fuente no se pueden
  escribir. La ü sale como u.
- En **Partida → Fuente**: *Española (de serie)*, *La de la ROM* (sin tildes), *Importar…* y
  *Exportar…*. Una fuente propia con las letras españolas en el mismo sitio se marca con la casilla
  de debajo.

## Tiles de 8×8

- Casilla **Tiles de 8×8** en la pestaña Scroll, para los cinco tipos de scroll. Al activarla, cada
  tile se parte en sus 4 caracteres y el mapa pasa a tener el doble de filas y columnas.
- Sólido, plataforma, mortal, rompible, objeto, puerta y profundidad se miran carácter a carácter
  (comprobado en el emulador: muros de 8 píxeles, objetos de 8×8 que se recogen solos, suelos a
  media altura de un tile, en las variantes V, H, B, D y C).
- El motor dibuja los grupos de 2×2 caracteres como tiles de 16×16: la velocidad no cambia.
  Límite: 256 grupos distintos (128 con scroll horizontal fino); la pestaña Mapa los cuenta.

## Tiles de profundidad

- Un tile de profundidad tapa a los personajes (dibujo, tinta y papel del tile), salvo que sus
  líneas digan otra cosa:
  - **Tras**: si el borde elegido del personaje queda por debajo, se ve el personaje.
  - **Ante**: si queda por debajo o en la línea, se ve el tile; si queda por encima, el personaje.
- Las líneas son rectas o diagonales, se dibujan con dos clics en el editor de tiles y pueden
  salirse del tile. El borde puede ser inferior, superior, izquierdo o derecho.
- **Se traspasa**: sin ella, ese borde de los personajes no cruza la línea (vallas, barandillas,
  rampas en plataformas).
- El tile se redibuja píxel a píxel solo en el trozo que tapa al personaje. Con color propio de
  los personajes también se devuelve el color del tile a esas casillas.

## Otros cambios

- **Color propio de los personajes también en el scroll libre**: conservan su tinta sobre el papel
  del fondo.
- Corregido: en el scroll libre con gravedad, las plataformas se pisaban mal en algunos casos.
- Las fases se reparten mejor por los bancos: si no caben por orden, se colocan de la más grande a
  la más pequeña, cada una en el hueco más justo.
- Nuevo ejemplo **JUNGLA 8x8** (`ejemplos_v11.py`): vertical, mapa de 8×8, árboles y columnas por
  los que se pasa por detrás y vallas que no se cruzan.
- Las 14 cintas de ejemplo anteriores se han regenerado y probado con el motor nuevo.

## Versión 11.1

- **Lado que cuenta** en cada línea de profundidad: «cuenta debajo» o «cuenta encima» (bordes
  inferior y superior), «cuenta a la derecha» o «cuenta a la izquierda» (izquierdo y derecho).
  Unas rayitas en el dibujo del tile señalan ese lado.
- Al cambiar el borde de una línea, la línea de partida se coloca en ese lado del tile (antes, con
  el borde superior o el derecho, la línea seguía abajo o a la izquierda). Las líneas que se salen
  del tile se marcan en el borde del dibujo.
- Las vallas de los ejemplos usan una línea **Tras** que no se traspasa: desde el sur se ve al
  personaje delante, desde el norte detrás, y nadie la cruza.
- Nuevo ejemplo **ALDEA ZX** (`ejemplos_v12.py`): scroll libre, tinta propia de cada personaje,
  casas en las que se entra (el tejado tapa a la protagonista), llaves bajo los tejados, huertos con
  vallas y árboles.
- **Archivo → Ejemplos** lista los 16 juegos de ejemplo, agrupados por tipo de scroll.
