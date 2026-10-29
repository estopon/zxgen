; ============================================================
;  MOTOR  -  FASE 6
;  Scroll por caracteres en una direccion por juego:
;   vertical (hacia arriba) u horizontal (hacia la derecha),
;   modo "sigue al jugador" (con o sin retroceso) o automatico.
;  Mapa de tiles 16x16, sprites pre-desplazados con mascara de
;  16x16 / 16x24 / 24x24 combinables, doble bufer (banco 7).
;
;  Fondo en memoria:
;   vertical:   anillo de 160 lineas x 24 bytes (filas que rotan)
;   horizontal: 160 lineas x 48 bytes, cada columna duplicada (c y c+24)
;               para que la ventana visible sea siempre contigua
;
;  Bancos de datos (paginados en 0xC000):
;   0  nivel: cabecera + tiles + mapa
;   1  pantalla de presentacion (0xC000) y marco (0xDB00)
;   3  textos
;   4  sprites: cabecera + fotogramas
;   6  musica: reproductor PT3 de Sergey Bulba en 0xC000 + modulos
; ============================================================
BANKM   equ 0x5CFF          ; copia del puerto 0x7FFD (propia: la de la ROM, 0x5B5C, cae dentro de conf)
RAMB    equ 0x5C40          ; variables que empiezan a cero (antes variables de sistema de la ROM, libres)

BUF     equ 0x6000          ; fondo: hasta 160 x 48 = 7680 bytes
BUFFIN  equ 0x6F00          ; fin del anillo vertical (160 x 24)
PILA    equ 0x8000          ; pila: 0x7E00-0x7FFF
ABUF    equ 0x8000          ; atributos: hasta 20 x 48 = 960 bytes
ANILLO_V equ 21             ; filas de caracteres del anillo vertical (una mas que la vista)
LINEAS_V equ ANILLO_V*8     ; 168 lineas
ABUFFIN equ ABUF+ANILLO_V*24 ; fin del anillo vertical de atributos (21 x 24)
LTAB    equ 0x8400          ; tabla de direcciones de linea (hasta 320 palabras)
SAVE    equ 0x8700          ; guardado de fondo: 7 x 128 (personajes) + 7 x 16 (balas)
SOLIDOS equ 0x8B00          ; propiedades de cada tile (bit0 solido, bit1 detiene disparos)
IM2TAB  equ 0xBE00
IM2JP   equ 0xBFBF
conf    equ 0x5B00          ; configuracion general (CONF_LEN bytes, hasta 0x5C3F; el motor no usa la ROM)
fuente  equ 0x5D00          ; fuente (768 bytes) en memoria baja: 0x5D00-0x5FFF (alli estaba el cargador)
cabnivel equ 0xBF01         ; cabecera de la fase (32 bytes), en el hueco libre tras la tabla IM2
buf_msg equ 0xBF21          ; texto de los mensajes (24 bytes)
golpe_z equ 0xBF39          ; zona del golpe (una ficha de sprite, SLOT bytes)
caja_t  equ 0xBF5A          ; caja barrida de una bala (SLOT bytes; se usan x, y, ancho y alto)
EXT     equ 0xBF7C          ; 8 bytes tras la cabecera de la fase: tiles de 8x8 y profundidad
EXT_META equ EXT+0          ; celda de cada cuarto de cada tile (tiles de 8x8)
EXT_TRASM equ EXT+2         ; tile que queda al cambiar cada cuarto
EXT_PROF equ EXT+4          ; tabla de profundidad
EXT_T8  equ EXT+6           ; 1 = tiles de 8x8
EXT_FLG equ EXT+7           ; bits 0-3: bordes con lineas que no se traspasan; bit 4: hay profundidad
PRFG    equ 0xBF84          ; dibujo y colores del tile que se redibuja (36 bytes)
VPRF    equ 0xBFA8          ; variables de la profundidad (21 bytes, hasta 0xBFBC)
prf_n   equ VPRF+0
ps_x0   equ VPRF+1
ps_x1   equ VPRF+2
ps_y0   equ VPRF+3
ps_y1   equ VPRF+4
ps_px   equ VPRF+5
ps_py   equ VPRF+6
ps_meta equ VPRF+7
ps_id   equ VPRF+8
ps_cx16 equ VPRF+9
ps_cy16 equ VPRF+10
ps_mx16 equ VPRF+11
ps_my16 equ VPRF+12
pr_sx   equ VPRF+13
pr_sy   equ VPRF+14
pc_l    equ VPRF+15
rp_y    equ VPRF+17
rp_s    equ VPRF+18
rp_t    equ VPRF+19
pc_op   equ VPRF+20         ; opciones de la linea en curso (bit 3: lado invertido)
PRFL    equ 0x8680          ; trozos de tiles de profundidad que tapan sprites (7 bytes cada uno)
PRFMAX  equ 18

ANCHO   equ 24              ; ancho del area de juego en bytes
ALTO    equ 20              ; alto en caracteres
; huecos de sprites: 0 jugador, luego n_ene enemigos, n_bj balas del jugador y n_be enemigas
; (cuantos de cada, en la configuracion: el generador los ajusta a la memoria y al tamano)
NSPR_MAX equ 25             ; como mucho 10 enemigos, 6 balas del jugador y 8 enemigas
SLOT    equ 33
VEL_BJ  equ 4               ; velocidad de las balas del jugador
VEL_BE  equ 2               ; velocidad de las balas enemigas
; campos de un sprite
S_ACT   equ 0
S_X     equ 1
S_Y     equ 2
S_W     equ 3               ; ancho en bytes
S_H     equ 4
S_FR    equ 5               ; fotograma (palabra)
S_DX    equ 7
S_DY    equ 8
S_COMP  equ 9               ; comportamiento: 0 quieto, 1 rebota, 2 persigue, 3 cruza
S_ENER  equ 10
S_CDISP equ 11              ; cuenta atras para disparar
S_LP    equ 12
S_XB    equ 14
S_WP    equ 15              ; ancho en pixeles
S_SV    equ 16
S_VEL   equ 18
S_TIPO  equ 19              ; puntero a la ficha del tipo (palabra)
S_CAD   equ 21              ; cadencia de disparo (0 = no dispara)
S_ACNT  equ 22              ; cuenta atras hasta el siguiente fotograma de animacion
S_AFR   equ 23              ; paso de animacion (0-7)
S_MIRA  equ 24              ; 0 mira a la derecha, 1 a la izquierda
S_COMPI equ 25              ; 1 = sprite compilado (codigo en el banco 7, solo en modo bloques)
S_COLOR equ 26              ; color propio (brillo + tinta) o 0 = toma el del fondo (modo bloques)
S_AP    equ 27              ; enemigos: entrada de la lista de apariciones de la que salio (palabra)
S_BX    equ 29              ; enemigos: caja de sus pixeles de verdad (para el laser): x, y, ancho, alto
S_BY    equ 30
S_BW    equ 31
S_BH    equ 32

; cabecera de la fase (copiada a RAM desde su banco)
N_FILAS equ cabnivel+0x00
N_TILES equ cabnivel+0x02
N_MAPA  equ cabnivel+0x04
N_COL   equ cabnivel+0x06
N_FILA  equ cabnivel+0x07
N_PX    equ cabnivel+0x08
N_PY    equ cabnivel+0x09
N_VEL   equ cabnivel+0x0A
N_UMB   equ cabnivel+0x0B
N_DIR   equ cabnivel+0x0C          ; 0 vertical, 1 horizontal
N_AUTO  equ cabnivel+0x0D          ; 0 sigue al jugador, 1 automatico
N_RETRO equ cabnivel+0x0E          ; 1 = permite retroceso
N_VAUTO equ cabnivel+0x0F          ; fotogramas de juego por caracter (modo automatico)
N_UMBR  equ cabnivel+0x10          ; umbral de retroceso
N_APAR  equ cabnivel+0x11          ; lista de apariciones de enemigos
N_FLAGS equ cabnivel+0x13          ; tabla de 256 propiedades de tile
N_CADJ  equ cabnivel+0x15          ; cadencia de disparo del jugador
N_PASO  equ cabnivel+0x16          ; paso del scroll en pixeles (1, 2, 4 u 8)
N_RITMO equ cabnivel+0x17          ; interrupciones por fotograma de juego
N_PARMAP equ cabnivel+0x18         ; mapa de parejas (modo bloques): 10 bytes por columna de caracteres
N_TPROP equ cabnivel+0x1A          ; propiedades de cada tile: tras, accion, valor, mensaje, puntos
N_NREG  equ cabnivel+0x1F          ; bits 1-7: reglas de combinacion (justo antes de N_TPROP, 6 bytes cada una)
N_PARLIST equ cabnivel+0x1C        ; (modo bloques) lista de parejas: media columna izquierda y derecha
N_NPARL equ cabnivel+0x1E          ; numero de parejas de la lista
N_HAYOBJ equ cabnivel+0x1F         ; bit 0: la fase tiene objetos que recoger
; configuracion general (banco 3, copiada a RAM en "conf")
CONF_LEN  equ 288
C_VIDAS   equ conf+0
C_ENER    equ conf+1
C_KEMP    equ conf+2
C_NNIV    equ conf+3
C_INSTR   equ conf+4          ; textos de instrucciones (banco 3)
C_MENU    equ conf+6          ; textos del menu (banco 3)
C_FUENTE  equ conf+8          ; fuente propia (banco 3) o 0
C_CTRLF   equ conf+10         ; linea de controles: fila, columna, atributo
C_CTRLC   equ conf+11
C_CTRLA   equ conf+12
C_MSGT    equ conf+13         ; textos (banco 3)
C_MSGK    equ conf+15
C_MSGFASE equ conf+17
C_MSGGO   equ conf+19
C_MSGFIN  equ conf+21
C_MSGA    equ conf+23
C_NIVELES equ conf+24         ; 16 fases x (banco, direccion de la cabecera)
C_HUD     equ conf+72         ; 5 elementos x 13 bytes
C_MUSM    equ conf+137        ; modulo PT3 del menu (banco 6) o 0
C_MUSJ    equ conf+139        ; modulo PT3 de las fases (banco 6) o 0
C_MUSP    equ conf+141        ; 1 si el banco 6 tiene el reproductor
C_PLAT    equ conf+142        ; 1 = modo plataformas
C_SALTO   equ conf+143        ; subida del salto: pixeles por fotograma, terminada en 0 (24 bytes)
C_CAIDA   equ conf+167        ; caida: pixeles por fotograma; el ultimo se repite (16 bytes)
C_PARES   equ conf+183        ; bloques pre-desplazados (banco 3) y su longitud
C_PARLEN  equ conf+185
C_PATR    equ conf+187        ; colores de cada pareja (4 bytes)
C_NPAR    equ conf+189        ; numero de parejas
C_V16     equ conf+190        ; bytes por pareja (16 x versiones)
C_MONO    equ conf+191        ; 1 = todas las parejas del mismo color (no hace falta repintar colores)
C_COMP    equ conf+192        ; 1 = bloques compilados (codigo que escribe sus bytes), si caben
C_ARMA    equ conf+193        ; arma del jugador: 0 disparo, 1 golpe, 2 ninguna
C_ALC     equ conf+194        ; alcance del golpe en pixeles
C_PISAR   equ conf+195        ; 1 = (plataformas) caer sobre un enemigo lo dana y el jugador rebota
C_MSGS    equ conf+196        ; mensajes de objetos y reglas (16 punteros en el banco 3)
C_LCOMP   equ conf+228        ; bytes de cada version de un bloque compilado
C_HUDOBJ  equ conf+229        ; inventario en el marcador: activo, fila, columna, color
C_SIMB    equ conf+233        ; simbolo de cada elemento (8)
C_NELEM   equ conf+241        ; elementos definidos (0-8)
C_FALTA   equ conf+242        ; mensaje del altar si no se cumple ninguna regla (255 = ninguno)
C_MEZCLA  equ conf+243        ; modo mezcla (estilo SMB): paginas entre los bloques A y los B (0 = no)
C_COLSPR  equ conf+244        ; 1 = los personajes pintan su color en los atributos
C_NVAC    equ conf+245        ; parejas 0..C_NVAC-1 sin pixeles: solo color (no se dibujan)
C_MITAD   equ conf+246        ; 1 = alguna pareja cambia de color a mitad de camino
C_NENE    equ conf+265        ; enemigos a la vez (1-10)
C_NBJ     equ conf+266        ; balas del jugador a la vez (1-6)
C_NBE     equ conf+267        ; balas enemigas a la vez (1-8)
C_SVJ     equ conf+268        ; fondo guardado por hueco (bytes; modos con anillo): jugador,
C_SVE     equ conf+269        ;   enemigo,
C_SVB     equ conf+270        ;   bala del jugador
C_SVBE    equ conf+271        ;   y bala enemiga
C_VBJ     equ conf+272        ; velocidad de las balas del jugador (px por fotograma)
C_VBE     equ conf+273        ; y de las enemigas
C_TBJ     equ conf+274        ; tamano de la bala del jugador: ancho en bytes, alto en px
C_TBE     equ conf+276        ; y de la enemiga
C_LAS     equ conf+278        ; laser: bit0 se para en el primer enemigo, bit1 en los tiles que detienen
C_LGRO    equ conf+279        ; grosor (1-3 lineas)
C_LDUR    equ conf+280        ; fotogramas que se ve
C_LALC    equ conf+281        ; alcance maximo en px (0 = hasta el borde)
C_LPAT    equ conf+282        ; dibujo: un byte por linea (se repite cada 8 px)
C_LANIM   equ conf+285        ; 1 = el dibujo avanza un pixel por fotograma
C_ATRC    equ conf+286        ; scroll libre: atributo del area (fondo de dos colores)
C_ACEL    equ conf+263        ; inercia (plataformas): aceleracion en 1/16 px por fotograma (0 = sin inercia)
C_FRENO   equ conf+264        ; y frenada
C_SFX     equ conf+247        ; 8 efectos de sonido (direcciones en el banco 6, 0 = ninguno):
                              ; 0 salto, 1 golpe, 2 disparo, 3 enemigo muere, 4 jugador herido,
                              ; 5 objeto, 6 romper, 7 puerta o hablar
PT3_INIT  equ 0xC003          ; reproductor de Bulba: START+3 (HL = modulo)
PT3_PLAY  equ 0xC005          ; START+5, una vez por interrupcion
PT3_MUTE  equ 0xC008          ; START+8
; cabecera de sprites (banco 4)
G_PW    equ 0xC000
G_PH    equ 0xC001
G_VANIM equ 0xC002          ; velocidad de animacion del jugador (fotogramas de juego por paso)
G_DFIJO equ 0xC003          ; direccion fija del disparo del jugador + 1 (0 = hacia donde mira)
G_ANIM  equ 0xC004          ; 8 direcciones x 8 fotogramas (palabras)
G_QUIETO equ 0xC084         ; fotograma en reposo por direccion (8 palabras)
G_DISPARO equ 0xC094        ; fotograma al disparar por direccion (8 palabras)
G_BALAJ equ 0xC0A4          ; fotograma de la bala del jugador
G_BALAE equ 0xC0A6          ; fotograma de la bala enemiga
G_TIPOS equ 0xC0A9          ; 16 tipos de enemigo x 48 bytes:
                            ; 0 w, 1 h, 2 comportamiento, 3 vel, 4 energia, 5 cadencia, 6 direccion,
                            ; 7 puntos (decenas BCD), 8 vel. animacion, 16-31 fotogramas mirando a la
                            ; derecha (8 palabras), 32-47 mirando a la izquierda (8 palabras)
FICHA   equ 48              ; (byte 9: numero de fotogramas del ciclo, 1-8)
G_ALEN  equ 0xC3A9          ; longitud del ciclo de andar del jugador por direccion (8 bytes)
G_COMPJ equ 0xC3B1          ; 1 = fotogramas del jugador compilados (sus direcciones son descriptores
G_COMPBJ equ 0xC3B2         ;     en el banco 7: 4 palabras, una por desplazamiento)
G_COMPBE equ 0xC3B3
G_COLORJ equ 0xC3B4         ; color propio del jugador (0 = el del fondo)
G_AGACHA equ 0xC3B5         ; fotograma agachado por direccion (8 palabras, 0 = no se agacha)
G_MUERTE equ 0xC3C5         ; fotograma al morir (0 = sin animacion)
G_CAJAS equ 0xC3C7          ; caja de los pixeles de cada tipo de enemigo: x, y, ancho, alto (16 x 4)

        org 0x8C00
entrada:
        di
        ld sp,PILA
        call crear_tablas
        ld a,IM2TAB/256
        ld i,a
        im 2
        ld hl,RAMB              ; variables a cero
        ld de,RAMB+1
        ld bc,RAMB_LEN-1
        ld (hl),b
        ldir
        ld a,0x10
        ld (BANKM),a
        ei
        xor a
        ld (pantalla),a
        ld a,3                  ; configuracion general (banco 3) a RAM
        call pon_banco
        ld hl,0xC000
        ld de,conf
        ld bc,CONF_LEN
        ldir
        call preparar_huecos
        ld a,(C_KEMP)
        ld (kempston),a
        ld hl,(C_FUENTE)        ; fuente propia (banco 3) o la de la ROM
        ld a,h
        or l
        jr nz,en1
        ld hl,0x3D00
en1:    ld de,fuente
        ld bc,768
        ldir
        ld hl,fuente+95*8       ; caracter 127: bloque macizo (barra de energia)
        ld b,8
en2:    ld (hl),0xFF
        inc hl
        djnz en2
        call espera_tecla       ; pantalla de carga
        ld hl,0
        ld (sfx_ptr),hl

; ------------------------------------------------------------
;  MENU: 1 jugar, 2 instrucciones, 3 controles
; ------------------------------------------------------------
menu_inicio:
        ld sp,PILA
        ld hl,(C_MUSM)          ; melodia del menu
        call musica
menu:
        ld sp,PILA
        xor a
        out (0xFE),a
        ld (pantalla),a
        ld a,0x40
        ld (base_txt),a
        ld a,1                  ; presentacion
        call pon_banco
        ld hl,0xC000
        ld de,0x4000
        ld bc,6912
        ldir
        ld a,3
        call pon_banco
        ld hl,(C_MENU)
        call imprime_lista
        call imprime_controles
mn1:    call espera_suelta
mn2:    ld a,0xF7               ; teclas 1 2 3
        in a,(0xFE)
        bit 0,a
        jp z,partida
        bit 1,a
        jr z,instrucciones
        bit 2,a
        jr nz,mn2
        ld a,(kempston)
        xor 1
        ld (kempston),a
        call imprime_controles
        jr mn1

instrucciones:
        call borra_pantalla
        ld a,3
        call pon_banco
        ld hl,(C_INSTR)
        call imprime_lista
        call espera_tecla
        jr menu

imprime_controles:
        ld a,3
        call pon_banco
        ld a,(C_CTRLA)
        ld (atributo),a
        ld a,(C_CTRLF)
        ld b,a
        ld a,(C_CTRLC)
        ld c,a
        ld hl,(C_MSGT)
        ld a,(kempston)
        or a
        jr z,ictl1
        ld hl,(C_MSGK)
ictl1:  jp imprime_cadena

; ------------------------------------------------------------
;  PARTIDA Y FASES
; ------------------------------------------------------------
partida:
        ld sp,PILA
        ld hl,(C_MUSJ)          ; melodia de las fases (sigue sonando de una fase a otra)
        call musica
        ld a,(C_VIDAS)
        ld (vidas),a
        ld a,(C_ENER)
        ld (energia),a
        xor a
        ld (inv),a              ; inventario vacio
        call restaurar_mapas    ; lo que se rompio o se recogio en la partida anterior
        xor a
        ld (nivel),a
        ld hl,puntos
        ld (hl),a
        inc hl
        ld (hl),a
        inc hl
        ld (hl),a
nivel_inicio:
        ld sp,PILA
        ld a,(nivel)            ; ficha de la fase: banco y direccion de su cabecera
        ld l,a
        add a,a
        add a,l
        ld e,a
        ld d,0
        ld hl,C_NIVELES
        add hl,de
        ld a,(hl)
        ld (banco_nivel),a
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        push de
        call pon_banco
        pop hl
        ld de,cabnivel          ; cabecera de la fase a RAM
        ld bc,32
        ldir
        ld de,EXT               ; y los 8 bytes que la siguen (si el bit 7 del ritmo dice que estan;
        ld bc,8                 ; si no, a cero)
        ld a,(N_RITMO)
        add a,a
        jr c,nic0
        xor a
        ld (de),a
        ld h,d
        ld l,e
        inc de
        dec bc
nic0:   ldir
        ld a,(EXT_T8)           ; celdas de 16 u 8 pixeles
        or a
        ld a,16
        jr z,nic1
        ld a,8
nic1:   ld (csz),a
        dec a
        ld (cmsk),a
        ld (cbs1+1),a           ; (los puntos de las cajas se miran cada celda)
        ld (cbs2+1),a
        ld (ffs1+1),a
        ld a,(N_COL)
        ld (pcol),a
        ld a,(N_FILA)
        ld (pfila),a
        ld a,(via_puerta)       ; por una puerta no se avisa de la fase
        or a
        jr nz,ni_sin
        ld a,(nivel)            ; aviso "FASE nn"
        inc a
        call a_bcd
        ld (num_msg),a
        ld hl,(C_MSGFASE)
        ld a,1
        ld b,100
        call mensaje
ni_sin: xor a
        ld (via_puerta),a
        ld a,1                  ; marco a las dos pantallas
        call pon_banco
        ld hl,0xC000+6912
        ld de,0x4000
        ld bc,6912
        ldir
        ld a,7
        call pon_banco
        ld hl,0x4000
        ld de,0xC000
        ld bc,6912
        ldir
        ; configuracion del nivel
        ld a,(banco_nivel)
        call pon_banco
        ld hl,(N_FILAS)         ; largo del mapa (filas o columnas de tiles) x2
        add hl,hl
        ld (largo2),hl
        ld hl,(N_TILES)
        ld (tiles),hl
        ld hl,(N_MAPA)
        ld (mapa),hl
;@ SOLO D
        ld hl,(N_PARMAP)        ; pantalla a pantalla: rejilla de salas y sala inicial
        ld (salas),hl
        ld a,(N_PARLIST)
        ld (sala_x),a
        ld a,(N_PARLIST+1)
        ld (sala_y),a
        call sala_segura
;@ FIN
        ld a,(N_COL)
        ld (pcol),a
        ld a,(N_FILA)
        ld (pfila),a
        ld a,(N_VEL)
        ld (velocidad),a
        ld a,(N_UMB)
        ld (umbral),a
        ld a,(N_UMBR)
        ld (umbral_r),a
        ld a,(N_DIR)
        ld (dir),a
        ld a,(N_AUTO)
        ld (auto),a
        ld a,(N_RETRO)
        ld (retro),a
        ld a,(N_VAUTO)
        ld (vel_auto),a
        ld (auto_cnt),a
        ld a,(N_PX)
        ld (sprites+S_X),a
        ld a,(N_PY)
        ld (sprites+S_Y),a
        xor a
        ld (c0),a
        ld (fino),a
        ld (bloques),a
        ld hl,(col_entrada)     ; columna de caracteres por la que se entra (puertas; horizontal)
        ld (izq),hl
;@ SOLO D
        ld hl,0                 ; (pantalla a pantalla: siempre la sala entera)
        ld (izq),hl
;@ FIN
        ld hl,0
        ld (col_entrada),hl
        ld hl,LTAB
        ld (ltab_act),hl
        ld a,(N_RITMO)
        and 0x7F
        ld (ritmo),a
        ld a,(dir)
        or a
        jp nz,ini_h
;@ SOLO V
        ; --- vertical: se empieza abajo del mapa ---
        ld a,(N_PASO)
        ld (paso_v),a
        ld a,ANCHO
        ld c,2
        ld b,LINEAS_V
        call crear_ltab
        ld hl,(largo2)          ; tpx = tmax = largo2*8 - 160
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,ALTO*8
        or a
        sbc hl,de
        ld (tpx),hl
        ld (tmax),hl
        ld de,LINEAS_V
        call modulo
        ld (linea0),a
        ld hl,(largo2)          ; filas cargadas: de r_top a r_bot
        ld de,ALTO
        or a
        sbc hl,de
        ld (r_top),hl
        ld de,ANILLO_V
        call modulo
        ld (a_top),a
        ld hl,(r_top)
        ld b,0
ini_filas:
        push bc
        push hl
        ld (fmundo),hl
        ld (r_bot),hl
        ld de,ANILLO_V
        call modulo
        ld (anillo),a
        ld (a_bot),a
        call pintar_fila
        pop hl
        inc hl
        pop bc
        inc b
        ld a,b
        cp ALTO
        jr nz,ini_filas
        ld hl,0xFFFF            ; fuerza el calculo de la fila de atributos
        ld (arow),hl
        call fila_atr
        jr ini_fondo_ok
;@ FIN
        ; --- horizontal: se empieza a la izquierda ---
;@ SOLO H B D
ini_h:  ld a,(N_PASO)
        ld (paso_h),a
        cp 8
        jp nc,ini_h8
        ld a,1                  ; --- horizontal fino: bloques pre-desplazados ---
        ld (bloques),a
        call ini_bloques
        jp ini_fondo_ok
;@ FIN
;@ SOLO H D
ini_h8: ld a,ANCHO*2            ; --- horizontal de 8 en 8 ---
        ld c,1
        ld b,160
        call crear_ltab
        ld b,0
ini_cols:
        push bc
        ld a,b
        ld (anillo),a
        ld hl,(izq)
        ld e,b
        ld d,0
        add hl,de
        ld (fmundo),hl
        call pintar_col
        pop bc
        inc b
        ld a,b
        cp ANCHO
        jr nz,ini_cols
;@ FIN
ini_fondo_ok:
        ld a,2
        ld (cnt_atr),a
        ; propiedades de los tiles y apariciones (banco 0)
        ld hl,(N_FLAGS)
        ld de,SOLIDOS
        ld bc,256
        ldir
        ld hl,(N_APAR)
        ld (apar),hl
        ld a,(N_CADJ)
        ld (cad_j),a
        ld a,(dir)              ; el jugador mira hacia donde avanza el scroll
        or a
        jr z,ini_d1
        ld a,2
ini_d1: ld (dir_j),a
        ; sprites: todos inactivos
        ld ix,sprites
        ld a,(n_spr)
        ld b,a
        ld de,SLOT
ini_s1: ld (ix+S_ACT),0
        add ix,de
        djnz ini_s1
        ld a,4
        call pon_banco
        ld hl,G_TIPOS           ; fichas de los enemigos a RAM
        ld de,tipos
        ld bc,16*FICHA
        ldir
        ld hl,G_CAJAS           ; y la caja de sus pixeles
        ld de,cajas
        ld bc,64
        ldir
        ld hl,(G_BALAJ)
        ld (fr_bala_j),hl
        ld hl,(G_BALAE)
        ld (fr_bala_e),hl
        ld a,(G_COMPBJ)
        ld (comp_bj),a
        ld a,(G_COMPBE)
        ld (comp_be),a
        ld ix,sprites
        ld a,(G_COMPJ)
        ld (ix+S_COMPI),a
        ld a,(G_COLORJ)
        ld (ix+S_COLOR),a
        ld hl,(G_MUERTE)
        ld (fr_muerte),hl
        ld hl,(G_AGACHA+4)      ; se agacha si tiene fotograma mirando a la derecha
        ld a,h
        ld (agacha_ok),a
        xor a
        ld (muerte),a
        ld (agachado),a
        ld (npc_cool),a
        ld (vx),a
        ld (ix+S_ACT),1
        ld a,(G_PW)
        ld (ix+S_W),a
        add a,a
        add a,a
        add a,a
        ld (ix+S_WP),a
        ld a,(G_PH)
        ld (ix+S_H),a
        ld a,(G_VANIM)
        ld (vanim_j),a
        ld a,(G_DFIJO)
        ld (dfijo),a
        ld hl,G_ALEN
        ld de,alen_j
        ld bc,8
        ldir
        ld a,1
        ld (acnt_j),a
        xor a
        ld (cuadros),a
        ld (cool),a
        ld (invul),a
        ld (golpes),a
        ld (evento),a
        ld (las_t),a
        ld (las_vis),a
        ld (idx_v),a
        ld (salto_listo),a
        ld a,2
        ld (cnt_hud),a
        ld (estado_v),a         ; plataformas: empieza cayendo hasta el suelo
        ld (mira_j),a
        ld a,(N_PX)
        ld (seguro_x),a
        ld a,(N_PY)
        ld (seguro_y),a

; ------------------------------------------------------------
;  BUCLE PRINCIPAL
; ------------------------------------------------------------
bucle:
        ld a,(muerte)           ; muriendo: la escena se para y solo se mueve el jugador
        or a
        jp nz,bu_muerte
        call leer_entrada
        ld a,(banco_nivel)      ; logica con el banco de la fase (mapa) paginado
        call pon_banco
        call mover_jugador
        call recoger
        call fin_nivel
        call disparar
        call laser_cuadro
        call aparecer
        call mover_enemigos
        call mover_balas
        call colisiones
        call profundidad
        ld a,4                  ; dibujo con el banco 4 (sprites) paginado
        call pon_banco
        call fotograma_jugador
        call parpadeo
bu_dib: ld a,(bloques)
        or a
        jr nz,bu_bloques
        call dibujar_sprites
        call restaurar_prof     ; (los tiles de profundidad que tapan a los sprites)
        call dibujar_laser      ; (con XOR en el anillo)
        call volcar
        call dibujar_laser      ; (otra vez: lo borra)
        call restaurar_sprites
        jr bu_fin
bu_bloques:
        call volcar             ; fondo y marcador en la pantalla oculta
        ld hl,LTAB              ; los sprites, encima, directamente en esa pantalla
        ld a,(base)
        cp 0x40
        jr z,bu_b1
        ld hl,LTAB+320
bu_b1:  ld (ltab_act),hl
        call dibujar_sprites
        call dibujar_laser
        call restaurar_prof
        call pintar_atrs        ; color propio de los personajes (si esta activo)
        call atr_prof
bu_fin:
        ld hl,reloj
        inc (hl)
espera:
        halt
        ld a,(cuadros)
        ld hl,ritmo             ; cadencia fija: siempre las mismas interrupciones por fotograma
        cp (hl)
        jr c,espera
        xor a
        ld (cuadros),a
        ld a,(pantalla)         ; intercambia pantallas
        xor 8
        ld (pantalla),a
        ld a,(banco)
        call pon_banco
        ld a,(evento)
        or a
        jp nz,evento_juego
        jp bucle

; bu_muerte: un fotograma de la animacion de muerte (A = cuenta atras). Sube 2 px durante 12
; fotogramas y luego cae 3 px por fotograma hasta salir del area; al acabar, reaparece.
bu_muerte:
        dec a
        ld (muerte),a
        ld hl,prf_n             ; (durante la animacion no se mira la profundidad)
        ld (hl),0
        ld ix,sprites
        jr z,mue_fin
        cp 32
        ld a,(ix+S_Y)
        jr c,mue_cae
        sub 2
        jr nc,mue_py
        xor a
        jr mue_py
