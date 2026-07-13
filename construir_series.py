# construir_series.py
# ============================================================
# Se ejecuta UNA VEZ, offline, antes de la feria.
#
#   python construir_series.py
#
# Genera dos CSV en ./datos/ :
#   serie_sst.csv         (1982 - hoy, mensual)   <- permite backtest de 1997
#   serie_vegetacion.csv  (2013 - hoy, mensual)   <- limite de Landsat 8
#
# POR QUE ESTO IMPORTA:
# Estos CSV son el PLAN B de la demo. Con ellos, el motor de acoplamiento,
# el lag y el backtest funcionan SIN INTERNET. Si el wifi del auditorio
# se cae, solo pierdes los tiles del mapa; tu tesis sigue en pie.
#
# Va anio por anio y escribe incrementalmente: si Earth Engine da timeout
# en 2019, no pierdes los 6 anios anteriores. Puedes relanzarlo y continua.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

from config import PROYECTO_ID, RUTAS_ASSETS
from config_ecosistemas import (
    CAMPO_ECOSISTEMA, ECO_ANDES, ECO_MONTES,
    REGION_NINO_1_2, REGION_MAR_PIURA,
    ESCALA_SST, ESCALA_ANDES, ESCALA_MONTES, TOLERANCIA_SIMPLIFICACION,
)
from core_series import (
    serie_sst_anual, serie_vegetacion_anual,
    geometria_ecosistema, caja,
)

CARPETA_DATOS = 'datos'
CSV_SST = os.path.join(CARPETA_DATOS, 'serie_sst.csv')
CSV_VEG = os.path.join(CARPETA_DATOS, 'serie_vegetacion.csv')

ANIO_INICIO_SST = 1982          # OISST arranca en sep-1981
ANIO_INICIO_VEG = 2013          # Landsat 8 arranca en abr-2013
ANIO_FIN = date.today().year

CAMPOS_SST = ['anio', 'mes', 'sst_nino12', 'anom_nino12',
              'sst_piura', 'anom_piura', 'n_dias_sst']
CAMPOS_VEG = ['anio', 'mes', 'ndmi_andes', 'msavi_montes', 'n_escenas']


def anios_ya_descargados(ruta, campos):
    """Permite reanudar sin repetir trabajo."""
    if not os.path.exists(ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=campos).writeheader()
        return set()

    with open(ruta, newline='', encoding='utf-8') as f:
        return {int(fila['anio']) for fila in csv.DictReader(f) if fila.get('anio')}


def volcar(coleccion, ruta, campos):
    """Trae un FeatureCollection de EE y lo anexa al CSV."""
    datos = coleccion.getInfo()['features']
    with open(ruta, 'a', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        for elemento in datos:
            props = elemento['properties']
            escritor.writerow({c: props.get(c) for c in campos})
    return len(datos)


def descargar(nombre, ruta, campos, anio_desde, constructor):
    hechos = anios_ya_descargados(ruta, campos)
    pendientes = [a for a in range(anio_desde, ANIO_FIN + 1) if a not in hechos]

    if not pendientes:
        print(f'[{nombre}] ya completo ({len(hechos)} anios).')
        return

    print(f'[{nombre}] faltan {len(pendientes)} anios.')
    for anio in pendientes:
        for intento in (1, 2, 3):
            try:
                n = volcar(constructor(anio), ruta, campos)
                print(f'  {anio}  ok  ({n} meses)')
                break
            except Exception as e:
                if intento == 3:
                    print(f'  {anio}  FALLO tras 3 intentos: {e}')
                else:
                    espera = 5 * intento
                    print(f'  {anio}  reintento {intento} en {espera}s...')
                    time.sleep(espera)


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    asset = RUTAS_ASSETS['ecosistemas_2022']
    geom_andes = geometria_ecosistema(
        asset, CAMPO_ECOSISTEMA, ECO_ANDES, TOLERANCIA_SIMPLIFICACION)
    geom_montes = geometria_ecosistema(
        asset, CAMPO_ECOSISTEMA, ECO_MONTES, TOLERANCIA_SIMPLIFICACION)

    # Chequeo de cordura: si un filtro devuelve area 0, el resto es basura.
    a_andes = geom_andes.area(1000).divide(1e6).getInfo()
    a_montes = geom_montes.area(1000).divide(1e6).getInfo()
    print(f'Area ANDES  (paramo+bofedal): {a_andes:,.0f} km2')
    print(f'Area MONTES (bosque seco)   : {a_montes:,.0f} km2')
    if a_andes < 1 or a_montes < 1:
        raise SystemExit('ERROR: un filtro de ECO_REGION devolvio area nula.')

    region_n12 = caja(REGION_NINO_1_2)
    region_loc = caja(REGION_MAR_PIURA)

    descargar(
        'SST', CSV_SST, CAMPOS_SST, ANIO_INICIO_SST,
        lambda a: serie_sst_anual(a, region_n12, region_loc, ESCALA_SST),
    )
    descargar(
        'VEGETACION', CSV_VEG, CAMPOS_VEG, ANIO_INICIO_VEG,
        lambda a: serie_vegetacion_anual(
            a, geom_andes, geom_montes, ESCALA_ANDES, ESCALA_MONTES),
    )

    print(f'\nListo. Revisa {CSV_SST} y {CSV_VEG}')


if __name__ == '__main__':
    main()