# backend/scripts/construir_mapas.py
# ============================================================
# PRE-GENERA LOS MAPAS. Se ejecuta ANTES, no durante.
#
#   cd backend && python scripts/construir_mapas.py
#
# Produce backend/data/salidas/mapas/*.png y .../indice.json
#
# ============================================================
# POR QUE EXISTE ESTE SCRIPT
#
# El mapa interactivo tardaba entre diez y cuarenta segundos por clic.
# No era la red: eran tres costes acumulados, y conviene nombrarlos.
#
# 1. EL KPI. Se llamaba a reduceRegion() para obtener UN numero — la
#    media del indice — recorriendo 18,673 km² a 30 m de resolucion. Es
#    una llamada sincrona: la interfaz se queda congelada esperandola.
#    Ese era el grueso del retraso.
#
# 2. LOS TILES SE CALCULAN AL VUELO. Cuando pides la mediana de una
#    coleccion Landsat, Earth Engine no tiene esa imagen almacenada: la
#    compone tesela por tesela en el momento, y lo repite en cada zoom y
#    en cada arrastre. Esto NO se puede optimizar hasta volverlo
#    instantaneo. Es trabajo de computo real.
#
# 3. El puente navegador-servidor añadia un viaje mas en cada cambio.
#
# La conclusion incomoda es que un mapa interactivo servido desde GEE
# nunca sera instantaneo. Asi que no lo optimizamos: lo sacamos del
# camino critico.
#
# ------------------------------------------------------------
# LA DECISION
#
# Las combinaciones que la demostracion necesita son POCAS y CONOCIDAS:
# 3 ecosistemas x 3 periodos = 9 imagenes. Se generan una vez, se
# guardan en disco y FastAPI las sirve como estaticos al instante.
#
# ------------------------------------------------------------
# LO QUE SE PIERDE, Y HAY QUE SABERLO
#
# Una imagen fija no tiene zoom ni desplazamiento. Para una demostracion
# de diez minutos eso no es una perdida: nadie hace zoom delante de un
# jurado. Para exploracion real, si.
# ============================================================

import json
import os
import sys
from datetime import date, timedelta

import ee

# --- RUTAS ANCLADAS AL ARCHIVO, NO AL DIRECTORIO DE TRABAJO ---
#
# Este script vive en backend/scripts/ pero importa desde backend/. Sin
# insertar la raiz del backend en sys.path, `from config.config import`
# falla en cuanto lo lanzas desde un directorio distinto — que es
# justo lo que hace GitHub Actions.
#
# Y CARPETA_MAPAS no puede ser relativa: un path relativo significa que
# el script escribe en un sitio distinto segun desde donde lo ejecutes.
# En local acertabas por casualidad; en el runner, no.
RAIZ_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ_BACKEND)

from config.config import PROYECTO_ID, RUTAS_ASSETS
from config.config_ecosistemas import (
    CAMPO_ECOSISTEMA, ECO_ANDES, ECO_MONTES,
    ESCALA_ANDES, ESCALA_MONTES, TOLERANCIA_SIMPLIFICACION,
)
from core.core_series import (
    COL_OISST, FACTOR_ESCALA_OISST, coleccion_landsat_limpia,
    geometria_ecosistema,
)

CARPETA_MAPAS = os.path.join(RAIZ_BACKEND, 'data', 'salidas', 'mapas')

# --- VENTANAS MOVILES PARA EL PERIODO "ACTUAL" ---
#
# El periodo actual NO puede ser un par de fechas fijas: si lo es, la
# imagen envejece en silencio y un dia el sistema muestra el mar de hace
# ocho meses como si fuera el de hoy. Un sistema de alerta que muestra
# datos viejos SIN DECIRLO es peor que uno que no muestra nada.
#
# Las dos ventanas son distintas a proposito, y la diferencia no es un
# detalle de implementacion: es la fisica de cada sensor.
#
#   OISST es diario y sin nubes -> 30 dias bastan y sobran.
#   Landsat revisita cada 16 dias y la mitad de las escenas vienen
#   nubladas -> con menos de 90 dias hay zonas sin un solo pixel valido
#   y el compuesto sale agujereado.
VENTANA_MAR = 30
VENTANA_TIERRA = 90