mue_cae:
        add a,3
        ld b,a
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        cp b
        jr c,mue_py
        ld a,b
mue_py: ld (ix+S_Y),a
        ld hl,(fr_muerte)
        ld (ix+S_FR),l
        ld (ix+S_FR+1),h
        ld (ix+S_ACT),1
        ld a,4
        call pon_banco
        jp bu_dib
mue_fin:
        ld a,(mue_x)            ; vuelve a su sitio con 2 segundos de invulnerabilidad
        ld (ix+S_X),a
        ld a,(mue_y)
        ld (ix+S_Y),a
        ld a,50
        ld (invul),a
        xor a
        ld (estado_v),a
        ld a,(mue_ev)           ; sin vidas: fin de la partida
        ld (evento),a
        jp bucle

; morir: empieza la animacion de muerte (si el jugador tiene fotograma de muerte). A = evento al
; acabar (1 = fin de la partida, 0 = sigue); B, C = donde reaparece. NZ si hay animacion.
morir:  ld (mue_ev),a
        xor a
        ld (vx),a
        ld (las_t),a
        ld (las_vis),a
        ld a,b
        ld (mue_x),a
        ld a,c
        ld (mue_y),a
        ld a,4
        call sonido
        ld a,(fr_muerte+1)
        or a
        ret z
        ld a,44
        ld (muerte),a
        ret

; ------------------------------------------------------------
;  ENTRADA: QAOP y joystick Sinclair (6789)
;  devuelve A: bit0 dcha, bit1 izq, bit2 abajo, bit3 arriba, bit4 disparo
; ------------------------------------------------------------
leer_entrada:
        ld e,0
        ld a,0xFB
        in a,(0xFE)
        bit 0,a
        jr nz,le1
        set 3,e
le1:    ld a,0xFD
        in a,(0xFE)
        bit 0,a
        jr nz,le2
        set 2,e
le2:    ld a,0xDF
        in a,(0xFE)
        bit 1,a
        jr nz,le3
        set 1,e
le3:    bit 0,a
        jr nz,le4
        set 0,e
le4:    ld a,0x7F               ; ESPACIO = disparo
        in a,(0xFE)
        bit 0,a
        jr nz,le4b
        set 4,e
le4b:   ld a,0xEF
        in a,(0xFE)
        bit 0,a                 ; 0 = disparo (joystick Sinclair)
        jr nz,le4c
        set 4,e
le4c:   bit 4,a
        jr nz,le5
        set 1,e
le5:    bit 3,a
        jr nz,le6
        set 0,e
le6:    bit 2,a
        jr nz,le7
        set 2,e
le7:    bit 1,a
        jr nz,le8
        set 3,e
le8:    ld a,(kempston)         ; Kempston: mismos bits que la entrada
        or a
        jr z,le8b
        in a,(0x1F)
        and 0x1F
        or e
        ld e,a
le8b:   ld a,e
        and 3                   ; izquierda+derecha a la vez: se anulan
        cp 3
        jr nz,le9
        ld a,e
        and 0xFC
        ld e,a
le9:    ld a,e
        and 12
        cp 12
        jr nz,le10
        ld a,e
        and 0xF3
        ld e,a
le10:   ld a,e
        ld (entrada_j),a
        ret

; ------------------------------------------------------------
;  MOVIMIENTO DEL JUGADOR Y SCROLL
; ------------------------------------------------------------
mover_jugador:
        ld a,(C_PLAT)
        or a
        jp nz,mover_plataformas
        ld ix,sprites
        ld a,(entrada_j)
        ld c,a
        ld a,(velocidad)
        ld b,a
        bit 0,c                 ; derecha
        jr z,mj1
        push bc
        ld a,b
        call mover_x_bloq
        pop bc
mj1:    bit 1,c                 ; izquierda
        jr z,mj2
        push bc
        ld a,b
        neg
        call mover_x_bloq
        pop bc
mj2:    bit 2,c                 ; abajo
        jr z,mj3
        push bc
        ld a,b
        call mover_y_bloq
        pop bc
mj3:    bit 3,c                 ; arriba
        jr z,mj4
        ld a,b
        neg
        call mover_y_bloq
mj4:    call desplazar
        ld a,(entrada_j)        ; direccion y animacion
        and 15
        ld e,a
        ld d,0
        ld hl,tabla_dir
        add hl,de
        ld a,(hl)
        cp 0xFF
        jr z,mj6                ; quieto
        ld (dir_j),a
        xor a
        ld (quieto_j),a
anim_paso:
        ld hl,acnt_j            ; avanza la animacion cada vanim_j fotogramas
        dec (hl)
        ret nz
        ld a,(vanim_j)
        ld (hl),a
        call alen_dir           ; HL = longitud del ciclo de la direccion actual
        ld a,(afr_j)
        inc a
        cp (hl)
        jr c,mj5b
        xor a
mj5b:   ld (afr_j),a
        ret

alen_dir:
        ld a,(dir_j)
        ld e,a
        ld d,0
        ld hl,alen_j
        add hl,de
        ret
mj6:    ld a,1
        ld (quieto_j),a
        ret

; ------------------------------------------------------------
;  DECISION DE SCROLL (IX = jugador)
; ------------------------------------------------------------
;@ SOLO V H B
desplazar:
        ld a,(auto)
        or a
        jr z,dz_sigue
        ld hl,auto_cnt          ; automatico: un caracter cada vel_auto fotogramas
        dec (hl)
        ret nz
        ld a,(vel_auto)
        ld (hl),a
        ld a,(dir)
        or a
        jr nz,dza_h
        call scroll_arriba
        ret nc
        ld d,(ix+S_X)           ; si el escenario le alcanza, lo empuja
        ld e,(ix+S_Y)
        ld a,1
        call bloqueado_en
        ret z
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        ld d,a
        ld a,(ultimo_paso)
        add a,(ix+S_Y)
        cp d
        jr c,dza1
        ld a,d
dza1:   ld (ix+S_Y),a
        ret
dza_h:  call scroll_dcha
        ret nc
        ld d,(ix+S_X)
        ld e,(ix+S_Y)
        ld a,1
        call bloqueado_en
        ret z
        ld a,(ultimo_paso)
        ld b,a
        ld a,(ix+S_X)
        sub b
        jr nc,dza2
        xor a
dza2:   ld (ix+S_X),a
        ret
dz_sigue:
        ld a,(dir)
        or a
        jr nz,dz_h
        ld a,(umbral)           ; vertical: y < umbral -> avanza
        ld e,a
        ld a,(ix+S_Y)
        cp e
        jr nc,dz_v2
        call scroll_arriba
        jr nc,dz_v2
        ld a,(ultimo_paso)
        add a,(ix+S_Y)
        ld (ix+S_Y),a
        ret
dz_v2:  ld a,(retro)            ; y + h > 160 - umbral_r -> retrocede
        or a
        ret z
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        ld d,a
        ld a,(umbral_r)
        neg
        add a,ALTO*8
        cp d
        ret nc
        call scroll_abajo
        ret nc
        ld a,(ultimo_paso)
        ld b,a
        ld a,(ix+S_Y)
        sub b
        ld (ix+S_Y),a
        ret
dz_h:   ld a,8                  ; horizontal: x + w*8 > 192 - umbral -> avanza
        ld (dz_cnt),a
dz_hr:  ld a,(ix+S_W)
        add a,a
        add a,a
        add a,a
        add a,(ix+S_X)
        ld d,a
        ld a,(umbral)
        neg
        add a,192
        cp d
        jr nc,dz_hx
        call scroll_dcha
        jr nc,dz_hx
        ld a,(ultimo_paso)
        ld b,a
        ld a,(ix+S_X)
        sub b
        ld (ix+S_X),a
        ld a,(bloques)          ; de 8 en 8: un paso por fotograma
        or a
        ret z
        ld hl,dz_cnt            ; por bloques: el fondo sigue al jugador (el jugador no salta)
        dec (hl)
        jr nz,dz_hr
        ret
dz_hx:  ld a,(dz_cnt)
        cp 8
        ret nz                  ; ya avanzo este fotograma
dz_h2:  ld a,8                  ; x < umbral_r -> retrocede
        ld (dz_cnt),a
dz_h2r: ld a,(retro)
        or a
        ret z
        ld a,(umbral_r)
        ld e,a
        ld a,(ix+S_X)
        cp e
        ret nc
        call scroll_izq
        ret nc
        ld a,(ultimo_paso)
        add a,(ix+S_X)
        ld (ix+S_X),a
        ld a,(bloques)
        or a
        ret z
        ld hl,dz_cnt
        dec (hl)
        jr nz,dz_h2r
        ret

;@ FIN
;@ SOLO D
; ------------------------------------------------------------
;  PANTALLA A PANTALLA: al llegar a un borde empujando hacia fuera se pasa a la sala de al lado
;  (si existe en la rejilla de la fase). En plataformas, arriba y abajo se pasa al saltar o caer
;  (subir y bajar llaman a sala_arriba y sala_abajo).
; ------------------------------------------------------------
desplazar:
        ld a,(entrada_j)
        ld (ds_ent),a
        bit 0,a                 ; derecha
        jr z,dsd1
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        cp 192-3
        jr c,dsd1
        ld bc,0x0100
        call cambiar_sala
        jr nc,dsd1
        ld (ix+S_X),0
        jr ds_seguro
dsd1:   ld a,(ds_ent)           ; izquierda
        bit 1,a
        jr z,dsd2
        ld a,(ix+S_X)
        cp 4
        jr nc,dsd2
        ld bc,0xFF00
        call cambiar_sala
        jr nc,dsd2
        ld a,(ix+S_WP)
        neg
        add a,192
        ld (ix+S_X),a
        jr ds_seguro
dsd2:   ld a,(C_PLAT)
        or a
        ret nz
        ld a,(ds_ent)           ; arriba
        bit 3,a
        jr z,dsd3
        ld a,(ix+S_Y)
        cp 4
        jr nc,dsd3
        ld bc,0x00FF
        call cambiar_sala
        jr nc,dsd3
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        ld (ix+S_Y),a
        jr ds_seguro
dsd3:   ld a,(ds_ent)           ; abajo
        bit 2,a
        ret z
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        cp ALTO*8-3
        ret c
        ld bc,0x0001
        call cambiar_sala
        ret nc
        ld (ix+S_Y),0
ds_seguro:                      ; punto de reaparicion: donde se entra en la sala (en plataformas, el
        ld a,(C_PLAT)           ; ultimo suelo firme, aunque sea de otra sala: si no, al entrar sobre un
        or a                    ; foso se moriria una y otra vez)
        ret nz
        ld a,(ix+S_X)
        ld (seguro_x),a
        ld a,(ix+S_Y)
        ld (seguro_y),a
sala_segura:
        ld a,(sala_x)
        ld (seg_sx),a
        ld a,(sala_y)
        ld (seg_sy),a
        ret

; volver_sala: a la sala del punto seguro (si no es la actual)
volver_sala:
        ld a,(seg_sx)
        ld hl,sala_x
        sub (hl)
        ld b,a
        ld a,(seg_sy)
        ld hl,sala_y
        sub (hl)
        ld c,a
        or b
        ret z
        jp cambiar_sala

; sala_arriba / sala_abajo (plataformas, desde subir y bajar): NZ si se ha cambiado de sala
sala_arriba:
        push bc
        ld bc,0x00FF
        call cambiar_sala
        pop bc
        jr nc,sal_no
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        ld (ix+S_Y),a
        call ds_seguro
        ld a,(ix+S_Y)           ; (subir sigue con A = y)
        or a
        ret
sala_abajo:
        push bc
        ld bc,0x0001
        call cambiar_sala
        pop bc
        jr nc,sal_no
        ld (ix+S_Y),0
        call ds_seguro
        or 1
        ret
sal_no: xor a
        ret

; cambiar_sala: B = dx, C = dy (-1, 0 o 1). CF=1 si hay sala en esa direccion (y ya se esta en ella).
; (salas): ancho y alto de la rejilla, tabla de salas (4 bytes cada una: mapa y apariciones) y la
; rejilla (ancho x alto bytes: numero de sala + 1, o 0 si no hay)
cambiar_sala:
        ld hl,(salas)
        ld a,(sala_x)
        add a,b
        cp (hl)
        ret nc                  ; fuera de la rejilla (-1 = 255 tambien)
        ld d,a
        inc hl
        ld a,(sala_y)
        add a,c
        cp (hl)
        ret nc
        ld e,a
        dec hl
        ld c,(hl)               ; C = ancho de la rejilla
        ld a,d                  ; A = fila * ancho + columna
        ld b,e
        inc b
cs1:    dec b
        jr z,cs2
        add a,c
        jr cs1
cs2:    ld hl,(salas)
        inc hl
        inc hl
        inc hl
        inc hl
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld a,(hl)
        or a
        ret z                   ; no hay sala (CF=0)
        dec a
        push af
        ld a,d
        ld (sala_x),a
        ld a,e
        ld (sala_y),a
        ld hl,(salas)
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)               ; DE = tabla de salas
        pop af
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (mapa),de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (apar),de
        ld (N_APAR),de          ; (aparecer no rebobina mas alla del principio de su lista)
        call entrar_sala
        scf
        ret

; entrar_sala: quita enemigos, balas y laser, y pinta la sala nueva en el anillo
entrar_sala:
        push ix
        ld ix,sprites+SLOT
        ld a,(n_spr)
        dec a
        ld b,a
        ld de,SLOT
es1:    ld (ix+S_ACT),0
        add ix,de
        djnz es1
        xor a
        ld (las_t),a
        ld (las_vis),a
        ld (c0),a
        ld hl,0
        ld (ap_l),hl
        ld (ap_lv),hl
        ld b,0
es2:    push bc
        ld a,b
        ld (anillo),a
        ld l,b
        ld h,0
        ld (fmundo),hl
        call pintar_col
        pop bc
        inc b
        ld a,b
        cp ANCHO
        jr nz,es2
        ld a,2
        ld (cnt_atr),a
        pop ix
        ret

ds_ent:    db 0
seg_sx:    db 0
seg_sy:    db 0
sala_x:    db 0
sala_y:    db 0
salas:     dw 0
;@ FIN

;@ SOLO C
; ------------------------------------------------------------
;  SCROLL LIBRE EN 8 DIRECCIONES (variante C)
;  La camara se mueve pixel a pixel en vertical y de 2 en 2 en horizontal (como los sprites).
;  El fondo es de dos colores: el atributo del area no cambia nunca, asi no hay choque de color.
;  Esta en 4 copias, desplazadas 0, 2, 4 y 6 pixeles a la izquierda; cada copia es un anillo de
;  160 lineas x 24 bytes en las dos direcciones: la columna de bytes w del mundo va en la columna
;  w mod 24 del anillo, y la linea l en la linea l mod 160. Asi, al moverse la camara solo se
;  construye la columna o las lineas que entran, y el volcado copia la copia que toca.
;  Copias: 0x6000 y 0x6F00 (memoria baja), 0xDB00 y 0xEA00 (banco 7, tras la pantalla oculta).
; ------------------------------------------------------------
COP0    equ 0x6000
SCRC    equ 0x8700          ; grafico del sprite en curso (hasta 320 bytes)
WBC     equ 0x8840          ; columna en construccion: 2 bytes por linea (160 lineas)
WBF     equ 0x8980          ; linea en construccion: 25 bytes
ROWT    equ 0x89A0          ; direccion de cada fila del mapa (hasta 160 filas)

; inicio de fase (desde nivel_inicio)
ini_h:  ld a,2
        ld (paso_h),a
        ld a,1
        ld (bloques),a
        ld hl,(N_PARMAP)        ; ancho del mapa en tiles y largo de cada fila (2^k)
        ld a,l
        ld (map_w),a
        ld a,h
        ld (map_sh),a
        ld hl,1
        or a
        jr z,ih0
ihs:    add hl,hl
        dec a
        jr nz,ihs
ih0:    ld (stride),hl
        ld a,(map_w)            ; limites de la camara
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,-192
        add hl,de
        ld (cmx),hl
        ld hl,(N_FILAS)
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,-160
        add hl,de
        ld (cmy),hl
        ld de,(mapa)            ; tabla de filas del mapa
        ld ix,ROWT
        ld a,(N_FILAS)
        ld b,a
ih1:    ld (ix+0),e
        ld (ix+1),d
        inc ix
        inc ix
        ld hl,(stride)
        add hl,de
        ex de,hl
        djnz ih1
        ld a,(N_PARLIST)        ; pantalla inicial: x = columna*192, y = fila*160
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld (cam_x),hl
        ld a,(N_PARLIST+1)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld (cam_y),hl
        xor a
        ld (rcol),a
        ld (rlin),a
        call cam_partes
        ld b,0x40               ; tablas de lineas de las dos pantallas
        ld hl,LTAB
        call ltab_pantalla
        ld b,0xC0
        call ltab_pantalla
        call color_area
        ld b,0                  ; las 24 columnas de la vista
ih2:    push bc
        ld hl,(cam_x)
        call div8
        ld e,b
        ld d,0
        add hl,de
        ld (cc_w),hl
        ld hl,(cam_y)
        ld (cc_l),hl
        ld a,160
        ld (cc_n),a
        call construir_col
        pop bc
        inc b
        ld a,b
        cp ANCHO
        jr nz,ih2
        call ap_reset
        jp ini_fondo_ok

div8:   srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ret

; cam_partes: parte alta (en tiles) y baja (0-15) de la posicion de la camara
cam_partes:
        ld hl,(cam_x)
        ld a,l
        and 15
        ld (cx_lo),a
        call div16
        ld a,l
        ld (cx_hi),a
        ld hl,(cam_y)
        ld a,l
        and 15
        ld (cy_lo),a
        call div16
        ld a,l
        ld (cy_hi),a
        ret

; color_area: el atributo del area (dos colores) en las dos pantallas
color_area:
        ld a,(C_ATRC)
        ld (ca_v+1),a
        ld a,7
        call pon_banco
        ld d,0x58
        call ca_una
        ld d,0xD8
        call ca_una
        ld a,(banco_nivel)
        jp pon_banco
ca_una: ld a,(pfila)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(pcol)
        add a,l
        ld l,a
        ld a,h
        add a,d
        ld h,a
        ld c,ALTO
ca1:    push hl
        ld b,ANCHO
ca_v:   ld a,0
ca2:    ld (hl),a
        inc hl
        djnz ca2
        pop hl
        ld de,32
        add hl,de
        dec c
        jr nz,ca1
        ret

; atr_oculta: el atributo del area en la pantalla oculta (la tinta de los personajes se repinta despues)
atr_oculta:
        ld a,(C_ATRC)
        ld (ca_v+1),a
        ld a,(base)
        add a,0x18
        ld d,a
        jp ca_una

; ptr_tile: A = tile -> HL = (tiles) + tile*36 + (cc_t2)   (usa DE)
ptr_tile:
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(tiles)
        add hl,de
        ld a,(cc_t2)
        ld e,a
        ld d,0
        add hl,de
        ret

; escribe en las 4 copias: D = byte w, E = byte w+1, HL = entrada en la copia 0 (se conserva)
; (la copia k lleva el par desplazado 2k pixeles a la izquierda)
esc4:   ld (hl),d
        ex de,hl
        add hl,hl
        add hl,hl
        ex de,hl
        ld a,h
        add a,0x0F
        ld h,a
        ld (hl),d
        ex de,hl
        add hl,hl
        add hl,hl
        ex de,hl
        ld a,h
        add a,0x6C
        ld h,a
        ld (hl),d
        ex de,hl
        add hl,hl
        add hl,hl
        ex de,hl
        ld a,h
        add a,0x0F
        ld h,a
        ld (hl),d
        ld a,h
        sub 0x8A
        ld h,a
        ret

; construir_col: (cc_w) = columna de bytes del mundo, (cc_l) = primera linea, (cc_n) = lineas (1-160)
construir_col:
        ld a,(banco_nivel)      ; 1) con el banco de la fase: los bytes w y w+1 de cada linea en WBC
        call pon_banco
        ld hl,(cc_w)
        ld a,l
        and 1
        ld (cc_med),a
        srl h
        rr l
        ld (cc_tc),hl
        ld iy,WBC
        ld hl,(cc_l)
        ld a,(cc_n)
        ld b,a
cct0:   push bc
        push hl
        ld a,l
        and 15
        ld c,a
        add a,a
        ld (cc_t2),a
        ld a,16
        sub c
        ld c,a                  ; lineas hasta el final de esta fila de tiles
        ld a,b
        cp c
        jr nc,cct1
        ld c,a
cct1:   ld a,c
        ld (cc_seg),a
        call div16              ; fila de tiles
        add hl,hl
        ld de,ROWT
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld hl,(cc_tc)
        add hl,de               ; HL = tile en el mapa
        ld a,(cc_med)
        or a
        jr nz,cct2
        ld a,(hl)               ; columna par: los dos bytes del mismo tile
        call ptr_tile
        ld d,h
        ld e,l
        inc de
        jr cct3
cct2:   ld a,(hl)               ; impar: derecha de este tile, izquierda del siguiente
        inc hl
        ld c,(hl)
        call ptr_tile
        inc hl
        push hl
        ld a,c
        call ptr_tile
        ex de,hl
        pop hl
cct3:   ld a,(cc_seg)
        ld c,a
cclp:   ld a,(hl)
        ld (iy+0),a
        ld a,(de)
        ld (iy+1),a
        inc hl
        inc hl
        inc de
        inc de
        inc iy
        inc iy
        dec c
        jr nz,cclp
        pop hl
        ld a,(cc_seg)
        ld e,a
        ld d,0
        add hl,de
        pop bc
        ld a,b
        sub e
        ld b,a
        jr nz,cct0
        ld a,7                  ; 2) en las 4 copias (dos estan en el banco 7)
        call pon_banco
        ld hl,(cam_x)           ; columna del anillo = (rcol + w - cx) mod 24
        call div8
        ex de,hl
        ld hl,(cc_w)
        or a
        sbc hl,de
        ld a,(rcol)
        add a,l
        cp ANCHO
        jr c,cct4
        sub ANCHO
cct4:   ld (cc_rc),a
        ld hl,(cc_l)            ; linea del anillo = (rlin + l - cam_y) mod 160
        ld de,(cam_y)
        or a
        sbc hl,de
        ld a,(rlin)
        add a,l
        jr c,cct5
        cp 160
        jr c,cct6
cct5:   sub 160
cct6:   call dir_anillo
        ld a,(cc_rc)
        ld e,a
        ld d,0
        add hl,de
        ld ix,WBC
        ld a,(cc_n)
        ld b,a
cct7:   ld d,(ix+0)
        ld e,(ix+1)
        inc ix
        inc ix
        call esc4
        ld de,ANCHO
        add hl,de
        ld a,h
        cp 0x6F
        jr c,cct8
        sub 0x0F
        ld h,a
cct8:   djnz cct7
        ld a,(banco_nivel)
        jp pon_banco

; dir_anillo: A = linea del anillo -> HL = COP0 + A*24
dir_anillo:
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,COP0
        add hl,de
        ret

; construir_fila: (cf_l) = linea del mundo. Sus 24 entradas a la vista (columnas cx .. cx+23).
construir_fila:
        ld a,(banco_nivel)
        call pon_banco
        ld hl,(cf_l)
        ld a,l
        and 15
        add a,a
        ld (cc_t2),a
        call div16
        add hl,hl
        ld de,ROWT
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)               ; DE = fila del mapa
        ld hl,(cam_x)
        call div8
        ld a,l
        and 1
        ld (cc_med),a
        srl h
        rr l
        add hl,de               ; HL = primer tile
        ld iy,WBF
        ld b,25
        ld a,(cc_med)
        or a
        jr z,cfl1
        push hl                 ; empieza por la mitad derecha de un tile
        ld a,(hl)
        call ptr_tile
        inc hl
        ld a,(hl)
        ld (iy+0),a
        inc iy
        pop hl
        inc hl
        dec b
cfl1:   push hl
        ld a,(hl)
        call ptr_tile
        ld a,(hl)
        ld (iy+0),a
        inc iy
        dec b
        jr z,cfl2
        inc hl
        ld a,(hl)
        ld (iy+0),a
        inc iy
        pop hl
        inc hl
        djnz cfl1
        jr cfl3
cfl2:   pop hl
cfl3:   ld a,7
        call pon_banco
        ld hl,(cf_l)            ; linea del anillo
        ld de,(cam_y)
        or a
        sbc hl,de
        ld a,(rlin)
        add a,l
        jr c,cfl4
        cp 160
        jr c,cfl5
cfl4:   sub 160
cfl5:   call dir_anillo
        ld (cf_ini),hl
        ld a,(rcol)
        ld e,a
        ld d,0
        add hl,de
        ld a,(rcol)
        neg
        add a,ANCHO
        ld c,a                  ; entradas hasta el final de la linea del anillo
        ld ix,WBF
        ld b,ANCHO
cfl6:   ld d,(ix+0)
        ld e,(ix+1)
        inc ix
        call esc4
        inc hl
        dec c
        jr nz,cfl7
        ld hl,(cf_ini)
cfl7:   djnz cfl6
        ld a,(banco_nivel)
        jp pon_banco

; ------------------------------------------------------------
;  CAMARA: sigue al jugador (IX) cuando se acerca a los bordes (margenes N_UMB y N_UMBR)
; ------------------------------------------------------------
desplazar:
        ld a,(umbral)           ; --- horizontal: lo que se pasa del margen, par y hasta 8
        ld c,a
        ld a,(ix+S_X)
        sub c
        jr c,dzc_i
        ld a,(umbral)
        neg
        add a,192
        ld c,a
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        sub c
        jr c,dzc_x0
        jr z,dzc_x0
        inc a
        and 0xFE
        cp 9
        jr c,dzc_x1
        ld a,8
        jr dzc_x1
dzc_i:  and 0xFE
        cp 0xF8
        jr nc,dzc_x1
        ld a,0xF8
        jr dzc_x1
dzc_x0: xor a
dzc_x1: or a
        jr z,dzc_x9
        ld hl,(cam_x)           ; nueva posicion, dentro de 0 .. cmx
        call sumar_lim_x
        push hl
        ld de,(cam_x)
        or a
        sbc hl,de
        ld a,l
        ld (cdx),a
        ld hl,(cam_x)
        call div8
        ex de,hl                ; DE = columna de antes
        pop hl
        ld (cam_x),hl
        call div8
        or a
        sbc hl,de
        ld a,l
        or a
        jr z,dzc_y
        dec a
        jr nz,dzc_xi
        ld a,(rcol)             ; una columna a la derecha: entra la cx+23
        inc a
        cp ANCHO
        jr c,dzc_x2
        xor a
dzc_x2: ld (rcol),a
        ld hl,(cam_x)
        call div8
        ld de,ANCHO-1
        add hl,de
        jr dzc_xc
dzc_xi: ld a,(rcol)             ; a la izquierda: entra la cx
        or a
        jr nz,dzc_x3
        ld a,ANCHO
dzc_x3: dec a
        ld (rcol),a
        ld hl,(cam_x)
        call div8
dzc_xc: ld (cc_w),hl
        ld hl,(cam_y)
        ld (cc_l),hl
        ld a,160
        ld (cc_n),a
        push ix
        call construir_col
        pop ix
        jr dzc_y
dzc_x9: ld (cdx),a
dzc_y:  ld a,(umbral_r)         ; --- vertical: pixel a pixel, hasta 8
        ld c,a
        ld a,(ix+S_Y)
        sub c
        jr c,dzc_a
        ld a,(umbral_r)
        neg
        add a,ALTO*8
        ld c,a
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        sub c
        jr c,dzc_y0
        jr z,dzc_y0
        cp 9
        jr c,dzc_y1
        ld a,8
        jr dzc_y1
dzc_a:  cp 0xF8
        jr nc,dzc_y1
        ld a,0xF8
        jr dzc_y1
dzc_y0: xor a
dzc_y1: ld (cdy),a
        or a
        jr z,dzc_fin
        ld hl,(cam_y)
        call sumar_lim_y
        ld de,(cam_y)
        or a
        sbc hl,de
        ld a,l
        ld (cdy),a
        or a
        jr z,dzc_fin
        bit 7,a
        jr nz,dzc_sube
        ld b,a
dzc_bj: push bc                 ; baja: entra por abajo la linea cam_y + 159
        ld hl,(cam_y)
        inc hl
        ld (cam_y),hl
        ld a,(rlin)
        inc a
        cp 160
        jr c,dzc_b1
        xor a
dzc_b1: ld (rlin),a
        ld de,159
        add hl,de
        ld (cf_l),hl
        push ix
        call construir_fila
        pop ix
        pop bc
        djnz dzc_bj
        jr dzc_fin
dzc_sube:
        neg
        ld b,a
dzc_sb: push bc                 ; sube: entra por arriba la linea cam_y
        ld hl,(cam_y)
        dec hl
        ld (cam_y),hl
        ld (cf_l),hl
        ld a,(rlin)
        or a
        jr nz,dzc_s1
        ld a,160
dzc_s1: dec a
        ld (rlin),a
        push ix
        call construir_fila
        pop ix
        pop bc
        djnz dzc_sb
dzc_fin:
        call cam_partes
        ld a,(cdx)              ; todo lo que hay en pantalla se mueve al reves que la camara
        neg
        ld b,a
        ld a,(cdy)
        neg
        ld c,a
        or b
        ret z
        ld a,(ix+S_X)
        add a,b
        ld (ix+S_X),a
        ld a,(ix+S_Y)
        add a,c
        ld (ix+S_Y),a
        ld a,(seguro_y)
        add a,c
        ld (seguro_y),a
        jp desplazar_objetos

; sumar_lim_x / _y: HL = posicion, A = desplazamiento con signo -> HL dentro de 0 .. cmx (cmy)
sumar_lim_x:
        ld de,(cmx)
        jr sl0
sumar_lim_y:
        ld de,(cmy)
sl0:    ld (sl_max),de
        ld e,a
        ld d,0
        bit 7,a
        jr z,sl1
        dec d
sl1:    add hl,de
        bit 7,d
        jr nz,sl_neg
        ex de,hl
        ld hl,(sl_max)
        or a
        sbc hl,de
        ex de,hl
        ret nc
        ld hl,(sl_max)
        ret
sl_neg: ret c                   ; (sin acarreo: ha pasado de 0)
        ld hl,0
        ret

; ------------------------------------------------------------
;  MAPA: tile en un punto de la pantalla (B = x, C = y), con el banco de la fase
; ------------------------------------------------------------
flags_en:
        call dir_mapa
        ld a,(hl)
        call id_celda
        ld l,a
        ld h,SOLIDOS/256
        ld a,(hl)
        ret
dir_mapa:
        ld a,(cy_lo)
        add a,c
        ld e,a
        and 15
        ld (ct_fy),a
        ld a,(cx_lo)
        add a,b
        and 15
        ld (ct_fx),a
        ld a,e
        rrca
        rrca
        rrca
        rrca
        and 15
        ld hl,cy_hi
        add a,(hl)
        ld l,a
        ld h,0
        add hl,hl
        ld de,ROWT
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(cx_lo)
        add a,b
        rrca
        rrca
        rrca
        rrca
        and 15
        ld hl,cx_hi
        add a,(hl)
        ld l,a
        ld h,0
        add hl,de
        ret

