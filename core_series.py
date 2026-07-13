# core_series.py
# ============================================================
# Motor de series temporales de P.A.L.M.A.
#
# Responsabilidad unica: extraer de Google Earth Engine la serie
# mensual de los tres ecosistemas. NO grafica, NO decide, NO opina.
#
# Correcciones respecto al codigo anterior:
#   1. SST de OISST (diario, desde 1981) en lugar de Landsat (16 dias, 2013+).
#      Esto habilita el backtest de 1997/2017/2023.
#   2. Landsat COLECCION 2 NIVEL 2 (reflectancia de superficie) en lugar de TOA.
#      Sin esto los indices no son comparables entre fechas.
#   3. Mascara de nubes real con QA_PIXEL (antes: ninguna).
#   4. NDMI (NIR-SWIR) para humedad del paramo, en lugar de NDWI de McFeeters
#      que solo detecta cuerpos de agua abiertos.
# ============================================================

import ee

COL_LANDSAT8 = 'LANDSAT/LC08/C02/T1_L2'
COL_OISST = 'NOAA/CDR/OISST/V2_1'

FACTOR_ESCALA_OISST = 0.01          # centesimas de grado -> grados C
FACTOR_ESCALA_SR = 0.0000275        # digital number -> reflectancia
OFFSET_SR = -0.2


# ------------------------------------------------------------
# Preprocesamiento Landsat
# ------------------------------------------------------------

def enmascarar_nubes(imagen):
    """
    Mascara de nubes usando la banda QA_PIXEL de Landsat Coleccion 2.
    Bits: 1 = nube dilatada, 2 = cirro, 3 = nube, 4 = sombra de nube.
    """
    qa = imagen.select('QA_PIXEL')
    mascara = (
        qa.bitwiseAnd(1 << 1).eq(0)
        .And(qa.bitwiseAnd(1 << 2).eq(0))
        .And(qa.bitwiseAnd(1 << 3).eq(0))
        .And(qa.bitwiseAnd(1 << 4).eq(0))
    )
    return imagen.updateMask(mascara)


def escalar_reflectancia(imagen):
    """Convierte los enteros de Landsat C2 L2 a reflectancia fisica [0,1]."""
    opticas = imagen.select('SR_B.').multiply(FACTOR_ESCALA_SR).add(OFFSET_SR)
    return imagen.addBands(opticas, None, True)


def anadir_indices(imagen):
    """
    NDMI: humedad de la vegetacion/suelo    (NIR - SWIR1) / (NIR + SWIR1)
    MSAVI: vigor vegetal robusto a suelo desnudo (clave en bosque seco)
    """
    ndmi = imagen.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDMI')

    msavi = imagen.expression(
        '(2 * NIR + 1 - sqrt(pow((2 * NIR + 1), 2) - 8 * (NIR - RED))) / 2',
        {'NIR': imagen.select('SR_B5'), 'RED': imagen.select('SR_B4')}
    ).rename('MSAVI')

    return imagen.addBands([ndmi, msavi])


def coleccion_landsat_limpia(fecha_inicio, fecha_fin, region):
    """Landsat 8 L2, sin nubes, escalado, con NDMI y MSAVI listos."""
    return (
        ee.ImageCollection(COL_LANDSAT8)
        .filterDate(fecha_inicio, fecha_fin)
        .filterBounds(region)
        .map(enmascarar_nubes)
        .map(escalar_reflectancia)
        .map(anadir_indices)
        .select(['NDMI', 'MSAVI'])
    )


# ------------------------------------------------------------
# Geometrias de ecosistema
# ------------------------------------------------------------

def geometria_ecosistema(ruta_asset, campo, valores, tolerancia=500):
    """
    Devuelve la geometria disuelta de una lista de clases de ECO_REGION.
    Simplifica para que reduceRegion no colapse por exceso de vertices.
    """
    fc = ee.FeatureCollection(ruta_asset).filter(
        ee.Filter.inList(campo, ee.List(valores))
    )
    return fc.geometry().simplify(maxError=tolerancia)


