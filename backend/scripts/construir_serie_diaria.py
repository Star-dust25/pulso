# construir_serie_diaria.py
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/construir_serie_diaria.py
#
#   Requiere backend/ y sus subcarpetas en el PYTHONPATH. En PowerShell:
#       $env:PYTHONPATH="<ruta>\backend;<ruta>\backend\config;<ruta>\backend\core"
#
# Genera data/datos/serie_sst_diaria.csv   (1982 - hoy, DIARIO)
#
# ------------------------------------------------------------
# POR QUE ESTO EXISTE
#
# El ICEN es un indice de DIAGNOSTICO, no de alerta. Exige 3 meses
# consecutivos sobre el umbral. Con esa regla, la alerta de 2017 se habria
# emitido el 1 de abril: 5 DIAS DESPUES del desborde del rio Piura del 27
# de marzo. (Cifra reproducible con scripts/backtest_fen.py.)
#
# No es un fallo nuestro: es una limitacion del propio ICEN. El ENFEN lo
# reconocio y en 2015 creo un Sistema de Alerta SEPARADO justamente para
# alertar mas oportunamente sin esperar el criterio de los 3 meses.
#
# OISST es DIARIO desde septiembre de 1981. Al promediar por mes estabamos
# tirando esa resolucion a la basura. Aqui la recuperamos.
#
# ------------------------------------------------------------
# BUG CORREGIDO: EL AÑO EN CURSO NUNCA SE ACTUALIZABA
#
# La version anterior decidia que años faltaban asi:
#
#     {fila['fecha'][:4] for fila in csv.DictReader(f)}
#
# Es decir, se quedaba con el AÑO de cada fecha. Bastaba UNA fila de 2026
# para que 2026 entero contara como "hecho", y el script imprimia "Serie
# diaria ya completa" sin descargar nada.
#
# Consecuencia real: la serie se quedo parada en el 11 de julio de 2026 y
# nadie se entero durante 39 dias. Un sistema de alerta temprana que sirve
# datos congelados y ademas se declara completo es el peor de los fallos
# posibles: silencioso.
#
# AHORA: los años ya cerrados se saltan (siguen siendo reanudables), pero
# el AÑO EN CURSO se vuelve a descargar SIEMPRE y sus filas se reemplazan.
# Al final se deduplica por fecha y se ordena, asi que ejecutarlo dos
# veces seguidas no puede corromper el archivo.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

# Imports tolerantes a las dos formas de ejecucion: con backend/ en el path
# (paquete) o con las subcarpetas sueltas en el path.
try:
    from config.config import PROYECTO_ID
    from config.config_ecosistemas import (
        REGION_NINO_1_2, REGION_MAR_PIURA, ESCALA_SST)
    from core.core_series import COL_OISST, FACTOR_ESCALA_OISST, caja
except ImportError:
    from config import PROYECTO_ID
    from config_ecosistemas import (
        REGION_NINO_1_2, REGION_MAR_PIURA, ESCALA_SST)
    from core_series import COL_OISST, FACTOR_ESCALA_OISST, caja

# Anclado al archivo, no al directorio de trabajo.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.path.join(CARPETA_BACKEND, 'data', 'datos')
CSV_DIARIO = os.path.join(CARPETA_DATOS, 'serie_sst_diaria.csv')

ANIO_INICIO = 1982
ANIO_FIN = date.today().year

CAMPOS = ['fecha', 'sst_nino12', 'sst_piura']


def serie_diaria_anual(anio, region_n12, region_piura, escala=ESCALA_SST):
    """Una fila por dia: SST media en Niño 1+2 y en la caja frente a Piura."""
    col = (ee.ImageCollection(COL_OISST)
           .filterDate(f'{anio}-01-01', f'{anio + 1}-01-01')
           .select('sst'))

    def por_imagen(img):
        sst = img.multiply(FACTOR_ESCALA_OISST)
        n12 = sst.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region_n12,
            scale=escala, maxPixels=1e9, bestEffort=True).get('sst')
        piu = sst.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region_piura,
            scale=escala, maxPixels=1e9, bestEffort=True).get('sst')
        return ee.Feature(None, {
            'fecha': img.date().format('YYYY-MM-dd'),
            'sst_nino12': n12,
            'sst_piura': piu,
        })

    return ee.FeatureCollection(col.map(por_imagen))