def periodos(hoy=None):
    """
    Las combinaciones que ofrece la pestaña de monitoreo.

    Es una FUNCION, no una constante, porque 'actual' se mueve con el
    calendario. Si añades un periodo en el frontend, añadelo aqui: la
    app solo puede mostrar lo que este script haya generado.
    """
    hoy = hoy or date.today()
    return {
        # El fin es AYER, no hoy: OISST publica con uno o dos dias de
        # latencia. Pedir el dia de hoy devuelve una coleccion vacia.
        'actual_2026': (hoy - timedelta(days=VENTANA_MAR),
                        hoy - timedelta(days=1),
                        hoy - timedelta(days=VENTANA_TIERRA)),
        'nino_2017': (date(2017, 1, 1), date(2017, 5, 31), None),
        'nino_2015_16': (date(2015, 10, 1), date(2016, 3, 31), None),
    }


ECOSISTEMAS = ('LITORAL', 'MONTES', 'ANDES')

# Lado mayor de la miniatura. 900 px basta para proyectar sin pixelar y
# mantiene cada archivo por debajo de ~400 KB.
ANCHO_MINIATURA = 900

# ANDES es el ecosistema que mas falla al descargar (timeout, HTTP 500):
# la geometria del paramo es la mas recortada y compleja, y el thumbnail
# tarda mas en componerse del lado de GEE. Pedirlo mas pequeño reduce el
# tiempo de render del servidor lo suficiente para que entre en plazo.
ANCHO_POR_ECOSISTEMA = {'ANDES': 700}

# Escala a la que se calcula el KPI.
#
# NO es la resolucion del sensor: es la resolucion a la que promediamos.
# Promediar a 300 m en lugar de 30 m da practicamente el mismo numero
# —estamos calculando una media sobre miles de km²— y cuesta cien veces
# menos. Usar 30 m aqui era pagar una precision que despues redondeamos
# a tres decimales.
ESCALA_KPI = {'LITORAL': 25000, 'MONTES': 300, 'ANDES': 300}

VIS = {
    'LITORAL': {'banda': 'sst', 'min': 17, 'max': 29,
                'palette': ['#2C5D73', '#5B8FA8', '#D68910', '#C0392B']},
    'MONTES': {'banda': 'MSAVI', 'min': 0.0, 'max': 0.6,
               'palette': ['#8C6D46', '#B08D57', '#7D9E73', '#ACC8A2']},
    'ANDES': {'banda': 'NDMI', 'min': -0.2, 'max': 0.4,
              'palette': ['#C0392B', '#D68910', '#5B8FA8', '#2C5D73']},
}


def iniciar():
    """
    Arranca Earth Engine en los dos entornos posibles.

    LOCAL: OAuth personal, el de `earthengine authenticate`.

    AUTOMATIZADO (GitHub Actions): ese OAuth no existe — no hay navegador
    ni sesion de usuario en un runner. Hace falta una cuenta de servicio,
    cuyo JSON llega por la variable de entorno GEE_SERVICE_ACCOUNT.
    """
    import json as _json

    bruto = os.environ.get('GEE_SERVICE_ACCOUNT')
    if bruto:
        info = _json.loads(bruto)
        cred = ee.ServiceAccountCredentials(info['client_email'],
                                            key_data=bruto)
        ee.Initialize(cred, project=PROYECTO_ID)
    else:
        ee.Initialize(project=PROYECTO_ID)
    ee.Number(1).getInfo()      # llamada real: confirma que hay conexion


def geometrias():
    asset = RUTAS_ASSETS['ecosistemas_2022']
    return {
        'ANDES': geometria_ecosistema(asset, CAMPO_ECOSISTEMA, ECO_ANDES,
                                      TOLERANCIA_SIMPLIFICACION),
        'MONTES': geometria_ecosistema(asset, CAMPO_ECOSISTEMA, ECO_MONTES,
                                       TOLERANCIA_SIMPLIFICACION),
        'LITORAL': ee.Geometry.BBox(-81.6, -6.2, -80.5, -4.0),
    }


def imagen(ecosistema, geom, f_ini, f_fin):
    if ecosistema == 'LITORAL':
        col = ee.ImageCollection(COL_OISST).filterDate(str(f_ini), str(f_fin))
        return col.select('sst').mean().multiply(FACTOR_ESCALA_OISST).clip(geom)
    col = coleccion_landsat_limpia(str(f_ini), str(f_fin), geom)
    banda = 'NDMI' if ecosistema == 'ANDES' else 'MSAVI'
    return col.select(banda).median().clip(geom)


