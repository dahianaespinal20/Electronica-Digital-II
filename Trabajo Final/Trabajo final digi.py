
# CUNA MULTIFUNCIONAL INTELIGENTE

# Proyecto desarrollado en ESP32 para el monitoreo
# de las condiciones del bebé dentro de la cuna.
#
# Sensores:
# - DHT11 (temperatura y humedad)
# - Sensor de luz
# - MPU6050 (movimiento)
# - Botón (simulación de presencia del bebé)
#
# Actuadores:
# - Ventilador
# - Módulo Peltier
# - Servo motor
# - Buzzer
# - LED verde
# - LED rojo
#
# El sistema supervisa continuamente las variables
# ambientales y activa alarmas o actuadores cuando
# detecta condiciones fuera de los rangos definidos.


from machine import Pin, ADC, PWM, I2C
import dht
import time
import struct
import math


# PINES

# Definición de todos los GPIO utilizados
# para sensores, actuadores y comunicación I2C.

PIN_DHT = 4
PIN_LUZ = 34
PIN_BOTON = 18

PIN_VENTILADOR = 13
PIN_PELTIER = 16
PIN_SERVO = 23
PIN_LED_VERDE = 25
PIN_LED_ROJO = 26
PIN_BUZZER = 27

PIN_SDA = 21
PIN_SCL = 22


# CONFIGURACION

# Parámetros de funcionamiento del sistema.

# Ventilador:
# 1 = encendido
# 0 = apagado
VENTILADOR_ON = 1
VENTILADOR_OFF = 0

# Estados del módulo Peltier
PELTIER_ON = 1
PELTIER_OFF = 0

# Configuración de presencia del bebé.
# Si el botón entrega este valor,
# se considera que hay un bebé en la cuna.
BEBE_CUANDO_BOTON = 1

# Límites de temperatura permitidos (°C)
TEMP_ALTA = 25
TEMP_BAJA = 22

# Rango de humedad permitido (%)
HUM_MIN = 35
HUM_MAX = 75

# Umbral para considerar ambiente oscuro
UMBRAL_LUZ_OSCURA = 1200

# Umbral de movimiento para el MPU6050.
# Valores alejados de 1 g indican movimiento.
UMBRAL_MOVIMIENTO = 0.25

# Posiciones predefinidas del servo
SERVO_CENTRO = 90
SERVO_IZQUIERDA = 60
SERVO_DERECHA = 120


# SENSORES


# Inicialización del sensor DHT11 para
# lectura de temperatura y humedad.
sensor_dht = dht.DHT11(
    Pin(PIN_DHT, Pin.IN, Pin.PULL_UP)
)

# Sensor de luz.
# Se utiliza tanto lectura digital
# como lectura analógica.
pin_luz_digital = Pin(PIN_LUZ, Pin.IN)

sensor_luz = ADC(Pin(PIN_LUZ))
sensor_luz.atten(ADC.ATTN_11DB)

# Configuración de resolución ADC.
try:
    sensor_luz.width(ADC.WIDTH_12BIT)
except:
    pass

# Botón que simula presencia del bebé.
boton = Pin(
    PIN_BOTON,
    Pin.IN,
    Pin.PULL_UP
)


# ACTUADORES


# Salida para ventilador
ventilador = Pin(
    PIN_VENTILADOR,
    Pin.OUT
)

# Salida para módulo Peltier
peltier = Pin(
    PIN_PELTIER,
    Pin.OUT
)

# LEDs indicadores
led_verde = Pin(
    PIN_LED_VERDE,
    Pin.OUT
)

led_rojo = Pin(
    PIN_LED_ROJO,
    Pin.OUT
)

# Configuración del servo motor.
# Los servos normalmente trabajan a 50 Hz.
servo = PWM(Pin(PIN_SERVO))
servo.freq(50)

# Configuración del buzzer.
# Se establece una frecuencia audible.
buzzer = PWM(Pin(PIN_BUZZER))
buzzer.freq(2000)
buzzer.duty(0)


# MPU6050