def leer_filas(ruta):
    """Todas las filas del CSV, o lista vacia si no existe."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline='', encoding='utf-8') as f:
        return [fila for fila in csv.DictReader(f) if fila.get('fecha')]


def escribir_filas(ruta, filas):
    """Reescribe el CSV entero, deduplicando por fecha y ordenando."""
    vistas = {}
    for fila in filas:
        # keep='last': si una fecha aparece dos veces, gana la descarga mas
        # reciente. OISST publica valores preliminares y luego los corrige.
        vistas[fila['fecha']] = fila

    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for fecha in sorted(vistas):
            escritor.writerow({c: vistas[fecha].get(c) for c in CAMPOS})
    return len(vistas)


def anios_cerrados_hechos(filas):
    """Años ya presentes en el CSV. El año en curso NO cuenta: se rehace."""
    return {fila['fecha'][:4] for fila in filas}


def descargar_anio(anio, region_n12, region_piura, intentos=3):
    """
    Descarga un año y devuelve la lista de filas. None si falla.

    Devuelve los datos EN MEMORIA en vez de escribirlos: asi el archivo
    solo se toca cuando la descarga ha ido bien. Antes, borrar y volver a
    escribir habria dejado un hueco si Earth Engine fallaba a mitad.
    """
    for intento in range(1, intentos + 1):
        try:
            coleccion = serie_diaria_anual(anio, region_n12, region_piura)
            datos = coleccion.getInfo()['features']
            return [{c: d['properties'].get(c) for c in CAMPOS}
                    for d in datos]
        except Exception as e:
            if intento == intentos:
                print(f'  {anio}  FALLO tras {intentos} intentos: {e}')
                return None
            time.sleep(5 * intento)
    return None


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    region_n12 = caja(REGION_NINO_1_2)
    region_piura = caja(REGION_MAR_PIURA)

    filas = leer_filas(CSV_DIARIO)
    hechos = anios_cerrados_hechos(filas)

    # Años CERRADOS que faltan. El año en curso se trata aparte.
    pendientes = [a for a in range(ANIO_INICIO, ANIO_FIN)
                  if str(a) not in hechos]

    if pendientes:
        print(f'Años cerrados pendientes: {len(pendientes)}')
        print('(la primera vez tarda: son ~16,000 dias. Dejalo correr.)\n')
        for anio in pendientes:
            nuevas = descargar_anio(anio, region_n12, region_piura)
            if nuevas is None:
                continue
            filas.extend(nuevas)
            print(f'  {anio}  ok  ({len(nuevas)} dias)')
    else:
        print('Años cerrados: completos.')

    # --- El año en curso SIEMPRE se vuelve a descargar ---
    #
    # Es el arreglo del bug. Sin esto, la serie se congela el dia de la
    # primera ejecucion del año y el script asegura que esta completa.
    print(f'\nActualizando el año en curso ({ANIO_FIN})...')
    nuevas = descargar_anio(ANIO_FIN, region_n12, region_piura)

    if nuevas is None:
        print(f'  No se pudo actualizar {ANIO_FIN}. Se conserva lo que habia.')
    else:
        antes = sum(1 for f in filas if f['fecha'][:4] == str(ANIO_FIN))
        # Se quitan las filas viejas del año en curso y se ponen las nuevas.
        filas = [f for f in filas if f['fecha'][:4] != str(ANIO_FIN)]
        filas.extend(nuevas)
        print(f'  {ANIO_FIN}: {antes} dias -> {len(nuevas)} dias')

    total = escribir_filas(CSV_DIARIO, filas)

    ultima = max(f['fecha'] for f in filas) if filas else '—'
    print(f'\nListo. {total} filas, ultimo dia: {ultima}')
    print(f'  {CSV_DIARIO}')
    print('\nOJO: OISST se publica con retraso. Que el ultimo dia sea de hace')
    print('dos a cuatro dias es normal, no un fallo.')


if __name__ == '__main__':
    main()