# construir_serie_diaria.py
# ============================================================
#   python construir_serie_diaria.py
#
# Genera ./datos/serie_sst_diaria.csv   (1982 - hoy, DIARIO)
#
# POR QUE ESTO EXISTE:
# El ICEN es un indice de DIAGNOSTICO, no de alerta. Exige 3 meses
# consecutivos sobre el umbral. En 2017 esa regla hizo que P.A.L.M.A.
# emitiera la alerta 5 DIAS DESPUES del desborde del rio Piura.
#
# No es un fallo nuestro: es una limitacion del propio ICEN. El ENFEN
# lo reconocio y en 2015 creo un Sistema de Alerta SEPARADO justamente
# "para alertar mas oportunamente sin esperar el criterio de 3 meses".
#
# OISST es DIARIO desde 1981. Al promediar por mes estabamos tirando
# esa resolucion a la basura. Aqui la recuperamos.
#
# Ejecutar SOLO cuando no haya otro script corriendo.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

from config import PROYECTO_ID
from config_ecosistemas import REGION_NINO_1_2, REGION_MAR_PIURA, ESCALA_SST
from core_series import COL_OISST, FACTOR_ESCALA_OISST, caja

CARPETA_DATOS = 'datos'
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


def anios_hechos(ruta):
    if not os.path.exists(ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=CAMPOS).writeheader()
        return set()

    with open(ruta, newline='', encoding='utf-8') as f:
        return {fila['fecha'][:4] for fila in csv.DictReader(f)
                if fila.get('fecha')}


def volcar(coleccion, ruta):
    datos = coleccion.getInfo()['features']
    with open(ruta, 'a', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        for e in datos:
            p = e['properties']
            escritor.writerow({c: p.get(c) for c in CAMPOS})
    return len(datos)


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    region_n12 = caja(REGION_NINO_1_2)
    region_piura = caja(REGION_MAR_PIURA)

    hechos = anios_hechos(CSV_DIARIO)
    pendientes = [a for a in range(ANIO_INICIO, ANIO_FIN + 1)
                  if str(a) not in hechos]

    if not pendientes:
        print('Serie diaria ya completa.')
        return

    print(f'Descargando {len(pendientes)} anios de SST diaria...')
    print('(esto tarda: son ~16,000 dias. Dejalo correr.)\n')

    for anio in pendientes:
        for intento in (1, 2, 3):
            try:
                n = volcar(serie_diaria_anual(anio, region_n12, region_piura),
                           CSV_DIARIO)
                print(f'  {anio}  ok  ({n} dias)')
                break
            except Exception as e:
                if intento == 3:
                    print(f'  {anio}  FALLO: {e}')
                else:
                    time.sleep(5 * intento)

    print(f'\nListo. Revisa {CSV_DIARIO}')


if __name__ == '__main__':
    main()