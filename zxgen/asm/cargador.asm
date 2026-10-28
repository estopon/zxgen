; ============================================================
;  CARGADOR 128K  -  se carga en 0x5E00 desde el BASIC
;  Lee una tabla de bloques sin cabecera y coloca cada uno
;  en su banco de memoria. Despues salta al motor.
;  Tabla (la añade el generador detras del codigo):
;     byte  numero de bloques
;     por bloque: byte banco, word direccion, word longitud
;     word  direccion de entrada al motor
; ============================================================
BANKM   equ 23388
LDBYTES equ 0x0556

        org 0x5E00
inicio:
        di
        ld sp,0x6000
        ld hl,tabla
        ld b,(hl)
        inc hl
siguiente:
        push bc
        ld a,(hl)               ; banco destino
        inc hl
        or 0x10                 ; ROM 1 (48 BASIC) con la rutina de carga
        ld (BANKM),a
        ld bc,0x7FFD
        out (c),a
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push de
        pop ix                  ; IX = direccion
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl                  ; DE = longitud
        push hl
        ld a,0xFF               ; bloque de datos
        scf                     ; cargar (no verificar)
        call LDBYTES
        di
        pop hl
        pop bc
        jr nc,error
        djnz siguiente
        ld a,0x10               ; banco 0 en 0xC000, ROM 1
        ld (BANKM),a
        ld bc,0x7FFD
        out (c),a
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        jp (hl)                 ; al motor
error:
        ld a,2                  ; borde rojo: error de carga
        out (0xFE),a
        jr error
tabla:
        end
