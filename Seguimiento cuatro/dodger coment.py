from machine import Pin, I2C, PWM  # Importa control de pines, comunicación I2C y PWM (sonido)
from time import ticks_ms, ticks_diff  # Funciones para manejar tiempo en milisegundos
import ssd1306, random  # Librería de pantalla OLED y números aleatorios

# OLED
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Inicializa I2C con pines 22 (SCL) y 21 (SDA)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # Crea pantalla OLED de 128x64

# Si la función fill_rect no existe, la toma del frame buffer interno
if not hasattr(oled, "fill_rect"):
    oled.fill_rect = oled.framebuf.fill_rect

# BOTONES
up_btn = Pin(13, Pin.IN, Pin.PULL_UP)     # Botón subir
down_btn = Pin(12, Pin.IN, Pin.PULL_UP)   # Botón bajar
start_btn = Pin(14, Pin.IN, Pin.PULL_UP)  # Botón start

# Estados anteriores (para detectar pulsación, no mantener)
prev_up = prev_down = prev_start = 1

def read_buttons():
    global prev_up, prev_down, prev_start

    u=d=s=False  # Variables de salida

    cu = up_btn.value()     # Estado actual botón arriba
    cd = down_btn.value()   # Estado actual botón abajo
    cs = start_btn.value()  # Estado actual botón start

    # Detecta solo cuando se presiona (flanco de bajada)
    if prev_up==1 and cu==0: u=True
    if prev_down==1 and cd==0: d=True
    if prev_start==1 and cs==0: s=True

    # Guarda estados actuales
    prev_up, prev_down, prev_start = cu, cd, cs
    return u,d,s

# BUZZER
buzzer = PWM(Pin(27))  # Buzzer en pin 27
buzzer.duty(0)         # Apagado

def beep(f,d):
    buzzer.freq(f)       # le decimos al buzzer que use frecuencia
    buzzer.duty(512)     # encendido a nivel medio porque va de 0 a 1023
    import time
    time.sleep_ms(d)     # Duración
    buzzer.duty(0)       # Apaga sonido

# Sonidos
def mario_lose():
    beep(784,120); beep(659,120); beep(523,150); beep(392,220)
    # Reproduce una secuencia de sonidos cuando pierdes (como efecto de derrota)

def mario_win():
    beep(523,90); beep(659,90); beep(784,90); beep(1047,180)
    # Reproduce una secuencia de sonidos cuando ganas

def pause_sound():
    beep(880,70); beep(660,90)
    # Sonido corto al pausar o reanudar el juego

def jump_sound():
    beep(1200,40)
    # Sonido rápido cuando el personaje salta


#  MUSICA MODO TIME 
music_notes = [523,0,659,0,784,0,659,0]
# Lista de notas musicales que el buzzer va a tocar(frecuencias en Hz)

music_index = 0
# Índice actual de la nota que se está reproduciendo

music_timer = 0
# Guarda el último tiempo en que cambió la nota

def music_update(now):
    global music_index, music_timer

    # Verifica si ya pasaron 220 ms desde la última nota
    if ticks_diff(now, music_timer) > 220:
        music_timer = now  # Actualiza el tiempo

        n = music_notes[music_index]  # Toma la nota actual

        if n == 0:
            buzzer.duty(0)  # Si es 0, apaga el sonido
        else:
            buzzer.freq(n)      # Cambia la frecuencia
            buzzer.duty(180)    # Activa el sonido (más suave)

        # Avanza a la siguiente nota (y vuelve al inicio al terminar)
        music_index = (music_index+1) % len(music_notes)


# SPRITE (PERSONAJE) 
CRAB1 = [
"00111000","01000010","10100101","11111111",
"10111101","11111111","01011010","10000001",
]
# Primer frame del personaje (matriz de píxeles)

CRAB2 = [
"00111000","01000010","10100101","11111111",
"10111101","11111111","00100100","01000010",
]
# Segundo frame (para animación, cambia patas)

# Dibuja el sprite en pantalla
def draw_sprite(s,x,y):  # s sprite (matrix de caracteres 0 y 1) x, y posicion en el que se va a dibujar en la pantalla
    for r,row in enumerate(s): # recorre cada fila del s, r numero de filas 0,1,2 row contenido de esa fila
        for c,p in enumerate(row): #recorre cada columna, p valor del pixel 1 o 0
            if p=="1": # solo dibuja cuando hay un 1
                oled.pixel(x+c,y+r,1)  # x+c posicion horizontal, y+r posicion vertical ( lo dibuja en la pantalla)


#  ESTADOS DEL JUEGO 
MENU,GAME,PAUSE,OVER,WIN = 0,1,2,3,4
# Define constantes para los estados del juego

state=MENU
# Estado inicial: menú


#  MODOS 
mode=0
# Modo actual seleccionado

modes=["CLASICO","TIME","HARDCORE"]
# Lista de nombres de los modos


# PLAYER 
x=10
# Posición horizontal del jugador (casi fija)
y=40
# Posición vertical del jugador
vel=0
# Velocidad vertical (para salto o movimiento)