; cambiar_tile: B = x, C = y. Cambia el tile por su "tras", da sus puntos y reconstruye su trozo
cambiar_tile:
        push ix
        push bc
        call dir_mapa
        ld a,(hl)
        call id_celda
        ld (ct_id),a
        push hl
        xor a
        call nuevo_tile
        pop hl
        call anotar
        ld (hl),a
        ld a,4
        call propiedad
        call sumar_puntos
        ld a,2
        ld (cnt_hud),a
        pop bc
        ld a,(cy_lo)            ; fila y columna de tiles del mundo
        add a,c
        rrca
        rrca
        rrca
        rrca
        and 15
        ld hl,cy_hi
        add a,(hl)
        ld (ct_fila),a
        ld a,(cx_lo)
        add a,b
        rrca
        rrca
        rrca
        rrca
        and 15
        ld hl,cx_hi
        add a,(hl)
        ld (ct_col),a
        ld a,(ct_fila)          ; lineas: las del tile que estan a la vista
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,(cam_y)
        ld a,16
        ld (cc_n),a
        or a
        sbc hl,de               ; 16 f - cam_y
        jr nc,ctc1
        ld a,h
        inc a
        jr nz,ctc_fin           ; muy por encima
        ld a,l
        add a,16
        jr nc,ctc_fin           ; (todo por encima)
        jr z,ctc_fin
        ld (cc_n),a
        ld hl,0
ctc1:   ld a,h
        or a
        jr nz,ctc_fin
        ld a,l
        cp 160
        jr nc,ctc_fin           ; por debajo
        ld a,(cc_n)
        add a,l
        sub 160
        jr c,ctc2
        jr z,ctc2
        ld e,a
        ld a,(cc_n)
        sub e
        ld (cc_n),a
ctc2:   ld de,(cam_y)
        add hl,de
        ld (cc_l),hl
        ld hl,(cam_x)
        call div8
        ex de,hl                ; DE = cx
        ld a,(ct_col)
        ld l,a
        ld h,0
        add hl,hl
        dec hl                  ; columnas de bytes 2c-1, 2c y 2c+1
        ld b,3
ctc3:   push bc
        push hl
        push de
        or a
        sbc hl,de
        jr c,ctc4
        ld a,h
        or a
        jr nz,ctc4
        ld a,l
        cp ANCHO
        jr nc,ctc4
        pop de
        pop hl
        push hl
        push de
        ld (cc_w),hl
        call construir_col
ctc4:   pop de
        pop hl
        inc hl
        pop bc
        djnz ctc3
ctc_fin:
        pop ix
        ret

; ------------------------------------------------------------
;  APARICIONES: lista ordenada por x del mundo (x, y en pixeles, tipo, estado). Cada fotograma se
;  miran las que tienen x cerca de la vista (entre ap_lo y ap_hi): una aparece cuando su sitio
;  entra entero en la vista (estado bit 0: ya se veia; bit 1: destruida).
; ------------------------------------------------------------
ap_reset:
        ld hl,(N_APAR)
        ld (ap_lo),hl
        ld (ap_hi),hl
apr1:   ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        and e
        inc a
        ret z
        inc hl
        inc hl
        inc hl
        inc hl
        ld (hl),0
        inc hl
        jr apr1

aparecer:
        ld hl,(cam_x)
        ld de,-32
        add hl,de
        jr c,apc0
        ld hl,0
apc0:   ld (ap_xa),hl
        ld hl,(cam_x)
        ld de,192
        add hl,de
        ld (ap_xb),hl
apc1:   ld hl,(ap_lo)           ; lo avanza mientras x < xa
        call ap_x
        jr z,apc2
        ld hl,(ap_xa)
        ex de,hl
        or a
        sbc hl,de
        jr nc,apc2
        ld hl,(ap_lo)
        call ap_novista
        ld de,6
        add hl,de
        ld (ap_lo),hl
        jr apc1
apc2:   ld hl,(ap_lo)           ; lo retrocede mientras la anterior tenga x >= xa
        ld de,(N_APAR)
        or a
        sbc hl,de
        jr z,apc3
        ld hl,(ap_lo)
        ld de,-6
        add hl,de
        push hl
        call ap_x
        ld hl,(ap_xa)
        ex de,hl
        or a
        sbc hl,de
        pop hl
        jr c,apc3
        ld (ap_lo),hl
        jr apc2
apc3:   ld hl,(ap_hi)           ; hi avanza mientras x < xb
        call ap_x
        jr z,apc4
        ld hl,(ap_xb)
        ex de,hl
        or a
        sbc hl,de
        jr nc,apc4
        ld hl,(ap_hi)
        ld de,6
        add hl,de
        ld (ap_hi),hl
        jr apc3
apc4:   ld hl,(ap_hi)           ; hi retrocede mientras la anterior tenga x >= xb
        ld de,(N_APAR)
        or a
        sbc hl,de
        jr z,apc5
        ld hl,(ap_hi)
        ld de,-6
        add hl,de
        push hl
        call ap_x
        ld hl,(ap_xb)
        ex de,hl
        or a
        sbc hl,de
        pop hl
        jr c,apc5
        ld (ap_hi),hl
        call ap_novista
        jr apc4
apc5:   ld hl,(ap_lo)           ; las de la ventana
apc6:   ld de,(ap_hi)
        push hl
        or a
        sbc hl,de
        pop hl
        ret nc
        push hl
        call ap_mirar
        pop hl
        ld de,6
        add hl,de
        jr apc6

; ap_x: HL = entrada -> DE = su x (Z si es el final de la lista)
ap_x:   ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        and e
        inc a
        ret
; ap_novista: HL = entrada (se conserva) -> estado bit 0 a cero
ap_novista:
        push hl
        ld de,5
        add hl,de
        res 0,(hl)
        pop hl
        ret

; ap_mirar: HL = entrada. Si su sitio esta entero en la vista y antes no lo estaba, aparece
ap_mirar:
        ld (ap_ent),hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld hl,(cam_x)
        ex de,hl
        or a
        sbc hl,de
        ld a,h
        or a
        jr nz,am_no
        ld a,l
        ld (ap_px),a
        ld hl,(ap_ent)
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,(hl)
        ld (ap_tipo),a
        ld hl,(cam_y)
        ex de,hl
        or a
        sbc hl,de
        ld a,h
        or a
        jr nz,am_no
        ld a,l
        ld (ap_py),a
        ld a,(ap_tipo)          ; su tamano
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,tipos
        add hl,de
        ld a,(hl)
        add a,a
        add a,a
        add a,a
        ld b,a
        inc hl
        ld c,(hl)
        ld a,(ap_px)
        add a,b
        jr c,am_no
        cp 193
        jr nc,am_no
        ld a,(ap_py)
        add a,c
        jr c,am_no
        cp ALTO*8+1
        jr nc,am_no
        ld hl,(ap_ent)
        ld de,5
        add hl,de
        ld a,(hl)
        and 3
        ret nz                  ; ya se veia, o esta destruida
        push hl
        call ap_crear_c
        pop hl
        ret nz                  ; sin hueco: se reintenta
        set 0,(hl)
        ret
am_no:  ld hl,(ap_ent)
        jp ap_novista

; ap_crear_c: crea el enemigo de (ap_ent) en (ap_px, ap_py). NZ si no hay hueco
ap_crear_c:
        ld hl,(ap_ent)
        ld ix,sprites+SLOT      ; ¿ya esta en juego?
        ld a,(n_ene)
        ld b,a
        ld de,SLOT
acc0:   ld a,(ix+S_ACT)
        or a
        jr z,acc1
        ld a,(ix+S_AP)
        cp l
        jr nz,acc1
        ld a,(ix+S_AP+1)
        cp h
        ret z
acc1:   add ix,de
        djnz acc0
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld b,a
        call buscar_libre
        ret nz
        ld hl,(ap_ent)
        ld (ix+S_AP),l
        ld (ix+S_AP+1),h
        ld a,(ap_tipo)
        call activar_tipo
        ld a,(ap_px)
        ld (ix+S_X),a
        ld a,(ap_py)
        ld (ix+S_Y),a
        xor a
        ret

; ------------------------------------------------------------
;  VOLCADO de la copia que toca a la pantalla oculta (en lugar de render_bloques)
; ------------------------------------------------------------
render_bloques:
        ld a,7
        call pon_banco
        ld a,(C_COLSPR)         ; con tinta propia de los personajes: el area vuelve a su color
        or a
        call nz,atr_oculta
        ld a,(cam_x)            ; copia = (x / 2) mod 4
        rrca
        and 3
        add a,a
        ld e,a
        ld d,0
        ld hl,tab_copias
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        add a,14
        ld (vlim),a             ; (si H pasa de la copia + 14 paginas, vuelve 15 atras)
        ld a,(rlin)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,bc
        add hl,de
        ld a,(rcol)
        ld c,a
        ld b,0
        add hl,bc
        push hl
        call vc_codigo
        pop hl
        ld a,(pfila)
        ld c,a
        ld b,ALTO
vcf:    push bc
        ld a,c                  ; DE = fila C de la pantalla oculta
        and 0x18
        ld d,a
        ld a,(base)
        or d
        ld d,a
        ld a,c
        and 7
        rrca
        rrca
        rrca
        ld e,a
        ld a,(pcol)
        or e
        ld e,a
        rept 7
        call VCOD
        ld bc,ANCHO
        add hl,bc
        ld a,(vlim)
        cp h
        jr nc,$+6
        ld a,h
        sub 15
        ld h,a
        ld a,e
        sub ANCHO
        ld e,a
        inc d
        endm
        call VCOD
        ld bc,ANCHO
        add hl,bc
        ld a,(vlim)
        cp h
        jr nc,$+6
        ld a,h
        sub 15
        ld h,a
        pop bc
        inc c
        dec b
        jp nz,vcf
        ret

; vc_codigo: prepara VCOD: 24-rcol LDI, vuelta al principio de la linea (HL-24), rcol LDI, ret
vc_codigo:
        ld hl,VCOD
        ld a,(rcol)
        neg
        add a,ANCHO
        ld b,a
        call vcc_ldi
        ld (hl),0x01            ; ld bc,-24
        inc hl
        ld (hl),0xE8
        inc hl
        ld (hl),0xFF
        inc hl
        ld (hl),0x09            ; add hl,bc
        inc hl
        ld a,(rcol)
        ld b,a
        call vcc_ldi
        ld (hl),0xC9            ; ret
        ret
vcc_ldi:
        ld a,b
        or a
        ret z
vcl1:   ld (hl),0xED
        inc hl
        ld (hl),0xA0
        inc hl
        djnz vcl1
        ret

tab_copias: dw 0x6000,0x6F00,0xDB00,0xEA00
VCOD:      ds 54
vlim:      db 0
cam_x:     dw 0
cam_y:     dw 0
cmx:       dw 0
cmy:       dw 0
stride:    dw 16
map_w:     db 12
map_sh:    db 4
rcol:      db 0
rlin:      db 0
cx_lo:     db 0
cx_hi:     db 0
cy_lo:     db 0
cy_hi:     db 0
cdx:       db 0
cdy:       db 0
sl_max:    dw 0
cc_w:      dw 0
cc_l:      dw 0
cc_n:      db 0
cc_tc:     dw 0
cc_med:    db 0
cc_t2:     db 0
cc_seg:    db 0
cc_rc:     db 0
cf_l:      dw 0
cf_ini:    dw 0
ct_col:    db 0
ap_lo:     dw 0
ap_hi:     dw 0
ap_xa:     dw 0
ap_xb:     dw 0
ap_px:     db 0
ap_py:     db 0
ap_tipo:   db 0
;@ FIN


; ------------------------------------------------------------
;  TILES DE 8x8 Y TILES DE PROFUNDIDAD
;  Tras la cabecera de cada fase hay 8 bytes (EXT): direcciones de META (celda de 8x8 de cada cuarto
;  de cada tile de 16x16), TRASM (tile que queda al cambiar cada cuarto) y de la tabla de
;  profundidad; 1 si los tiles son de 8x8, y FLG: bits 0-3 bordes con lineas que no se traspasan,
;  bit 4 hay tiles de profundidad.
;  Tabla de profundidad: numero de entradas y, en cada una (35 bytes): celda, linea Tras y linea
;  Ante, cada linea con un byte de opciones (bit 7 existe, bits 0-1 borde del sprite que se mira:
;  0 abajo, 1 arriba, 2 izquierda, 3 derecha; bit 2 no se traspasa; bit 3 cuenta el otro lado) y 16 bytes con la altura de la
;  linea en cada columna (o su columna en cada fila, para los bordes izquierdo y derecho).
; ------------------------------------------------------------

; id_celda: A = tile del mapa -> A = celda (con tiles de 8x8: META[tile*4 + cuarto]). Usa DE
id_celda:
        ld e,a
        ld a,(EXT_T8)
        or a
        ld a,e
        ret z
        ld (ct_meta),a
        push hl                 ; (HL se conserva: suele ser la casilla del mapa)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        call cuarto
        or l
        ld l,a
        ld de,(EXT_META)
        add hl,de
        ld a,(hl)
        pop hl
        ret
; cuarto: A = cuarto del tile del ultimo punto mirado (0 arriba-izq, 1 arriba-dcha, 2, 3)
cuarto: ld a,(ct_fy)
        and 8
        rrca
        rrca
        ld e,a
        ld a,(ct_fx)
        and 8
        rrca
        rrca
        rrca
        or e
        ret
; nuevo_tile: A = tile que queda al cambiar el punto (su "tras", o con 8x8 el de TRASM)
nuevo_tile:
        ld a,(EXT_T8)
        or a
        jr nz,ntt8
        jp propiedad            ; (A = 0: campo "tras")
ntt8:   ld a,(ct_meta)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        call cuarto
        or l
        ld l,a
        ld de,(EXT_TRASM)
        add hl,de
        ld a,(hl)
        ret

; ------------------------------------------------------------
;  PROFUNDIDAD (logica, con el banco de la fase): que celdas de profundidad tapan a cada sprite
;  Lista PRFL: tile, x+16 e y+16 de su origen en pantalla y el rectangulo que hay que redibujar
; ------------------------------------------------------------
profundidad:
        xor a
        ld (prf_n),a
        ld a,(EXT_FLG)
        and 0x10
        ret z
;@ SOLO B C
        jp prf_cuerpo           ; (en el modo de bloques, fuera del motor: solo se carga si hace falta)
;@ FIN
;@ APARTE B 0x7400 C 0x8000
prf_cuerpo:
        ld ix,sprites
        ld a,(n_spr)
        ld b,a
prf1:   push bc
        ld a,(ix+S_ACT)
        or a
        call nz,prf_sprite
        ld de,SLOT
        add ix,de
        pop bc
        djnz prf1
        ret

prf_sprite:
        ld a,(ix+S_X)
        ld (pr_sx),a
        ld (ps_x0),a
        add a,(ix+S_WP)
        dec a
        cp 192
        jr c,psp1
        ld a,191
psp1:   ld (ps_x1),a
        ld a,(ix+S_Y)
        ld (pr_sy),a
        ld (ps_y0),a
        add a,(ix+S_H)
        dec a
        cp ALTO*8
        jr c,psp2
        ld a,ALTO*8-1
psp2:   ld (ps_y1),a
        ld a,(ps_y0)
        ld (ps_py),a
psy:    ld a,(ps_x0)
        ld (ps_px),a
psx:    ld a,(ps_px)
        ld b,a
        ld a,(ps_py)
        ld c,a
        call celda_en           ; A = celda, NZ si es de profundidad
        call nz,prf_celda
        ld a,(ps_cx16)          ; siguiente columna de celdas
        ld hl,csz
        add a,(hl)
        sub 16
        jr c,psx2
        ld hl,ps_x1
        cp (hl)
        jr z,psx3
        jr nc,psx2
psx3:   ld (ps_px),a
        jr psx
psx2:   ld a,(ps_cy16)          ; siguiente fila de celdas
        ld hl,csz
        add a,(hl)
        sub 16
        ret c
        ld hl,ps_y1
        cp (hl)
        jr z,psy3
        ret nc
psy3:   ld (ps_py),a
        jr psy

; celda_en: B = x, C = y -> A = celda, ps_meta, origen de la celda (ps_cx16, ps_cy16) y del tile
; (ps_mx16, ps_my16), con 16 sumado. NZ si la celda es de profundidad
celda_en:
        call dir_mapa
        ld a,(hl)
        ld (ps_meta),a
        call id_celda
        ld (ps_id),a
        ld a,(ct_fx)
        ld e,a
        ld a,b
        add a,16
        sub e
        ld (ps_mx16),a
        ld a,(cmsk)
        and e
        ld e,a
        ld a,b
        add a,16
        sub e
        ld (ps_cx16),a
        ld a,(ct_fy)
        ld e,a
        ld a,c
        add a,16
        sub e
        ld (ps_my16),a
        ld a,(cmsk)
        and e
        ld e,a
        ld a,c
        add a,16
        sub e
        ld (ps_cy16),a
        ld a,(ps_id)
        ld l,a
        ld h,SOLIDOS/256
        bit 7,(hl)
        ret

; prf_busca: A = celda -> HL = su entrada (lineas) en la tabla de profundidad; Z si no esta
prf_busca:
        ld hl,(EXT_PROF)
        ld b,(hl)
        inc hl
        inc b
        dec b
        ret z
pb1:    cp (hl)
        jr z,pb2
        ld de,35
        add hl,de
        djnz pb1
        xor a
        ret
pb2:    inc hl
        or 1
        ret

; prf_celda: (ps_id) de profundidad tocada por el sprite IX en (pr_sx, pr_sy): ¿manda el tile?
prf_celda:
        ld a,(ps_id)
        call prf_busca
        ret z
        ld (pc_l),hl
        bit 7,(hl)              ; linea Tras: si el borde esta por debajo, manda el sprite
        jr z,pce1
        call pc_lado
        jr z,pce1
        ret p
pce1:   ld hl,(pc_l)            ; linea Ante: si el borde esta por debajo o en ella, manda el tile;
        ld de,17                ; si no, el sprite
        add hl,de
        bit 7,(hl)
        jr z,pce_tile
        call pc_lado
        ret m
pce_tile:
        ld a,(prf_n)            ; anade el trozo que hay que redibujar
        cp PRFMAX
        ret nc
        ld l,a
        ld h,0
        ld e,l
        ld d,h
        add hl,hl
        add hl,hl
        add hl,hl
        or a
        sbc hl,de               ; *7
        ld de,PRFL
        add hl,de
        ld a,(ps_meta)
        ld (hl),a
        inc hl
        ld a,(ps_mx16)
        ld (hl),a
        inc hl
        ld a,(ps_my16)
        ld (hl),a
        inc hl
        ld bc,(ps_x0)           ; x: de max(celda, sprite) a min(...)
        ld a,(ps_cx16)
        call pct_rng
        ret c                   ; (vacio)
        ld bc,(ps_y0)
        ld a,(ps_cy16)
        call pct_rng
        ret c
        ld hl,prf_n
        inc (hl)
        ret
; pct_rng: A = origen de la celda (+16), C, B = principio y fin del sprite -> (HL), (HL+1) = el
; trozo comun; HL += 2. C si queda vacio
pct_rng:
        ld d,a
        ld a,c
        add a,16
        cp d
        jr nc,pct1
        ld a,d
pct1:   sub 16
        ld (hl),a
        inc hl
        ld e,a
        ld a,(cmsk)
        add a,d
        ld d,a
        ld a,b
        add a,16
        cp d
        jr c,pct2
        ld a,d
pct2:   sub 16
        ld (hl),a
        inc hl
        cp e
        ret

; pc_lado: HL = linea (opciones y 16 valores), IX = sprite en (pr_sx, pr_sy), celda en
; (ps_cx16, ps_cy16) -> A = distancia con signo del borde del sprite a la linea (positiva: por
; debajo, o a la derecha en los bordes izquierdo y derecho)
pc_lado:
        ld a,(hl)
        ld (pc_op),a
        and 3
        inc hl
        ld c,a
        ld a,(ix+S_WP)          ; punto del borde: abajo o arriba, en el centro
        srl a
        ld e,a
        ld a,(ix+S_H)
        srl a
        ld d,a                  ; D = mitad del alto, E = mitad del ancho
        ld a,c
        cp 2
        jr nc,pcl_lat
        ld a,(pr_sx)
        add a,e
        ld e,a
        ld a,c
        or a
        ld a,(pr_sy)
        jr nz,pcl1
        add a,(ix+S_H)
        dec a
pcl1:   ld d,a                  ; E = x, D = y del punto
        ld a,(ps_cx16)          ; t = x - celda (recortado)
        ld b,a
        ld a,e
        add a,16
        sub b
        call pcl_t
        ld a,(ps_cy16)
        ld b,a
        ld a,d
        add a,16
        sub b                   ; distancia = y - celda - valor
        sub (hl)
        jr pcl_fin
pcl_lat:
        ld a,(pr_sy)            ; izquierdo o derecho, a media altura
        add a,d
        ld d,a
        ld a,c
        cp 2
        ld a,(pr_sx)
        jr z,pcl2
        add a,(ix+S_WP)
        dec a
pcl2:   ld e,a
        ld a,(ps_cy16)
        ld b,a
        ld a,d
        add a,16
        sub b
        call pcl_t
        ld a,(ps_cx16)
        ld b,a
        ld a,e
        add a,16
        sub b
        sub (hl)
pcl_fin:                        ; con el bit 3, el lado se invierte (encima o a la izquierda)
        ld c,a
        ld a,(pc_op)
        and 8
        ld a,c
        jr z,pclf1
        neg
        ret
pclf1:  or a
        ret
; pcl_t: A = posicion en la celda (con signo) -> HL apuntando a su valor (recortada a la celda)
pcl_t:  bit 7,a
        jr z,pclt1
        xor a
pclt1:    push bc
        ld b,a
        ld a,(cmsk)
        cp b
        jr c,pclt2
        ld a,b
pclt2:    pop bc
        add a,l
        ld l,a
        ret nc
        inc h
        ret
;@ FINAPARTE

; ------------------------------------------------------------
;  LINEAS QUE NO SE TRASPASAN: IX = sprite, D = x nueva, E = y nueva -> NZ si cruzaria alguna
;  (se mira la celda del borde antes y despues del paso). Conserva DE
; ------------------------------------------------------------
linea_bloquea:
        ld a,(EXT_FLG)
        and 15
        ret z
;@ SOLO B C
        jp lb_cuerpo
;@ FIN
;@ APARTE B 0x7400 C 0x8000
lb_cuerpo:
        push de
        ld (lb_eds),a
        ld a,d
        ld (lb_nx),a
        ld a,e
        ld (lb_ny),a
        xor a
lb1:    ld (lb_e),a
        ld hl,lb_eds
        srl (hl)
        jr nc,lb_sig
        call lb_borde
        jr nz,lb_fin
lb_sig: ld a,(lb_eds)
        or a
        jr z,lb_fin
        ld a,(lb_e)
        inc a
        jr lb1
lb_fin: pop de
        ret
; lb_borde: borde (lb_e): mira la celda del punto del borde en la posicion nueva y en la vieja
lb_borde:
        ld a,(lb_nx)
        ld (pr_sx),a
        ld a,(lb_ny)
        ld (pr_sy),a
        call lb_punto
        call lb_celda
        ret nz
        ld a,(ix+S_X)
        ld (pr_sx),a
        ld a,(ix+S_Y)
        ld (pr_sy),a
        call lb_punto
lb_celda:                       ; B, C = punto: si su celda tiene una linea de este borde que no se
        call celda_en           ; traspasa y el paso la cruza -> NZ
        ret z
        ld a,(ps_id)
        call prf_busca
        ret z
        call lb_linea
        ret nz
        ld de,17
        add hl,de
lb_linea:                       ; HL = linea
        ld a,(hl)
        bit 7,a
        ret z
        bit 2,a
        ret z
        and 3
        ld b,a
        ld a,(lb_e)
        cp b
        jr z,lbl0
        xor a
        ret
lbl0:   push hl
        ld a,(lb_nx)            ; lado en la posicion nueva
        ld (pr_sx),a
        ld a,(lb_ny)
        ld (pr_sy),a
        call pc_lado
        pop hl
        push hl
        ld c,0
        or a
        jp m,lbl1
        jr z,lbl1
        inc c
lbl1:   push bc
        ld a,(ix+S_X)           ; y en la vieja
        ld (pr_sx),a
        ld a,(ix+S_Y)
        ld (pr_sy),a
        call pc_lado
        pop bc
        pop hl
        ld b,0
        or a
        jp m,lbl2
        jr z,lbl2
        inc b
lbl2:   ld a,b
        xor c
        ret
; lb_punto: (pr_sx, pr_sy) y borde (lb_e) -> B, C = punto del borde del sprite IX
lb_punto:
        ld a,(lb_e)
        cp 2
        jr nc,lbp_lat
        ld b,a
        ld a,(ix+S_WP)
        srl a
        ld hl,pr_sx
        add a,(hl)
        ld e,a
        ld a,(pr_sy)
        dec b
        jr z,lbp1
        add a,(ix+S_H)
        dec a
lbp1:   ld c,a
        ld b,e
        ret
lbp_lat:
        ld b,a
        ld a,(ix+S_H)
        srl a
        ld hl,pr_sy
        add a,(hl)
        ld c,a
        ld a,(pr_sx)
        bit 0,b
        jr z,lbp2
        add a,(ix+S_WP)
        dec a
lbp2:   ld b,a
        ret

; ------------------------------------------------------------
;  PROFUNDIDAD (dibujo): despues de los sprites, los trozos de la lista se vuelven a dibujar con
;  el tile, al pixel (en el anillo o en la pantalla oculta)
; ------------------------------------------------------------
;@ FINAPARTE
restaurar_prof:
        ld a,(prf_n)
        or a
        ret z
;@ SOLO B C
        jp rp_cuerpo
;@ FIN
;@ APARTE B 0x7400 C 0x8000
rp_cuerpo:
        ld b,a
        ld ix,PRFL
rpf1:   push bc
        call rp_uno
        ld de,7
        add ix,de
        pop bc
        djnz rpf1
        ret
rp_uno:
        ld a,(banco_nivel)      ; el dibujo del tile, a memoria comun
        call pon_banco
        ld l,(ix+0)
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(tiles)
        add hl,de
        ld de,PRFG
        ld bc,36
        ldir
        ld a,(bloques)          ; scroll fino o libre: se dibuja en la pantalla oculta
        or a
        jr z,rpu1
        ld a,(base)
        cp 0xC0
        ld a,7
        call z,pon_banco
rpu1:   ld a,(ix+1)
        and 7
        ld (rp_s),a
        ld a,(ix+5)
        ld (rp_y),a
rpy:    ld a,(rp_y)             ; fila del tile
        add a,16
        sub (ix+2)
        add a,a
        ld e,a
        ld d,0
        ld hl,PRFG
        add hl,de
        ld b,(hl)
        inc hl
        ld d,(hl)
        ld e,0                  ; B D E = fila << 8, desplazada s a la derecha
        ld a,(rp_s)
        or a
        jr z,rpy2
rpy1:   srl b
        rr d
        rr e
        dec a
        jr nz,rpy1
rpy2:   push bc
        push de
        ld a,(rp_y)
        call dir_linea          ; HL = linea, columna 0
        pop de
        pop bc
        ld a,(ix+3)             ; columnas de rx0/8 a rx1/8
        rrca
        rrca
        rrca
        and 31
        ld c,a
rpc:    push hl
        ld a,c                  ; byte del tile para esta columna: k = c + 2 - (x+16)/8
        add a,2
        push bc
        ld b,a
        ld a,(ix+1)
        rrca
        rrca
        rrca
        and 31
        neg
        add a,b
        pop bc
        push af
        ld a,c
        add a,l
        ld l,a
        jr nc,rpc0
        inc h
rpc0:   pop af
        push de
        or a
        jr z,rpk0
        dec a
        jr z,rpk1
        ld a,e
        jr rpk
rpk0:   ld a,b
        jr rpk
rpk1:   ld a,d
rpk:    ld (rp_t),a
        ld a,c                  ; mascara: los pixeles de rx0..rx1 en este byte
        add a,a
        add a,a
        add a,a
        ld e,a                  ; E = 8c
        ld a,(ix+3)
        sub e
        jr nc,rpm1
        xor a
rpm1:   push hl
        ld hl,tabla_md
        add a,l
        ld l,a
        jr nc,rpm1b
        inc h
rpm1b:  ld d,(hl)
        ld a,(ix+4)
        sub e
        cp 8
        jr c,rpm2
        ld a,7
rpm2:   ld hl,tabla_mi
        add a,l
        ld l,a
        jr nc,rpm2b
        inc h
rpm2b:  ld a,(hl)
        and d
        pop hl
        ld d,a                  ; D = mascara
        ld a,(rp_t)
        xor (hl)
        and d
        xor (hl)
        ld (hl),a
        pop de
        pop hl
        ld a,(ix+4)
        rrca
        rrca
        rrca
        and 31
        cp c
        jr z,rpc9
        inc c
        jr rpc
rpc9:   ld hl,rp_y
        ld a,(ix+6)
        cp (hl)
        ret z
        inc (hl)
        jp rpy

; atr_prof: con la tinta propia de los personajes, las casillas de los trozos redibujados
; recuperan el color (el del area en el scroll libre; el del cuarto del tile en el fino)
;@ FINAPARTE
;@ SOLO B C
atr_prof:                       ; (solo con personajes de color propio)
        ld a,(C_COLSPR)
        or a
        ret z
        ld a,(prf_n)
        or a
        ret z
;@ SOLO B
        jp ap_cuerpo
;@ FIN
;@ APARTE B 0x7400
ap_cuerpo:
        ld b,a
        ld ix,PRFL
apf1:   push bc
        call ap_uno
        ld de,7
        add ix,de
        pop bc
        djnz apf1
        ret
ap_uno:
;@ SOLO B
        ld a,(banco_nivel)      ; los 4 colores del tile, a PRFG+32
        call pon_banco
        ld l,(ix+0)
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(tiles)
        add hl,de
        ld de,32
        add hl,de
        ld de,PRFG+32
        ld bc,4
        ldir
;@ FIN
        ld a,(base)
        cp 0xC0
        ld a,7
        call z,pon_banco
        ld a,(ix+4)             ; ultima columna: una casilla mas (el color del sprite la cubre
        add a,7                 ; aunque no tenga pixeles), sin salir del tile ni del area
        jr nc,apn1
        ld a,255
apn1:   ld e,a
        ld a,(ix+1)
        dec a
        cp e
        jr nc,apn2
        ld e,a
apn2:   ld a,e
        cp 192
        jr c,apn3
        ld a,191
apn3:   rrca
        rrca
        rrca
        and 31
        ld (rp_t),a
        ld a,(ix+5)
        rrca
        rrca
        rrca
        and 31
        ld c,a                  ; C = fila de casillas
apu1:   push bc
        ld a,(pfila)
        add a,c
        call dir_atr            ; DE = atributo de la fila, columna 0 del area
        ex de,hl
        ld a,(ix+3)
        rrca
        rrca
        rrca
        and 31
        ld b,a
