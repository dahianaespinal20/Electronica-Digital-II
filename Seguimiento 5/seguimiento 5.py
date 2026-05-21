# LIBRERIAS

from machine import Pin, PWM, I2C
# Pin -> utilizar pines del ESP32 como entrada o salida.
# PWM -> controlar el buzzer con señales PWM.
# I2C -> comunicación entre ESP32 y sensores.

import network
# Librería para conectar el ESP32 a WiFi.

import socket
# Librería para crear el servidor web.

import time
# Librería para manejar tiempos y pausas.

import math
# Librería para operaciones matemáticas.

import urequests
# Librería para que el ESP32 se comunique con internet,
# por ejemplo Telegram.

import dht
# Librería para utilizar sensores DHT11/DHT22.

from mpu6050 import MPU6050
# Librería/controlador del sensor MPU6050.


# WIFI


SSID = "DANIELA"
# Nombre de la red WiFi.

PASSWORD = "1000895580"
# Contraseña del WiFi.


# TELEGRAM


BOT_TOKEN = "8641360210:AAFsA8xRB7a5iasvpu034Y7ssxebVXN6fcY"
# Token del bot de Telegram.

CHAT_ID = "5013881618"
# Usuario o chat donde llegarán las alertas.


# LIMITES


TEMP_MIN = 25
# Temperatura mínima permitida.

TEMP_MAX = 35
# Temperatura máxima permitida.

HUM_MIN = 40
# Humedad mínima permitida.

HUM_MAX = 60
# Humedad máxima permitida.


# I2C MPU6050


i2c = I2C(
    0,
    # Utilizamos el bus I2C número 0.

    scl=Pin(22),
    # Pin del reloj de comunicación.

    sda=Pin(21),
    # Pin por donde viajan los datos.

    freq=400000
    # Comunicación a 400 kHz.
)


# DHT11


sensor_dht = dht.DHT11(Pin(4, Pin.IN, Pin.PULL_UP))
# Configuramos el sensor DHT11 en el pin 4.


# MPU6050


mpu = MPU6050(i2c)
# Configuramos el MPU6050 usando I2C.

mpu.wake()
# Despertamos el sensor para que empiece a medir.


# BUZZER


buzzer = PWM(Pin(25))
# Configuramos el buzzer en el pin 25.

buzzer.duty_u16(0)
# Inicialmente el buzzer está apagado.


# BOTON PANICO


panic_button = Pin(18, Pin.IN, Pin.PULL_UP)
# Botón de pánico configurado como entrada pull-up.


# VARIABLES


temperature = 0
# Variable para guardar temperatura.

humidity = 0
# Variable para guardar humedad.

movement_state = "REPOSO"
# Estado inicial de movimiento.

alarm_state = "NORMAL"
# Estado inicial de alarma.


# ESTADOS ALERTA


temp_alert_sent = False
# Verifica si alerta de temperatura ya fue enviada.

hum_alert_sent = False
# Verifica si alerta de humedad ya fue enviada.

combined_alert_sent = False
# Verifica si alerta combinada ya fue enviada.

mov_alert_sent = False
# Verifica si alerta de movimiento ya fue enviada.


# TELEGRAM


last_update_id = 0
# Guarda el último mensaje leído en Telegram.


# WIFI


def connect_wifi():

    wlan = network.WLAN(network.STA_IF)
    # Configuramos el ESP32 en modo estación,
    # es decir, conectado a una red existente.

    wlan.active(True)
    # Encendemos el módulo WiFi.

    wlan.connect(SSID, PASSWORD)
    # Conectamos usando SSID y contraseña.

    print("Conectando WiFi...")

    while not wlan.isconnected():
        # Mientras no esté conectado.

        time.sleep(1)
        # Espera de 1 segundo.

    print("WiFi conectado")

    print(wlan.ifconfig())
    # Muestra IP, máscara de red, gateway, etc.

    return wlan.ifconfig()[0]
    # Devuelve únicamente la IP.


# TELEGRAM ALERTAS


def send_telegram(message):

    try:

        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        # URL para enviar mensajes mediante el bot.

        data = {
            "chat_id": CHAT_ID,
            # Usuario que recibirá mensaje.

            "text": message
            # Mensaje a enviar.
        }

        response = urequests.post(url, json=data)
        # Enviamos mensaje en formato JSON.

        response.close()
        # Cerramos conexión.

    except Exception as e:
        # Si ocurre un error.

        print("Error Telegram:", e)


