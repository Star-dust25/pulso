# construir_reservorios.py
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/construir_reservorios.py
#
#   Requiere backend/ y sus subcarpetas en el PYTHONPATH. En PowerShell:
#       $env:PYTHONPATH="<ruta>\backend;<ruta>\backend\config;<ruta>\backend\core"
#
# Genera data/datos/serie_reservorios.csv  (2013 - hoy, mensual)
#
# EJECUTAR **DESPUES** de que construir_series.py haya terminado.
# No lo lances en paralelo: dos procesos golpeando Earth Engine a la vez
# es lo que corrompio los CSV la vez pasada.
#
# ------------------------------------------------------------
# BUG CORREGIDO: EL AÑO EN CURSO NUNCA SE ACTUALIZABA
#
# La version anterior consideraba hecho cualquier par (reservorio, año)
# con al menos una fila. Bastaba enero de 2026 para que 2026 entero
# contara como descargado.
#
# Es el mismo fallo que tenian construir_serie_diaria.py y
# construir_series.py: la serie se congela el dia de la primera ejecucion
# del año y el script asegura estar al dia. Tres scripts con el mismo
# error de fondo — el año en curso no es un año cerrado.
#
# AHORA: los años cerrados se saltan, el año en curso se rehace siempre, y
# al escribir se deduplica por (reservorio, anio, mes) y se ordena. Eso
# ademas cierra el modo de fallo que menciona el aviso de arriba: aunque
# dos procesos escriban a la vez, la siguiente ejecucion limpia el
# archivo en vez de acumular filas repetidas.
#
# ------------------------------------------------------------
# ADVERTENCIA SOBRE ESTOS DATOS
#
# El 36% de los meses de Poechos se descarta por nubosidad
# (cobertura_valida < 0.60). Y core_lag.py midio que la cadena
# SST -> embalse -> bosque seco NO se sostiene: el primer eslabon no es
# significativo y el segundo sale con signo negativo.
#
# Esta serie se mantiene para poder REPORTAR ese resultado nulo con
# evidencia, no porque la alerta dependa de ella. La Etapa 2 usa el
# vinculo directo mar -> bosque seco. Ver core_reservorio.py.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

# Imports tolerantes a las dos formas de ejecucion.
try:
    from config.config import PROYECTO_ID, RUTAS_ASSETS
    from core.core_reservorio import (
        envolvente_reservorio, serie_reservorio_anual)
except ImportError:
    from config import PROYECTO_ID, RUTAS_ASSETS
    from core_reservorio import envolvente_reservorio, serie_reservorio_anual

# Anclado al archivo, no al directorio de trabajo.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.path.join(CARPETA_BACKEND, 'data', 'datos')
CSV_RESERVORIOS = os.path.join(CARPETA_DATOS, 'serie_reservorios.csv')

RESERVORIOS = ['Poechos', 'San Lorenzo']

ANIO_INICIO = 2013                # Landsat 8
ANIO_FIN = date.today().year

CAMPOS = ['reservorio', 'anio', 'mes', 'agua_ha', 'cobertura_valida',
          'n_escenas']


def leer_filas(ruta):
    """Filas existentes del CSV, o lista vacia si no existe."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline='', encoding='utf-8') as f:
        return [fila for fila in csv.DictReader(f) if fila.get('anio')]


def escribir_filas(ruta, filas):
    """
    Reescribe el CSV entero, deduplicando por (reservorio, anio, mes).

    keep='last': si un mes aparece dos veces gana la descarga mas
    reciente. Landsat incorpora escenas retroactivamente, asi que una
    lectura posterior puede ser mejor que la anterior.
    """
    vistas = {}
    for fila in filas:
        clave = (fila['reservorio'], int(fila['anio']), int(fila['mes']))
        vistas[clave] = fila

    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for clave in sorted(vistas):
            escritor.writerow({c: vistas[clave].get(c) for c in CAMPOS})
    return len(vistas)


def descargar_anio(anio, envolvente, nombre, intentos=3):
    """
    Descarga un año y devuelve sus filas EN MEMORIA. None si falla.

    No escribe nada: el archivo solo se toca cuando la descarga ha ido
    bien. Asi, si Earth Engine falla mientras se rehace el año en curso,
    el CSV queda intacto en vez de perder filas sin ganar otras.
    """
    for intento in range(1, intentos + 1):
        try:
            datos = serie_reservorio_anual(anio, envolvente).getInfo()['features']
            filas = []
            for elemento in datos:
                props = dict(elemento['properties'])
                props['reservorio'] = nombre
                filas.append({c: props.get(c) for c in CAMPOS})
            return filas
        except Exception as e:
            if intento == intentos:
                print(f'  {anio}  FALLO tras {intentos} intentos: {e}')
                return None
            time.sleep(5 * intento)
    return None


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    filas = leer_filas(CSV_RESERVORIOS)
    hechos = {(f['reservorio'], int(f['anio'])) for f in filas}
    asset = RUTAS_ASSETS['reservorios']

    for nombre in RESERVORIOS:
        envolvente = envolvente_reservorio(asset, nombre)

        area_km2 = envolvente.area(100).divide(1e6).getInfo()
        print(f'\n[{nombre}] envolvente: {area_km2:,.1f} km2')
        if area_km2 < 1:
            print(f'  ERROR: el filtro T21_Nombre = "{nombre}" no devolvio '
                  f'nada. Revisa el nombre contra el asset.')
            continue

        # Años CERRADOS que faltan.
        pendientes = [a for a in range(ANIO_INICIO, ANIO_FIN)
                      if (nombre, a) not in hechos]
        if pendientes:
            print(f'  años cerrados pendientes: {len(pendientes)}')
            for anio in pendientes:
                nuevas = descargar_anio(anio, envolvente, nombre)
                if nuevas is None:
                    continue
                filas.extend(nuevas)
                print(f'  {anio}  ok  ({len(nuevas)} meses)')
        else:
            print('  años cerrados: completos.')

        # --- El año en curso SIEMPRE se rehace ---
        nuevas = descargar_anio(ANIO_FIN, envolvente, nombre)
        if nuevas is None:
            print(f'  no se pudo actualizar {ANIO_FIN}. '
                  f'Se conserva lo que habia.')
        else:
            antes = sum(1 for f in filas
                        if f['reservorio'] == nombre
                        and int(f['anio']) == ANIO_FIN)
            filas = [f for f in filas
                     if not (f['reservorio'] == nombre
                             and int(f['anio']) == ANIO_FIN)]
            filas.extend(nuevas)
            print(f'  {ANIO_FIN}: {antes} meses -> {len(nuevas)} meses')

    total = escribir_filas(CSV_RESERVORIOS, filas)
    print(f'\nListo. {total} filas.\n  {CSV_RESERVORIOS}')
    print('\nRECUERDA: core_lag.py descarta los meses con '
          'cobertura_valida < 0.60.')
    print('En la ultima corrida eso supuso el 36% de los meses de Poechos.')


if __name__ == '__main__':
    main()