# Clase encargada de la comunicación
# con el acelerómetro MPU6050 mediante I2C.
class MPU6050:

    # Constructor de la clase.
    # Recibe el objeto I2C y la dirección del sensor.
    def __init__(self, i2c, addr=0x68):

        # Guarda la referencia al bus I2C
        self.i2c = i2c

        # Dirección I2C del MPU6050
        self.addr = addr

        # Variable para indicar si el sensor fue detectado
        self.ok = False

        try:

            # Despierta el MPU6050 escribiendo 0
            # en el registro Power Management (0x6B)
            self.i2c.writeto_mem(
                self.addr,
                0x6B,
                b'\x00'
            )

            # Espera breve para estabilización
            time.sleep_ms(100)

            self.ok = True

            print("MPU6050 conectado")

        except Exception as e:

            print("MPU6050 no detectado:", e)

            self.ok = False

    # Función para obtener la aceleración total
    def leer_aceleracion(self):

        # Si el sensor no fue detectado,
        # no se realiza la lectura
        if not self.ok:
            return None

        try:

            # Lee 14 bytes consecutivos desde el registro 0x3B
            # donde se encuentran los datos del acelerómetro
            # y giroscopio
            data = self.i2c.readfrom_mem(
                self.addr,
                0x3B,
                14
            )

            # Convierte los datos binarios a enteros
            ax, ay, az, temp, gx, gy, gz = struct.unpack(
                ">hhhhhhh",
                data
            )

            # Conversión a unidades g
            ax = ax / 16384
            ay = ay / 16384
            az = az / 16384

            # Cálculo de la magnitud total de aceleración
            aceleracion_total = math.sqrt(
                ax * ax +
                ay * ay +
                az * az
            )

            return aceleracion_total

        except Exception as e:

            print("Error MPU6050:", e)

            return None



# INICIALIZACION I2C

# Configuración del bus I2C utilizado
# para la comunicación con el MPU6050.

i2c = I2C(
    0,
    scl=Pin(PIN_SCL),
    sda=Pin(PIN_SDA),
    freq=400000
)

# Creación del objeto MPU6050
mpu = MPU6050(i2c)


# FUNCIONES ACTUADORES


# Enciende el ventilador
def ventilador_on():
    ventilador.value(VENTILADOR_ON)


# Apaga el ventilador
def ventilador_off():
    ventilador.value(VENTILADOR_OFF)


# Enciende el módulo Peltier
def peltier_on():
    peltier.value(PELTIER_ON)


# Apaga el módulo Peltier
def peltier_off():
    peltier.value(PELTIER_OFF)


# Apaga completamente el buzzer
def buzzer_off():
    buzzer.duty(0)


# Genera una alarma sonora.
# cantidad = número de pitidos
# duracion = tiempo de cada pitido en ms
def beep(cantidad=1, duracion=150):

    for i in range(cantidad):

        # Activa el buzzer
        buzzer.duty(512)

        time.sleep_ms(duracion)

        # Desactiva el buzzer
        buzzer.duty(0)

        time.sleep_ms(120)


# Control del servo mediante ángulo
def mover_servo(angulo):

    # Limita el valor entre 0 y 180 grados
    angulo = max(
        0,
        min(180, angulo)
    )

    # Conversión de ángulo a duty cycle
    duty = int(
        26 +
        (angulo / 180) *
        (128 - 26)
    )

    # Aplica el duty calculado
    servo.duty(duty)


# Movimiento automático de balanceo
# cuando se detecta movimiento.
def servo_por_movimiento():

    print("Servo moviendose por movimiento del MPU")

    # Movimiento hacia la izquierda
    mover_servo(SERVO_IZQUIERDA)

    time.sleep_ms(350)

    # Movimiento hacia la derecha
    mover_servo(SERVO_DERECHA)

    time.sleep_ms(350)

    # Regreso al centro
    mover_servo(SERVO_CENTRO)

    time.sleep_ms(300)