# TELEGRAM RESPUESTAS


def send_custom_telegram(chat_id, message):

    try:

        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        # URL del bot.

        data = {
            "chat_id": chat_id,
            # Usuario que envió comando.

            "text": message
            # Respuesta enviada.
        }

        response = urequests.post(url, json=data)
        # Enviamos mensaje a Telegram.

        response.close()
        # Cerramos conexión.

    except Exception as e:

        print("Error Telegram:", e)
        

# CONSULTAS TELEGRAM


def check_telegram_commands():

    global last_update_id
    # Actualizamos la variable del último mensaje leído.

    try:

        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(
            BOT_TOKEN,
            last_update_id + 1
        )
        # URL para verificar mensajes nuevos enviados al bot.

        response = urequests.get(url)
        # Consultamos Telegram.

        data = response.json()
        # Convertimos respuesta a formato JSON.

        response.close()
        # Cerramos conexión.

        if data["ok"]:
            # Verificamos que la comunicación haya salido bien.

            for result in data["result"]:
                # Recorremos mensajes nuevos.

                last_update_id = result["update_id"]
                # Guardamos último mensaje leído.

                if "message" in result:
                    # Verificamos que exista mensaje.

                    message = result["message"]
                    # Guardamos mensaje.

                    if "text" in message:
                        # Verificamos que tenga texto.

                        text = message["text"]
                        # Guardamos texto recibido.

                        user_chat_id = message["chat"]["id"]
                        # Guardamos ID del usuario.

                        
                        # TEMPERATURA
                        

                        if text == "/temp":
                            # Si usuario escribe /temp.

                            send_custom_telegram(
                                user_chat_id,

                                "Temperatura actual: {} °C".format(
                                    temperature
                                )
                                # Enviamos temperatura actual.
                            )

                        
                        # HUMEDAD
                        

                        elif text == "/hum":
                            # Si usuario escribe /hum.

                            send_custom_telegram(
                                user_chat_id,

                                "Humedad actual: {} %".format(
                                    humidity
                                )
                                # Enviamos humedad actual.
                            )

                        
                        # MOVIMIENTO
                        

                        elif text == "/mov":
                            # Si usuario escribe /mov.

                            send_custom_telegram(
                                user_chat_id,

                                "Movimiento: {}".format(
                                    movement_state
                                )
                                # Enviamos estado del movimiento.
                            )

                        
                        # UMBRALES
                        

                        elif text == "/umbrales":
                            # Si usuario escribe /umbrales.

                            mensaje = (
                                "UMBRALES\n"

                                "Temp Min: {} C\n"

                                "Temp Max: {} C\n"

                                "Hum Min: {} %\n"

                                "Hum Max: {} %\n"
                            ).format(
                                TEMP_MIN,
                                TEMP_MAX,
                                HUM_MIN,
                                HUM_MAX
                            )
                            # Creamos mensaje con límites configurados.

                            send_custom_telegram(
                                user_chat_id,
                                mensaje
                            )
                            # Enviamos mensaje al usuario.

    except Exception as e:

        print("Error comandos Telegram:", e)


# BUZZER


def beep(freq, duration):

    buzzer.freq(freq)
    # Damos frecuencia al buzzer.

    buzzer.duty_u16(30000)
    # Encendemos buzzer usando PWM.

    time.sleep(duration)
    # Tiempo que dura el sonido.

    buzzer.duty_u16(0)
    # Apagamos buzzer.


# LEER DHT


def read_dht():

    global temperature
    global humidity
    # Actualizamos variables globales.

    try:

        sensor_dht.measure()
        # Tomamos una nueva medición.

        temperature = sensor_dht.temperature()
        # Guardamos temperatura medida.

        humidity = sensor_dht.humidity()
        # Guardamos humedad medida.

    except:

        print("Error DHT")


# LEER MPU