apu2:   push hl
        ld a,b
        add a,l
        ld l,a
        call ap_color
        ld (hl),a
        pop hl
        ld a,(rp_t)
        cp b
        jr z,apu3
        inc b
        jr apu2
apu3:   pop bc
        ld a,(ix+6)
        rrca
        rrca
        rrca
        and 31
        cp c
        ret z
        inc c
        jr apu1
; ap_color: B = columna, C = fila de la casilla -> A = su color
ap_color:
;@ SOLO C
        ld a,(C_ATRC)
        ret
;@ FIN
;@ SOLO V H B D
        push hl
        ld a,c                  ; cuarto de abajo si la casilla empieza 8 o mas px bajo el tile
        add a,a
        add a,a
        add a,a
        add a,16
        sub (ix+2)
        and 8
        rrca
        rrca
        ld l,a
        ld a,b
        add a,a
        add a,a
        add a,a
        add a,16
        sub (ix+1)
        and 8
        rrca
        rrca
        rrca
        or l
        ld l,a
        ld h,0
        ld de,PRFG+32
        add hl,de
        ld a,(hl)
        pop hl
        ret
;@ FIN
;@ FINAPARTE
;@ FIN


tabla_dir:      ; bits: arriba abajo izq dcha
        db 0xFF,2,6,0xFF, 4,3,5,0xFF, 0,1,7,0xFF, 0xFF,0xFF,0xFF,0xFF

;@ SOLO V
; scroll_arriba: sube la vista paso_v pixeles (o lo que quede). CF=1 si se hizo;
; el paso real queda en ultimo_paso
scroll_arriba:
        ld hl,(tpx)
        ld a,h
        or l
        ret z                   ; ya se ve el final del mapa (CF=0)
        push hl
        ld a,(paso_v)
        ld e,a
        ld d,0
        or a
        sbc hl,de
        jr nc,sa1
        ld hl,0
sa1:    ld (tpx),hl
        ex de,hl
        pop hl
        or a
        sbc hl,de
        ld a,l
        ld (ultimo_paso),a
        ld b,a
        ld a,(linea0)
        sub b
        jr nc,sa2
        add a,LINEAS_V
sa2:    ld (linea0),a
sa3:    ld hl,(tpx)             ; ¿hace falta una fila nueva arriba?
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ld de,(r_top)
        or a
        sbc hl,de
        jr nc,sa_fin
        ld hl,(r_top)
        dec hl
        ld (r_top),hl
        ld (fmundo),hl
        ld a,(a_top)
        or a
        jr nz,sa4
        ld a,ANILLO_V
sa4:    dec a
        ld (a_top),a
        ld (anillo),a
        call pintar_fila
        ld hl,(r_bot)           ; si sobran filas, la de abajo se pierde
        ld de,(r_top)
        or a
        sbc hl,de
        ld a,l
        cp ANILLO_V
        jr c,sa3
        ld hl,(r_bot)
        dec hl
        ld (r_bot),hl
        ld a,(a_bot)
        or a
        jr nz,sa5
        ld a,ANILLO_V
sa5:    dec a
        ld (a_bot),a
        jr sa3
sa_fin: call fila_atr
        ld a,(ultimo_paso)
        ld c,a
        ld b,0
        call desplazar_objetos
        scf
        ret

; scroll_abajo (retroceso vertical): CF=1 si se hizo
scroll_abajo:
        ld hl,(tpx)
        ld de,(tmax)
        or a
        sbc hl,de
        ret nc                  ; ya se ve el inicio del mapa
        ld hl,(tmax)            ; paso real = min(paso_v, tmax - tpx)
        ld de,(tpx)
        or a
        sbc hl,de
        ld a,(paso_v)
        ld e,a
        ld d,0
        push hl
        or a
        sbc hl,de
        pop hl
        jr c,sb0
        ld l,e
        ld h,0
sb0:    ld a,l
        ld (ultimo_paso),a
        ld e,a
        ld d,0
        ld hl,(tpx)
        add hl,de
        ld (tpx),hl
        ld a,(linea0)
        add a,e
        cp LINEAS_V
        jr c,sb1
        sub LINEAS_V
sb1:    ld (linea0),a
sb2:    ld hl,(tpx)             ; ¿hace falta una fila nueva abajo?
        ld de,ALTO*8-1
        add hl,de
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ld de,(r_bot)
        or a
        sbc hl,de
        jr z,sb_fin
        jr c,sb_fin
        ld hl,(r_bot)
        inc hl
        ld (r_bot),hl
        ld (fmundo),hl
        ld a,(a_bot)
        inc a
        cp ANILLO_V
        jr c,sb3
        xor a
sb3:    ld (a_bot),a
        ld (anillo),a
        call pintar_fila
        ld hl,(r_bot)
        ld de,(r_top)
        or a
        sbc hl,de
        ld a,l
        cp ANILLO_V
        jr c,sb2
        ld hl,(r_top)
        inc hl
        ld (r_top),hl
        ld a,(a_top)
        inc a
        cp ANILLO_V
        jr c,sb4
        xor a
sb4:    ld (a_top),a
        jr sb2
sb_fin: call fila_atr
        ld a,(ultimo_paso)
        neg
        ld c,a
        ld b,0
        call desplazar_objetos
        scf
        ret

; fila_atr: fila de tiles de la que se toman los colores, (tpx+4)/8; si cambia, se vuelcan
fila_atr:
        ld hl,(tpx)
        ld de,4
        add hl,de
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ld de,(arow)
        or a
        sbc hl,de
        ret z
        add hl,de
        ld (arow),hl
        ld de,(r_top)
        or a
        sbc hl,de
        ld a,(a_top)
        add a,l
        cp ANILLO_V
        jr c,fa1
        sub ANILLO_V
fa1:    ld (a_attr),a
        ld a,2
        ld (cnt_atr),a
        ret

;@ FIN
; modulo: A = HL mod DE (conserva HL)
modulo:
        push hl
md1:    or a
        sbc hl,de
        jr nc,md1
        add hl,de
        ld a,l
        pop hl
        ret

; scroll_dcha: CF=1 si se hizo
scroll_dcha:
        ld a,8
        ld (ultimo_paso),a
        ld a,(paso_h)
        cp 8
        jp c,scroll_dcha_f
;@ SOLO H D
        ld hl,(izq)
        ld de,ANCHO
        add hl,de               ; columna del mundo que entra por la derecha
        ld de,(largo2)
        or a
        sbc hl,de
        ret nc                  ; final del mapa
        add hl,de
        ld (fmundo),hl
        ld hl,(izq)
        inc hl
        ld (izq),hl
        ld a,(c0)
        ld (anillo),a
        inc a
        cp ANCHO
        jr c,sd1
        xor a
sd1:    ld (c0),a
        call pintar_col
        ld bc,0xF800
        call desplazar_objetos
        ld a,2
        ld (cnt_atr),a
        scf
        ret

;@ FIN
; scroll_izq (retroceso horizontal): CF=1 si se hizo
scroll_izq:
        ld a,8
        ld (ultimo_paso),a
        ld a,(paso_h)
        cp 8
        jp c,scroll_izq_f
;@ SOLO H D
        ld hl,(izq)
        ld a,h
        or l
        ret z
        dec hl
        ld (izq),hl
        ld (fmundo),hl
        ld a,(c0)
        or a
        jr nz,si1
        ld a,ANCHO
si1:    dec a
        ld (c0),a
        ld (anillo),a
        call pintar_col
        ld bc,0x0800
        call desplazar_objetos
        ld a,2
        ld (cnt_atr),a
        scf
        ret

; ------------------------------------------------------------
;  PINTAR UNA COLUMNA DE CARACTERES DEL MAPA (modo horizontal)
;  (fmundo) = columna del mundo, (anillo) = columna del bufer (0-23)
;  Se escribe dos veces: en c y en c+24.
; ------------------------------------------------------------
pintar_col:
        push ix
        ld a,(banco_nivel)
        call pon_banco
        ld hl,(fmundo)
        ld a,l
        and 1
        ld (pf_mitad),a
        srl h
        rr l                    ; columna de tiles
        add hl,hl               ; *10 (10 tiles por columna)
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(mapa)
        add hl,de
        ld (pf_mapa),hl
        ld a,(anillo)
        ld e,a
        ld d,0
        ld hl,BUF
        add hl,de
        ld (pf_dst),hl
        ld hl,ABUF
        add hl,de
        ld (pf_adst),hl
        ld b,ALTO/2
pc_tile:
        push bc
        ld hl,(pf_mapa)
        ld a,(hl)
        inc hl
        ld (pf_mapa),hl
        ld l,a                  ; HL = tiles + id*36
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(tiles)
        add hl,de
        push hl
        ld a,(pf_mitad)
        ld e,a
        ld d,0
        add hl,de               ; byte izquierdo o derecho del tile
        ld ix,(pf_dst)
        ld de,ANCHO*2
        ld b,16
pc_lin: ld a,(hl)
        ld (ix+0),a
        ld (ix+ANCHO),a
        inc hl
        inc hl
        add ix,de
        djnz pc_lin
        ld (pf_dst),ix
        pop hl
        ld a,(pf_mitad)         ; atributo superior (32/33) e inferior (34/35)
        add a,32
        ld e,a
        ld d,0
        add hl,de
        ld ix,(pf_adst)
        ld a,(hl)
        ld (ix+0),a
        ld (ix+ANCHO),a
        inc hl
        inc hl
        ld de,ANCHO*2
        add ix,de
        ld a,(hl)
        ld (ix+0),a
        ld (ix+ANCHO),a
        add ix,de
        ld (pf_adst),ix
        pop bc
        djnz pc_tile
        pop ix
        ret

;@ FIN
;@ SOLO H B D C
; ------------------------------------------------------------
;  MODO PLATAFORMAS: gravedad, salto, plataformas y caidas
;  estado_v: 0 en el suelo, 1 subiendo, 2 cayendo
; ------------------------------------------------------------
mover_plataformas:
        ld ix,sprites
        ld a,(entrada_j)
        ld c,a
        xor a                   ; abajo en el suelo: se agacha (y no anda)
        ld (agachado),a
        ld a,(estado_v)
        or a
        jr nz,mp0
        bit 2,c
        jr z,mp0
        ld a,(agacha_ok)
        or a
        jr z,mp0
        ld (agachado),a
        ld a,c
        and 0xFC
        ld c,a
mp0:
        ld a,(C_ACEL)           ; con inercia: la velocidad sube y baja poco a poco
        or a
        jr z,mp0_d
        call inercia
        jr mp2
mp0_d:  bit 0,c                 ; derecha
        jr z,mp1
        ld a,2
        ld (mira_j),a
        ld a,(velocidad)
        push bc
        call mover_x_bloq
        pop bc
        jr mp2
mp1:    bit 1,c                 ; izquierda
        jr z,mp2
        ld a,6
        ld (mira_j),a
        ld a,(velocidad)
        neg
        push bc
        call mover_x_bloq
        pop bc
mp2:    ld a,(estado_v)
        or a
        jr nz,mp_aire
        call hay_suelo          ; en el suelo: ¿sigue habiendo suelo debajo?
        jr nz,mp_suelo
        ld a,2
        ld (estado_v),a
        xor a
        ld (idx_v),a
        jr mp_aire
mp_suelo:
        push bc                 ; punto seguro para reaparecer: solo con los dos pies en suelo firme
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        ld c,a
        ld a,(ix+S_X)
        add a,2
        ld b,a
        call suelo_punto
        jr z,mp_s_no
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        sub 3
        ld b,a
        call suelo_punto
        jr z,mp_s_no
        ld a,(ix+S_X)
        ld (seguro_x),a
        ld a,(ix+S_Y)
        ld (seguro_y),a
;@ SOLO D
        call sala_segura
;@ FIN
mp_s_no:
        pop bc
        bit 3,c                 ; arriba = saltar
        jr z,mp_suelta
        ld a,(salto_listo)      ; hay que soltar la tecla entre salto y salto
        or a
        jr z,mp_fin
        xor a
        ld (salto_listo),a
        ld (idx_v),a
        inc a
        ld (estado_v),a
        xor a
        call sonido
        jr mp_aire
mp_suelta:
        ld a,1
        ld (salto_listo),a
        jr mp_fin
mp_aire:
        ld a,(estado_v)
        cp 1
        jr nz,mp_cae
        bit 3,c                 ; subiendo: al soltar la tecla empieza a caer (salto corto)
        jr z,mp_a_caer
        ld hl,C_SALTO
        ld a,(idx_v)
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jr z,mp_a_caer          ; fin de la subida
        ld hl,idx_v
        inc (hl)
        call subir
        jr nc,mp_fin
mp_a_caer:
        ld a,2
        ld (estado_v),a
        xor a
        ld (idx_v),a
        jr mp_fin
mp_cae: ld hl,C_CAIDA
        ld a,(idx_v)
        ld e,a
        ld d,0
        add hl,de
        ld a,(idx_v)            ; la ultima velocidad de caida se repite
        cp 15
        jr nc,mp_c1
        inc a
        ld (idx_v),a
mp_c1:  ld a,(hl)
        call bajar
        jr nc,mp_fin
        xor a                   ; aterriza
        ld (estado_v),a
mp_fin: call desplazar          ; scroll (como en el modo horizontal)
        ; animacion: andar a izquierda o derecha; en el aire, arriba-dcha o arriba-izq
        ld a,(mira_j)
        ld b,a
        ld a,(estado_v)
        or a
        jr z,mp_an1
        cp 2                    ; cayendo: abajo-dcha (3) o abajo-izq (5)
        jr nz,mp_sube
        ld a,b
        cp 2
        ld a,3
        jr z,mp_an0
        ld a,5
        jr mp_an0
mp_sube:
        ld a,b
        dec a                   ; 2 -> 1 (arriba-dcha), 6 -> 5 ...
        cp 5
        jr nz,mp_an0
        ld a,7                  ; ... que debe ser 7 (arriba-izq)
mp_an0: ld (dir_j),a
        jr mp_anda
mp_an1: ld a,b
        ld (dir_j),a
        ld a,(entrada_j)
        and 3
        jr nz,mp_anda
        ld a,1                  ; parado en el suelo: reposo
        ld (quieto_j),a
        ret
mp_anda:
        xor a
        ld (quieto_j),a
        jp anim_paso

; hay_suelo: NZ si bajo los pies del jugador (IX) hay suelo solido o una plataforma
hay_suelo:
        push bc
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        cp ALTO*8
        jr nc,hs_no             ; borde inferior del area: vacio
        ld c,a
        call fila_flags
        ld b,a
        and 1
        jr nz,hs_si
        ld a,b
        and 4
        jr z,hs_ln
        ld a,(cmsk)             ; plataforma: solo cuenta su borde superior (y del mundo)
        ld hl,ct_fy
        and (hl)
        jr z,hs_si
hs_ln:  ld d,(ix+S_X)           ; ¿una linea de profundidad que no se traspasa?
        ld a,(ix+S_Y)
        inc a
        ld e,a
        call linea_bloquea
        jr nz,hs_si
hs_no:  pop bc
        xor a
        ret
hs_si:  pop bc
        or 1
        ret

; suelo_punto: B = x, C = y. NZ si en ese punto hay suelo solido o el borde superior de una plataforma
suelo_punto:
        call flags_en
        ld d,a
        and 1
        ret nz
        ld a,d
        and 4
        ret z
        ld a,(cmsk)
        ld hl,ct_fy
        and (hl)
        jr nz,sp_no
        or 1
        ret
sp_no:  xor a
        ret

; fila_flags: C = fila (px). OR de las propiedades bajo el ancho del sprite IX (reducido 2 px)
fila_flags:
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        sub 3
        ld (ff_fin),a
        ld a,(ix+S_X)
        add a,2
        ld b,a
        xor a
        ld (ff_acc),a
ff1:    call flags_en
        ld hl,ff_acc
        or (hl)
        ld (hl),a
        ld a,(ff_fin)
        cp b
        jr z,ff_fin2
        ld a,b
ffs1:   add a,15
        ld b,a
        ld a,(ff_fin)
        cp b
        jr nc,ff1
        ld b,a
        jr ff1
ff_fin2:
        ld a,(ff_acc)
        ret

; bajar: A = pixeles. Baja de uno en uno; CF=1 si aterriza. Si llega al fondo sin suelo, pierde una vida
bajar:
        push bc
        ld (n_pasos),a
ba1:    call hay_suelo
        jr nz,ba_suelo
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        cp ALTO*8
        jr nc,ba_vacio
        ld d,(ix+S_X)           ; (una linea que no se traspasa sostiene)
        ld a,(ix+S_Y)
        inc a
        ld e,a
        call linea_bloquea
        jr nz,ba_ln
        inc (ix+S_Y)
        ld hl,n_pasos
        dec (hl)
        jr nz,ba1
        pop bc
        or a
        ret
ba_suelo:
        ld a,(ix+S_Y)           ; tile fragil bajo los pies: se rompe y el jugador rebota
        add a,(ix+S_H)
        ld c,a
        ld a,(ix+S_WP)
        srl a
        add a,(ix+S_X)
        ld b,a
        call flags_en
        and R_FRAG
        jr z,bs1
        push ix
        call cambiar_tile
        pop ix
        call rebote
        pop bc
        or a
        ret
bs1:    pop bc
        scf
        ret
ba_ln:  pop bc
        scf
        ret
ba_vacio:
;@ SOLO D
        call sala_abajo
        jr nz,ba1
;@ FIN
        pop bc
        call caer_vacio
        or a
        ret

; subir: A = pixeles. Sube de uno en uno; CF=1 si toca techo (tile solido o borde superior)
subir:
        push bc
        ld (n_pasos),a
su1:    ld a,(ix+S_Y)
        or a
;@ SOLO D
        call z,sala_arriba
;@ FIN
        jr z,su_techo
        dec a
        ld c,a
        call fila_flags
        and 1
        jr nz,su_techo
        ld d,(ix+S_X)
        ld a,(ix+S_Y)
        dec a
        ld e,a
        call linea_bloquea
        jr nz,su_techo
        dec (ix+S_Y)
        ld hl,n_pasos
        dec (hl)
        jr nz,su1
        pop bc
        or a
        ret
su_techo:
        ld a,(ix+S_Y)           ; cabezazo: rompe el tile rompible de encima
        or a
        jr z,st1
        dec a
        ld c,a
        ld a,(ix+S_WP)
        srl a
        add a,(ix+S_X)
        ld b,a
        push ix
        call romper_en
        pop ix
st1:    pop bc
        scf
        ret

; caer_vacio: el jugador cae fuera del area: pierde una vida y reaparece en el ultimo punto seguro
caer_vacio:
        ld a,(seguro_x)         ; animacion de muerte; reaparece en el ultimo sitio seguro
        ld b,a
        ld a,(seguro_y)
        ld c,a
        ld hl,vidas
        ld a,(hl)
        dec a
        ld a,0
        jr nz,cv0
        inc a
cv0:    call morir
        ld a,2
        out (0xFE),a
        ld (cnt_hud),a
        ld hl,golpes
        inc (hl)
        ld hl,vidas
        dec (hl)
        jr z,cv_fin
        ld a,(C_ENER)
        ld (energia),a
        ld a,50
        ld (invul),a
        ld a,(seguro_x)
        ld (ix+S_X),a
        ld a,(seguro_y)
        ld (ix+S_Y),a
        xor a
        ld (estado_v),a
;@ SOLO D
        jp volver_sala          ; (el punto seguro puede estar en otra sala)
;@ FIN
        ret
cv_fin: ld a,(muerte)            ; con animacion, la partida acaba cuando termina
        or a
        ret nz
        ld a,1
        ld (evento),a
        ret

; c_patrulla_suelo: camina sobre el suelo y da la vuelta en paredes y bordes
c_patrulla_suelo:
        ld a,(ix+S_DX)
        or a
        ret z
        bit 7,a
        ld a,(ix+S_X)
        jr nz,cps_i
        add a,(ix+S_WP)         ; columna justo delante del pie
        jr cps_c
cps_i:  or a
        jr z,cps_vuelta
        dec a
cps_c:  ld b,a
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        cp ALTO*8
        jr nc,cps_vuelta
        ld c,a
        call flags_en           ; ¿hay suelo delante?
        and 5
        jr z,cps_vuelta
        ld a,(ix+S_DX)
        call mover_x_bloq
        ret z
cps_vuelta:
        ld a,(ix+S_DX)
        neg
        ld (ix+S_DX),a
        ret

;@ FIN
; ------------------------------------------------------------
;  COLISIONES CON EL MAPA (banco 0 paginado)
; ------------------------------------------------------------
;@ SOLO V H B D
; flags_en: B = x, C = y (pixeles del area) -> A = propiedades de su celda (conserva BC)
flags_en:
        call dir_mapa
        ld a,(hl)
        call id_celda
        ld l,a
        ld h,SOLIDOS/256
        ld a,(hl)
        ret

;@ FIN
; caja_de: IX = sprite, D = x, E = y -> caja reducida 2 px por cada lado
caja_de:
        ld a,d
        add a,2
        ld (cx0),a
        ld a,d
        add a,(ix+S_WP)
        sub 3
        ld (cx1),a
        ld a,e
        add a,2
        ld (cy0),a
        ld a,e
        add a,(ix+S_H)
        sub 3
        ld (cy1),a
        ret

; caja_bloqueada: recorre la caja (cx0..cx1, cy0..cy1) cada 15 px
; NZ si algun punto tiene alguna propiedad de (cmask)
caja_bloqueada:
        ld a,(cy0)
        ld (py),a
cb_y:   ld a,(cx0)
        ld (px),a
cb_x:   ld a,(px)
        ld b,a
        ld a,(py)
        ld c,a
        call flags_en
        ld hl,cmask
        and (hl)
        ret nz
        ld hl,cx1
        ld a,(px)
        cp (hl)
        jr z,cb_xf
cbs1:   add a,15
        cp (hl)
        jr c,cb_x2
        ld a,(hl)
cb_x2:  ld (px),a
        jr cb_x
cb_xf:  ld hl,cy1
        ld a,(py)
        cp (hl)
        ret z                   ; Z: libre
cbs2:   add a,15
        cp (hl)
        jr c,cb_y2
        ld a,(hl)
cb_y2:  ld (py),a
        jr cb_y

; bloqueado_en: IX, D = x, E = y, A = mascara -> NZ si choca
bloqueado_en:
        ld (cmask),a
        call caja_de
        jp caja_bloqueada

;@ SOLO H B D C
; inercia: C = teclas. Acelera hacia la tecla pulsada hasta la velocidad del jugador
; (en 1/16 px: velocidad*16) y, sin tecla, frena hasta pararse. Mueve la parte entera.
inercia:
        ld a,(velocidad)        ; D = maximo
        add a,a
        add a,a
        add a,a
        add a,a
        ld d,a
        ld a,(vx)
        bit 0,c
        jr z,in1
        ld e,a                  ; derecha
        ld a,2
        ld (mira_j),a
        ld a,(C_ACEL)
        add a,e
        bit 7,a
        jr nz,in_v
        cp d
        jr c,in_v
        ld a,d
        jr in_v
in1:    bit 1,c
        jr z,in3
        ld e,a                  ; izquierda
        ld a,6
        ld (mira_j),a
        ld a,(C_ACEL)
        neg
        add a,e
        bit 7,a
        jr z,in_v
        neg
        cp d
        jr c,in2
        ld a,d
in2:    neg
        jr in_v
in3:    ld e,a                  ; sin tecla: frena
        or a
        jr z,in_v
        ld a,(C_FRENO)
        bit 7,e
        jr nz,in4
        neg
        add a,e                 ; vx - freno; si cruza el cero, se para
        jr c,in_v
        xor a
        jr in_v
in4:    add a,e                 ; vx + freno
        jr nc,in_v
        xor a
in_v:   ld (vx),a
        ld hl,vfrac             ; avance = (fraccion + vx) / 16
        add a,(hl)
        ld e,a
        and 15
        ld (hl),a
        ld a,e
        sra a
        sra a
        sra a
        sra a
        or a
        ret z
        push bc
        call mover_x_bloq
        pop bc
        ret z
        xor a                   ; choca: se para
        ld (vx),a
        ld (vfrac),a
        ret

;@ FIN
; mover_x_bloq: IX, A = dx con signo (no 0). Mueve si puede.
; Z = se ha movido, NZ = bloqueado (borde o tile solido)
mover_x_bloq:
        ld c,a
        add a,(ix+S_X)
        bit 7,c
        jr z,mxb_p
        jr nc,mxb_no            ; se saldria por la izquierda
        jr mxb_ok
mxb_p:  ld d,a
        ld a,(ix+S_WP)
        neg
        add a,192
        cp d
        jr c,mxb_no             ; se saldria por la derecha
        ld a,d
mxb_ok: ld d,a
        ld e,(ix+S_Y)
        push de
        call caja_de
        bit 7,c                 ; solo hace falta mirar el borde que avanza
        jr nz,mxb_i
        ld a,(cx1)
        ld (cx0),a
        jr mxb_c
mxb_i:  ld a,(cx0)
        ld (cx1),a
mxb_c:  ld a,1
        ld (cmask),a
        call caja_bloqueada
        pop de
        ret nz
        call linea_bloquea
        ret nz
        ld (ix+S_X),d
        xor a
        ret
mxb_no: or 1
        ret

; mover_y_bloq: igual que mover_x_bloq en vertical
mover_y_bloq:
        ld c,a
        add a,(ix+S_Y)
        bit 7,c
        jr z,myb_p
        jr nc,myb_no
        jr myb_ok
myb_p:  ld e,a
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        cp e
        jr c,myb_no
        ld a,e
myb_ok: ld e,a
        ld d,(ix+S_X)
        push de
        call caja_de
        bit 7,c
        jr nz,myb_a
        ld a,(cy1)
        ld (cy0),a
        jr myb_c
myb_a:  ld a,(cy0)
        ld (cy1),a
myb_c:  ld a,1
        ld (cmask),a
        call caja_bloqueada
        pop de
        ret nz
        call linea_bloquea
        ret nz
        ld (ix+S_Y),e
        xor a
        ret
myb_no: or 1
        ret

; ------------------------------------------------------------
;  SCROLL HORIZONTAL FINO POR BLOQUES PRE-DESPLAZADOS (paso 1, 2 o 4)
;  Tecnica de Cobra y Stormlord: el fondo se redibuja entero en cada
;  fotograma copiando bloques de 8x16 ya desplazados. Cada bloque es una
;  "pareja" de medias columnas de tile vecinas (izquierda, derecha) en una
;  de sus posiciones de desplazamiento; el generador las prepara todas.
;  El coste no depende del desplazamiento: cadencia constante y el fondo
;  puede seguir al jugador pixel a pixel.
;  Memoria: PARES 0x6000-0x79FF (bloques), SCRATCH 0x7A00 (sprite en curso),
;  TPAR 0x7C00/0x7D00 (direccion de cada pareja), VENT 0x8000 (parejas
;  visibles, 10 x 24), PATR 0x8700-0x8AFF (colores: 4 tablas de 256).
; ------------------------------------------------------------
PARES   equ 0x6000
SCRATCH equ 0x7A00
TPARL   equ 0x7C00
TPARH   equ 0x7D00
VENT    equ 0x8000
PATR    equ 0x8700          ; 4 paginas: arriba/abajo de la columna izquierda y de la derecha
; (0x7A00-0x7BFF: version del sprite en curso, hasta 32 x 32 = 320 bytes)
SUCIO5  equ 0x8100          ; casillas con algo dibujado en la pantalla 5 (10 x 24)
SUCIO7  equ 0x8200          ; y en la 7. La pareja 0 es "vacio + vacio": no se dibuja nunca
SUCF5   equ 0x82F0          ; filas de tiles con alguna casilla sucia (10 bytes) en la pantalla 5
SUCF7   equ 0x8300          ; y en la 7
VCNT    equ 0x8310          ; casillas no vacias de cada fila de la ventana (10 bytes)
RF5     equ 0x8320          ; filas cuyos colores en la pantalla 5 no son todos los del vacio (10 bytes)
RF7     equ 0x8330          ; y en la 7

;@ SOLO B
; prepara el modo bloques al empezar la fase
ini_bloques:
        ld a,(C_NVAC)           ; parejas sin pixeles: no cuentan como contenido ni se dibujan
        ld (rb_k+1),a
        ld (inv_k+1),a
        ld (ajc_k+1),a
        ld a,3                  ; bloques y colores desde el banco 3
        call pon_banco
        ld hl,(C_PARES)
        ld de,PARES
        ld bc,(C_PARLEN)
        ldir
        ld hl,(C_PATR)          ; colores: 4 tablas de C_NPAR bytes, cada una en su pagina
        ld de,PATR
        ld b,4
cpa1:   push bc
        push de
        ld a,(C_NPAR)
        ld c,a
        ld b,0
        ldir
        pop de
        inc d
        pop bc
        djnz cpa1
inb1:    ld a,(C_V16)            ; bytes por pareja: datos (16 x versiones) ...
        ld l,a
        ld h,0
        ld a,(C_COMP)
        or a
        jr z,inb1b
        ld a,(C_LCOMP)          ; ... o compilados: C_LCOMP bytes x (8 / paso) versiones
        ld e,a
        ld d,0
        ld hl,0
        ld a,(paso_h)
        ld b,a
        ld a,8
inb1a:  add hl,de
        sub b
        jr nz,inb1a
inb1b:  ld (par_tam),hl
        ld hl,PARES             ; TPAR[k] = PARES + k * bytes por pareja
        ld b,0
inb2:    push hl
        ld e,l
        ld d,h
        ld l,b
        ld h,TPARL/256
        ld (hl),e
        inc h
        ld (hl),d
        pop hl
        ld de,(par_tam)
        add hl,de
        inc b
        jr nz,inb2
        ld a,(banco_nivel)      ; parejas visibles: columnas izq .. izq+23
        call pon_banco
        ld b,0
inb3:    push bc
        ld a,b
        ld (vc_pos),a
        ld hl,(izq)
        ld e,b
        ld d,0
        add hl,de
        call cargar_col_par
        pop bc
        inc b
        ld a,b
        cp ANCHO
        jr nz,inb3
        ld b,0x40               ; tablas de lineas de pantalla para los sprites (pantallas 5 y 7)
        ld hl,LTAB
        call ltab_pantalla
        ld b,0xC0
        call ltab_pantalla
        ld hl,SUCIO5            ; al empezar, todo sucio en las dos pantallas (casillas y filas)
        ld de,SUCIO5+1
        ld bc,0x023F
        ld (hl),1
        ldir
        ld ix,VENT              ; recuento de casillas no vacias por fila
        ld hl,VCNT
        ld c,ALTO/2
inv1:   ld b,ANCHO
        ld (hl),0
inv2:   ld a,(ix+0)
inv_k:  cp 1
        jr c,inv3
        inc (hl)
inv3:   inc ix
        djnz inv2
        inc hl
        dec c
        jr nz,inv1
        ld a,2
        ld (cnt_atr),a
        ld hl,rb_cb             ; con color en los personajes, las casillas que se redibujan
        call parchea            ; recuperan tambien su color
        ld hl,rb_cc
        call parchea
        ld hl,rb_cd             ; (sigue en parchea)

