#!/usr/bin/python
# -*- coding:utf-8 -*-
# Muestra la calidad del aire (sensor SGP40) en la OLED SH1106 de la
# placa Waveshare Environment Sensor. Ejecutar desde la carpeta del
# ejemplo de Waveshare:  sudo python calidad_aire.py
# Compatible con Python 2 y 3.

import time
import sys
from PIL import Image, ImageDraw, ImageFont

import SGP40
import BME280

ARRANQUE_S = 60      # el SGP40 necesita ~1 minuto para estabilizarse
REFRESCO_S = 2       # cada cuantos segundos se actualiza la pantalla

# --- Sensores -----------------------------------------------------------
sgp = SGP40.SGP40()
print("SGP40 (calidad del aire) listo")
bme = BME280.BME280()
bme.get_calib_param()
print("BME280 (temperatura y humedad) listo")

# --- Pantalla -----------------------------------------------------------
try:
    import SH1106
    oled = SH1106.SH1106()
    print("Pantalla OLED lista")
except Exception as e:
    print("No se pudo iniciar la pantalla OLED: %s" % e)
    print("Los datos se mostraran solo por terminal.")
    oled = None

if oled is not None:
    ANCHO, ALTO = oled.width, oled.height
else:
    ANCHO, ALTO = 128, 64

fuente_peq = ImageFont.truetype('Font.ttc', 10)
fuente_grande = ImageFont.truetype('Font.ttc', 22)


def etiqueta(caida):
    """Valoracion aproximada segun cuanto ha bajado la lectura respecto
    al aire mas limpio medido (el SGP40 da valores MAS BAJOS cuanto mas
    compuestos organicos volatiles hay)."""
    if caida < 3:
        return "BUENA"
    elif caida < 8:
        return "REGULAR"
    return "MALA"


def pintar(lineas_peq_arriba, texto_grande, lineas_peq_abajo):
    imagen = Image.new('1', (ANCHO, ALTO), "BLACK")
    dibujo = ImageDraw.Draw(imagen)
    y = 0
    for linea in lineas_peq_arriba:
        dibujo.text((0, y), linea, font=fuente_peq, fill=1)
        y += 11
    dibujo.text((0, y + 1), texto_grande, font=fuente_grande, fill=1)
    y = ALTO - 11 * len(lineas_peq_abajo)
    for linea in lineas_peq_abajo:
        dibujo.text((0, y), linea, font=fuente_peq, fill=1)
        y += 11
    if oled is not None:
        oled.display(imagen)


referencia = None
inicio = time.time()

print("Midiendo... (Ctrl+C para salir)")
try:
    while True:
        bruto = sgp.raw()
        datos = bme.readData()          # [presion, temperatura, humedad]
        temp = round(datos[1], 1)
        hum = round(datos[2], 1)
        clima = "%.1f C   %.0f %%HR" % (temp, hum)

        transcurrido = time.time() - inicio
        if transcurrido < ARRANQUE_S:
            restante = int(ARRANQUE_S - transcurrido)
            pintar(["CALIDAD DEL AIRE"], "...", ["Calentando %ds" % restante, clima])
            print("Calentando sensor... %ds (bruto %d)" % (restante, bruto))
        else:
            # La referencia es la lectura mas alta vista (aire mas limpio)
            if referencia is None or bruto > referencia:
                referencia = bruto
            caida = (referencia - bruto) * 100.0 / referencia
            estado = etiqueta(caida)
            pintar(["CALIDAD DEL AIRE"], estado,
                   ["VOC bruto: %d" % bruto, clima])
            print("%s | bruto %d | caida %.1f%% | %s" % (estado, bruto, caida, clima))

        time.sleep(REFRESCO_S)

except KeyboardInterrupt:
    if oled is not None:
        oled.display(Image.new('1', (ANCHO, ALTO), "BLACK"))
    print("\nFin.")
    sys.exit(0)