def read_mpu():

    global movement_state
    # Actualizamos estado del movimiento.

    try:

        ax, ay, az = mpu.read_accel_data()
        # Leemos aceleración en X, Y y Z.

        magnitude = math.sqrt(ax**2 + ay**2 + az**2)
        # Calculamos magnitud total.

        delta = abs(magnitude - 1)
        # Calculamos cuánto cambió respecto al estado normal.

        
        # ESTADOS MOVIMIENTO
        

        if delta < 0.10:
            # Si el cambio es muy pequeño.

            movement_state = "REPOSO"
            # Se considera reposo.

        elif delta < 0.35:
            # Si hay movimiento moderado.

            movement_state = "MOVIMIENTO DETECTADO"

        else:
            # Si supera el umbral.

            movement_state = "MOVIMIENTO BRUSCO"

    except:

        print("Error MPU")


# BOTON PANICO


def check_panic_button():

    global alarm_state
    # Actualizamos estado de alarma.

    if panic_button.value() == 0:
        # Si botón fue presionado.

        time.sleep_ms(50)
        # Espera pequeña para evitar falsas pulsaciones.

        if panic_button.value() == 0:
            # Confirmamos que sigue presionado.

            alarm_state = "BOTON PANICO"
            # Estado de alarma.

            print("BOTON PANICO")

            beep(3500, 0.2)
            # Sonido de alerta.

            send_telegram(
                "ALERTA: BOTON DE PANICO ACTIVADO"
            )
            # Enviamos alerta a Telegram.

            while panic_button.value() == 0:
                # Mientras siga presionado.

                pass
                # No hacemos nada.

# ALERTAS


def check_alerts():

    global alarm_state
    # Actualizamos estado de alarma.

    global temp_alert_sent
    global hum_alert_sent
    global combined_alert_sent
    global mov_alert_sent
    # Variables para saber si alertas ya fueron enviadas.

    temp_out = (
        temperature > TEMP_MAX
        or
        temperature < TEMP_MIN
    )
    # Verificamos si temperatura salió del rango.

    hum_out = (
        humidity > HUM_MAX
        or
        humidity < HUM_MIN
    )
    # Verificamos si humedad salió del rango.

    
    # ALERTA COMBINADA
    

    if temp_out and hum_out:
        # Si temperatura y humedad están fuera del rango.

        alarm_state = "ALERTA COMBINADA"
        # Estado de alarma.

        buzzer.freq(4000)
        # Frecuencia del buzzer.

        buzzer.duty_u16(30000)
        # Encendemos buzzer.

        if not combined_alert_sent:
            # Si alerta aún no ha sido enviada.

            combined_alert_sent = True
            # Marcamos alerta enviada.

            send_telegram(
                "ALERTA COMBINADA\n"

                "Temperatura: {} °C\n"

                "Humedad: {} %".format(
                    temperature,
                    humidity
                )
                # Enviamos temperatura y humedad medidas.
            )

    
    # ALERTA TEMPERATURA
    

    elif temp_out:
        # Si solo temperatura salió del rango.

        alarm_state = "ALERTA TEMPERATURA"

        buzzer.freq(2000)

        buzzer.duty_u16(30000)

        if not temp_alert_sent:

            temp_alert_sent = True

            send_telegram(
                "ALERTA TEMPERATURA\n"

                "Temperatura: {} °C".format(
                    temperature
                )
                # Enviamos temperatura actual.
            )

    
    # ALERTA HUMEDAD
    

    elif hum_out:
        # Si solo humedad salió del rango.

        alarm_state = "ALERTA HUMEDAD"

        buzzer.freq(1200)

        buzzer.duty_u16(30000)

        if not hum_alert_sent:

            hum_alert_sent = True

            send_telegram(
                "ALERTA HUMEDAD\n"

                "Humedad: {} %".format(
                    humidity
                )
                # Enviamos humedad actual.
            )

    
    # MOVIMIENTO DETECTADO
    

    elif movement_state == "MOVIMIENTO DETECTADO":
        # Si hubo movimiento moderado.

        alarm_state = "MOVIMIENTO DETECTADO"

        buzzer.freq(1800)

        buzzer.duty_u16(30000)

        if not mov_alert_sent:

            mov_alert_sent = True

            send_telegram(
                "ALERTA: MOVIMIENTO DETECTADO"
            )

    
    # MOVIMIENTO BRUSCO
    

    elif movement_state == "MOVIMIENTO BRUSCO":
        # Si hubo movimiento fuerte.

        alarm_state = "MOVIMIENTO BRUSCO"

        buzzer.freq(3500)

        buzzer.duty_u16(30000)

        if not mov_alert_sent:

            mov_alert_sent = True

            send_telegram(
                "ALERTA: MOVIMIENTO BRUSCO DETECTADO"
            )

    
    # NORMAL
    

    else:
        # Si no hay alertas.

        alarm_state = "NORMAL"

        temp_alert_sent = False

        hum_alert_sent = False

        combined_alert_sent = False

        mov_alert_sent = False
        # Reiniciamos estados de alertas.

        buzzer.duty_u16(0)
        # Apagamos buzzer.