; parchea: HL = sitio de 3 bytes. Pone "call rest_atr" o, sin color propio, "jp" a la siguiente
parchea:
        ld a,(C_COLSPR)
        or a
        ld de,rest_atr
        ld a,0xCD
        jr nz,pch1
        ld d,h
        ld e,l
        inc de
        inc de
        inc de
        ld a,0xC3
pch1:   ld (hl),a
        inc hl
        ld (hl),e
        inc hl
        ld (hl),d
        ret

; rest_atr: devuelve a una casilla (8 x 16) el color de su pareja. A = pareja (se conserva),
; B y C = byte bajo de sus dos filas de caracteres. Usa HL y DE
rest_atr:
        ld l,a
ra_pg:  ld h,PATR/256
        ld e,(hl)
        inc h
        ld d,(hl)
ra_h0:  ld h,0
        ld l,b
        ld (hl),e
ra_h1:  ld h,0
        ld l,c
        ld (hl),d
        ret

;@ FIN
;@ SOLO B C
; pintar_atrs: cada personaje con color propio tine sus casillas de caracter en la pantalla oculta
pintar_atrs:
        ld a,(C_COLSPR)
        or a
        ret z
        ld a,(base)
        cp 0xC0
        ld a,7
        call z,pon_banco
        ld ix,sprites
        ld a,(n_spr)
        ld b,a
pas1:   push bc
        ld a,(ix+S_ACT)
        or a
        call nz,pintar_atr
        ld de,SLOT
        add ix,de
        pop bc
        djnz pas1
        ret

pintar_atr:
        ld a,(ix+S_COLOR)
        or a
        ret z
        ld (pa_col+1),a
        ld a,(ix+S_Y)           ; filas de caracter de y a y+h-1
        rrca
        rrca
        rrca
        and 31
        ld c,a
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        dec a
        rrca
        rrca
        rrca
        and 31
        sub c
        inc a
        ld b,a
        ld a,(ix+S_X)
        rrca
        rrca
        rrca
        and 31
        ld (pa_c0+1),a
pa_f:   push bc
        ld a,(pfila)
        add a,c
        call dir_atr            ; DE = atributo de la fila, columna 0 del area
        ex de,hl
pa_c0:  ld a,0
        ld e,a
        add a,l
        ld l,a
        ld a,(ix+S_W)
        inc a
        ld b,a
pa_k:   ld a,e
        cp ANCHO
        jr nc,pa_s
        ld a,(hl)
        and 0x38                ; conserva el papel; tinta y brillo del personaje
pa_col: or 0
        ld (hl),a
pa_s:   inc l
        inc e
        djnz pa_k
        pop bc
        inc c
        ld a,c
        cp ALTO
        ret nc
        djnz pa_f
        ret

;@ FIN
;@ SOLO B C
; ltab_pantalla: B = byte alto de la pantalla, HL = destino. 160 direcciones de linea del area
ltab_pantalla:
        ld a,(pfila)
        add a,a
        add a,a
        add a,a
        ld c,a                  ; C = linea de pantalla
        ld e,160
lp1:    ld a,c                  ; direccion = base | linea | columna
        and 0xC0
        rrca
        rrca
        rrca
        ld d,a
        ld a,c
        and 7
        or d
        or b
        inc hl
        ld (hl),a
        dec hl
        ld a,c
        and 0x38
        add a,a
        add a,a
        ld d,a
        ld a,(pcol)
        or d
        ld (hl),a
        inc hl
        inc hl
        inc c
        dec e
        jr nz,lp1
        ret
;@ FIN
;@ SOLO B

; cargar_col_par: HL = columna del mundo (caracteres), (vc_pos) = columna de VENT (0-23).
; Copia sus 10 parejas desde el mapa de parejas de la fase (banco de la fase paginado).
cargar_col_par:
        ld de,(largo2)          ; se recorta al mapa
        push hl
        or a
        sbc hl,de
        pop hl
        jr c,ccp1
        ld hl,(largo2)
        dec hl
ccp1:   add hl,hl               ; *10
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(N_PARMAP)
        add hl,de
        ld a,(vc_pos)
        ld e,a
        ld d,0
        ld ix,VENT
        add ix,de
        ld de,ANCHO
        ld b,ALTO/2
ccp2:   ld a,(hl)
        ld (ix+0),a
        inc hl
        add ix,de
        djnz ccp2
        ret

; scroll_dcha_f: avanza paso_h pixeles. CF=1 si se hizo
scroll_dcha_f:
        ld a,(fino)
        or a
        jr nz,sdf1
        ld hl,(largo2)          ; alineado y en el final del mapa: no hay mas
        ld de,ANCHO
        or a
        sbc hl,de
        ld de,(izq)
        or a
        sbc hl,de
        ret z
sdf1:   ld a,(paso_h)
        ld (ultimo_paso),a
        ld b,a
        ld a,(fino)
        add a,b
        cp 8
        jr c,sdf2
        xor a                   ; nueva columna por la derecha
        ld (fino),a
        ld hl,(izq)
        inc hl
        ld (izq),hl
        push ix
        xor a                   ; sale la columna 0 de la ventana
        ld e,-1
        call ajustar_cnt
        ld hl,VENT+1
        ld de,VENT
        ld bc,ALTO/2*ANCHO-1
        ldir
        ld a,ANCHO-1
        ld (vc_pos),a
        ld hl,(izq)
        ld de,ANCHO-1
        add hl,de
        call cargar_col_par
        ld a,ANCHO-1            ; entra la columna 23
        ld e,1
        call ajustar_cnt
        pop ix
        call colores_cambian
        jr sdf3
sdf2:   ld (fino),a
        cp 4                    ; el color cambia de columna a mitad de camino
        call z,colores_mitad
sdf3:   ld a,(ultimo_paso)
        neg
        ld b,a
        ld c,0
        call desplazar_objetos
        scf
        ret

; scroll_izq_f (retroceso): CF=1 si se hizo
scroll_izq_f:
        ld a,(fino)
        or a
        jr nz,sif1
        ld hl,(izq)
        ld a,h
        or l
        ret z
sif1:   ld a,(paso_h)
        ld (ultimo_paso),a
        ld b,a
        ld a,(fino)
        sub b
        jr nc,sif2
        add a,8                 ; nueva columna por la izquierda
        ld (fino),a
        ld hl,(izq)
        dec hl
        ld (izq),hl
        push ix
        ld a,ANCHO-1            ; sale la columna 23
        ld e,-1
        call ajustar_cnt
        ld hl,VENT+ALTO/2*ANCHO-2
        ld de,VENT+ALTO/2*ANCHO-1
        ld bc,ALTO/2*ANCHO-1
        lddr
        xor a
        ld (vc_pos),a
        ld hl,(izq)
        call cargar_col_par
        xor a                   ; entra la columna 0
        ld e,1
        call ajustar_cnt
        pop ix
        call colores_cambian
        jr sif3
sif2:   ld (fino),a
        ld b,a
        ld a,(paso_h)
        add a,b                 ; desplazamiento anterior
        cp 4
        jr c,sif3
        ld a,b
        cp 4
        call c,colores_mitad
sif3:   ld a,(ultimo_paso)
        ld b,a
        ld c,0
        call desplazar_objetos
        scf
        ret

; ajustar_cnt: A = columna de la ventana, E = +1 o -1. Suma E al recuento de cada fila
; en la que esa columna no esta vacia
ajustar_cnt:
        ld c,a
        ld b,0
        ld ix,VENT
        add ix,bc
        ld hl,VCNT
        ld b,ALTO/2
        ld c,ANCHO
ajc1:   ld a,(ix+0)
ajc_k:  cp 1
        jr c,ajc2
        ld a,(hl)
        add a,e
        ld (hl),a
ajc2:   push bc
        ld b,0
        add ix,bc
        pop bc
        inc hl
        djnz ajc1
        ret

colores_mitad:
        ld a,(C_MITAD)
        or a
        ret z
colores_cambian:
        ld a,(C_MONO)
        or a
        ret nz
        ld a,2
        ld (cnt_atr),a
        ret

; dib_compilado: el sprite es codigo Z80 en el banco 7 (zona libre tras la pantalla). Con el banco 7
; paginado, ese codigo puede escribir tanto en la pantalla 5 (0x4000) como en la 7 (0xC000).
; Entra en el codigo con HL = primera linea del sprite en pantalla y C = su byte bajo.
dib_compilado:
        call sprite_ensucia
        ld a,7
        call pon_banco
        ld l,(ix+S_FR)          ; descriptor: 4 direcciones, una por desplazamiento (0, 2, 4, 6)
        ld h,(ix+S_FR+1)
        ld a,(ix+S_X)
        rrca
        and 3
        add a,a
        ld e,a
        ld d,0
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (dc_call+1),de
        ld l,(ix+S_Y)           ; linea de pantalla (tabla con la columna del area incluida)
        ld h,0
        add hl,hl
        ld de,(ltab_act)
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(ix+S_X)
        rrca
        rrca
        rrca
        and 31
        add a,e
        ld l,a
        ld h,d
        ld c,l
dc_call:
        call 0
        ret

; sprite_nl: siguiente linea de pantalla para los sprites compilados. HL = linea actual
; (cualquier columna), C = byte bajo del principio de la linea. Devuelve HL al principio
; de la siguiente y C actualizado.
sprite_nl:
        inc h
        ld a,h
        and 7
        jr nz,snl1
        ld a,c
        add a,32
        ld c,a
        jr c,snl1
        ld a,h
        sub 8
        ld h,a
snl1:   ld l,c
        ret

; sprite_ensucia: modo bloques. Marca como sucias, en la pantalla oculta, las casillas
; (8 x 16) que toca el sprite IX, para que en su proxima vez se borren o redibujen
sprite_ensucia:
        ld a,(bloques)
        or a
        ret z
        push bc
        push de
        push hl
        ld hl,SUCIO5
        ld de,SUCF5
        ld a,(base)
        cp 0x40
        jr z,se1
        ld hl,SUCIO7
        ld de,SUCF7
se1:    ld (se_sf),de
        ld a,(ix+S_Y)           ; filas de tiles de y a y+h-1
        rrca
        rrca
        rrca
        rrca
        and 15
        ld (se_f0),a
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        dec a
        rrca
        rrca
        rrca
        rrca
        and 15
        ld (se_f1),a
        ld a,(ix+S_X)           ; columnas de x a x+w*8+7 (incluye el byte de desplazamiento)
        rrca
        rrca
        rrca
        and 31
        ld (se_c0),a
        ld a,(ix+S_W)
        ld c,a                  ; columnas = w + 1
        inc c
        ld a,(se_f0)
se2:    push af                 ; para cada fila de tiles
        push hl
        ld hl,(se_sf)           ; fila sucia
        ld e,a
        ld d,0
        add hl,de
        ld (hl),1
        pop hl
        push hl
        ld e,a                  ; HL += fila*24 + c0
        add a,a
        add a,e
        add a,a
        add a,a
        add a,a
        ld e,a
        ld d,0
        add hl,de
        ld a,(se_c0)
        ld e,a
        add hl,de
        ld b,c
se3:    ld a,(se_c0)            ; sin salirse del area (24 columnas)
        add a,c
        sub b
        cp ANCHO
        jr nc,se4
        ld (hl),2
se4:    inc hl
        djnz se3
        pop hl
        pop af
        ld e,a
        ld a,(se_f1)
        cp e
        ld a,e
        jr z,se5
        inc a
        jr se2
se5:    pop hl
        pop de
        pop bc
        ret

; render_bloques: dibuja el fondo entero en la pantalla oculta (base) a partir de los bloques
render_bloques:
        ld a,(fino)             ; desplazamiento dentro de cada pareja: (fino / paso) * 16
        ld b,a
        ld a,(paso_h)
        ld c,a
        xor a
rb0:    ld e,a                  ; division por resta (fino < 8)
        ld a,b
        sub c
        jr c,rb0b
        ld b,a
        ld a,e
        add a,16
        jr rb0
rb0b:   ld a,e
        ld (rb_off+1),a
        rrca                    ; v = desplazamiento / 16
        rrca
        rrca
        rrca
        and 15
        ld b,a                  ; version compilada: v * C_LCOMP (v <= 7)
        ld hl,0
        ld a,(C_LCOMP)
        ld e,a
        ld d,0
        inc b
        jr rb0v
rb0u:   add hl,de
rb0v:   djnz rb0u
        ld e,0                  ; modo mezcla: la pantalla 7 usa los bloques B
        ld a,(base)
        cp 0xC0
        jr nz,rbm1
        ld a,(C_MEZCLA)
        ld e,a
rbm1:   ld a,e
        ld (rb_dh+1),a
        add a,h
        ld h,a
        ld (rb_offc+1),hl
        ld a,(fino)             ; pagina de colores para rest_atr (como en rb_colores)
        cp 4
        ld a,PATR/256
        jr c,rbm2
        add a,2
rbm2:   ld (ra_pg+1),a
        ld hl,rb_dibd           ; datos o compilados
        ld a,(C_COMP)
        or a
        jr z,rb0z
        ld hl,rb_dibc
rb0z:   ld (rb_dib+1),hl
        ld de,SUCIO5            ; registros alternativos: HL' = parejas visibles, DE' = registro de
        ld a,(base)             ; casillas sucias de la pantalla oculta, B' = columnas que quedan
        cp 0x40
        jr z,rb0c
        ld de,SUCIO7
rb0c:   ld hl,VENT
        exx
        ld hl,SUCF5             ; filas sucias de la pantalla oculta
        ld a,(base)
        cp 0x40
        jr z,rb0d
        ld hl,SUCF7
rb0d:   ld (rb_sf),hl
        ld hl,VCNT
        ld (rb_vc),hl
        ld a,(pfila)
        ld (rb_fila),a
        ld a,ALTO/2
        ld (rb_n),a
rb_tile:
        ld hl,(rb_vc)           ; fila sin contenido y sin nada que borrar: se salta entera
        ld a,(hl)
        ld hl,(rb_sf)
        or (hl)
        jr nz,rb_t0
        exx
        ld bc,ANCHO
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl
        exx
        jp rb_tsig
rb_t0:  ld hl,(rb_vc)           ; tras dibujarla, queda sucia si tiene contenido
        ld a,(hl)
        or a
        jr z,rb_t1
        ld a,1
rb_t1:  ld hl,(rb_sf)
        ld (hl),a
        ld a,(C_COLSPR)         ; color propio: filas de atributos de este tile
        or a
        jr z,rb_t2
        ld a,(rb_fila)
        call dir_atr
        ld a,d
        ld (ra_h0+1),a
        ld a,(rb_fila)
        inc a
        call dir_atr
        ld a,d
        ld (ra_h1+1),a
rb_t2:  ld a,(rb_fila)          ; filas de pantalla de este tile: R y R+1
        call dir_fila           ; DE = direccion de la fila A (con base y pcol)
        ld a,d
        ld (rb_d0+1),a
        ld (rb_v0+1),a
        ld (rb_c0+1),a
        ld b,e
        ld a,(rb_fila)
        inc a
        call dir_fila
        ld a,d
        ld (rb_d1+1),a
        ld (rb_v1+1),a
        ld (rb_c1+1),a
        ld c,e
        exx
        ld b,ANCHO
rb_celda:                       ; (registros alternativos activos)
        ld a,(hl)               ; pareja
        inc hl
rb_k:   cp 1                    ; parejas con pixeles: desde C_NVAC (parcheado al empezar la fase)
        jr nc,rb_dib
        ld a,(de)               ; vacia: solo hay que borrar si estaba sucia
        or a
        jr nz,rb_borra
        inc de
rb_sig: exx
        inc b
        inc c
        exx
        djnz rb_celda
        exx
rb_tsig:
        ld hl,(rb_vc)
        inc hl
        ld (rb_vc),hl
        ld hl,(rb_sf)
        inc hl
        ld (rb_sf),hl
        ld hl,rb_fila
        inc (hl)
        inc (hl)
        ld hl,rb_n
        dec (hl)
        jp nz,rb_tile
        jp rb_colores
rb_borra:
        xor a
        ld (de),a
        inc de
        exx
rb_v0:  ld d,0
        ld e,b
        rept 7
        ld (de),a
        inc d
        endm
        ld (de),a
rb_v1:  ld d,0
        ld e,c
        rept 7
        ld (de),a
        inc d
        endm
        ld (de),a
        exx                     ; la pareja (puede ser una sin pixeles pero con color)
        dec hl
        ld a,(hl)
        inc hl
        exx
rb_cb:  call rest_atr               ; (parcheado al empezar la fase)
        exx
        jp rb_sig
rb_dib: jp rb_dibd               ; (se elige al empezar: datos o compilados)
rb_dibc:                        ; --- bloque compilado ---
        ex af,af'
        ld a,(de)               ; 2 = la toco un personaje: hay que devolverle el color
        cp 2
        ld a,1
        ld (de),a
        inc de
        jr nz,rbc_n
        ex af,af'
        exx
rb_cc:  call rest_atr               ; (parcheado al empezar la fase)
        jr rbc_x
rbc_n:  ex af,af'
        exx
rbc_x:
        ld l,a                  ; HL = codigo de la pareja
        ld h,TPARL/256
        ld a,(hl)
        inc h
        ld h,(hl)
        ld l,a
rb_offc:
        ld de,0                 ; + version * 50
        add hl,de
        ld (rb_call+1),hl
rb_c0:  ld h,0                  ; HL = mitad superior, DE = mitad inferior, A = 0
        ld l,b
rb_c1:  ld d,0
        ld e,c
        xor a
rb_call:
        call 0
        exx
        jp rb_sig
rb_dibd:                        ; --- bloque de datos ---
        ex af,af'
        ld a,(de)               ; 2 = la toco un personaje: hay que devolverle el color
        cp 2
        ld a,1
        ld (de),a
        inc de
        jr nz,rbd_n
        ex af,af'
        exx
rb_cd:  call rest_atr               ; (parcheado al empezar la fase)
        jr rbd_x
rbd_n:  ex af,af'
        exx
rbd_x:
        ld l,a                  ; HL = bloque de la pareja + desplazamiento
        ld h,TPARL/256
        ld a,(hl)
rb_off: add a,0
        inc h
        ld h,(hl)
        ld l,a
        ld a,h                  ; modo mezcla: bloques B en la pantalla 7
rb_dh:  add a,0
        ld h,a
rb_d0:  ld d,0                  ; mitad superior: 8 lineas
        ld e,b
        rept 7
        ld a,(hl)
        ld (de),a
        inc l
        inc d
        endm
        ld a,(hl)
        ld (de),a
        inc l
rb_d1:  ld d,0                  ; mitad inferior: 8 lineas
        ld e,c
        rept 7
        ld a,(hl)
        ld (de),a
        inc l
        inc d
        endm
        ld a,(hl)
        ld (de),a
        exx
        jp rb_sig
rb_colores:
        ld a,(cnt_atr)          ; colores (solo cuando cambian)
        or a
        ret z
        dec a
        ld (cnt_atr),a
        ld a,(fino)             ; antes de la mitad, color de la columna izquierda de la pareja
        cp 4
        ld a,PATR/256
        jr c,rba0
        add a,2
rba0:   ld (rba_pg+1),a
        ld hl,RF5
        ld a,(base)
        cp 0x40
        jr z,rba1
        ld hl,RF7
rba1:   ld (rb_sf),hl
        ld hl,VENT
        ld (rb_vc),hl
        ld a,(pfila)
        ld (rb_fila),a
        ld a,ALTO/2
        ld (rb_n),a
rba_tile:
        ld hl,(rb_vc)           ; fila sin ninguna pareja y ya con el color del vacio: se salta
        ld b,ANCHO
        xor a
rba_v:  or (hl)
        inc l
        djnz rba_v
        ld hl,(rb_sf)
        ld c,a
        or (hl)
        jr z,rba_sig
        ld (hl),c
        ld a,(rb_fila)
        call dir_atr            ; DE = atributo de la fila A
        push de
        ld a,(rb_fila)
        inc a
        call dir_atr
        push de
        exx
        pop bc                  ; (alternativos) BC = fila inferior, DE = superior, H = pagina
        pop de
rba_pg: ld h,PATR/256
        exx
        ld hl,(rb_vc)
        ld b,ANCHO
rba_celda:
        ld a,(hl)               ; pareja
        inc l
        exx
        ld l,a
        ld a,(hl)               ; color de arriba (pagina) y de abajo (pagina siguiente)
        ld (de),a
        inc h
        ld a,(hl)
        ld (bc),a
        dec h
        inc e
        inc c
        exx
        djnz rba_celda
rba_sig:
        ld hl,(rb_vc)
        ld de,ANCHO
        add hl,de
        ld (rb_vc),hl
        ld hl,(rb_sf)
        inc hl
        ld (rb_sf),hl
        ld hl,rb_fila
        inc (hl)
        inc (hl)
        ld hl,rb_n
        dec (hl)
        jr nz,rba_tile
        ret

;@ FIN
; dir_fila: A = fila de pantalla -> DE = direccion de su primera linea en la columna pcol (con base)
dir_fila:
        ld c,a
        and 0x18
        ld d,a
        ld a,(base)
        or d
        ld d,a
        ld a,c
        and 7
        rrca
        rrca
        rrca
        ld e,a
        ld a,(pcol)
        or e
        ld e,a
        ret

; dir_atr: A = fila de pantalla -> DE = direccion de su atributo en la columna pcol (con base)
dir_atr:
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(pcol)
        or l
        ld e,a
        ld a,(base)
        add a,0x18
        add a,h
        ld d,a
        ret

; ------------------------------------------------------------
;  TILES QUE CAMBIAN, GOLPES, OBJETOS
; ------------------------------------------------------------
R_ROMP  equ 16                  ; propiedades: rompible (golpes, disparos, cabezazo)
R_FRAG  equ 32                  ; fragil: se rompe al caer sobre el (plataformas)
R_OBJ   equ 64                  ; objeto: se recoge al tocarlo

;@ SOLO V H B D
; dir_mapa: B = x, C = y (pixeles del area) -> HL = direccion del tile en el mapa (banco de la fase)
dir_mapa:
        ld a,(dir)
        or a
        jr nz,dm_h
        ld hl,(tpx)
        ld e,c
        ld d,0
        add hl,de
        ld a,l
        and 15
        ld (ct_fy),a
        ld a,b
        and 15
        ld (ct_fx),a
        call div16
        ld d,h                  ; fila * 12 + x/16
        ld e,l
        add hl,hl
        add hl,de
        add hl,hl
        add hl,hl
        ld a,b
        jr dm_fin
dm_h:   ld hl,(izq)             ; columna * 10 + y/16
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(fino)
        add a,b
        ld e,a
        ld d,0
        add hl,de
        ld a,l
        and 15
        ld (ct_fx),a
        ld a,c
        and 15
        ld (ct_fy),a
        call div16
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld a,c
dm_fin: rrca
        rrca
        rrca
        rrca
        and 15
        ld e,a
        ld d,0
        add hl,de
        ld de,(mapa)
        add hl,de
        ret
;@ FIN
div16:  srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ret

; propiedad: A = campo (0 tras, 1 accion, 2 valor, 3 mensaje, 4 puntos), (ct_id) = tile -> A
propiedad:
        push hl
        push de
        ld e,a
        ld d,0
        ld a,(ct_id)
        ld l,a
        ld h,0
        ld c,l                  ; *5
        ld b,h
        add hl,hl
        add hl,hl
        add hl,bc
        add hl,de
        ld de,(N_TPROP)
        add hl,de
        ld a,(hl)
        pop de
        pop hl
        ret

;@ SOLO V H B D
; cambiar_tile: B = x, C = y del punto. Sustituye el tile por su tile "tras", da sus puntos
; y lo redibuja en el modo que corresponda.
cambiar_tile:
        push ix
        push bc
        call dir_mapa
        ld a,(hl)
        call id_celda
        ld (ct_id),a
        push hl
        xor a
        call nuevo_tile
        pop hl
        call anotar             ; (para restaurarlo en la proxima partida)
        ld (hl),a               ; nuevo tile en el mapa
        ld a,4
        call propiedad
        call sumar_puntos
        ld a,2
        ld (cnt_hud),a
        pop bc
        ld a,(dir)              ; posicion del tile en el mundo
        or a
        jr nz,ctl_h
        ld hl,(tpx)             ; vertical: fila de tiles (tpx + y) / 16
        ld e,c
        ld d,0
        add hl,de
        call div16
        add hl,hl               ; filas de caracteres 2F y 2F+1
        ld b,2
ctv1:   push bc
        push hl
        ld (fmundo),hl
        ld de,(r_top)           ; ¿esta cargada en el anillo?
        or a
        sbc hl,de
        jr c,ctv2
        ld a,h
        or a
        jr nz,ctv2
        ld a,l
        cp ANILLO_V
        jr nc,ctv2
        ld b,a
        ld a,(a_top)
        add a,b
        cp ANILLO_V
        jr c,ctv1b
        sub ANILLO_V
ctv1b:  ld (anillo),a
        call pintar_fila
ctv2:   pop hl
        inc hl
        pop bc
        djnz ctv1
        ld a,2
        ld (cnt_atr),a
        jp ctl_fin
ctl_h:  ld hl,(izq)             ; horizontal: columna de tiles (izq*8 + fino + x) / 16
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(fino)
        add a,b
        ld e,a
        ld d,0
        add hl,de
        call div16
        ld a,c                  ; fila de tiles
        rrca
        rrca
        rrca
        rrca
        and 15
        ld (ct_fila),a
        add hl,hl               ; columnas de caracteres 2C y 2C+1
        ld a,(bloques)
        or a
        jr nz,ctl_b
        ld b,2
cth1:   push bc
        push hl
        ld (fmundo),hl
        ld de,(izq)             ; ¿visible?
        or a
        sbc hl,de
        jr c,cth2
        ld a,h
        or a
        jr nz,cth2
        ld a,l
        cp ANCHO
        jr nc,cth2
        ld b,a
        ld a,(c0)
        add a,b
        cp ANCHO
        jr c,cth1b
        sub ANCHO
cth1b:  ld (anillo),a
        call pintar_col
cth2:   pop hl
        inc hl
        pop bc
        djnz cth1
        ld a,2
        ld (cnt_atr),a
        jr ctl_fin
ctl_b:  dec hl                  ; bloques: parejas de las columnas 2C-1, 2C y 2C+1
        ld b,3
ctb1:   push bc
        push hl
        bit 7,h
        jr nz,ctb2
        call nueva_pareja
ctb2:   pop hl
        inc hl
        pop bc
        djnz ctb1
        call colores_cambian
ctl_fin:
        pop ix
        ret

;@ FIN
;@ SOLO B
; hc: HL = columna de caracteres (recortada al mapa), (ct_fila) -> A = media columna (tile*2 + mitad)
hc:     push hl
        ld de,(largo2)
        or a
        sbc hl,de
        add hl,de
        jr c,hc1
        ld hl,(largo2)
        dec hl
hc1:    ld a,l
        and 1
        ld c,a
        srl h
        rr l
        add hl,hl               ; *10 + fila
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld a,(ct_fila)
        ld e,a
        ld d,0
        add hl,de
        ld de,(mapa)
        add hl,de
        ld a,(hl)
        add a,a
        or c
        pop hl
        ret

; nueva_pareja: HL = columna de caracteres. Busca la pareja de sus medias columnas en la lista de
; la fase, la apunta en el mapa de parejas y, si esta a la vista, en la ventana (sucia en las dos pantallas)
nueva_pareja:
        ld de,(largo2)
        push hl
        or a
        sbc hl,de
        pop hl
        ret nc
        call hc
        ld (np_izq),a
        inc hl
        call hc
        dec hl
        ld (np_dch),a
        push hl
        ld hl,(N_PARLIST)       ; busqueda lineal
        ld a,(N_NPARL)
        ld b,a
        ld c,0
np1:    ld a,(np_izq)           ; entradas de 3 bytes: izquierda, derecha, pareja
        cp (hl)
        inc hl
        jr nz,np2
        ld a,(np_dch)
        cp (hl)
        jr z,np3
np2:    inc hl
        inc hl
        djnz np1
        ld c,0
        jr np3b
np3:    inc hl
        ld c,(hl)
np3b:   pop hl                  ; C = pareja
        push hl
        add hl,hl               ; mapa de parejas: columna*10 + fila
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld a,(ct_fila)
        ld e,a
        ld d,0
        add hl,de
        ld de,(N_PARMAP)
        add hl,de
        call anotar
        ld (hl),c
        pop hl
        ld de,(izq)             ; ¿visible?
        or a
        sbc hl,de
        ret c
        ld a,h
        or a
        ret nz
        ld a,l
        cp ANCHO
        ret nc
        ld e,a                  ; indice en la ventana: fila*24 + columna
        ld a,(ct_fila)
        ld b,a
        add a,a
        add a,b
        add a,a
        add a,a
        add a,a
        add a,e
        ld e,a
        ld d,0
        ld hl,VENT
        add hl,de
        ld a,(hl)               ; recuento de la fila: quita la vieja, pone la nueva
        ld (hl),c
        push de
        ld hl,VCNT
        ld e,b
        ld d,0
        add hl,de
        or a
        jr z,np4
        dec (hl)
np4:    ld a,c
        or a
        jr z,np5
        inc (hl)
np5:    pop de
        ld a,1                  ; sucia en las dos pantallas
        ld hl,SUCIO5
        add hl,de
        ld (hl),a
        ld hl,SUCIO7
        add hl,de
        ld (hl),a
        ld e,b
        ld d,0
        ld hl,SUCF5
        add hl,de
        ld (hl),a
        ld hl,SUCF7
        add hl,de
        ld (hl),a
        ret

; ------------------------------------------------------------
;  REGISTRO DE CAMBIOS DEL MAPA: lo que se rompe o se recoge vuelve a su sitio en la proxima
;  partida. Se guarda en el banco 1, tras el titulo y el marco: banco, direccion, valor original.
; ------------------------------------------------------------
REG_INI equ 0xF600
REG_FIN equ 0x10000-4

;@ FIN
; anotar: HL = direccion (en el banco de la fase, paginado) que se va a cambiar. Conserva todo.
anotar: push af
        push bc
        push de
        push hl
        ld c,(hl)               ; valor original
        ld de,(reg_ptr)
        ld a,d                  ; ¿lleno?
        cp REG_FIN/256
        jr nc,ano_fin
        ld a,1
        call pon_banco
        ld a,(banco_nivel)
        ld (de),a
        inc de
        ld a,l
        ld (de),a
        inc de
        ld a,h
        ld (de),a
        inc de
        ld a,c
        ld (de),a
        inc de
        ld (reg_ptr),de
        ld a,(banco_nivel)
        call pon_banco
ano_fin:
        pop hl
        pop de
        pop bc
        pop af
        ret

; restaurar_mapas: deshace todos los cambios anotados (de atras adelante) y vacia el registro
restaurar_mapas:
rm1:    ld hl,(reg_ptr)
        ld de,REG_INI
        or a
        sbc hl,de
        ret z
        add hl,de
        dec hl                  ; ultima anotacion: banco, dir baja, dir alta, valor
        dec hl
        dec hl
        dec hl
        ld (reg_ptr),hl
        ld a,1
        call pon_banco
        ld b,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        ld a,b
        call pon_banco
        ld a,c
        ld (de),a
        jr rm1