# Apaga todos los actuadores del sistema.
# Se utiliza cuando no hay bebé en la cuna
# o durante la inicialización.
def todo_apagado():

    ventilador_off()
    peltier_off()
    buzzer_off()

    # Mantiene el servo en posición neutra
    mover_servo(SERVO_CENTRO)

    # NO HAY BEBE
    
    # Si no se detecta presencia del bebé,
    # la cuna entra en modo de espera.

    if not bebe:

        print("Estado: cuna vacia")

        # Apaga todos los actuadores
        todo_apagado()

        # Enciende indicador de alerta
        led_alerta()

        # Espera antes de repetir el ciclo
        time.sleep(1)

        continue

    
    # SI HAY BEBE
    
    # Se inicia el monitoreo completo
    # de las condiciones ambientales.

    print("Estado: bebe detectado")

    # Variable para indicar si existe alarma
    alarma = False

    # Lista donde se almacenan las causas
    # que activaron la alarma
    razones = []

    
    # TEMPERATURA
    

    if temperatura is not None:

        # Si la temperatura supera
        # el límite máximo permitido
        if temperatura >= TEMP_ALTA:

            print(
                "Temperatura alta: ventilador y peltier encendidos"
            )

            # Activa sistema de enfriamiento
            ventilador_on()
            peltier_on()

            alarma = True

            razones.append(
                "temperatura alta"
            )

        # Si la temperatura es baja
        elif temperatura <= TEMP_BAJA:

            print(
                "Temperatura baja: ventilador y peltier apagados"
            )

            ventilador_off()
            peltier_off()

        # Temperatura dentro del rango normal
        else:

            print("Temperatura normal")

            ventilador_off()
            peltier_off()

        # Verificación del rango de humedad
        if humedad < HUM_MIN or humedad > HUM_MAX:

            print("Humedad fuera de rango")

            alarma = True

            razones.append(
                "humedad fuera de rango"
            )

    else:

        # Si falla el DHT11
        ventilador_off()
        peltier_off()

    
    # LUZ
    

    # Se utiliza la lectura analógica
    # si está disponible.
    if luz_analogica > 0:

        if luz_analogica < UMBRAL_LUZ_OSCURA:

            print(
                "Ambiente oscuro por lectura analogica"
            )

        else:

            print(
                "Ambiente con luz por lectura analogica"
            )

    # Si no hay lectura analógica,
    # se utiliza la salida digital.
    else:

        if luz_digital == 0:

            print(
                "Ambiente oscuro o salida digital en 0"
            )

        elif luz_digital == 1:

            print(
                "Ambiente con luz o salida digital en 1"
            )

        else:

            print(
                "No hay lectura de luz"
            )


# Activa el LED verde e indica
# funcionamiento normal del sistema.
def led_normal():

    led_verde.value(1)
    led_rojo.value(0)


# Activa el LED rojo para indicar
# una condición de alarma.
def led_alerta():

    led_verde.value(0)
    led_rojo.value(1)



# FUNCIONES SENSORES


# Lectura de temperatura y humedad
# mediante el sensor DHT11.
def leer_dht():

    try:

        # Solicita una nueva medición
        sensor_dht.measure()

        # Obtiene temperatura en °C
        temperatura = sensor_dht.temperature()

        # Obtiene humedad relativa %
        humedad = sensor_dht.humidity()

        return temperatura, humedad

    except Exception as e:

        print("Error DHT11:", e)

        return None, None


# Lectura del sensor de luz.
# Devuelve tanto lectura analógica
# como lectura digital.
def leer_luz():

    try:

        # Lectura analógica del ADC
        luz_analogica = sensor_luz.read()

    except:

        luz_analogica = 0

    try:

        # Lectura digital del pin
        luz_digital = pin_luz_digital.value()

    except:

        luz_digital = -1

    return luz_analogica, luz_digital


# Verifica si existe presencia del bebé
# mediante el estado del botón.
def hay_bebe():

    # Lectura del botón
    valor = boton.value()

    # Compara con el valor configurado
    # como presencia del bebé
    if valor == BEBE_CUANDO_BOTON:

        return True, valor

    else:

        return False, valor


