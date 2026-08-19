# construir_series.py
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/construir_series.py
#
#   Requiere backend/ y sus subcarpetas en el PYTHONPATH. En PowerShell:
#       $env:PYTHONPATH="<ruta>\backend;<ruta>\backend\config;<ruta>\backend\core"
#
# Genera dos CSV en data/datos/ :
#   serie_sst.csv         (1982 - hoy, mensual)   <- permite backtest de 1997
#   serie_vegetacion.csv  (2013 - hoy, mensual)   <- limite de Landsat 8
#
# POR QUE ESTO IMPORTA:
# Estos CSV son el PLAN B de la demo. Con ellos, el motor de acoplamiento,
# el lag y el backtest funcionan SIN INTERNET. Si el wifi del auditorio
# se cae, solo pierdes los tiles del mapa; tu tesis sigue en pie.
#
# Va anio por anio: si Earth Engine da timeout en 2019, no pierdes los
# anios anteriores. Puedes relanzarlo y continua donde lo dejo.
#
# ------------------------------------------------------------
# BUG CORREGIDO: EL AÑO EN CURSO NUNCA SE ACTUALIZABA
#
# La version anterior consideraba "hecho" cualquier año con al menos una
# fila. Bastaba que existiera enero de 2026 para que 2026 entero contara
# como descargado, y el script imprimia "ya completo" sin traer nada.
#
# Es el mismo fallo que tenia construir_serie_diaria.py, y tuvo el mismo
# efecto: las series mensuales de SST y vegetacion se quedaron paradas en
# julio de 2026 mientras el script aseguraba estar al dia. Un fallo
# silencioso en la capa de datos es peor que una caida ruidosa.
#
# AHORA: los años cerrados se saltan (siguen siendo reanudables), pero el
# AÑO EN CURSO se vuelve a descargar SIEMPRE y sus filas se reemplazan.
# Al escribir se deduplica por (anio, mes) y se ordena, asi que ejecutarlo
# dos veces seguidas no puede corromper el archivo.
#
# NOTA sobre los meses futuros: Earth Engine devuelve las 12 filas del año
# en curso, y las de meses que aun no han ocurrido salen con valores nulos
# y n_dias_sst / n_escenas = 0. Se conservan a proposito: una fila nula es
# informacion ("aun no ha pasado"), y los modulos que leen estos CSV ya
# saben distinguir un nulo de un cero.
# ============================================================

import csv
import os
import time
from datetime import date

import ee

# Imports tolerantes a las dos formas de ejecucion: con backend/ en el path
# (paquete) o con las subcarpetas sueltas en el path.
try:
    from config.config import PROYECTO_ID, RUTAS_ASSETS
    from config.config_ecosistemas import (
        CAMPO_ECOSISTEMA, ECO_ANDES, ECO_MONTES,
        REGION_NINO_1_2, REGION_MAR_PIURA,
        ESCALA_SST, ESCALA_ANDES, ESCALA_MONTES, TOLERANCIA_SIMPLIFICACION,
    )
    from core.core_series import (
        serie_sst_anual, serie_vegetacion_anual,
        geometria_ecosistema, caja,
    )
except ImportError:
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

# Anclado al archivo, no al directorio de trabajo.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.path.join(CARPETA_BACKEND, 'data', 'datos')
CSV_SST = os.path.join(CARPETA_DATOS, 'serie_sst.csv')
CSV_VEG = os.path.join(CARPETA_DATOS, 'serie_vegetacion.csv')

ANIO_INICIO_SST = 1982          # OISST arranca en sep-1981
ANIO_INICIO_VEG = 2013          # Landsat 8 arranca en abr-2013
ANIO_FIN = date.today().year

CAMPOS_SST = ['anio', 'mes', 'sst_nino12', 'anom_nino12',
              'sst_piura', 'anom_piura', 'n_dias_sst']
CAMPOS_VEG = ['anio', 'mes', 'ndmi_andes', 'msavi_montes', 'n_escenas']