def kpi(img, geom, ecosistema):
    """Media del indice. Si falla, devuelve None: un KPI ausente no debe
    impedir que la imagen se genere."""
    try:
        v = img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom,
            scale=ESCALA_KPI[ecosistema], maxPixels=1e9,
            bestEffort=True, tileScale=4,
        ).getNumber(VIS[ecosistema]['banda']).getInfo()
        return round(v, 3) if v is not None else None
    except Exception as e:
        print(f'      KPI no disponible: {type(e).__name__}')
        return None


BBOX_PIURA_COORDS = (-81.6, -6.5, -79.0, -4.0)


def aplicar_fondo(img_vis):
    """Mezcla la imagen de datos sobre un mapa base estetico generado en
    Earth Engine."""
    region_piura = ee.Geometry.BBox(*BBOX_PIURA_COORDS)
    land = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")

    # Fondo base (agua)
    agua = ee.Image.constant(0).visualize(palette=['#f1f5f9']).clip(region_piura)

    # Tierra (hillshade sutil para dar contexto de relieve)
    srtm = ee.Image("USGS/SRTMGL1_003")
    hillshade = ee.Terrain.hillshade(srtm).visualize(
        min=0, max=255, palette=['#e2e8f0', '#ffffff'])
    tierra_mask = ee.Image.constant(0).paint(land, 1)
    tierra = hillshade.updateMask(tierra_mask).clip(region_piura)

    # Fronteras internacionales y costa
    costa_mask = ee.Image.constant(0).paint(land, 1, 1)
    costa = (ee.Image.constant(0).visualize(palette=['#94a3b8'])
             .updateMask(costa_mask.eq(1)).clip(region_piura))

    # Fronteras departamentales (Level 1)
    departamentos = ee.FeatureCollection("FAO/GAUL/2015/level1")
    dept_mask = ee.Image.constant(0).paint(departamentos, 1, 2)
    dept_bordes = (ee.Image.constant(0).visualize(palette=['#64748b'])
                   .updateMask(dept_mask.eq(1)).clip(region_piura))

    fondo = agua.blend(tierra).blend(costa).blend(dept_bordes)

    # mosaic() en lugar de blend() porque blend hereda el footprint de la
    # imagen superpuesta (img_vis), lo que recorta el mapa y hace perder
    # el contexto geografico.
    return ee.ImageCollection([fondo, img_vis]).mosaic().clip(region_piura)


def descargar(url, destino, intentos=3, timeout=300):
    """
    Descarga con reintentos y espera creciente.

    POR QUE HAY REINTENTOS
    ----------------------
    Los dos mapas de ANDES que faltaban en el indice fallaron por
    'The read operation timed out' y 'HTTP Error 500'. Ninguno de los dos
    es un error de la peticion: son sintomas de que el servidor de GEE
    estaba componiendo el thumbnail bajo carga. Un solo intento convierte
    una congestion pasajera en un mapa ausente durante 24 horas.

    Escribimos primero a un temporal y renombramos al final: si la
    descarga se corta a la mitad, el PNG bueno del dia anterior sigue
    intacto en su sitio en vez de quedar sobrescrito por bytes truncados.
    """
    import time
    import urllib.request

    temporal = destino + '.parcial'

    for n in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                datos = r.read()
            with open(temporal, 'wb') as f:
                f.write(datos)
            os.replace(temporal, destino)
            return len(datos)
        except Exception as e:
            if os.path.exists(temporal):
                os.remove(temporal)
            if n == intentos:
                raise
            espera = 5 * n
            print(f'      intento {n}/{intentos} fallo '
                  f'({type(e).__name__}); reintento en {espera}s')
            time.sleep(espera)


def indice_previo(ruta):
    """Lee el indice de la corrida anterior. Un indice corrupto o ausente
    no es motivo para abortar: se trata como vacio."""
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Aviso: indice previo ilegible ({type(e).__name__}); '
              f'se parte de cero.')
        return {}


def ruta_de(entrada):
    """Ruta absoluta al PNG de una entrada del indice, o None.

    Tolera los dos formatos historicos del campo 'archivo': ruta completa
    ('salidas/mapas/X.png') y nombre suelto ('X.png')."""
    archivo = entrada.get('archivo') if entrada else None
    if not archivo:
        return None
    return os.path.join(CARPETA_MAPAS,
                        os.path.basename(archivo.replace('\\', '/')))