# Detecta movimiento utilizando
# la aceleración total obtenida
# desde el MPU6050.
def detectar_movimiento(aceleracion):

    # Si la lectura falló
    if aceleracion is None:

        return False

    # En reposo la aceleración total
    # suele ser cercana a 1 g.
    diferencia = abs(
        aceleracion - 1.0
    )

    # Si supera el umbral definido,
    # se considera movimiento.
    if diferencia >= UMBRAL_MOVIMIENTO:

        return True

    else:

        return False



# INICIO


# Mensajes de verificación al iniciar
# el sistema.
print("Sistema de cuna inteligente iniciado")

print("Boton bebe en GPIO 18")

print(
    "Valor",
    BEBE_CUANDO_BOTON,
    "= hay bebe en cuna"
)

print(
    "Ventilador GPIO 13: 1 prende, 0 apaga"
)

print(
    "Servo GPIO 23: se mueve SOLO si hay movimiento en MPU"
)

print(
    "Luz GPIO 34: lectura analogica y digital"
)

# Apaga todos los actuadores
# antes de iniciar el monitoreo.
todo_apagado()

# LEDs apagados al inicio
led_verde.off()
led_rojo.off()


# LOOP PRINCIPAL


while True:

    print("")
    print("===== CUNA INTELIGENTE =====")

    # Lectura de presencia del bebé
    bebe, valor_boton = hay_bebe()

    # Lectura del sensor de luz
    luz_analogica, luz_digital = leer_luz()

    # Lectura de temperatura y humedad
    temperatura, humedad = leer_dht()

    # Lectura del acelerómetro
    aceleracion = mpu.leer_aceleracion()

    # Visualización de datos
    print("Valor boton:", valor_boton)

    if bebe:

        print("Hay bebe en cuna")

    else:

        print("No hay bebe en cuna")

    print("Luz analogica:", luz_analogica)

    print("Luz digital:", luz_digital)

    if luz_analogica == 0:

        print(
            "Luz analogica en 0. Si tu sensor es de salida digital, usa Luz digital."
        )

    if temperatura is not None:

        print(
            "Temperatura:",
            temperatura,
            "C"
        )

        print(
            "Humedad:",
            humedad,
            "%"
        )

    else:

        print(
            "No se pudo leer temperatura/humedad"
        )

    if aceleracion is not None:

        print(
            "Aceleracion MPU:",
            aceleracion
        )

        print(
            "Diferencia movimiento:",
            abs(aceleracion - 1.0)
        )

    else:

        print(
            "No se pudo leer movimiento"
        )

    # MOVIMIENTO MPU + SERVO
    
    # Se analiza la aceleración obtenida
    # por el MPU6050 para determinar si
    # existe movimiento significativo.

    movimiento_detectado = detectar_movimiento(
        aceleracion
    )

    # Si se detecta movimiento por encima
    # del umbral configurado
    if movimiento_detectado:

        print("Movimiento detectado en MPU")

        # Activa condición de alarma
        alarma = True

        # Registra la causa de la alarma
        razones.append(
            "movimiento detectado"
        )

        # Realiza el movimiento de balanceo
        # de la cuna mediante el servo
        servo_por_movimiento()

    else:

        print(
            "Sin movimiento fuerte en MPU"
        )

        # Mantiene el servo centrado
        mover_servo(SERVO_CENTRO)

    
    # ESTADO FINAL
    
    # Después de evaluar todos los sensores,
    # se determina si existe o no una alarma.

    if alarma:

        print(
            "ALARMA:",
            razones
        )

        # Enciende LED rojo
        led_alerta()

        # Genera dos pitidos de advertencia
        beep(2, 150)

    else:

        print("Estado normal")

        # Enciende LED verde
        led_normal()

        # Asegura que el buzzer permanezca apagado
        buzzer_off()

        # Mantiene el servo en posición central
        mover_servo(SERVO_CENTRO)

    # Espera un segundo antes de iniciar
    # un nuevo ciclo de monitoreo
    time.sleep(1)