def caja(coords):
    """(oeste, sur, este, norte) -> ee.Geometry.BBox"""
    oeste, sur, este, norte = coords
    return ee.Geometry.BBox(oeste, sur, este, norte)


# ------------------------------------------------------------
# Serie mensual: LITORAL (anomalia de SST)
# ------------------------------------------------------------

def serie_sst_anual(anio, region_nino12, region_local, escala=25000):
    """
    Media mensual de SST y de su ANOMALIA sobre dos regiones:
      - Nino 1+2 (referencia oficial, base del ICEN de ENFEN)
      - caja local frente a Piura (senal costera)

    Devuelve un ee.FeatureCollection de 12 features (uno por mes).
    """
    meses = ee.List.sequence(1, 12)

    def por_mes(m):
        m = ee.Number(m)
        inicio = ee.Date.fromYMD(anio, m, 1)
        fin = inicio.advance(1, 'month')

        col = ee.ImageCollection(COL_OISST).filterDate(inicio, fin)
        n_dias = col.size()

        # Los meses futuros (o sin dato) devuelven una coleccion vacia.
        # mean() sobre coleccion vacia da una imagen SIN BANDAS y multiply()
        # revienta. Devolvemos una imagen enmascarada -> reduceRegion da null.
        vacio = ee.Image.constant([0, 0]).rename(['sst', 'anom']).selfMask()
        img = ee.Image(ee.Algorithms.If(
            n_dias.gt(0),
            col.select(['sst', 'anom']).mean().multiply(FACTOR_ESCALA_OISST),
            vacio,
        ))

        n12 = img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region_nino12,
            scale=escala, maxPixels=1e9, bestEffort=True
        )
        loc = img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region_local,
            scale=escala, maxPixels=1e9, bestEffort=True
        )

        return ee.Feature(None, {
            'anio': anio,
            'mes': m,
            'sst_nino12': n12.get('sst'),
            'anom_nino12': n12.get('anom'),
            'sst_piura': loc.get('sst'),
            'anom_piura': loc.get('anom'),
            'n_dias_sst': n_dias,
        })

    return ee.FeatureCollection(meses.map(por_mes))


# ------------------------------------------------------------
# Serie mensual: ANDES y MONTES (vegetacion)
# ------------------------------------------------------------

def serie_vegetacion_anual(anio, geom_andes, geom_montes,
                           escala_andes=60, escala_montes=200):
    """
    Media mensual de NDMI (paramo+bofedal) y MSAVI (bosque seco costero).
    Si un mes no tiene escenas utiles tras la mascara de nubes, devuelve null:
    eso es informacion honesta, no un cero inventado.
    """
    meses = ee.List.sequence(1, 12)
    region_total = geom_andes.union(geom_montes, 1000)

    def por_mes(m):
        m = ee.Number(m)
        inicio = ee.Date.fromYMD(anio, m, 1)
        fin = inicio.advance(1, 'month')

        col = coleccion_landsat_limpia(inicio, fin, region_total)
        n = col.size()

        # Si el mes esta vacio, generamos una imagen totalmente enmascarada
        # para que reduceRegion devuelva null en vez de reventar.
        vacio = ee.Image.constant([0, 0]).rename(['NDMI', 'MSAVI']).selfMask()
        img = ee.Image(ee.Algorithms.If(n.gt(0), col.median(), vacio))

        v_andes = img.select('NDMI').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_andes,
            scale=escala_andes, maxPixels=1e10, bestEffort=True, tileScale=4
        )
        v_montes = img.select('MSAVI').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_montes,
            scale=escala_montes, maxPixels=1e10, bestEffort=True, tileScale=4
        )

        return ee.Feature(None, {
            'anio': anio,
            'mes': m,
            'ndmi_andes': v_andes.get('NDMI'),
            'msavi_montes': v_montes.get('MSAVI'),
            'n_escenas': n,
        })

    return ee.FeatureCollection(meses.map(por_mes))