def main():
    os.makedirs(CARPETA_MAPAS, exist_ok=True)
    print('Conectando con Earth Engine...')
    iniciar()
    geoms = geometrias()

    tabla = periodos()
    ruta_indice = os.path.join(CARPETA_MAPAS, 'indice.json')
    previo = indice_previo(ruta_indice)
    indice = {}
    total = len(ECOSISTEMAS) * len(tabla)
    hecho = 0
    conservados = 0

    for eco in ECOSISTEMAS:
        geom = geoms[eco]
        for nombre_periodo, (f_ini, f_fin, f_ini_tierra) in tabla.items():
            # El bosque seco y el paramo necesitan una ventana mas larga
            # que el mar para juntar escenas sin nubes.
            if eco != 'LITORAL' and f_ini_tierra is not None:
                f_ini = f_ini_tierra
            hecho += 1
            clave = f'{eco}__{nombre_periodo}'
            print(f'[{hecho}/{total}] {eco} · {nombre_periodo}')

            try:
                img = imagen(eco, geom, f_ini, f_fin)
                vis = {k: v for k, v in VIS[eco].items() if k != 'banda'}

                # Pre-visualizar la imagen (RGB) y añadirle el mapa base
                img_rgb = img.visualize(**vis)
                img_final = aplicar_fondo(img_rgb)

                region_piura = ee.Geometry.BBox(*BBOX_PIURA_COORDS)
                url = img_final.getThumbURL({
                    'dimensions': ANCHO_POR_ECOSISTEMA.get(
                        eco, ANCHO_MINIATURA),
                    'region': region_piura,
                    'format': 'png',
                })
                archivo = os.path.join(CARPETA_MAPAS, f'{clave}.png')
                peso = descargar(url, archivo)
                valor = kpi(img, geom, eco)

                indice[clave] = {
                    # Solo el NOMBRE, no la ruta. Quien consume el indice
                    # (la API) ya sabe en que carpeta esta; guardar la
                    # ruta de disco filtraba la organizacion del servidor
                    # hasta el navegador.
                    'archivo': f'{clave}.png',
                    'kpi': valor,
                    'banda': VIS[eco]['banda'],
                    'desde': str(f_ini), 'hasta': str(f_fin),
                    # 'generado' NO es decoracion: la app lo muestra para
                    # que nadie confunda una imagen de hace un mes con la
                    # de hoy. Un dato viejo sin fecha es un dato que miente.
                    'generado': date.today().isoformat(),
                }
                print(f'      OK  {peso / 1024:.0f} KB   KPI = {valor}')

            except Exception as e:
                # UN FALLO NO DEBE BORRAR UN MAPA QUE YA EXISTE.
                #
                # La version anterior escribia {'archivo': None} y punto.
                # Resultado: una corrida con un timeout pasajero de GEE
                # borraba del indice dos mapas de ANDES perfectamente
                # buenos que seguian en disco. Un error transitorio se
                # convertia en perdida permanente.
                #
                # Conservamos la entrada anterior CON su fecha 'generado'
                # original — la app la muestra, asi que el usuario ve que
                # es vieja. Un mapa fechado de hace tres dias informa;
                # un hueco no informa nada.
                print(f'      FALLO: {type(e).__name__}: {e}')
                anterior = previo.get(clave)
                ruta_anterior = ruta_de(anterior)

                if ruta_anterior and os.path.exists(ruta_anterior):
                    anterior = dict(anterior)
                    anterior['archivo'] = os.path.basename(ruta_anterior)
                    anterior['error_ultimo_intento'] = str(e)
                    anterior['ultimo_intento'] = date.today().isoformat()
                    indice[clave] = anterior
                    conservados += 1
                    print(f'      Se conserva el mapa previo '
                          f'(generado {anterior.get("generado")})')
                else:
                    indice[clave] = {'archivo': None, 'error': str(e)}

    with open(ruta_indice, 'w', encoding='utf-8') as f:
        json.dump(indice, f, indent=2, ensure_ascii=False)

    nuevos = sum(1 for v in indice.values()
                 if v.get('archivo') and 'error_ultimo_intento' not in v)
    disponibles = sum(1 for v in indice.values() if v.get('archivo'))

    print(f'\n{disponibles}/{total} mapas disponibles '
          f'({nuevos} regenerados hoy, {conservados} conservados).')
    print(f'Carpeta: {CARPETA_MAPAS}')

    if disponibles < total:
        faltan = [k for k, v in indice.items() if not v.get('archivo')]
        print('SIN MAPA: ' + ', '.join(faltan))
        print('La app mostrara un aviso en esas combinaciones.')


if __name__ == '__main__':
    main()