; danar_enemigo: IX = enemigo. Le quita una unidad de energia; si llega a 0 desaparece y da sus puntos
danar_enemigo:
        ld a,1
        call sonido
        dec (ix+S_ENER)
        ret nz
        ld a,3
        call sonido
        ld (ix+S_ACT),0
;@ SOLO C
        ld l,(ix+S_AP)          ; su aparicion queda destruida (estado, bit 1)
        ld h,(ix+S_AP+1)
        ld de,5
        add hl,de
        set 1,(hl)
;@ FIN
        ld l,(ix+S_TIPO)
        ld h,(ix+S_TIPO+1)
        push hl
        ld de,12                ; fotograma de muerte (ficha + 12)
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        or a
        jr z,de0
        ld (ix+S_FR),e
        ld (ix+S_FR+1),d
        ld (ix+S_COMP),6
        ld (ix+S_CDISP),15
        ld (ix+S_CAD),0
        ld (ix+S_ACT),1
de0:    pop hl
        ld de,7
        add hl,de
        ld a,(hl)
        call sumar_puntos
        ld a,2
        ld (cnt_hud),a
        ret

; golpe: zona de impacto del tamano del jugador, desplazada "alcance" pixeles hacia donde mira.
; Dana a los enemigos que toca y rompe el tile rompible que haya en su centro.
golpe:
        ld a,(C_PLAT)
        or a
        ld a,(dir_j)
        jr z,gp0
        ld a,(mira_j)
gp0:    add a,a
        ld e,a
        ld d,0
        ld hl,tabla_vel
        add hl,de
        ld iy,golpe_z
        ld ix,sprites
        ld a,(C_ALC)
        ld e,a
        ld a,(hl)               ; x = x + dx * alcance (dentro del area)
        call por_vel
        add a,(ix+S_X)
        ld b,a
        ld a,(ix+S_WP)
        ld (iy+S_WP),a
        neg
        add a,192
        call recorta
        ld (iy+S_X),a
        inc hl
        ld a,(hl)               ; y = y + dy * alcance
        call por_vel
        add a,(ix+S_Y)
        ld b,a
        ld a,(ix+S_H)
        ld (iy+S_H),a
        neg
        add a,ALTO*8
        call recorta
        ld (iy+S_Y),a
        ld ix,sprites+SLOT      ; enemigos alcanzados
        ld a,(n_ene)
        ld b,a
gp1:    push bc
        call hostil
        jr z,gp2
        call solapan
        call c,danar_enemigo
gp2:    ld de,SLOT
        add ix,de
        pop bc
        djnz gp1
        ld a,(iy+S_WP)          ; tile en el centro de la zona
        srl a
        add a,(iy+S_X)
        ld b,a
        ld a,(iy+S_H)
        srl a
        add a,(iy+S_Y)
        ld c,a
        ; (sigue en romper_en)
; romper_en: B, C = punto. Si el tile es rompible, lo cambia
romper_en:
        call flags_en
        and R_ROMP
        ret z
        ld a,6
        call sonido
        jp cambiar_tile

; recorta: B = valor con signo calculado, A = maximo -> A dentro de [0, maximo]
recorta:
        bit 7,b
        jr z,rc1
        xor a                   ; negativo (o se salio por la izquierda/arriba)
        ret
rc1:    cp b
        ret c
        ld a,b
        ret

; recoger: si el jugador toca un objeto, lo recoge y aplica su respuesta
recoger:
        ld a,(N_HAYOBJ)         ; solo en fases con objetos
        and 1
        ret z
        ld ix,sprites
        ld d,(ix+S_X)
        ld e,(ix+S_Y)
        ld a,R_OBJ
        call bloqueado_en
        ret z
        ld a,(px)
        ld b,a
        ld a,(py)
        ld c,a
        push bc
        call dir_mapa
        ld a,(hl)
        call id_celda
        ld (ct_id),a
        ld a,1
        call propiedad
        ld (ob_acc),a
        ld a,2
        call propiedad
        ld (ob_val),a
        ld a,3
        call propiedad
        ld (ob_msg),a
        pop bc
        ld a,(ob_acc)
        cp 9
        jr z,puerta
        call cambiar_tile
        ld a,5
        call sonido
        ld a,(ob_acc)
        jp aplicar_accion
; puerta: lleva a otra fase (y columna). En plataformas se entra con abajo. Puede necesitar un
; elemento del inventario (propiedad 0 = elemento + 1); si falta, muestra su mensaje.
puerta: ld a,(npc_cool)
        or a
        ret nz
        ld a,(C_PLAT)
        or a
        jr z,pt1
        ld a,(entrada_j)
        bit 2,a
        ret z
pt1:    ld a,50
        ld (npc_cool),a
        xor a
        call propiedad
        or a
        jr z,pt3
        ld b,a                  ; elemento necesario
        ld a,1
        jr pt2b
pt2:    add a,a
pt2b:   djnz pt2
        ld hl,inv
        and (hl)
        jr nz,pt3
        ld a,(ob_msg)           ; cerrada
        cp 15
        ret z
        ld a,6
        ld (evento),a
        ret
pt3:    ld a,4                  ; propiedad 4: columna de entrada (tiles)
        call propiedad
        ld l,a
        ld h,0
        add hl,hl
        ld (col_entrada),hl
        ld a,1
        ld (via_puerta),a
        ld a,7
        call sonido
        ld a,3
        ld (evento),a
        ld a,15                 ; sin mensaje
        ld (ob_msg),a
        ret

; aplicar_accion: A = accion (1 vida, 2 energia, 3 fase, 4 ganar, 5 perder, 6 mensaje y seguir,
; 7 guardar el elemento ob_val, 8 altar). ob_val y ob_msg ya preparados.
aplicar_accion:
        or a                    ; 0: solo puntos
        ret z
        dec a
        jr nz,ap2
        ld a,(vidas)            ; 1: vida extra
        cp 9
        ret nc
        inc a
        ld (vidas),a
        ret
ap2:    dec a
        jr nz,ap3
        ld a,(C_ENER)           ; 2: energia completa
        ld (energia),a
        ret
ap3:    cp 5                    ; (A = accion - 2)
        jr nc,ap7
        add a,2
        ld (evento),a           ; 3 fase, 4 ganar, 5 perder, 6 mensaje: al final del fotograma
        ret
ap7:    jr nz,ap8
        ld a,(ob_val)           ; 7: guardar el elemento
        and 7
        ld b,a
        ld a,1
        inc b
        jr ap7b
ap7a:   add a,a
ap7b:   djnz ap7a
        ld hl,inv
        or (hl)
        ld (hl),a
        ld a,2
        ld (cnt_hud),a
        ld a,1                  ; reglas que se cumplen al completar
        jp reglas
ap8:    xor a                   ; 8: altar: la primera regla de altar que se cumpla
        call reglas
        ret nz
        ld a,(C_FALTA)
        cp 255
        ret z
        ld (ob_msg),a
        ld a,6
        ld (evento),a
        ret

; reglas: A = 1 (al completar) o 0 (en altar). Aplica la primera regla de ese tipo que se cumple
; con el inventario. NZ si se aplico alguna. Regla (6 bytes): elementos, opciones (bit0 exacta,
; bit1 al completar, bit2 gasta), accion, valor, mensaje, puntos.
reglas:
        ld c,a
        ld a,(N_NREG)
        srl a
        ret z
        ld b,a
        ld l,a                  ; principio = N_TPROP - 6*n
        ld h,0
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ex de,hl
        ld hl,(N_TPROP)
        or a
        sbc hl,de
        push hl
        pop ix
rgl1:   ld a,(ix+1)             ; clave: (personaje << 1) | al completar
        rrca
        ld e,a
        and 1
        ld d,a
        ld a,e
        rrca
        and 0x1E
        or d
        cp c
        jr nz,rgl3
        ld a,(ix+1)
        rrca
        ld a,(inv)
        jr c,rgl2               ; exacta: el inventario es justo ese conjunto
        and (ix+0)              ; si no: lo contiene
rgl2:   cp (ix+0)
        jr z,rgl_si
rgl3:   ld de,6
        add ix,de
        djnz rgl1
        xor a
        ret
rgl_si: ld a,(ix+1)
        and 4
        jr z,rgs1
        ld a,(ix+0)             ; gasta los elementos
        cpl
        ld hl,inv
        and (hl)
        ld (hl),a
rgs1:   ld a,(ix+5)
        call sumar_puntos
        ld a,2
        ld (cnt_hud),a
        ld a,(ix+3)
        ld (ob_val),a
        ld a,(ix+4)
        ld (ob_msg),a
        ld a,(ix+2)
        call aplicar_accion
        ld a,(evento)           ; si la accion no muestra nada, se ve el mensaje de la regla
        or a
        jr nz,rgs2
        ld a,(ob_msg)
        cp 15
        jr z,rgs2
        ld a,6
        ld (evento),a
rgs2:   or 1
        ret

; ------------------------------------------------------------
;  UTILIDADES DE SPRITES
; ------------------------------------------------------------
; buscar_libre: IX = primer hueco, B = cuantos. Z si encuentra (IX = hueco)
buscar_libre:
        ld de,SLOT
bl1:    ld a,(ix+S_ACT)
        or a
        ret z
        add ix,de
        djnz bl1
        or 1
        ret

; vel_dir: A = direccion (0-7), E = velocidad -> DX y DY del sprite IX
vel_dir:
        add a,a
        ld l,a
        ld h,0
        push de
        ld de,tabla_vel
        add hl,de
        pop de
        ld a,(hl)
        call por_vel
        ld (ix+S_DX),a
        inc hl
        ld a,(hl)
        call por_vel
        ld (ix+S_DY),a
        ret
por_vel:                        ; A en {-1,0,1} -> A * E
        or a
        ret z
        jp m,pv_neg
        ld a,e
        ret
pv_neg: ld a,e
        neg
        ret
tabla_vel:      ; arriba, arriba-dcha, dcha, abajo-dcha, abajo, abajo-izq, izq, arriba-izq
        db 0,-1, 1,-1, 1,0, 1,1, 0,1, -1,1, -1,0, -1,-1

; centrar_bala: IY = origen, IX = bala, HL = su tamano (ancho en bytes, alto) -> la coloca en el
; centro de IY (sin salirse del area)
centrar_bala:
        ld a,(hl)
        ld (ix+S_W),a
        add a,a
        add a,a
        add a,a
        ld (ix+S_WP),a
        ld c,a
        inc hl
        ld a,(hl)
        ld (ix+S_H),a
        ld b,a
        ld a,(iy+S_WP)
        ld d,(iy+S_X)
        call cb_eje
        ld (ix+S_X),a
        ld c,b
        ld a,(iy+S_H)
        ld d,(iy+S_Y)
        call cb_eje
        ld (ix+S_Y),a
        ld (ix+S_ACT),1
        ret
; cb_eje: A = tamano del origen, C = tamano de la bala, D = posicion del origen -> A = posicion
cb_eje: sub c
        sra a                   ; (origen - bala) / 2, con signo
        ld e,a
        add a,d
        bit 7,e
        ret z
        ret c
        xor a                   ; se saldria por la izquierda o por arriba
        ret

; dir_disparo: A = direccion del disparo del jugador (fija, hacia donde mira en plataformas o la
; ultima en que se ha movido)
dir_disparo:
        ld a,(dfijo)            ; direccion fija (por ejemplo, una nave que siempre dispara al frente)
        or a
        jr z,dd1
        dec a
        ret
dd1:    ld a,(C_PLAT)
        or a
        ld a,(dir_j)
        ret z
        ld a,(mira_j)           ; plataformas: solo izquierda o derecha
        ret

; ------------------------------------------------------------
;  DISPARO DEL JUGADOR
; ------------------------------------------------------------
disparar:
        ld hl,cool
        ld a,(hl)
        or a
        jr z,dp1
        dec (hl)
        ret
dp1:    ld a,(entrada_j)
        bit 4,a
        ret z
        ld a,(C_ARMA)           ; 0 disparo, 1 golpe, 2 ninguna, 3 laser
        or a
        jr z,dp1d
        cp 3
        jp z,laser_disparo
        dec a
        ret nz
        ld a,(cad_j)            ; golpe: se ve el fotograma de disparo/ataque
        ld (cool),a
        ld a,6
        ld (disp_t),a
        ld a,1
        call sonido
        jp golpe
dp1d:   ld ix,(p_bj)
        ld a,(n_bj)
        ld b,a
        call buscar_libre
        ret nz
        ld a,(cad_j)
        ld (cool),a
        ld a,4                  ; 4 fotogramas mostrando el de disparo
        ld (disp_t),a
        ld a,2
        call sonido
        ld iy,sprites
        ld hl,C_TBJ
        call centrar_bala
        call dir_disparo
        ld hl,C_VBJ
        ld e,(hl)
        call vel_dir
        ld hl,(fr_bala_j)
        ld (ix+S_FR),l
        ld (ix+S_FR+1),h
        ld a,(comp_bj)
        ld (ix+S_COMPI),a
        ret

; ------------------------------------------------------------
;  APARICION DE ENEMIGOS
;  Lista en el banco 0, 6 bytes por enemigo, ordenada por progreso:
;  progreso (palabra, 0xFFFF = fin), coordenada del mundo en caracteres
;  en el eje del scroll (palabra), coordenada transversal en px, tipo
; ------------------------------------------------------------
;@ SOLO V H B D
aparecer:
        ld a,(dir)
        or a
        jr nz,ap_h
        ld hl,(tmax)            ; vertical: progreso = tmax - tpx (pixeles)
        ld de,(tpx)
        or a
        sbc hl,de
        jr ap1
ap_h:   ld hl,(izq)             ; horizontal: progreso = izq
ap1:    ld (progreso),hl
; retroceso: las entradas que vuelven a quedar por delante de la vista se rebobinan
; (sus enemigos reapareceran al avanzar otra vez)
ap_reb: ld hl,(apar)
        ld de,(N_APAR)
        or a
        sbc hl,de
        jr z,ap_izq
        add hl,de
        ld de,-6
        add hl,de               ; entrada anterior
        ld e,(hl)
        inc hl
        ld d,(hl)
        dec hl
        push hl
        ld hl,(progreso)
        or a
        sbc hl,de               ; progreso < su progreso: vuelve a estar por delante
        pop hl
        jr nc,ap_izq
        ld (apar),hl
        jr ap_reb
; horizontal: los enemigos ya pasados cuya columna vuelve a entrar por la izquierda reaparecen
ap_izq: ld a,(dir)
        or a
        jr z,ap_bucle
        ld hl,(izq)             ; L = primera columna entera a la vista
        ld a,(fino)
        or a
        jr z,ai0
        inc hl
ai0:    ld de,(ap_l)
        ld (ap_lv),de
        ld (ap_l),hl
        or a
        sbc hl,de
        jr nc,ap_bucle          ; no ha retrocedido
        ld hl,(N_APAR)
ai1:    ld de,(apar)
        or a
        sbc hl,de
        jr nc,ap_bucle
        add hl,de
        push hl
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)               ; DE = columna del enemigo
        ld hl,(ap_l)
        ex de,hl
        or a
        sbc hl,de
        jr c,ai2                ; columna < L: sigue fuera
        add hl,de
        ld de,(ap_lv)
        or a
        sbc hl,de
        jr nc,ai2               ; columna >= L anterior: ya estaba a la vista
        pop hl
        push hl
        call ap_crear
ai2:    pop hl
        ld de,6
        add hl,de
        jr ai1
ap_bucle:
        ld hl,(apar)
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld hl,(progreso)
        or a
        sbc hl,de
        ret c                   ; aun no ha llegado
        ld hl,(apar)
        call ap_crear
        ret nz                  ; sin hueco: se reintenta en el siguiente fotograma
        ld hl,(apar)
        ld de,6
        add hl,de
        ld (apar),hl
        jr ap_bucle

; ap_crear: HL = entrada de la lista. Crea su enemigo (Z) salvo que ya este en juego (Z) o
; que no haya hueco (NZ). Si no cabe en pantalla, se descarta (Z).
ap_crear:
        ld (ap_ent),hl
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld b,a
        ld de,SLOT
ac0:    ld a,(ix+S_ACT)
        or a
        jr z,ac1
        ld a,(ix+S_AP)
        cp l
        jr nz,ac1
        ld a,(ix+S_AP+1)
        cp h
        ret z                   ; ya esta en juego
ac1:    add ix,de
        djnz ac0
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld b,a
        call buscar_libre
        ret nz
        ld hl,(ap_ent)
        ld (ix+S_AP),l
        ld (ix+S_AP+1),h
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,(hl)
        ld (ap_trans),a
        inc hl
        ld a,(hl)
        push de
        call activar_tipo
        pop de
        ld a,(dir)
        or a
        jr nz,ap_ph
        ex de,hl                ; y = fila*8 - tpx
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,(tpx)
        or a
        sbc hl,de
        jr c,ap_no
        ld a,h
        or a
        jr nz,ap_no
        ld a,l
        cp ALTO*8
        jr nc,ap_no
        ld d,a
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        cp d
        jr c,ap_no
        ld (ix+S_Y),d
        ld a,(ap_trans)
        ld (ix+S_X),a
        xor a
        ret
ap_ph:  ld hl,(izq)             ; x = (columna - izq) * 8
        ex de,hl
        or a
        sbc hl,de
        jr c,ap_no
        ld a,h
        or a
        jr nz,ap_no
        ld a,l
        cp ANCHO
        jr nc,ap_no
        add a,a
        add a,a
        add a,a
        ld d,a
        ld a,(fino)
        ld e,a
        ld a,d
        sub e
        jr c,ap_no
        ld d,a
        ld a,(ix+S_WP)
        neg
        add a,192
        cp d
        jr c,ap_no
        ld (ix+S_X),d
        ld a,(ap_trans)
        ld (ix+S_Y),a
        xor a
        ret
ap_no:  ld (ix+S_ACT),0         ; ya no cabe en pantalla: se descarta
        xor a
        ret

;@ FIN
; activar_tipo: A = tipo, IX = hueco
activar_tipo:
        push af
        add a,a                 ; caja de sus pixeles (para el laser)
        add a,a
        ld e,a
        ld d,0
        ld hl,cajas
        add hl,de
        ld a,(hl)
        ld (ix+S_BX),a
        inc hl
        ld a,(hl)
        ld (ix+S_BY),a
        inc hl
        ld a,(hl)
        ld (ix+S_BW),a
        inc hl
        ld a,(hl)
        ld (ix+S_BH),a
        pop af
        ld l,a                  ; HL = tipos + tipo*48
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,tipos
        add hl,de
        ld (ix+S_TIPO),l
        ld (ix+S_TIPO+1),h
        push hl
        pop iy
        ld a,(iy+0)
        ld (ix+S_W),a
        add a,a
        add a,a
        add a,a
        ld (ix+S_WP),a
        ld a,(iy+1)
        ld (ix+S_H),a
        ld a,(iy+2)
        ld (ix+S_COMP),a
        ld a,(iy+3)
        ld (ix+S_VEL),a
        ld a,(iy+4)
        ld (ix+S_ENER),a
        ld a,(iy+5)
        ld (ix+S_CAD),a
        ld (ix+S_CDISP),a
        ld a,(iy+16)
        ld (ix+S_FR),a
        ld a,(iy+17)
        ld (ix+S_FR+1),a
        ld (ix+S_ACNT),1
        ld (ix+S_AFR),0
        ld (ix+S_MIRA),0
        ld a,(iy+10)            ; compilado (ficha + 10)
        ld (ix+S_COMPI),a
        ld a,(iy+11)            ; color propio (ficha + 11)
        ld (ix+S_COLOR),a
        ld a,(iy+6)             ; direccion
        ld e,(ix+S_VEL)
        call vel_dir
        ld (ix+S_ACT),1
        ret

; ------------------------------------------------------------
;  ENEMIGOS
; ------------------------------------------------------------
mover_enemigos:
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld b,a
me1:    push bc
        ld a,(ix+S_ACT)
        or a
        jp z,me_sig
        ld a,(ix+S_COMP)
        cp 6                    ; 6 muriendo: fotograma de muerte un rato y desaparece
        jr z,me_muere
        cp 5                    ; 5 personaje que habla: quieto, mira al jugador
        jp z,me_anim
        or a
        jr z,me_disp            ; 0 quieto
        dec a
        jr nz,me2
        call c_rebota           ; 1 rebota / patrulla
        jr me_disp
me2:    dec a
        jr nz,me3
        call c_persigue         ; 2 persigue
        jr me_disp
me3:    dec a
        jr nz,me4
        call c_cruza            ; 3 cruza
        jr me_disp
me4:    call c_patrulla_suelo   ; 4 patrulla sobre el suelo (plataformas)
        jr me_disp
me_muere:
        dec (ix+S_CDISP)
        jp nz,me_sig
        ld (ix+S_ACT),0
        jp me_sig
me_disp:
        ld a,(ix+S_ACT)
        or a
        jp z,me_sig
        ld a,(ix+S_CAD)
        or a
        jr z,me_anim
        dec (ix+S_CDISP)
        jr nz,me_anim
        ld (ix+S_CDISP),a
        call disparo_enemigo
me_anim:
        ld a,(ix+S_COMP)        ; hacia donde mira
        cp 1
        jr z,ma_dx
        cp 3
        jr z,ma_dx
        cp 4
        jr z,ma_dx
        ld a,(sprites+S_X)      ; quieto o persigue: mira al jugador
        cp (ix+S_X)
        ld a,0
        jr nc,ma_m
        inc a
        jr ma_m
ma_dx:  ld a,(ix+S_DX)          ; rebota o cruza: hacia donde se mueve
        or a
        jr z,ma_paso
        rlca
        and 1
ma_m:   ld (ix+S_MIRA),a
ma_paso:
        ld l,(ix+S_TIPO)
        ld h,(ix+S_TIPO+1)
        dec (ix+S_ACNT)         ; avanza la animacion cada (ficha+8) fotogramas
        jr nz,ma_fr
        ld de,8
        add hl,de
        ld a,(hl)
        ld (ix+S_ACNT),a
        inc hl                  ; ficha + 9: fotogramas del ciclo
        ld a,(ix+S_AFR)
        inc a
        cp (hl)
        jr c,ma_ok
        xor a
ma_ok:  ld (ix+S_AFR),a
        ld l,(ix+S_TIPO)
        ld h,(ix+S_TIPO+1)
ma_fr:  ld a,(ix+S_MIRA)        ; ficha + 16 + mira*16 + paso*2
        add a,a
        add a,a
        add a,a
        add a,a
        add a,16
        ld e,a
        ld a,(ix+S_AFR)
        add a,a
        add a,e
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (ix+S_FR),a
        inc hl
        ld a,(hl)
        ld (ix+S_FR+1),a
me_sig: ld de,SLOT
        add ix,de
        pop bc
        dec b
        jp nz,me1
        ret

c_rebota:
        ld a,(ix+S_DX)
        or a
        jr z,cr_y
        call mover_x_bloq
        jr z,cr_y
        ld a,(ix+S_DX)
        neg
        ld (ix+S_DX),a
cr_y:   ld a,(ix+S_DY)
        or a
        ret z
        call mover_y_bloq
        ret z
        ld a,(ix+S_DY)
        neg
        ld (ix+S_DY),a
        ret

c_persigue:
        ld a,(sprites+S_X)
        cp (ix+S_X)
        jr z,cp_y
        ld a,(ix+S_VEL)
        jr nc,cp_x1
        neg
cp_x1:  call mover_x_bloq
cp_y:   ld a,(sprites+S_Y)
        cp (ix+S_Y)
        ret z
        ld a,(ix+S_VEL)
        jr nc,cp_y1
        neg
cp_y1:  jp mover_y_bloq

c_cruza:                        ; ignora el mapa; desaparece al salir
        ld a,(ix+S_DX)
        ld c,a
        add a,(ix+S_X)
        bit 7,c
        jr z,cz_xp
        jr nc,cz_fuera
        jr cz_xok
cz_xp:  ld d,a
        ld a,(ix+S_WP)
        neg
        add a,192
        cp d
        jr c,cz_fuera
        ld a,d
cz_xok: ld (ix+S_X),a
        ld a,(ix+S_DY)
        ld c,a
        add a,(ix+S_Y)
        bit 7,c
        jr z,cz_yp
        jr nc,cz_fuera
        jr cz_yok
cz_yp:  ld d,a
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        cp d
        jr c,cz_fuera
        ld a,d
cz_yok: ld (ix+S_Y),a
        ret
cz_fuera:
        ld (ix+S_ACT),0
        ret

; disparo_enemigo: IX = enemigo
disparo_enemigo:
        push ix
        pop iy
        ld ix,(p_be)
        ld a,(n_be)
        ld b,a
        call buscar_libre
        jr nz,de_fin
        ld hl,C_TBE
        call centrar_bala
        call dir_al_jugador
        ld hl,C_VBE
        ld e,(hl)
        call vel_dir
        ld hl,(fr_bala_e)
        ld (ix+S_FR),l
        ld (ix+S_FR+1),h
        ld a,(comp_be)
        ld (ix+S_COMPI),a
de_fin: push iy
        pop ix
        ret

; dir_al_jugador: IX = bala -> A = direccion (0-7) hacia el centro del jugador
dir_al_jugador:
        ld a,(sprites+S_WP)
        srl a
        ld hl,sprites+S_X
        add a,(hl)
        ld d,a
        ld a,(ix+S_X)
        add a,4
        ld e,a
        ld c,0
        ld a,d
        sub e
        jr nc,dj1
        neg
        set 0,c                 ; jugador a la izquierda
dj1:    ld d,a                  ; D = |dx|
        ld a,(sprites+S_H)
        srl a
        ld hl,sprites+S_Y
        add a,(hl)
        ld e,a
        ld a,(ix+S_Y)
        add a,4
        ld b,a
        ld a,e
        sub b
        jr nc,dj2
        neg
        set 1,c                 ; jugador arriba
dj2:    ld e,a                  ; E = |dy|
        ld a,d
        srl a
        cp e
        jr c,dj3
        jr z,dj3
        ld a,c                  ; casi horizontal
        and 1
        ld a,2
        ret z
        ld a,6
        ret
dj3:    ld a,e
        srl a
        cp d
        jr c,dj4
        jr z,dj4
        bit 1,c                 ; casi vertical
        ld a,4
        ret z
        xor a
        ret
dj4:    ld e,c                  ; diagonal
        ld d,0
        ld hl,tabla_diag
        add hl,de
        ld a,(hl)
        ret
tabla_diag:
        db 3,5,1,7

; ------------------------------------------------------------
;  BALAS
; ------------------------------------------------------------
mover_balas:
        ld ix,(p_bj)
        ld a,(n_bal)
        ld b,a
mb1:    push bc
        ld a,(ix+S_ACT)
        or a
        jr z,mb_sig
        ld a,(ix+S_DX)
        ld c,a
        add a,(ix+S_X)
        bit 7,c
        jr z,mb_xp
        jr nc,mb_mata
        jr mb_xok
mb_xp:  jr c,mb_mata              ; pasa de 255
        ld d,a
        ld a,192
        sub (ix+S_WP)
        cp d
        jr c,mb_mata
        ld a,d
mb_xok: ld (ix+S_X),a
        ld a,(ix+S_DY)
        ld c,a
        add a,(ix+S_Y)
        bit 7,c
        jr z,mb_yp
        jr nc,mb_mata
        jr mb_yok
mb_yp:  jr c,mb_mata
        ld d,a
        ld a,ALTO*8
        sub (ix+S_H)
        cp d
        jr c,mb_mata
        ld a,d
mb_yok: ld (ix+S_Y),a
        ld a,(ix+S_WP)          ; tile que detiene disparos (en el centro)
        srl a
        add a,(ix+S_X)
        ld b,a
        ld a,(ix+S_H)
        srl a
        add a,(ix+S_Y)
        ld c,a
        call flags_en
        ld d,a
        and 2
        jr z,mb_sig
        ld a,d                  ; disparo del jugador contra un tile rompible
        and R_ROMP
        jr z,mb_mata
        push ix
        pop hl
        ld de,(p_be)
        or a
        sbc hl,de
        jr nc,mb_mata
        call cambiar_tile
mb_mata:
        ld (ix+S_ACT),0
mb_sig: ld de,SLOT
        add ix,de
        pop bc
        djnz mb1
        ret

; ------------------------------------------------------------
;  CHOQUES ENTRE SPRITES
; ------------------------------------------------------------
; solapan: IX, IY -> CF=1 si sus rectangulos se tocan (usa A y D)
solapan:
        ld a,(iy+S_X)
        add a,(iy+S_WP)
        ld d,a
        ld a,(ix+S_X)
        cp d
        ret nc
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        ld d,a
        ld a,(iy+S_X)
        cp d
        ret nc
        ld a,(iy+S_Y)
        add a,(iy+S_H)
        ld d,a
        ld a,(ix+S_Y)
        cp d
        ret nc
        ld a,(ix+S_Y)
        add a,(ix+S_H)
        ld d,a
        ld a,(iy+S_Y)
        cp d
        ret

; barrida: IY = bala -> caja_t = su caja ampliada con el movimiento de este fotograma (desde
; donde estaba hasta donde esta). Asi una bala rapida no atraviesa a nadie sin danarlo.
barrida:
        push bc                 ; (los bucles que la llaman cuentan con B)
        ld a,(iy+S_DX)
        ld c,(iy+S_X)
        ld b,(iy+S_WP)
        call bar1
        ld (caja_t+S_X),a
        ld a,b
        ld (caja_t+S_WP),a
        ld a,(iy+S_DY)
        ld c,(iy+S_Y)
        ld b,(iy+S_H)
        call bar1
        ld (caja_t+S_Y),a
        ld a,b
        ld (caja_t+S_H),a
        pop bc
        ret
; bar1: A = desplazamiento con signo, C = posicion, B = tamano -> A = inicio y B = tamano barridos
bar1:   or a
        jp m,bar_n
        ld d,a                  ; venia de la izquierda (o de arriba): empieza d antes
        add a,b
        ld b,a
        ld a,c
        sub d
        ret nc
        add a,b                 ; recortado en 0
        ld b,a
        xor a
        ret
bar_n:  neg                     ; venia de la derecha: acaba |d| despues
        add a,b
        ld b,a
        ld a,c
        ret

colisiones:
        ld iy,(p_bj)            ; balas del jugador contra enemigos
        ld a,(n_bj)
        ld b,a
co1:    push bc
        ld a,(iy+S_ACT)
        or a
        jr z,co_sig
        call barrida
        push iy
        ld iy,caja_t
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld c,a
co2:    call hostil
        jr z,co3
        call solapan
        jr nc,co3
        pop iy
        ld (iy+S_ACT),0         ; la bala desaparece
        call danar_enemigo
        jp co_sig
co3:    ld de,SLOT
        add ix,de
        dec c
        jr nz,co2
        pop iy
co_sig: ld de,SLOT
        add iy,de
        pop bc
        djnz co1
        ld a,(invul)            ; jugador: invulnerable tras un golpe
        or a
        jr z,co4
        dec a
        ld (invul),a
        cp 19
        ret nz
        xor a                   ; fin del destello rojo del borde
        out (0xFE),a
        ret