gravity=2
# Aceleración hacia abajo

jump=-9
# Velocidad inicial del salto (negativa = hacia arriba)


#  VARIABLES DEL JUEGO 
obs=[]
# Lista de obstáculos (cada uno tiene posición y tamaño)

last_spawn=0
# Último momento en que apareció un obstáculo

spawn_delay=1200
# Tiempo entre generación de obstáculos (ms)

start_time=0
# Momento en que empieza la partida

score=0
# Puntaje actual

speed=2
# Velocidad del juego (qué tan rápido se mueven los obstáculos)
prev_score_time = 0
# Guarda el puntaje anterior (modo TIME)
beat_record = False
# Indica si ya superaste tu récord (para no repetir sonido)
frame=0
# Frame actual del sprite (0 o 1)

last_anim=0
# Último tiempo en que cambió la animación

# HITBOX (colisión)
P_W, P_H = 6, 6   # tamaño del muñeco 6x6
P_OFF = 1  # posicion del muñeco

def reset():
    global y,vel,obs,score,start_time,speed,last_spawn
    global prev_score_time, beat_record
    # Declara variables globales para poder modificarlas dentro de la función

    if mode==1:   # si el modo es 1 que es time 
        prev_score_time = score  # Guarda el puntaje anterior en modo TIME

    y = 32 if mode==1 else 40  # Posición inicial (más arriba en modo TIME)
    vel=0                      # Reinicia velocidad
    obs=[]                     # Borra obstáculos
    score=0                    # Reinicia puntaje
    start_time=ticks_ms()      # Guarda tiempo de inicio
    last_spawn=ticks_ms()      # Reinicia spawn
    beat_record = False        # Reinicia bandera de récord

    # Ajusta velocidad según modo
    if mode==0:
        speed = 3
    elif mode==2:
        speed = 8
    else:
        speed = 2


