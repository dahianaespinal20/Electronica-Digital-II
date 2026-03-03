# Electronica-Digital-II
## PROYECTO ACTUAL

### Sistema Avanzado de Medición de Reflejos
Este proyecto implementa un sistema avanzado de medición de reflejos utilizando un
ESP32 programado en MicroPython, orientado a evaluar el tiempo de reacción de uno o
dos jugadores frente a estímulos visuales y sonoros. El sistema genera de manera aleatoria
señales mediante tres LEDs y un buzzer activo, y mide el tiempo que tarda cada jugador en
responder correctamente presionando el pulsador correspondiente.
El dispositivo permite seleccionar el número de jugadores a través de un menú inicial,
lleva el conteo de puntajes, aplica penalizaciones por respuestas incorrectas y muestra los
resultados de cada ronda en la terminal. Adicionalmente, el sistema incluye un tercer modo
de juego activado por interrupciones, basado en la dinámica de Simón dice, en el cual se
evalúa la memoria y la secuencia de estímulos del jugador.

### Características 

- Selección de 1 o 2 jugadores
- 3 LEDs y 1 buzzer 
- Medición de tiempo por software
- Antirrebote por software
- Sistema de puntuación
- Penalización por error
- Modo especial "Simón Dice" mediante interrupción