co4:    ld hl,npc_cool
        ld a,(hl)
        or a
        jr z,co4b
        dec (hl)
co4b:   ld ix,sprites           ; tiles mortales
        ld d,(ix+S_X)
        ld e,(ix+S_Y)
        ld a,8
        call bloqueado_en
        jp nz,tocado
        ld iy,sprites
        ld ix,sprites+SLOT      ; contra enemigos
        ld a,(n_ene)
        ld b,a
co5:    ld a,(ix+S_ACT)
        or a
        jr z,co6
        ld a,(ix+S_COMP)
        cp 5
        jr z,co_npc
        call hostil
        jr z,co6
        call solapan
        jr nc,co6
        call pisa               ; ¿le ha caido encima?
        jp nc,tocado
co6:    ld de,SLOT
        add ix,de
        djnz co5
        ld ix,(p_be)            ; contra balas enemigas
        ld a,(n_be)
        ld b,a
co7:    ld a,(ix+S_ACT)
        or a
        jr z,co8
        push ix
        pop iy
        call barrida
        ld iy,caja_t
        push ix
        ld ix,sprites
        call solapan
        pop ix
        jr nc,co8
        ld (ix+S_ACT),0
        jp tocado
co8:    ld de,SLOT
        add ix,de
        djnz co7
        ret
; pisa: IY = jugador, IX = enemigo que lo toca. Si el jugador cae y sus pies estan por encima del
; enemigo, lo dana y rebota (CF=1); si no, CF=0
co_npc: call solapan            ; personaje: se habla con el (abajo en plataformas)
        jr nc,co6
        push bc
        call hablar
        pop bc
        jr co6

; hostil: NZ si el sprite IX esta activo y no es un personaje ni esta muriendo
hostil: ld a,(ix+S_ACT)
        or a
        ret z
        ld a,(ix+S_COMP)
        cp 5
        jr nc,hos0
        or 1
        ret
hos0:   xor a
        ret

; hablar: IX = personaje que toca el jugador. Primero sus reglas (las que dicen «al hablar con el»);
; si no se cumple ninguna, su mensaje
hablar: ld a,(npc_cool)
        or a
        ret nz
        ld a,(C_PLAT)
        or a
        jr z,hb1
        ld a,(entrada_j)
        bit 2,a
        ret z
hb1:    ld a,50
        ld (npc_cool),a
        ld a,7
        call sonido
        push ix
        ld l,(ix+S_TIPO)
        ld h,(ix+S_TIPO+1)
        ld de,14
        add hl,de
        ld a,(hl)               ; ficha + 14: mensaje propio
        ld (ob_msg),a
        inc hl
        ld a,(hl)               ; ficha + 15: numero de personaje
        add a,a
        call reglas
        pop ix
        ret nz
        ld a,(ob_msg)
        cp 15
        ret z
        ld a,6
        ld (evento),a
        ret

pisa:   ld a,(C_PISAR)
        or a
        ret z
        ld a,(estado_v)
        cp 2
        jr nz,pis_no
        ld a,(iy+S_Y)
        add a,(iy+S_H)
        sub 8
        cp (ix+S_Y)
        jr nc,pis_no
        call danar_enemigo
        call rebote
        scf
        ret
pis_no: or a
        ret
rebote: ld a,1                  ; salto corto: empieza mas adelante en la tabla de subida
        ld (estado_v),a
        ld a,4
        ld (idx_v),a
        ret

tocado: ld a,4
        call sonido
        ld a,25                 ; 1 segundo invulnerable
        ld (invul),a
        ld hl,golpes
        inc (hl)
        ld a,2                  ; borde rojo
        out (0xFE),a
        ld (cnt_hud),a
        ld hl,energia
        dec (hl)
        ret nz
        ld hl,vidas             ; sin energia: pierde una vida
        dec (hl)
        jr z,tc_fin
        ld a,(C_ENER)
        ld (energia),a
        ld a,50                 ; reaparece con 2 segundos de invulnerabilidad
        ld (invul),a
        xor a
tc_mu:  ld ix,sprites           ; animacion de muerte: reaparece donde estaba
        ld b,(ix+S_X)
        ld c,(ix+S_Y)
        call morir
        ret nz
        ld a,(mue_ev)
        ld (evento),a
        ret
tc_fin: ld a,1                  ; sin vidas: fin de la partida
        jr tc_mu

; parpadeo del jugador mientras es invulnerable
parpadeo:
        ld a,(invul)
        or a
        ld a,1
        jr z,pp1
        ld a,(reloj)
        and 2
        jr z,pp1
        ld a,1
pp1:    ld (sprites+S_ACT),a
        ret

; desplazar_objetos: B = dx, C = dy (+-8 o 0) a enemigos y balas tras un scroll.
; Los que salen del area desaparecen.
desplazar_objetos:
        push ix
        ld ix,sprites+SLOT
        ld a,(n_spr)
        dec a
do1:    push af
        ld a,(ix+S_ACT)
        or a
        jr z,do_sig
        ld a,b
        or a
        jr z,do_y
        add a,(ix+S_X)
        bit 7,b
        jr z,do_xp
        jr nc,do_mata
        jr do_xok
do_xp:  ld d,a
        ld a,(ix+S_WP)
        neg
        add a,192
        cp d
        jr c,do_mata
        ld a,d
do_xok: ld (ix+S_X),a
do_y:   ld a,c
        or a
        jr z,do_sig
        add a,(ix+S_Y)
        bit 7,c
        jr z,do_yp
        jr nc,do_mata
        jr do_yok
do_yp:  ld d,a
        ld a,(ix+S_H)
        neg
        add a,ALTO*8
        cp d
        jr c,do_mata
        ld a,d
do_yok: ld (ix+S_Y),a
        jr do_sig
do_mata:
        ld (ix+S_ACT),0
do_sig: ld de,SLOT
        add ix,de
        pop af
        dec a
        jr nz,do1
        pop ix
        ld a,b                  ; punto seguro de reaparicion (plataformas)
        or a
        ret z
        ld a,(seguro_x)
        add a,b
        bit 7,b
        jr z,do_s1
        jr c,do_s2
        xor a
        jr do_s2
do_s1:  ld d,a
        ld a,(sprites+S_WP)
        neg
        add a,192
        cp d
        jr c,do_s2
        ld a,d
do_s2:  ld (seguro_x),a
        ret

fotograma_jugador:
        ld a,(dir_j)
        add a,a
        ld e,a
        ld d,0
        ld hl,disp_t            ; recien disparado: fotograma de disparo
        ld a,(hl)
        or a
        jr z,fj1
        dec (hl)
        ld hl,G_DISPARO
        jr fj3
fj1:    ld a,(agachado)         ; agachado
        or a
        jr z,fj1b
        ld hl,G_AGACHA
        jr fj3
fj1b:   ld a,(quieto_j)         ; parado: fotograma de reposo
        or a
        jr z,fj2
        ld hl,G_QUIETO
        jr fj3
fj2:    call alen_dir           ; si cambio de direccion y el paso no existe, vuelve al 0
        ld a,(afr_j)
        cp (hl)
        jr c,fj2b
        xor a
        ld (afr_j),a
fj2b:   ld a,(dir_j)            ; andando: G_ANIM[dir*8 + paso]
        add a,a
        add a,a
        add a,a
        ld e,a
        ld a,(afr_j)
        add a,e
        add a,a
        ld e,a
        ld hl,G_ANIM
fj3:    add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld (sprites+S_FR),hl
        ret

;@ SOLO V
; ------------------------------------------------------------
;  PINTAR UNA FILA DE CARACTERES DEL MAPA EN EL ANILLO
;  (fmundo) = fila del mundo en caracteres, (anillo) = fila del anillo
; ------------------------------------------------------------
pintar_fila:
        ld a,(banco_nivel)
        call pon_banco
        ld a,(anillo)           ; destino bitmap = BUF + anillo*192
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,BUF
        add hl,de
        ld (pf_dst),hl
        ld a,(anillo)           ; destino atributos = ABUF + anillo*24
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,ABUF
        add hl,de
        ld (pf_adst),hl
        ld hl,(fmundo)          ; mitad del tile
        ld a,l
        and 1
        ld (pf_mitad),a
        srl h
        rr l                    ; fila de tiles
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        add hl,hl
        add hl,hl               ; *12
        ld de,(mapa)
        add hl,de
        ld (pf_mapa),hl
        ld b,12
pf_tile:
        push bc
        ld hl,(pf_mapa)
        ld a,(hl)
        inc hl
        ld (pf_mapa),hl
        ld l,a                  ; HL = tiles + id*36
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,(tiles)
        add hl,de
        push hl                 ; inicio del tile
        ld a,(pf_mitad)
        or a
        jr z,pf1
        ld de,16
        add hl,de
pf1:    ld de,(pf_dst)
        rept 8
        ldi
        ldi
        ex de,hl
        ld bc,ANCHO-2
        add hl,bc
        ex de,hl
        endm
        pop hl                  ; atributos: tile + 32 + mitad*2
        ld de,32
        add hl,de
        ld a,(pf_mitad)
        add a,a
        ld e,a
        ld d,0
        add hl,de
        ld de,(pf_adst)
        ldi
        ldi
        ld (pf_adst),de
        ld hl,(pf_dst)
        inc hl
        inc hl
        ld (pf_dst),hl
        pop bc
        dec b
        jp nz,pf_tile
        ret

;@ FIN
; ------------------------------------------------------------
;  SPRITES: guardar fondo, dibujar, restaurar
; ------------------------------------------------------------
dibujar_sprites:
        ld ix,sprites
        ld a,(n_spr)
        ld b,a
ds1:    push bc
        ld a,(ix+S_ACT)
        or a
        call nz,dibujar_sprite
        ld de,SLOT
        add ix,de
        pop bc
        djnz ds1
        ret

restaurar_sprites:              ; en orden inverso
        ld ix,(p_ult)
        ld a,(n_spr)
        ld b,a
rs1:    push bc
        ld a,(ix+S_ACT)
        or a
        call nz,restaurar_sprite
        ld de,-SLOT
        add ix,de
        pop bc
        djnz rs1
        ret

; Dibuja el sprite IX en el anillo guardando antes el fondo.
; Fotogramas pre-desplazados: 4 versiones (0,2,4,6 pixeles), cada una con
; h lineas de (w+1) pares (mascara AND, datos).
dibujar_sprite:
        ld a,(bloques)          ; modo bloques y sprite compilado: se ejecuta su codigo
        and (ix+S_COMPI)
        jp nz,dib_compilado
        ld a,(dir)              ; puntero a LTAB: (fila0 + y)*2
        or a
        ld a,0                  ; horizontal: fila0 = 0
        jr nz,dsv0
        ld a,(linea0)           ; vertical: linea del anillo arriba de la vista
dsv0:   ld l,a
        ld h,0
        ld e,(ix+S_Y)
        ld d,0
        add hl,de
        add hl,hl
        ld de,(ltab_act)
        add hl,de
        ld (ix+S_LP),l
        ld (ix+S_LP+1),h
        ld (ds_lp),hl
        ld a,(ix+S_X)
        rrca
        rrca
        rrca
        and 31
        ld e,a
        ld a,(dir)              ; horizontal: la ventana empieza en c0
        or a
        jr z,dsx
        ld a,(c0)
        add a,e
        ld e,a
dsx:    ld a,e
        ld (ix+S_XB),a
        ld a,(ix+S_W)           ; bytes por linea = w+1
        inc a
        ld (dw_smc+1),a
        ld b,a                  ; tamano de una version = h*(w+1)*2
        ld e,(ix+S_H)
        ld d,0
        ld hl,0
dsm1:   add hl,de
        djnz dsm1
        add hl,hl
        ex de,hl
        ld l,(ix+S_FR)
        ld h,(ix+S_FR+1)
        ld a,(ix+S_X)
        rrca
        and 3                   ; version = (x>>1) & 3
        jr z,dsm3
        ld b,a
dsm2:   add hl,de
        djnz dsm2
dsm3:   ld (ds_src),hl
        ld a,(bloques)          ; modo bloques: el sprite se dibuja en la pantalla oculta, que
        or a                    ; puede ocupar la misma ventana que el banco de sprites; se
        jr z,dsm4               ; copia antes su grafico a memoria baja
        push de
        ld a,4
        call pon_banco
        pop bc
        ld hl,(ds_src)
;@ SOLO V H B D
        ld de,SCRATCH
        ldir
        ld hl,SCRATCH
;@ FIN
;@ SOLO C
        ld de,SCRC
        ldir
        ld hl,SCRC
;@ FIN
        ld (ds_src),hl
        ld a,(base)
        cp 0xC0
        jr nz,dsm4
        ld a,7
        call pon_banco
;@ SOLO B
dsm4:   call sprite_ensucia     ; (en el modo bloques el fondo no se guarda: se redibuja)
;@ FIN
;@ SOLO C
dsm4:                           ; (scroll libre: el fondo se vuelca entero en cada fotograma)
;@ FIN
;@ SOLO V H D
dsm4:   ld l,(ix+S_SV)
        ld h,(ix+S_SV+1)
        push hl
        pop iy                  ; IY = zona de guardado
;@ FIN
        ld hl,(ds_lp)           ; registros alternativos: HL'=LTAB, B'=lineas, C'=xb
        ld b,(ix+S_H)
        ld c,(ix+S_XB)
        exx
        ld de,(ds_src)          ; DE = datos del sprite
        exx
dsl:    ld e,(hl)               ; (alternativos) direccion de la linea + xb
        inc hl
        ld d,(hl)
        inc hl
        ld a,e
        add a,c
        ld e,a
        jr nc,dsl1
        inc d
dsl1:   push de
        exx
        pop hl
dw_smc: ld b,3
dsb:
;@ SOLO V H D
        ld a,(hl)               ; guarda el fondo
        ld (iy+0),a
        inc iy
;@ FIN
        ld a,(de)               ; fondo AND mascara
        inc de
        and (hl)
        ld c,a
        ld a,(de)               ; OR datos
        inc de
        or c
        ld (hl),a
        inc hl
        djnz dsb
        exx
        djnz dsl
        exx
        ret

restaurar_sprite:
        ld l,(ix+S_LP)
        ld h,(ix+S_LP+1)
        ld b,(ix+S_H)
        ld c,(ix+S_XB)
        exx
        ld l,(ix+S_SV)
        ld h,(ix+S_SV+1)
        ld a,(ix+S_W)
        inc a
        ld (rw_smc+1),a
        exx
rsl:    ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,e
        add a,c
        ld e,a
        jr nc,rsl1
        inc d
rsl1:   push de
        exx
        pop de
rw_smc: ld bc,3
        ldir
        exx
        djnz rsl
        exx
        ret

ds_lp:  dw 0
ds_src: dw 0

; ------------------------------------------------------------
;  VOLCADO DEL ANILLO A LA PANTALLA OCULTA
; ------------------------------------------------------------
volcar:
        ld a,(pantalla)         ; si se ve la 5, la oculta es la 7
        or a
        ld a,0x40
        jr nz,vo1
        ld a,7
        call pon_banco
        ld a,0xC0
vo1:    ld (base),a
        call dibujar_hud
        ld a,(dir)
        or a
        jp nz,volcar_h
;@ SOLO V
        ld a,(linea0)
        ld (vcur),a
        ld a,(pfila)
        ld c,a
        ld b,ALTO
vo_fila:
        push bc
        ld a,c                  ; DE = direccion de la fila C
        and 0x18
        ld d,a
        ld a,(base)
        or d
        ld d,a
        ld a,c
        and 7
        rrca
        rrca
        rrca
        ld e,a
        ld a,(pcol)
        or e
        ld e,a
        ld a,(vcur)             ; HL = LTAB[vcur]
        ld l,a
        ld h,0
        add hl,hl
        push de
        ld de,LTAB
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        pop de
        ld a,(vcur)
        cp LINEAS_V-7           ; si el bloque cruza el final del anillo: linea a linea
        jp nc,vo_lento
        rept 7
        rept ANCHO
        ldi
        endm
        ld a,e
        sub ANCHO
        ld e,a
        inc d
        endm
        rept ANCHO
        ldi
        endm
vo_sig: ld a,(vcur)
        add a,8
        cp LINEAS_V
        jr c,vo2
        sub LINEAS_V
vo2:    ld (vcur),a
        pop bc
        inc c
        dec b
        jp nz,vo_fila
        jp vo_atr
vo_lento:
        ld a,(vcur)
        ld (vl_l),a
        ld b,8
vl1:    push bc
        push de
        ld a,(vl_l)
        ld l,a
        ld h,0
        add hl,hl
        ld de,LTAB
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        pop de
        push de
        rept ANCHO
        ldi
        endm
        pop de
        inc d
        ld a,(vl_l)
        inc a
        cp LINEAS_V
        jr c,vl2
        xor a
vl2:    ld (vl_l),a
        pop bc
        djnz vl1
        jp vo_sig
vo_atr: ld a,(cnt_atr)          ; atributos (solo cuando cambian, una vez por pantalla)
        or a
        ret z
        dec a
        ld (cnt_atr),a
        ld a,(a_attr)           ; origen = ABUF + a_attr*24
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,ABUF
        add hl,de
        ld a,(pfila)
        ld c,a
        ld b,ALTO
va_fila:
        push bc
        push hl
        ld l,c                  ; DE = base+0x1800 + fila*32 + col
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(pcol)
        or l
        ld e,a
        ld a,(base)
        add a,0x18
        add a,h
        ld d,a
        pop hl
        rept ANCHO
        ldi
        endm
        ld a,l
        cp ABUFFIN & 255
        jr nz,va2
        ld a,h
        cp ABUFFIN/256
        jr nz,va2
        ld hl,ABUF
va2:    pop bc
        inc c
        djnz va_fila
        ret

; volcado horizontal: ventana de 24 bytes en lineas de 48
;@ FIN
volcar_h:
        ld a,(paso_h)
        cp 8
        jp c,render_bloques
;@ SOLO H D
        ld a,(c0)
        ld e,a
        ld d,0
        ld hl,BUF
        add hl,de
        ld a,(pfila)
        ld c,a
        ld b,ALTO
vh_fila:
        push bc
        ld a,c                  ; DE = direccion de la fila C
        and 0x18
        ld d,a
        ld a,(base)
        or d
        ld d,a
        ld a,c
        and 7
        rrca
        rrca
        rrca
        ld e,a
        ld a,(pcol)
        or e
        ld e,a
        rept 7
        rept ANCHO
        ldi
        endm
        ld bc,ANCHO
        add hl,bc
        ld a,e
        sub ANCHO
        ld e,a
        inc d
        endm
        rept ANCHO
        ldi
        endm
        ld bc,ANCHO
        add hl,bc
        pop bc
        inc c
        dec b
        jp nz,vh_fila
        ld a,(cnt_atr)
        or a
        ret z
        dec a
        ld (cnt_atr),a
        ld a,(c0)
        ld e,a
        ld d,0
        ld hl,ABUF
        add hl,de
        ld a,(pfila)
        ld c,a
        ld b,ALTO
vha:    push bc
        push hl
        ld l,c                  ; DE = base+0x1800 + fila*32 + col
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(pcol)
        or l
        ld e,a
        ld a,(base)
        add a,0x18
        add a,h
        ld d,a
        pop hl
        rept ANCHO
        ldi
        endm
        ld bc,ANCHO
        add hl,bc
        pop bc
        inc c
        djnz vha
        ret

;@ FIN

; ------------------------------------------------------------
;  LASER DEL JUGADOR
;  Al disparar, el rayo sale del borde del jugador hacia donde mira (8 direcciones; en plataformas,
;  izquierda o derecha) y se traza pixel a pixel: hasta el borde del area, el alcance, el primer
;  tile que detiene disparos (opcional; si es rompible, lo rompe) o el primer enemigo (opcional;
;  si no, lo atraviesa y dana a todos los que toca). El choque con los enemigos usa la caja de sus
;  pixeles de verdad (S_BX..S_BH), asi que el rayo acaba justo donde empieza su dibujo. Se ve
;  C_LDUR fotogramas, siguiendo al jugador y con la misma longitud.
; ------------------------------------------------------------
laser_disparo:
        ld a,(cad_j)
        ld (cool),a
        ld a,4
        ld (disp_t),a
        ld a,2
        call sonido
        call dir_disparo
        add a,a
        ld e,a
        ld d,0
        ld hl,tabla_vel
        add hl,de
        ld a,(hl)
        ld (las_dx),a
        inc hl
        ld a,(hl)
        ld (las_dy),a
        call laser_origen       ; A = pixeles hasta el borde (0 = el origen esta fuera)
        or a
        ret z
        ld b,a
        ld a,(C_LALC)           ; alcance
        or a
        jr z,lsd1
        cp b
        jr nc,lsd1
        ld b,a
lsd1:   ld a,b
        ld (las_len),a
        ld a,(C_LAS)
        and 2
        call nz,laser_tiles
        xor a
        ld (las_ya),a
        ld h,a
        ld l,a
        ld (las_mask),hl
        call laser_enemigos
        ld a,(C_LDUR)
        ld (las_t),a
        ret

; laser_origen: (las_dx), (las_dy) -> (las_x), (las_y) a la salida del jugador y A = pixeles hasta
; el borde del area (contando el origen) o 0 si el origen ya esta fuera
laser_origen:
        ld ix,sprites
        ld a,(las_dx)
        ld c,(ix+S_X)
        ld b,(ix+S_WP)
        call lo_eje
        ld (las_x),a
        ld a,(las_dy)
        ld c,(ix+S_Y)
        ld b,(ix+S_H)
        call lo_eje
        ld (las_y),a
        ld a,(las_x)
        cp 192
        jr nc,lo_fuera
        ld c,a
        ld a,(las_dx)
        ld b,192
        call lo_lim
        ld d,a
        ld a,(las_y)
        cp ALTO*8
        jr nc,lo_fuera
        ld c,a
        ld a,(las_dy)
        ld b,ALTO*8
        call lo_lim
        cp d
        ret c
        ld a,d
        ret
lo_fuera:
        xor a
        ret
; lo_eje: A = d (-1, 0 o 1), C = posicion, B = tamano -> A = coordenada de salida
lo_eje: or a
        jr z,le0
        jp m,le_n
        ld a,c                  ; +1: justo detras de su borde
        add a,b
        ret
le_n:   ld a,c                  ; -1: justo antes (desde 0 queda en 255: fuera)
        dec a
        ret
le0:    ld a,b                  ; 0: en el centro
        srl a
        add a,c
        ret
; lo_lim: A = d, C = origen, B = limite -> A = pixeles hasta el borde contando el origen
lo_lim: or a
        jr z,lm0
        jp m,lm_n
        ld a,b
        sub c
        ret
lm_n:   ld a,c
        inc a
        ret
lm0:    ld a,255
        ret

; lpunto: A = t -> B, C = pixel t del rayo
lpunto: ld e,a
        ld a,(las_dx)
        ld b,a
        ld a,(las_x)
        call zlp1
        ld d,a
        ld a,(las_dy)
        ld b,a
        ld a,(las_y)
        call zlp1
        ld c,a
        ld b,d
        ret
zlp1:    dec b                   ; A = origen, B = d, E = t -> A = origen + d*t
        jr z,lp_mas
        inc b
        ret z
        sub e
        ret
lp_mas: add a,e
        ret

; laser_tiles: acorta el rayo en el primer pixel de un tile que detiene disparos (y si es
; rompible, lo rompe). Se mira cada 4 pixeles y luego se afina pixel a pixel.
laser_tiles:
        xor a
        ld (lt_t),a
zlt1:    ld a,(lt_t)
        ld e,a
        ld a,(las_len)
        cp e
        ret z
        ret c
        ld a,e
        call lpunto
        call flags_en
        and 2
        jr nz,lt_hay
        ld a,(lt_t)
        add a,4
        ld (lt_t),a
        jr zlt1
lt_hay: ld a,(lt_t)
        sub 3
        jr nc,zlt2
        xor a
zlt2:    ld (lt_t),a
lt3:    ld a,(lt_t)
        call lpunto
        call flags_en
        ld d,a
        and 2
        jr nz,lt4
        ld hl,lt_t
        inc (hl)
        jr lt3
lt4:    ld a,(lt_t)
        ld (las_len),a
        ld a,d
        and R_ROMP
        ret z
        jp cambiar_tile         ; B, C = punto del tile rompible

; laser_enemigos: dana a los enemigos que toca el rayo (el primero, o todos si lo atraviesa)
laser_enemigos:
        ld a,255
        ld (las_tmin),a
        ld ix,sprites+SLOT
        ld a,(n_ene)
        ld b,a
lse1:   push bc
        call hostil
        jr z,lse_sig
        call laser_caja         ; NC: lo toca; A = pixel del rayo donde entra
        jr c,lse_sig
        ld c,a
        ld a,(C_LAS)
        and 1
        jr z,lse_atr
        ld a,(las_tmin)
        cp c
        jr c,lse_sig
        jr z,lse_sig
        ld a,c
        ld (las_tmin),a
        ld (las_cand),ix
        jr lse_sig
lse_atr:                        ; atraviesa: dana una vez por disparo a cada enemigo
        pop bc
        push bc
        ld hl,1
        dec b
        jr z,lsa2
lsa1:   add hl,hl
        djnz lsa1
lsa2:   ld de,(las_mask)
        ld a,e
        and l
        jr nz,lse_sig
        ld a,d
        and h
        jr nz,lse_sig
        ld a,e
        or l
        ld e,a
        ld a,d
        or h
        ld d,a
        ld (las_mask),de
        call danar_enemigo
lse_sig:
        ld de,SLOT
        add ix,de
        pop bc
        djnz lse1
        ld a,(las_tmin)
        inc a
        ret z
        ld (las_len),a          ; el rayo llega hasta su primer pixel
        ld a,(las_ya)           ; solo dana una vez por disparo
        or a
        ret nz
        inc a
        ld (las_ya),a
        ld ix,(las_cand)
        jp danar_enemigo

; laser_caja: IX = enemigo -> NC si el rayo entra en la caja de sus pixeles antes de su final,
; con A = pixel del rayo donde entra
laser_caja:
        ld a,(ix+S_X)
        add a,(ix+S_BX)
        ld d,a
        add a,(ix+S_BW)
        dec a
        ld e,a
        ld a,(las_x)
        ld c,a
        ld a,(las_dx)
        call lc_eje
        ret c
        ld a,b
        ld (lc_in),a
        ld a,c
        ld (lc_out),a
        ld a,(ix+S_Y)
        add a,(ix+S_BY)
        ld d,a
        add a,(ix+S_BH)
        dec a
        ld e,a
        ld a,(las_y)
        ld c,a
        ld a,(las_dy)
        call lc_eje
        ret c
        ld a,(lc_in)            ; entrada = la mayor; salida = la menor
        cp b
        jr nc,lc1
        ld a,b
lc1:    ld b,a
        ld a,(lc_out)
        cp c
        jr c,lc2
        ld a,c
lc2:    cp b
        ret c                   ; sale antes de entrar: no se cruzan
        ld a,b
        ld hl,las_len
        cp (hl)
        ccf
        ret
; lc_eje: A = d, C = origen, D, E = caja (primer y ultimo pixel) -> CF=1 si no la cruza;
; si no, B = t de entrada y C = t de salida
lc_eje: or a
        jr z,lce0
        jp m,lce_n
        ld a,e                  ; +1
        cp c
        ret c
        sub c
        push af
        ld a,d
        sub c
        jr nc,lcp1
        xor a
lcp1:   ld b,a
        pop af
        ld c,a
        or a
        ret
lce_n:  ld a,c                  ; -1
        cp d
        ret c
        sub d
        push af
        ld a,c
        sub e
        jr nc,lcn1
        xor a
lcn1:   ld b,a
        pop af
        ld c,a
        or a
        ret
lce0:   ld a,c                  ; 0: tiene que estar dentro
        cp d
        ret c
        ld a,e
        cp c
        ret c
        ld b,0
        ld c,255
        or a
        ret

; laser_cuadro: cada fotograma de juego. Si el laser se ve, sigue al jugador (misma direccion y
; longitud, recortada al area)
laser_cuadro:
        xor a
        ld (las_vis),a
        ld a,(las_t)
        or a
        ret z
        dec a
        ld (las_t),a
        call laser_origen
        or a
        ret z
        ld b,a
        ld a,(las_len)
        cp b
        jr c,lq1
        ld a,b
lq1:    ld (las_dib),a
        or a
        ret z
        ld a,(las_dib)          ; el enemigo que se cruce despues tambien recibe el disparo
        ld (las_len),a          ; (una vez) y, si se para en el enemigo, lo para
        call laser_enemigos
        ld a,(las_len)
        ld (las_dib),a
        ld (las_vis),a
        ld a,(C_LANIM)
        or a
        ret z
        ld hl,las_fase
        inc (hl)
        ret

; dibujar_laser: dibuja el rayo (C_LGRO lineas paralelas, cada una con su byte de dibujo). En el
; modo bloques, encima de la pantalla oculta y ensuciando sus casillas; en los modos con anillo,
; con XOR en el anillo (se llama otra vez despues del volcado para borrarlo)
dibujar_laser:
        ld a,(las_vis)
        or a
        ret z
;@ SOLO B C
        ld a,(base)
        cp 0xC0
        ld a,7
        call z,pon_banco
        ld a,255
        ld (lg_cx),a
;@ FIN
        ld a,(las_dy)           ; perpendicular: (-dy, dx)
        neg
        ld (las_ox),a
        ld a,(las_dx)
        ld (las_oy),a
        ld a,(C_LGRO)
        ld b,a
        dec a
        srl a
        neg
        ld (dl_k),a
        ld hl,C_LPAT
        ld (dl_pat),hl
dl1:    push bc
        ld a,(dl_k)
        ld e,a
        ld a,(las_ox)
        call mul_k
        ld hl,las_x
        add a,(hl)
        ld (ll_x),a
        ld a,(las_oy)
        call mul_k
        ld hl,las_y
        add a,(hl)
        ld (ll_y),a
        ld hl,(dl_pat)
        ld c,(hl)
        inc hl
        ld (dl_pat),hl
        ld a,(las_fase)
        and 7
        jr z,dl2
        ld b,a
dl1r:   rrc c
        djnz dl1r
dl2:    ld a,c
        ld (ll_pat),a
        ld a,(las_dy)
        or a
        jr nz,dl_g
        call linea_h
        jr dl3
dl_g:   call linea_g
dl3:    ld hl,dl_k
        inc (hl)
        pop bc
        djnz dl1
        ret
; mul_k: A = o (-1, 0 o 1), E = k (-1, 0 o 1) -> A = o*k
mul_k:  or a
        ret z
        ld d,a
        ld a,e
        or a
        ret z
        ld a,d
        bit 7,e
        ret z
        neg
        ret

; dir_linea: A = y -> HL = direccion de esa linea del area (anillo o pantalla) en su columna 0
dir_linea:
        ld e,a
        ld d,0
        ld hl,0
        ld a,(dir)
        or a
        jr nz,dli0
        ld a,(linea0)
        ld l,a