def leer_filas(ruta):
    """Filas existentes del CSV, o lista vacia si no existe."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline='', encoding='utf-8') as f:
        return [fila for fila in csv.DictReader(f) if fila.get('anio')]


def escribir_filas(ruta, filas, campos):
    """
    Reescribe el CSV entero, deduplicando por (anio, mes) y ordenando.

    keep='last': si un mes aparece dos veces, gana la descarga mas
    reciente. Es lo correcto porque OISST y Landsat publican datos
    preliminares que luego se corrigen.
    """
    vistas = {}
    for fila in filas:
        clave = (int(fila['anio']), int(fila['mes']))
        vistas[clave] = fila

    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for clave in sorted(vistas):
            escritor.writerow({c: vistas[clave].get(c) for c in campos})
    return len(vistas)


def descargar_anio(anio, constructor, campos, intentos=3):
    """
    Descarga un año y devuelve sus filas EN MEMORIA. None si falla.

    No escribe nada: el archivo solo se toca cuando todo ha ido bien. Asi,
    si Earth Engine falla mientras se rehace el año en curso, el CSV queda
    intacto en vez de perder las filas viejas sin ganar las nuevas.
    """
    for intento in range(1, intentos + 1):
        try:
            datos = constructor(anio).getInfo()['features']
            return [{c: d['properties'].get(c) for c in campos}
                    for d in datos]
        except Exception as e:
            if intento == intentos:
                print(f'  {anio}  FALLO tras {intentos} intentos: {e}')
                return None
            espera = 5 * intento
            print(f'  {anio}  reintento {intento} en {espera}s...')
            time.sleep(espera)
    return None


def descargar(nombre, ruta, campos, anio_desde, constructor):
    filas = leer_filas(ruta)
    hechos = {int(f['anio']) for f in filas}

    # Años CERRADOS que faltan. El año en curso se trata aparte.
    pendientes = [a for a in range(anio_desde, ANIO_FIN) if a not in hechos]

    if pendientes:
        print(f'[{nombre}] faltan {len(pendientes)} años cerrados.')
        for anio in pendientes:
            nuevas = descargar_anio(anio, constructor, campos)
            if nuevas is None:
                continue
            filas.extend(nuevas)
            print(f'  {anio}  ok  ({len(nuevas)} meses)')
    else:
        print(f'[{nombre}] años cerrados: completos.')

    # --- El año en curso SIEMPRE se rehace ---
    nuevas = descargar_anio(ANIO_FIN, constructor, campos)
    if nuevas is None:
        print(f'[{nombre}] no se pudo actualizar {ANIO_FIN}. '
              f'Se conserva lo que habia.')
    else:
        antes = sum(1 for f in filas if int(f['anio']) == ANIO_FIN)
        filas = [f for f in filas if int(f['anio']) != ANIO_FIN]
        filas.extend(nuevas)
        print(f'[{nombre}] {ANIO_FIN}: {antes} meses -> {len(nuevas)} meses')

    total = escribir_filas(ruta, filas, campos)
    print(f'[{nombre}] {total} filas en total.')


def main():
    ee.Initialize(project=PROYECTO_ID)
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    asset = RUTAS_ASSETS['ecosistemas_2022']
    geom_andes = geometria_ecosistema(
        asset, CAMPO_ECOSISTEMA, ECO_ANDES, TOLERANCIA_SIMPLIFICACION)
    geom_montes = geometria_ecosistema(
        asset, CAMPO_ECOSISTEMA, ECO_MONTES, TOLERANCIA_SIMPLIFICACION)

    # Chequeo de cordura: si un filtro devuelve area 0, el resto es basura.
    #
    # No es decorativo: los nombres de ECO_ANDES y ECO_MONTES llevan tildes
    # ('Páramo', 'Bosque estacionalmente seco de montaña'). Si uno no
    # coincide EXACTAMENTE con el asset, el filtro devuelve vacio SIN
    # lanzar error y toda la serie sale nula. Esta comprobacion es lo unico
    # que lo detecta.
    a_andes = geom_andes.area(1000).divide(1e6).getInfo()
    a_montes = geom_montes.area(1000).divide(1e6).getInfo()
    print(f'Area ANDES  (paramo+bofedal): {a_andes:,.0f} km2')
    print(f'Area MONTES (bosque seco)   : {a_montes:,.0f} km2')
    if a_andes < 1 or a_montes < 1:
        raise SystemExit('ERROR: un filtro de ECO_REGION devolvio area nula. '
                         'Revisa los nombres (tildes incluidas) en '
                         'config_ecosistemas.py contra el asset.')
    print()

    region_n12 = caja(REGION_NINO_1_2)
    region_loc = caja(REGION_MAR_PIURA)

    descargar(
        'SST', CSV_SST, CAMPOS_SST, ANIO_INICIO_SST,
        lambda a: serie_sst_anual(a, region_n12, region_loc, ESCALA_SST),
    )
    print()
    descargar(
        'VEGETACION', CSV_VEG, CAMPOS_VEG, ANIO_INICIO_VEG,
        lambda a: serie_vegetacion_anual(
            a, geom_andes, geom_montes, ESCALA_ANDES, ESCALA_MONTES),
    )

    print(f'\nListo.\n  {CSV_SST}\n  {CSV_VEG}')
    print('\nDESPUES DE ESTO hay que regenerar lo que depende de las series:')
    print('  python scripts/backtest_fen.py')
    print('  python scripts/validar_icen.py --refrescar')
    print('  python -c "from core import core_alerta; core_alerta.main()"')
    print('y copiar a data/salidas/mapas/ las figuras que muestra la web.')


if __name__ == '__main__':
    main()