# PAGINA WEB


def webpage():

    html = """
    <html>

    <head>

        <meta http-equiv="refresh" content="2">
        <!-- Actualiza página cada 2 segundos -->

        <title>MONITOREO IOT</title>

    </head>

    <body style="font-family: Arial;">

        <h1>MONITOREO BIOMEDICO</h1>

        <h2>Temperatura: {} C</h2>

        <h2>Humedad: {} %</h2>

        <h2>Movimiento: {}</h2>

        <h2>Estado alarma: {}</h2>

        <hr>

        <h3>UMBRALES</h3>

        <p>Temp Min: {}</p>

        <p>Temp Max: {}</p>

        <p>Hum Min: {}</p>

        <p>Hum Max: {}</p>

    </body>

    </html>
    """.format(
        temperature,
        # Temperatura actual.

        humidity,
        # Humedad actual.

        movement_state,
        # Estado de movimiento.

        alarm_state,
        # Estado de alarma.

        TEMP_MIN,
        TEMP_MAX,
        HUM_MIN,
        HUM_MAX
        # Umbrales definidos.
    )

    return html
    # Devuelve la página web completa.


# SERVIDOR WEB


def start_server(ip):

    addr = socket.getaddrinfo(ip, 80)[0][-1]
    # Obtenemos dirección del servidor usando IP y puerto 80.

    s = socket.socket()
    # Creamos socket para comunicación.

    s.bind(addr)
    # Asociamos socket a dirección IP.

    s.listen(1)
    # Servidor queda esperando conexiones.

    s.settimeout(1)
    # Tiempo máximo de espera.

    print("Servidor web iniciado")

    print("Abrir navegador en: http://{}".format(ip))
    # Mostramos dirección del servidor web.

    
    # CONTADOR TELEGRAM
    

    telegram_counter = 0
    # Contador para revisar Telegram cada ciertos ciclos.

    while True:
        # Ciclo principal del programa.

        
        # BOTON PANICO PRIMERO
        

        check_panic_button()
        # Revisamos botón de pánico.

        
        # LEER SENSORES
        

        read_dht()
        # Leemos temperatura y humedad.

        read_mpu()
        # Leemos movimiento y aceleración.

        
        # ALERTAS
        

        check_alerts()
        # Revisamos alertas.

        
        # TELEGRAM CADA 4 CICLOS
        

        telegram_counter += 1
        # Sumamos contador.

        if telegram_counter >= 4:
            # Cada 4 ciclos.

            check_telegram_commands()
            # Revisamos mensajes de Telegram.

            telegram_counter = 0
            # Reiniciamos contador.

        
        # WEB SERVER
        

        try:

            cl, addr = s.accept()
            # Aceptamos conexión del navegador.

            request = cl.recv(1024)
            # Recibimos solicitud del navegador.

            response = webpage()
            # Creamos página web actualizada.

            cl.send("HTTP/1.1 200 OK\r\n")
            # Confirmamos conexión correcta.

            cl.send("Content-Type: text/html\r\n")
            # Indicamos contenido HTML.

            cl.send("Connection: close\r\n\r\n")
            # Cerramos conexión después del envío.

            cl.send(response)
            # Enviamos página web.

            cl.close()
            # Cerramos conexión.

        except:
            # Si no hay conexión o ocurre error.

            pass

        
        # DELAY GENERAL
        

        time.sleep(0.5)
        # Espera general del sistema.


# MAIN


print("Escaneando I2C...")
# Buscando dispositivos I2C conectados.

print(i2c.scan())
# Mostramos dispositivos encontrados.

ip = connect_wifi()
# Conectamos ESP32 al WiFi y obtenemos IP.

send_telegram(
    "ESP32 conectado\nIP: {}".format(ip)
)
# Enviamos mensaje indicando conexión exitosa.

start_server(ip)
# Iniciamos servidor web.