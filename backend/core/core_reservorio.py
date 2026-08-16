# core_reservorio.py
# ============================================================
# EL CAUDALIMETRO SATELITAL.
#
# Problema: no tenemos caudales de SENAMHI/ANA para validar el backtest.
# Solucion: los medimos nosotros. La superficie de agua de Poechos y
# San Lorenzo, extraida con MNDWI de Landsat, es un proxy fisico directo
# del almacenamiento hidrico regional. Tiene fecha, es continua desde 2013
# y sale del mismo pipeline que ya corre.
#
# Esto cierra la cadena causal:
#   anomalia SST  --(lag)-->  llenado de Poechos  --(lag)-->  bosque seco
#
# MNDWI = (Green - SWIR1) / (Green + SWIR1)   [Xu, 2006]
# Se prefiere a NDWI de McFeeters porque suprime mejor el ruido de suelo
# y construcciones en el borde del embalse.
# ============================================================

import ee

from core_series import (
    COL_LANDSAT8, enmascarar_nubes, escalar_reflectancia,
)

UMBRAL_AGUA = 0.0        # MNDWI > 0  -> agua
ESCALA_RESERVORIO = 30   # resolucion nativa de Landsat
BUFFER_ENVOLVENTE = 500  # m, para capturar el vaso lleno al maximo


def envolvente_reservorio(ruta_asset, nombre, campo='T21_Nombre',
                          buffer_m=BUFFER_ENVOLVENTE):
    """Poligono del vaso del embalse, con holgura para el nivel maximo."""
    fc = ee.FeatureCollection(ruta_asset).filter(ee.Filter.eq(campo, nombre))
    return fc.geometry().buffer(buffer_m)


def _mndwi(imagen):
    return imagen.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI')


def serie_reservorio_anual(anio, envolvente, escala=ESCALA_RESERVORIO):
    """
    Superficie de agua mensual (hectareas) dentro de la envolvente.

    Reporta tambien 'cobertura_valida': la fraccion del vaso que quedo
    visible tras la mascara de nubes. Si es baja, la medicion NO es fiable
    (las nubes se leen como 'no agua' y subestiman el embalse).
    Descartar los meses con cobertura < 0.6 en el analisis.
    """
    meses = ee.List.sequence(1, 12)
    area_total_m2 = envolvente.area(100)

    def por_mes(m):
        m = ee.Number(m)
        inicio = ee.Date.fromYMD(anio, m, 1)
        fin = inicio.advance(1, 'month')

        col = (ee.ImageCollection(COL_LANDSAT8)
               .filterDate(inicio, fin)
               .filterBounds(envolvente)
               .map(enmascarar_nubes)
               .map(escalar_reflectancia))
        n = col.size()

        vacio = ee.Image.constant(0).rename('MNDWI').selfMask()
        mndwi = ee.Image(ee.Algorithms.If(
            n.gt(0), _mndwi(col.median()), vacio))

        pixel = ee.Image.pixelArea()

        # Agua: MNDWI sobre umbral. Los pixeles enmascarados cuentan como 0.
        agua_m2 = (mndwi.gt(UMBRAL_AGUA).unmask(0).multiply(pixel)
                   .reduceRegion(reducer=ee.Reducer.sum(), geometry=envolvente,
                                 scale=escala, maxPixels=1e10, bestEffort=True)
                   .get('MNDWI'))

        # Cuanto del vaso pudimos observar realmente.
        valido_m2 = (mndwi.mask().multiply(pixel)
                     .reduceRegion(reducer=ee.Reducer.sum(), geometry=envolvente,
                                   scale=escala, maxPixels=1e10, bestEffort=True)
                     .get('MNDWI'))

        return ee.Feature(None, {
            'anio': anio,
            'mes': m,
            'agua_ha': ee.Number(agua_m2).divide(1e4),
            'cobertura_valida': ee.Number(valido_m2).divide(area_total_m2),
            'n_escenas': n,
        })

    return ee.FeatureCollection(meses.map(por_mes))