def spawn(now):    # obstaculos
    global last_spawn, spawn_delay
    # Usa variables globales

    # Genera obstáculo si pasó suficiente tiempo
    if ticks_diff(now,last_spawn) > spawn_delay:

        if mode==1:  # si el modo es 1 (time)
            # Obstáculos tipo "túnel" (como Flappy Bird)
            gap_y = random.randint(20, 40)  # altura del hueco
            gap_h = 22                      # Tamaño del hueco

            # Parte superior
            obs.append([128, 0, gap_y - gap_h//2])   # posicion en X (lado derecho de la pantalla) 0 empieza desde arriba (gap_y - gap_h//2)altura hasta donde llega el bloque 
            # Parte inferior
            obs.append([128, gap_y + gap_h//2, 64 - (gap_y + gap_h//2)])

            spawn_delay = random.randint(900, 1400)  # Tiempo aleatorio para el siguiente obstaculo

        else:  # si no es modo =1
            # Obstáculo en el suelo
            size = random.choice([5,10])  # Tamaño aleatorio
            obs.append([128, 48-size, size])  # aparece en la derecha, posicion vertical, altura del obstaculo

            # Ajusta dificultad
            if mode==2:
                spawn_delay = random.randint(400,700) # hace que los obstaculos aparezcan mas seguido
            else:
                spawn_delay = random.randint(600,1100) # aparecen mas lento

        last_spawn = now  # Actualiza tiempo de spawn


# Detecta colisión entre jugador y obstáculo
def collide(px,py, ox,oy, ow,oh): 
    px += P_OFF; py += P_OFF  # Ajusta la posición del jugador con ese pequeño offset que definiste antes
    return not (px+P_W <= ox or ox+ow <= px or py+P_H <= oy or oy+oh <= py)
    # Retorna True si hay colisión


def update(now, up, down):
    global y,vel,score,speed,beat_record,spawn_delay
    # Función principal del juego (física + lógica)

    if mode==1:
        # Movimiento libre (sube y baja)
        target = 0
        if up: target = -2  
        if down: target = 2

        vel += (target - vel)*0.25  # Suaviza movimiento
        y += vel # se aplica la velocidad=se mueve el personaje

        # Límites de pantalla
        if y<0: y=0
        if y>56: y=56

    else:
        # Modo salto
        if up and y>=40: # si se presiona arriba y estas en el suelo y=40
            if mode == 0:
                vel = jump - 2  # Salto más alto en clásico
            else:
                vel = jump # velocidad inicial de salto
            jump_sound() # reproduce el sonido de salto

        vel += gravity  # Aplica gravedad
        if vel>10: vel=10 # limita la velocidad de caida
        y += vel # actualiza la posicion vertical 

        # Evita que atraviese el suelo
        if y>=40: 
            y=40
            vel=0

    # Aumenta dificultad con el tiempo
    if mode==0:
        elapsed = ticks_diff(now, start_time)//1000 # calcula cuanto tiempo llevas jugando
        speed = 3 + (elapsed*0.08) # aumenta la velocidad del juego con el tiempo
        spawn_delay = int(1100 - (elapsed*8)) # hace que aparezcan mas seguido
        if spawn_delay < 500: # evita que el juego se vuelva imposible
            spawn_delay = 500

    elif mode==2:
        speed += 0.01  # Hardcore acelera más
    else:
        speed += 0.002

    # Mueve obstáculos hacia la izquierda
    for o in obs:
        o[0] -= speed  # mueve todos los obstaculos hacia la izquierda

    new=[] # guarda solo los obstaculos que siguen en pantalla
    for o in obs: # vuelves a recorrer todos los obstaculos
        if o[0]>-10: # -10 ya no esta a la vista del jugador
            new.append(o)  # Mantiene los visibles
        else:
            score+=1  # Suma punto al esquivar

            # Sonido si supera récord en TIME
            if mode==1 and not beat_record and score > prev_score_time:
                beep(1500,80)
                beat_record = True

    obs[:] = new  # Actualiza lista y la mantiene en memoria

    # Verifica colisiones
    for o in obs: # recorre todos los obstaculos que hay en pantalla
        if collide(x,int(y), int(o[0]), int(o[1]), 6, int(o[2])): # verifica si el jugador choco con ese obstaculo
            mario_lose() 
            return False  # Pierde

    # Gana en modo TIME
    if mode==1 and ticks_diff(now,start_time) > 45000:
        return "time"

    return True  # Sigue jugando


def draw():
    oled.fill(0)  # Limpia pantalla

    if mode!=1:
        oled.fill_rect(0,48,128,2,1)  # Dibuja suelo

    global frame,last_anim

    # Cambia sprite cada 150 ms (animación)
    if ticks_diff(ticks_ms(),last_anim) > 150:
        frame = 1-frame
        last_anim = ticks_ms()

    # Dibuja personaje
    draw_sprite(CRAB1 if frame==0 else CRAB2, x, int(y)) # 0 es la imagen 1 y sino la imagen 2

    # Dibuja obstáculos
    for o in obs:
        oled.fill_rect(int(o[0]), int(o[1]), 6, int(o[2]), 1)

    # Texto en pantalla
    if mode==1:
        t = 45 - ticks_diff(ticks_ms(),start_time)//1000
        oled.text("S:"+str(score),0,52)          # Score
        oled.text("O:"+str(prev_score_time),45,52)  # Récord
        oled.text("T:"+str(t),90,52)             # Tiempo
    else:
        oled.text("S:"+str(score),0,52)

    oled.show()  # Actualiza pantalla


def draw_menu():
    oled.fill(0) # limpia la pantalla para iniciar desde 0 
    oled.text("MENU",40,0) # lo escribe arriba

    # Muestra lista de modos
    for i,m in enumerate(modes): # recorre la lista de los modos
        if i==mode:
            oled.text(">",10,20+i*10)  # Indicador
        oled.text(m,20,20+i*10) # separa cada opcion verticalmente

    oled.show() # actualiza la pantalla


def draw_pause():
    oled.fill(0) 
    oled.text("PAUSA",40,20) # lo escribe arriba y centrado
    oled.text("START=SEGUIR",18,36) # lo escriba arriba
    oled.show() # actualiza pantalla


#  LOOP PRINCIPAL 
last_frame=0

while True: # loop infinito
    now=ticks_ms() # tiempo actual para anima,music,control FPS

    # Controla FPS (~30)
    if ticks_diff(now,last_frame) < 33:
        continue 
    last_frame = now # evita que el juego vaya muy rapido

    up,down,start = read_buttons()  # Lee botones

    if state==MENU:
        draw_menu() # dibuja el menu

        if up:
            mode=(mode-1)%3; beep(900,40)  # Cambia modo
        if down:
            mode=(mode+1)%3; beep(900,40)
        # hace que suene al moverte por el menu
        if start:
            reset(); state=GAME  # Inicia juego

    elif state==GAME:

        if mode==1:
            music_update(now)  # Música en modo TIME

        if start: # si se presiona el oausa mientras juegas
            pause_sound() # reproduce el sonido
            state=PAUSE # cambia el estado
            continue # salta al resto del loop

        # Empieza spawn después de 2 segundos
        if ticks_diff(now,start_time) > 2000:
            spawn(now)

        result = update(now, up, down)  # mueve personaje obstacu,coliciones
        draw()                          # dibuja toda la pantalla

        if result == False: # segun lo que devuelve el updat 
            state=OVER  # Perdió
        elif result == "time":
            state=WIN   # Ganó

    elif state==PAUSE:
        draw_pause() # muestra pantalla en pausa
        if start: # si presiona start
            pause_sound() 
            state=GAME # quita el pausa vuelve al juego

    elif state==OVER:
        oled.fill(0)
        oled.text("GAME OVER",20,30) # mensaje que perdio
        oled.text("S:"+str(score),30,45) # ountaje obtenido
        oled.show()

        if start:
            state=MENU  # Vuelve al menú

    elif state==WIN:
        oled.fill(0) # limpia pantalla
        oled.text("TIME!",40,30) # si sobrevivio todo el tiempo
        oled.text("S:"+str(score),30,45) # muestra puntaje
        oled.show() # envia lo que se dibujo a la pantalla

        if start:
            state=MENU # vuelve al menu