dli0:   add hl,de
        add hl,hl
        ld de,(ltab_act)
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ld a,(dir)
        or a
        ret z
        ld a,(c0)
        ld e,a
        ld d,0
        add hl,de
        ret

; linea_h: linea horizontal desde (ll_x, ll_y), las_dib pixeles hacia las_dx. Byte a byte.
linea_h:
        ld a,(ll_y)
        cp ALTO*8
        ret nc
        ld a,(las_dib)
        dec a
        ld e,a
        ld a,(las_dx)
        or a
        ld a,(ll_x)
        jp m,lh_n
        ld (lh_a),a
        add a,e
        ld (lh_b),a
        jr lh1
lh_n:   ld (lh_b),a
        sub e
        ld (lh_a),a
lh1:    ld a,(ll_y)
        call dir_linea
        ld a,(lh_a)
        rrca
        rrca
        rrca
        and 31
        ld c,a
        ld e,a
        ld d,0
        add hl,de
        ld a,(lh_b)
        rrca
        rrca
        rrca
        and 31
        sub c
        inc a
        ld b,a
        ld (lh_cnt),a
        ld a,c
        ld (lh_c),a
        push hl
        ld a,(lh_a)
        and 7
        ld e,a
        ld d,0
        ld hl,tabla_md
        add hl,de
        ld a,(hl)
        ld (lh_m0),a
        ld a,(lh_b)
        and 7
        ld e,a
        ld hl,tabla_mi
        add hl,de
        ld a,(hl)
        ld (lh_m1),a
        pop hl
        ld a,(lh_m0)
        ld d,a
lh2:    ld a,b
        dec a
        jr nz,lh3
        ld a,(lh_m1)
        and d
        ld d,a
lh3:    ld a,(ll_pat)
        and d
;@ SOLO B C
        or (hl)
;@ FIN
;@ SOLO V H D
        xor (hl)
;@ FIN
        ld (hl),a
        inc hl
        ld d,0xFF
        djnz lh2
;@ SOLO B
        ld a,(lh_cnt)
        ld b,a
        ld a,(lh_c)
        ld c,a
        ld a,(ll_y)
        jp ens_tramo
;@ FIN
;@ SOLO V H D C
        ret
;@ FIN

; linea_g: linea vertical o diagonal desde (ll_x, ll_y), las_dib pixeles. Pixel a pixel.
linea_g:
        ld a,(ll_x)
        ld (lg_x),a
        ld a,(ll_y)
        ld (lg_y),a
        ld a,(ll_pat)
        ld (lg_p),a
        ld a,(las_dib)
        ld b,a
lg1:    push bc
        ld a,(lg_p)             ; bit del dibujo de este pixel
        rlca
        ld (lg_p),a
        jr nc,lg_sig
        ld a,(lg_x)
        cp 192
        jr nc,lg_sig
        ld a,(lg_y)
        cp ALTO*8
        jr nc,lg_sig
        call dir_linea
        ld a,(lg_x)
        rrca
        rrca
        rrca
        and 31
        ld e,a
        ld d,0
        add hl,de
        ld a,(lg_x)
        and 7
        ld e,a
        push hl
        ld hl,tabla_bits
        add hl,de
        ld a,(hl)
        pop hl
;@ SOLO B C
        or (hl)
;@ FIN
;@ SOLO V H D
        xor (hl)
;@ FIN
        ld (hl),a
;@ SOLO B
        ld a,(lg_x)             ; casilla sucia (si cambia de casilla)
        rrca
        rrca
        rrca
        and 31
        ld c,a
        ld a,(lg_y)
        rrca
        rrca
        rrca
        rrca
        and 15
        ld b,a
        ld a,(lg_cx)
        cp c
        jr nz,lg_ens
        ld a,(lg_cy)
        cp b
        jr z,lg_sig
lg_ens: ld a,c
        ld (lg_cx),a
        ld a,b
        ld (lg_cy),a
        ld a,(lg_y)
        ld b,1
        call ens_tramo
;@ FIN
lg_sig: ld a,(las_dx)
        ld hl,lg_x
        add a,(hl)
        ld (hl),a
        ld a,(las_dy)
        ld hl,lg_y
        add a,(hl)
        ld (hl),a
        pop bc
        djnz lg1
        ret

;@ SOLO B
; ens_tramo: A = y (pixel), C = primera columna, B = columnas -> casillas sucias en la pantalla oculta
ens_tramo:
        rrca
        rrca
        rrca
        rrca
        and 15
        ld e,a
        ld d,0
        ld hl,SUCF5
        ld a,(base)
        cp 0x40
        jr z,zet1
        ld hl,SUCF7
zet1:    add hl,de
        ld (hl),1
        ld a,e                  ; casilla = fila*24 + columna
        add a,a
        add a,e
        add a,a
        add a,a
        add a,a
        add a,c
        ld e,a
        ld hl,SUCIO5
        ld a,(base)
        cp 0x40
        jr z,et2
        ld hl,SUCIO7
et2:    add hl,de
et3:    ld a,c
        cp ANCHO
        ret nc
        ld a,(hl)
        or a
        jr nz,et4
        ld (hl),1
et4:    inc hl
        inc c
        djnz et3
        ret
;@ FIN

tabla_bits:     db 0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01
tabla_md:       db 0xFF,0x7F,0x3F,0x1F,0x0F,0x07,0x03,0x01
tabla_mi:       db 0x80,0xC0,0xE0,0xF0,0xF8,0xFC,0xFE,0xFF

las_t:     db 0
las_vis:   db 0
las_len:   db 0
las_dib:   db 0
las_dx:    db 0
las_dy:    db 0
las_x:     db 0
las_y:     db 0
las_ox:    db 0
las_oy:    db 0
las_fase:  db 0
las_tmin:  db 0
las_cand:  dw 0
las_ya:    db 0
las_mask:  dw 0
lt_t:      db 0
lc_in:     db 0
lc_out:    db 0
dl_k:      db 0
dl_pat:    dw 0
ll_x:      db 0
ll_y:      db 0
ll_pat:    db 0
lh_a:      db 0
lh_b:      db 0
lh_cnt:    db 0
lh_c:      db 0
lh_m0:     db 0
lh_m1:     db 0
lg_x:      db 0
lg_y:      db 0
lg_p:      db 0
lg_cx:     db 0
lg_cy:     db 0

; destino de las rutinas que no existen en esta variante del motor (vertical, horizontal de 8 en 8
; o por bloques): solo se llaman desde ramas de los otros modos, que esta variante nunca ejecuta
stub_nada:
        ret
        nop
        nop
        nop

; ------------------------------------------------------------
;  UTILIDADES
; ------------------------------------------------------------
; pagina el banco A en 0xC000 respetando la pantalla visible
pon_banco:
        ld (banco),a
        push bc
        ld b,a
        ld a,(pantalla)
        or b
        or 0x10
        ld (BANKM),a
        ld bc,0x7FFD
        out (c),a
        pop bc
        ret

; crea la tabla de direcciones de linea: A = bytes por linea, C = vueltas
crear_ltab:
        ld (lt_smc+1),a
        ld a,b
        ld (lt_n),a
        ld hl,LTAB
lt1:    ld de,BUF
        ld a,(lt_n)
        ld b,a
lt2:    ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        push hl
lt_smc: ld hl,ANCHO
        add hl,de
        ex de,hl
        pop hl
        djnz lt2
        dec c
        jr nz,lt1
        ret

crear_tablas:
ct8:    ; vector de interrupciones IM2
        ld hl,IM2TAB
        ld b,0
ct9:    ld (hl),IM2JP/256
        inc hl
        djnz ct9
        ld (hl),IM2JP/256
        ld a,0xC3
        ld (IM2JP),a
        ld hl,interrupcion
        ld (IM2JP+1),hl
        ret

; preparar_huecos: cuantos huecos de cada clase (configuracion), donde empieza cada clase y la zona
; de guardado del fondo de cada hueco (modos con anillo: el generador reparte los 1024 bytes)
preparar_huecos:
        ld a,(C_NENE)
        ld (n_ene),a
        ld b,a
        ld a,(C_NBJ)
        ld (n_bj),a
        ld c,a
        ld a,(C_NBE)
        ld (n_be),a
        add a,c
        ld (n_bal),a
        add a,b
        inc a
        ld (n_spr),a
        ld hl,sprites+SLOT
        ld de,SLOT
ph1:    add hl,de
        djnz ph1
        ld (p_bj),hl
        ld a,(n_bj)
        ld b,a
ph2:    add hl,de
        djnz ph2
        ld (p_be),hl
        ld a,(n_be)
        ld b,a
        jr ph3b
ph3:    add hl,de
ph3b:   djnz ph3
        ld (p_ult),hl
        ld ix,sprites
        ld hl,SAVE
        ld a,(C_SVJ)
        call ph_sv
        ld a,(n_ene)
        ld b,a
ph5:    ld a,(C_SVE)
        call ph_sv
        djnz ph5
        ld a,(n_bj)
        ld b,a
ph6:    ld a,(C_SVB)
        call ph_sv
        djnz ph6
        ld a,(n_be)
        ld b,a
ph7:    ld a,(C_SVBE)
        call ph_sv
        djnz ph7
        ret
ph_sv:  ld (ix+S_SV),l
        ld (ix+S_SV+1),h
        ld e,a
        ld d,0
        add hl,de
        ld de,SLOT
        add ix,de
        ret

interrupcion:
        push af
        ld a,(cuadros)
        inc a
        ld (cuadros),a
        ld a,(musica_on)
        or a
        jr nz,int_son
        ld a,(sfx_ptr+1)        ; sin musica: solo si suena un efecto (siempre en 0xC000-0xFFFF)
        or a
        jr z,int_fin
int_son:
        push bc                 ; el reproductor usa AF, BC, DE, HL, IX y AF'
        push de
        push hl
        push ix
        ex af,af'
        push af
        ld a,(BANKM)            ; banco 6 (musica) respetando ROM y pantalla visible
        and 0xF8
        or 6
        ld bc,0x7FFD
        out (c),a
        ld a,(musica_on)
        or a
        call nz,PT3_PLAY
        ld hl,(sfx_ptr)         ; efecto de sonido en el canal C, encima de la musica
        ld a,h
        or a
        call nz,sfx_cuadro
        ld a,(BANKM)            ; vuelve el banco que estaba
        ld bc,0x7FFD
        out (c),a
        pop af
        ex af,af'
        pop ix
        pop hl
        pop de
        pop bc
int_fin:
        pop af
        ei
        reti

; sonido: A = efecto (0-7). Empieza a sonar en la siguiente interrupcion; si no hay, no hace nada
sonido:
        push hl
        push de
        add a,a
        ld e,a
        ld d,0
        ld hl,C_SFX
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        or a
        jr z,son1
        ld (sfx_ptr),de
son1:   pop de
        pop hl
        ret

; sfx_cuadro: un fotograma del efecto (banco 6 paginado). HL = posicion. Cada fotograma: volumen y
; banderas (bit 4 tono, bit 5 ruido; 0xFF = fin), tono (2 bytes) y ruido. Escribe el canal C del AY
; despues del reproductor PT3, que lo recalcula entero en cada interrupcion: la musica no se para.
sfx_cuadro:
        ld a,(hl)
        cp 0xFF
        jr z,sfx_fin
        ld d,a
        inc hl
        ld e,(hl)
        ld a,4
        call ay_out
        inc hl
        ld e,(hl)
        ld a,5
        call ay_out
        inc hl
        ld e,(hl)
        bit 5,d
        ld a,6
        call nz,ay_out
        inc hl
        ld (sfx_ptr),hl
        ld a,d
        and 15
        ld e,a
        ld a,10
        call ay_out
        ld a,7                  ; mezclador: se lee el que dejo la musica y se cambia solo el canal C
        ld bc,0xFFFD
        out (c),a
        in a,(c)
        and 0xDB
        bit 4,d
        jr nz,sfx_t
        or 4
sfx_t:  bit 5,d
        jr nz,sfx_n
        or 0x20
sfx_n:  ld e,a
        ld a,7
        jr ay_out
sfx_fin:
        ld hl,0
        ld (sfx_ptr),hl
        ld a,(musica_on)
        or a
        ret nz
        ld e,a
        ld a,10
ay_out: ld bc,0xFFFD            ; A = registro, E = valor
        out (c),a
        ld b,0xBF
        out (c),e
        ret

; musica: HL = modulo PT3 en el banco 6 (0 = silencio)
musica:
        di
        xor a
        ld (musica_on),a
        ld a,(C_MUSP)
        or a
        jr z,mu_fin             ; el juego no tiene musica
        ld a,(BANKM)
        and 0xF8
        or 6
        ld bc,0x7FFD
        out (c),a
        ld a,h
        or l
        jr z,mu_calla
        call PT3_INIT
        ld a,1
        ld (musica_on),a
        jr mu_banco
mu_calla:
        call PT3_MUTE
mu_banco:
        ld a,(BANKM)
        ld bc,0x7FFD
        out (c),a
mu_fin: ei
        ret

borra_pantalla:
        xor a
        out (0xFE),a
        ld hl,0x4000
        ld de,0x4001
        ld bc,6911
        ld (hl),a
        ldir
        ret

espera_suelta:
        xor a
        in a,(0xFE)
        cpl
        and 0x1F
        jr nz,espera_suelta
        ret

espera_tecla:
        call espera_suelta
et1:    xor a
        in a,(0xFE)
        cpl
        and 0x1F
        jr z,et1
        ret

; imprime_lista: HL = lista de textos (fila, columna, atributo, texto, 0 ... 0xFF)
imprime_lista:
        ld a,(hl)
        cp 0xFF
        ret z
        ld b,a
        inc hl
        ld c,(hl)
        inc hl
        ld a,(hl)
        ld (atributo),a
        inc hl
il1:    ld a,(hl)
        inc hl
        or a
        jr z,imprime_lista
        push hl
        call imprime_car
        pop hl
        inc c
        ld a,c
        cp 32
        jr c,il1
        ld c,0
        inc b
        jr il1

; imprime_cadena: HL = texto terminado en 0, B = fila, C = columna (avanza)
imprime_cadena:
        ld a,(hl)
        or a
        ret z
        push hl
        call imprime_car
        pop hl
        inc hl
        inc c
        jr imprime_cadena

imprime_car_av:
        call imprime_car
        inc c
        ret

; imprime_bcd2: A = dos digitos BCD
imprime_bcd2:
        push af
        rrca
        rrca
        rrca
        rrca
        and 15
        add a,'0'
        call imprime_car_av
        pop af
        and 15
        add a,'0'
        jp imprime_car_av

; imprime_bcd6: HL = 3 bytes BCD (6 digitos)
imprime_bcd6:
        ld e,3
ib1:    ld a,(hl)
        push hl
        push de
        call imprime_bcd2
        pop de
        pop hl
        inc hl
        dec e
        jr nz,ib1
        ret

; imprime_car: A = caracter, B = fila, C = columna, en la pantalla (base_txt)
imprime_car:
        push bc
        sub 32
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,fuente
        add hl,de
        ld a,b
        and 0x18
        ld d,a
        ld a,(base_txt)
        or d
        ld d,a
        ld a,b
        and 7
        rrca
        rrca
        rrca
        or c
        ld e,a
        push de
        ld b,8
ic1:    ld a,(hl)
        ld (de),a
        inc hl
        inc d
        djnz ic1
        pop de
        ld a,d                  ; atributo: base + 0x1800 + (fila/8)*256 + ...
        and 0x18
        rrca
        rrca
        rrca
        ld d,a
        ld a,(base_txt)
        add a,0x18
        add a,d
        ld d,a
        ld a,(atributo)
        ld (de),a
        pop bc
        ret

; a_bcd: A (0-99) -> A en BCD (conserva BC)
a_bcd:
        push bc
        ld c,0
ab1:    cp 10
        jr c,ab2
        sub 10
        inc c
        jr ab1
ab2:    ld b,a
        ld a,c
        rlca
        rlca
        rlca
        rlca
        or b
        pop bc
        ret

; ------------------------------------------------------------
;  MENSAJES A PANTALLA COMPLETA: HL = texto (banco 3), A = 1 si lleva
;  el numero (num_msg), B = fotogramas de espera
; ------------------------------------------------------------
mensaje:
        ld (msg_con),a
        push bc
        push hl
        xor a
        out (0xFE),a
        ld (pantalla),a
        ld a,0x40
        ld (base_txt),a
        ld a,1                  ; marco en la pantalla visible y area limpia
        call pon_banco
        ld hl,0xC000+6912
        ld de,0x4000
        ld bc,6912
        ldir
        call limpiar_area
        ld a,3
        call pon_banco
        pop hl
        ld a,(pfila)
        add a,ALTO/2-1
        ld (ms_fila),a
ms0:    ld de,buf_msg
        ld b,0
ms1:    ld a,(hl)
        or a
        jr z,ms2
        inc hl
        cp '|'
        jr z,ms2
        ld (de),a
        inc de
        inc b
        ld a,b
        cp 20
        jr c,ms1
        xor a
ms2:    ld (ms_sep),a
        push hl
        ld a,(msg_con)
        or a
        jr z,ms3
        ld a,' '
        ld (de),a
        inc de
        ld a,(num_msg)
        rrca
        rrca
        rrca
        rrca
        and 15
        add a,'0'
        ld (de),a
        inc de
        ld a,(num_msg)
        and 15
        add a,'0'
        ld (de),a
        inc de
        inc b
        inc b
        inc b
ms3:    xor a
        ld (de),a
        ld a,ANCHO              ; centrado en el area de juego
        sub b
        srl a
        ld c,a
        ld a,(pcol)
        add a,c
        ld c,a
        ld a,(ms_fila)
        ld b,a
        ld a,(C_MSGA)
        ld (atributo),a
        ld hl,buf_msg
        call imprime_cadena
        pop hl
        xor a
        ld (msg_con),a
        ld a,(ms_sep)
        or a
        jr z,ms5
        ld a,(ms_fila)          ; segunda linea
        add a,2
        ld (ms_fila),a
        jr ms0
ms5:    pop bc
ms4:    halt
        djnz ms4
        ret

; limpia el area de juego en la pantalla 5
limpiar_area:
        ld a,(pfila)
        ld c,a
        ld b,ALTO
la1:    push bc
        ld a,c
        and 0x18
        or 0x40
        ld d,a
        ld a,c
        and 7
        rrca
        rrca
        rrca
        ld e,a
        ld a,(pcol)
        or e
        ld e,a
        ld b,8
la2:    push bc
        push de
        ld h,d
        ld l,e
        ld (hl),0
        inc de
        ld bc,ANCHO-1
        ldir
        pop de
        inc d
        pop bc
        djnz la2
        pop bc
        push bc
        ld l,c                  ; atributos: 0x5800 + fila*32 + col
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(pcol)
        ld e,a
        ld d,0
        add hl,de
        ld de,0x5800
        add hl,de
        ld d,h
        ld e,l
        inc de
        ld (hl),0
        ld bc,ANCHO-1
        ldir
        pop bc
        inc c
        djnz la1
        ret

; ------------------------------------------------------------
;  MARCADOR (se dibuja en la pantalla oculta, desde volcar)
;  5 elementos de 13 bytes: activo, fila, col, atributo, etiqueta (9)
;  0 puntos, 1 record, 2 vidas, 3 energia, 4 fase
; ------------------------------------------------------------
dibujar_hud:
        ld a,(cnt_hud)
        or a
        ret z
        dec a
        ld (cnt_hud),a
        ld a,(base)
        ld (base_txt),a
        ld ix,C_HUD
        xor a
hud1:   ld (hud_k),a
        ld a,(ix+0)
        or a
        jr z,hud_sig
        ld a,(ix+3)
        ld (atributo),a
        ld b,(ix+1)
        ld c,(ix+2)
        push ix
        pop hl
        ld de,4
        add hl,de
        call imprime_cadena
        ld a,(hud_k)
        or a
        jr nz,hud_r
        ld hl,puntos
        call imprime_bcd6
        jr hud_sig
hud_r:  dec a
        jr nz,hud_v
        ld hl,record
        call imprime_bcd6
        jr hud_sig
hud_v:  dec a
        jr nz,hud_e
        ld a,(vidas)
        add a,'0'
        call imprime_car_av
        jr hud_sig
hud_e:  dec a
        jr nz,hud_f
        ld a,(C_ENER)
        ld e,a
        ld d,0
he1:    ld a,d
        ld hl,energia
        cp (hl)
        ld a,' '
        jr nc,he2
        ld a,127
he2:    push de
        call imprime_car_av
        pop de
        inc d
        dec e
        jr nz,he1
        jr hud_sig
hud_f:  ld a,(nivel)
        inc a
        call a_bcd
        call imprime_bcd2
hud_sig:
        ld de,13
        add ix,de
        ld a,(hud_k)
        inc a
        cp 5
        jr c,hud1
        ld a,(C_HUDOBJ)         ; inventario: simbolo de cada elemento que se lleva, '.' si no
        or a
        ret z
        ld a,(C_HUDOBJ+3)
        ld (atributo),a
        ld a,(C_HUDOBJ+1)
        ld b,a
        ld a,(C_HUDOBJ+2)
        ld c,a
        ld a,(C_NELEM)
        or a
        ret z
        ld e,a
        ld a,(inv)
        ld d,a
        ld hl,C_SIMB
hob1:   ld a,'.'
        srl d
        jr nc,hob2
        ld a,(hl)
hob2:   push hl
        push de
        call imprime_car_av
        pop de
        pop hl
        inc hl
        dec e
        jr nz,hob1
        ret

; sumar_puntos: A = decenas de puntos en BCD (0x25 = 250 puntos)
sumar_puntos:
        ld e,a
        and 15
        rlca
        rlca
        rlca
        rlca
        ld d,a                  ; decenas -> nibble alto del byte bajo
        ld a,e
        rrca
        rrca
        rrca
        rrca
        and 15
        ld e,a                  ; centenas -> byte medio
        ld hl,puntos+2
        ld a,(hl)
        add a,d
        daa
        ld (hl),a
        dec hl
        ld a,(hl)
        adc a,e
        daa
        ld (hl),a
        dec hl
        ld a,(hl)
        adc a,0
        daa
        ld (hl),a
        ret

actualizar_record:
        ld hl,puntos
        ld de,record
        ld b,3
ar1:    ld a,(de)
        cp (hl)
        jr c,ar_copia
        ret nz
        inc hl
        inc de
        djnz ar1
        ret
ar_copia:
        ld hl,puntos
        ld de,record
        ld bc,3
        ldir
        ret

; fin_nivel: el jugador llega al final del mapa -> evento 2
;@ SOLO V H B
fin_nivel:
        ld ix,sprites
        ld a,(dir)
        or a
        jr nz,fn_h
        ld hl,(tpx)
        ld a,h
        or l
        ret nz
        ld a,(ix+S_Y)
        cp 4
        ret nc
        jr fn_si
fn_h:   ld hl,(largo2)
        ld de,ANCHO
        or a
        sbc hl,de
        ld de,(izq)
        or a
        sbc hl,de
        ret nz
        ld a,(fino)
        or a
        ret nz
        ld a,(ix+S_X)
        add a,(ix+S_WP)
        cp 192-3
        ret c
fn_si:  ld a,(evento)
        or a
        ret nz
        ld a,2
        ld (evento),a
        ret

;@ FIN
; eventos al final de un fotograma: 1 = sin vidas, 2 = fase superada
evento_juego:
        cp 3
        jr c,ev_viejo
        push af                 ; 3 ir a fase, 4 ganar, 5 perder: primero su mensaje
        ld a,(ob_msg)
        add a,a
        ld e,a
        ld d,0
        ld hl,C_MSGS
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ld a,h
        or l
        jr z,ev_m1
        xor a
        ld b,150
        call mensaje
ev_m1:  pop af
        cp 6
        jr z,ev_seguir
        cp 3
        jr nz,ev_fin
        ld a,(ob_val)           ; ir a la fase N (1..)
        dec a
        ld hl,C_NNIV
        cp (hl)
        jr c,ev_m2
        xor a
ev_m2:  ld (nivel),a
        jp nivel_inicio
ev_fin: call actualizar_record  ; ganar o perder: fin de la partida
        jp menu_inicio
ev_seguir:                      ; mensaje y la partida sigue: se redibuja todo
        xor a
        ld (evento),a
        ld a,2
        ld (cnt_atr),a
        ld (cnt_hud),a
;@ SOLO B
        ld a,(bloques)
        or a
        jp z,bucle
        ld hl,SUCIO5
        ld de,SUCIO5+1
        ld bc,0x023F
        ld (hl),1
        ldir
;@ FIN
        jp bucle
ev_viejo:
        cp 1
        jr nz,ev_nivel
        ld hl,(C_MSGGO)
        xor a
        ld b,150
        call mensaje
        call actualizar_record
        jp menu_inicio
ev_nivel:
        ld a,(nivel)
        inc a
        ld (nivel),a
        ld hl,C_NNIV
        cp (hl)
        jp c,nivel_inicio
        ld hl,(C_MSGFIN)
        xor a
        ld b,200
        call mensaje
        call actualizar_record
        jp menu_inicio

; ------------------------------------------------------------
;  VARIABLES
; ------------------------------------------------------------
atributo:  db 0x47
pantalla equ RAMB+0            ; 0 = se ve el banco 5, 8 = se ve el banco 7
banco equ RAMB+1              
cuadros equ RAMB+2            
reloj equ RAMB+3              
base:      db 0x40
cnt_atr equ RAMB+4            
tpx equ RAMB+5                 ; vertical: linea del mundo arriba de la vista (pixeles)
tmax equ RAMB+7               
linea0 equ RAMB+9              ; tpx mod 168: linea del anillo arriba de la vista
r_top equ RAMB+10              ; filas del mundo cargadas en el anillo
r_bot equ RAMB+12             
a_top equ RAMB+14              ; sus filas en el anillo (mod 21)
a_bot equ RAMB+15             
arow equ RAMB+16               ; fila de tiles de la que se toman los colores
a_attr equ RAMB+18            
paso_v:    db 8
paso_h:    db 8
fino equ RAMB+19               ; horizontal fino: pixeles de desplazamiento dentro del byte (0-7)
bloques equ RAMB+20            ; 1 = scroll horizontal fino por bloques pre-desplazados
ltab_act:  dw LTAB      ; tabla de lineas donde se dibujan los sprites
ritmo:     db 2         ; interrupciones por fotograma de juego (cadencia fija)
vc_pos equ RAMB+21            
rb_fila equ RAMB+22           
rb_n equ RAMB+23              
bc_tpl equ RAMB+24            
dz_cnt equ RAMB+25            
se_f0 equ RAMB+26             
se_f1 equ RAMB+27             
se_c0 equ RAMB+28             
par_tam:   dw 16
comp_bj equ RAMB+29           
ct_id equ RAMB+30             
ct_fila equ RAMB+31           
np_izq equ RAMB+32            
np_dch equ RAMB+33            
inv equ RAMB+34                ; inventario: un bit por elemento
reg_ptr:   dw REG_INI   ; siguiente anotacion libre del registro de cambios
ob_acc equ RAMB+35            
ob_val equ RAMB+36            
ob_msg equ RAMB+37            
comp_be equ RAMB+38           
rb_vc equ RAMB+39             
rb_sf equ RAMB+41             
se_sf equ RAMB+43             
ultimo_paso: db 8
vcur equ RAMB+45              
vl_l equ RAMB+46              
lt_n:      db 160
anillo equ RAMB+47            
fmundo equ RAMB+48            
tiles equ RAMB+50             
mapa equ RAMB+52              
pcol:      db 4
pfila:     db 2
velocidad: db 1
umbral:    db 48
umbral_r:  db 40
dir equ RAMB+54               
auto equ RAMB+55              
retro equ RAMB+56             
vel_auto:  db 4
auto_cnt:  db 4
largo2 equ RAMB+57            
izq equ RAMB+59               
c0 equ RAMB+61                
entrada_j equ RAMB+62         
dir_j equ RAMB+63             
pf_dst equ RAMB+64            
pf_adst equ RAMB+66           
pf_mapa equ RAMB+68           
pf_mitad equ RAMB+70          
apar equ RAMB+71              
progreso equ RAMB+73          
ap_l equ RAMB+75               ; primera columna entera a la vista (para reapariciones por la izquierda)
ap_ent equ RAMB+77            
ap_lv equ RAMB+79             
ap_trans equ RAMB+81          
cad_j:     db 6
cool equ RAMB+82              
invul equ RAMB+83             
golpes equ RAMB+84            
fr_bala_j equ RAMB+85         
fr_bala_e equ RAMB+87         
cx0 equ RAMB+89               
cy0 equ RAMB+90               
cx1 equ RAMB+91               
cy1 equ RAMB+92               
cmask equ RAMB+93             
px equ RAMB+94                
py equ RAMB+95                
banco_nivel equ RAMB+96       
base_txt:  db 0x40
vidas:     db 3
energia:   db 3
nivel equ RAMB+97             
puntos equ RAMB+98            
record equ RAMB+101           
cnt_hud equ RAMB+104          
evento equ RAMB+105           
kempston equ RAMB+106         
musica_on equ RAMB+107        
hud_k equ RAMB+108            
msg_con equ RAMB+109          
num_msg equ RAMB+110          
estado_v equ RAMB+111         
idx_v equ RAMB+112            
salto_listo equ RAMB+113      
mira_j:    db 2
seguro_x equ RAMB+114         
seguro_y equ RAMB+115         
n_pasos equ RAMB+116          
ff_fin equ RAMB+117           
ff_acc equ RAMB+118           
vanim_j:   db 4
dfijo equ RAMB+119            
alen_j equ RAMB+120           
acnt_j:    db 1
afr_j equ RAMB+128            
quieto_j:  db 1
disp_t equ RAMB+129           
tipos:     ds 16*FICHA
cajas:     ds 64
sprites:   ds SLOT*NSPR_MAX
sfx_ptr equ RAMB+130          
fr_muerte equ RAMB+132        
col_entrada equ RAMB+134      
muerte equ RAMB+136           
mue_x equ RAMB+137            
mue_y equ RAMB+138            
mue_ev equ RAMB+139           
agachado equ RAMB+140         
agacha_ok equ RAMB+141        
npc_cool equ RAMB+142         
via_puerta equ RAMB+143       
ms_fila equ RAMB+144          
ms_sep equ RAMB+145           
vx      equ RAMB+146          ; inercia: velocidad en 1/16 px (con signo)
vfrac   equ RAMB+147          ; y fraccion acumulada
ct_fx   equ RAMB+148          ; x e y del mundo (mod 16) del ultimo punto mirado en el mapa
ct_fy   equ RAMB+149
ct_meta equ RAMB+150          ; (tiles de 8x8) tile del mapa del ultimo punto
csz     equ RAMB+151          ; tamano de celda: 16 u 8
cmsk    equ RAMB+152          ; y su mascara: 15 o 7
lb_eds  equ RAMB+153
lb_nx   equ RAMB+154
lb_ny   equ RAMB+155
lb_e    equ RAMB+156
RAMB_LEN equ 157
n_ene:     db 6
n_bj:      db 3
n_be:      db 4
n_bal:     db 7
n_spr:     db 14
p_bj:      dw 0
p_be:      dw 0
p_ult:     dw 0
fin_motor:
        end
