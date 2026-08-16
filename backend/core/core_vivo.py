# core_vivo.py
# ============================================================
# DATOS EN VIVO — la Etapa 1 deja de ser una foto
#
# ------------------------------------------------------------
# EL PROBLEMA QUE RESUELVE
#
# Los CSV del repositorio estan congelados en la fecha en que se
# descargaron. Un "sistema de alerta temprana" que muestra el estado del
# mar de hace una semana no es un sistema operativo: es una captura.
#
# ------------------------------------------------------------
# LA SOLUCION, Y SU LIMITE HONESTO
#
# ETAPA 1 (oceano) SI puede ir en vivo. OISST es diario y solo hacen falta
# los ultimos ~150 dias para calcular el precursor de 30 dias. Son unas
# pocas decenas de lecturas: rapido y barato.
#
# ETAPA 2 (territorio) NO puede ir en vivo, y decirlo importa. Landsat 8
# revisita cada 16 dias y el MSAVI se compone por mes. "Tiempo real" no
# significa nada para un indice mensual. Se declara como lo que es:
# actualizacion mensual.
#
# Un precursor oceanico diario y una confirmacion territorial mensual.
# Eso no es una limitacion del sistema: es la fisica de los sensores.
#
# ------------------------------------------------------------
# REGLA DE ORO
#
# Si Earth Engine responde -> dato vivo.
# Si no responde           -> se cae al CSV local, sin romperse.
#
# El sistema nunca deja de dar un diagnostico. Solo cambia la frescura del
# dato, y lo dice en pantalla.
# ============================================================

import pandas as pd

from config_ecosistemas import REGION_NINO_1_2, ESCALA_SST

DIAS_HISTORIA = 150      # suficiente para el precursor de 30 dias, con margen


def _caja(coords):
    import ee
    oeste, sur, este, norte = coords
    return ee.Geometry.BBox(oeste, sur, este, norte)


def sst_reciente(dias=DIAS_HISTORIA):
    """
    Ultimos N dias de TSM en la region Niño 1+2, leidos de OISST EN VIVO.

    Devuelve un DataFrame indexado por fecha con la columna 'sst_nino12',
    en el mismo formato que serie_sst_diaria.csv, para que el motor de
    alerta no tenga que distinguir de donde viene el dato.

    Lanza excepcion si Earth Engine no responde: el llamante decide si
    cae al respaldo local.
    """
    import ee
    from core_series import COL_OISST, FACTOR_ESCALA_OISST

    region = _caja(REGION_NINO_1_2)
    hoy = pd.Timestamp.utcnow().strftime('%Y-%m-%d')
    fin = ee.Date(hoy).advance(1, 'day')
    inicio = ee.Date(hoy).advance(-dias, 'day')

    col = (ee.ImageCollection(COL_OISST)
           .filterDate(inicio, fin)
           .select('sst'))

    def por_imagen(img):
        valor = (img.multiply(FACTOR_ESCALA_OISST)
                 .reduceRegion(reducer=ee.Reducer.mean(), geometry=region,
                               scale=ESCALA_SST, maxPixels=1e9,
                               bestEffort=True)
                 .get('sst'))
        return ee.Feature(None, {
            'fecha': img.date().format('YYYY-MM-dd'),
            'sst_nino12': valor,
        })

    datos = ee.FeatureCollection(col.map(por_imagen)).getInfo()['features']

    filas = [d['properties'] for d in datos]
    if not filas:
        raise RuntimeError('OISST no devolvio datos recientes.')

    df = pd.DataFrame(filas)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['sst_nino12'] = pd.to_numeric(df['sst_nino12'], errors='coerce')
    df = df.dropna(subset=['sst_nino12'])

    if df.empty:
        raise RuntimeError('OISST devolvio solo valores nulos.')

    return df.sort_values('fecha').set_index('fecha')


def fusionar(historico, reciente):
    """
    Une la serie historica del CSV con el tramo reciente de Earth Engine.

    Los dias presentes en ambos se resuelven a favor del dato EN VIVO:
    OISST publica una version preliminar y luego la corrige, asi que la
    lectura mas reciente de la fuente siempre gana a la que quedo congelada
    en el CSV.
    """
    columnas = ['sst_nino12']
    hist = historico[columnas].copy()
    nuevo = reciente[columnas].copy()

    unido = pd.concat([hist, nuevo])
    unido = unido[~unido.index.duplicated(keep='last')]
    return unido.sort_index()
