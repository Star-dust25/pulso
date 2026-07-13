# construir_reservorios.py
# ============================================================
#   python construir_reservorios.py
#
# Genera ./datos/serie_reservorios.csv  (2013 - hoy, mensual)
#
# EJECUTAR **DESPUES** de que construir_series.py haya terminado.
# No lo lances en paralelo: dos procesos golpeando Earth Engine a la vez
# es lo que corrompio los CSV la vez pasada.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

from config import PROYECTO_ID, RUTAS_ASSETS
from core_reservorio import envolvente_reservorio, serie_reservorio_anual

CARPETA_DATOS = 'datos'
CSV_RESERVORIOS = os.path.join(CARPETA_DATOS, 'serie_reservorios.csv')

RESERVORIOS = ['Poechos', 'San Lorenzo']

ANIO_INICIO = 2013                # Landsat 8
ANIO_FIN = date.today().year

CAMPOS = ['reservorio', 'anio', 'mes', 'agua_ha', 'cobertura_valida', 'n_escenas']


def ya_descargado(ruta):
    if not os.path.exists(ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=CAMPOS).writeheader()
        return set()

    with open(ruta, newline='', encoding='utf-8') as f:
        return {(fila['reservorio'], int(fila['anio']))
                for fila in csv.DictReader(f) if fila.get('anio')}


def volcar(coleccion, nombre, ruta):
    datos = coleccion.getInfo()['features']
    with open(ruta, 'a', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        for elemento in datos:
            props = elemento['properties']
            props['reservorio'] = nombre
            escritor.writerow({c: props.get(c) for c in CAMPOS})
    return len(datos)


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    hechos = ya_descargado(CSV_RESERVORIOS)
    asset = RUTAS_ASSETS['reservorios']

    for nombre in RESERVORIOS:
        envolvente = envolvente_reservorio(asset, nombre)

        area_km2 = envolvente.area(100).divide(1e6).getInfo()
        print(f'\n[{nombre}] envolvente: {area_km2:,.1f} km2')
        if area_km2 < 1:
            print(f'  ERROR: el filtro T21_Nombre = "{nombre}" no devolvio nada.')
            continue

        for anio in range(ANIO_INICIO, ANIO_FIN + 1):
            if (nombre, anio) in hechos:
                continue

            for intento in (1, 2, 3):
                try:
                    n = volcar(serie_reservorio_anual(anio, envolvente),
                               nombre, CSV_RESERVORIOS)
                    print(f'  {anio}  ok  ({n} meses)')
                    break
                except Exception as e:
                    if intento == 3:
                        print(f'  {anio}  FALLO: {e}')
                    else:
                        time.sleep(5 * intento)

    print(f'\nListo. Revisa {CSV_RESERVORIOS}')


if __name__ == '__main__':
    main()