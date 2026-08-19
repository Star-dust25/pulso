# core_reservorio.py
# ============================================================
# SUPERFICIE DE AGUA EMBALSADA, MEDIDA POR SATELITE
#
# ------------------------------------------------------------
# QUE MIDE, CON PRECISION
#
# Mide la SUPERFICIE de agua del vaso, en hectareas. Eso es un proxy del
# ALMACENAMIENTO, no del CAUDAL. Superficie no es flujo: dos embalses con
# la misma area pueden estar descargando cantidades muy distintas.
#
# (Una version anterior de este archivo se titulaba "el caudalimetro
# satelital". Era una sobreafirmacion y se corrigio: nunca hemos medido
# caudales.)
#
# ------------------------------------------------------------
# POR QUE EXISTE
#
# No disponemos de caudales de SENAMHI/ANA para el periodo del backtest.
# La superficie de agua de Poechos y San Lorenzo, extraida con MNDWI de
# Landsat, es lo mas cercano que podemos construir con datos abiertos:
# tiene fecha, es continua desde 2013 y sale del mismo pipeline que ya
# corre.
#
# ------------------------------------------------------------
# RESULTADO: LA CADENA DE TRES ESLABONES NO SE SOSTIENE
#
# La hipotesis era:
#   anomalia SST --(lag)--> llenado de Poechos --(lag)--> bosque seco
#
# core_lag.py la midio y NO se confirma:
#
#   Litoral -> Poechos    r = -0.235   p = 0.013    NO significativo
#   Poechos -> Montes     r = -0.336   lag 5 meses  signo NEGATIVO
#   Litoral -> Montes     r = +0.499   lag 1 mes    SI significativo
#
# Interpretacion honesta: el embalse NO actua como intermediario
# detectable. Poechos se opera con criterios humanos —descargas
# programadas, cotas de seguridad, demanda de riego— y esa gestion rompe
# el vinculo con la señal climatica. El eslabon negativo no describe un
# mecanismo plausible; lo mas probable es una tendencia comun.
#
# Ademas, el 36% de los meses se descartan por nubosidad (61 de 168), asi
# que la serie llega mermada al analisis y tiene poca potencia de partida.
#
# ESTE MODULO SE MANTIENE para poder REPORTAR ese resultado nulo con
# evidencia. Un hallazgo nulo publicado vale mas que uno omitido. Pero la
# Etapa 2 de Pulso NO depende de el: usa el vinculo directo mar -> bosque
# seco, que si se sostiene.
#
# ------------------------------------------------------------
# MNDWI = (Green - SWIR1) / (Green + SWIR1)   [Xu, 2006]
# Se prefiere a NDWI de McFeeters porque suprime mejor el ruido de suelo
# y construcciones en el borde del embalse.
# ============================================================

import ee

# Import tolerante a las dos formas de ejecucion: como paquete (backend/
# en el path) o como modulo suelto dentro de core/.
try:
    from core.core_series import (
        COL_LANDSAT8, enmascarar_nubes, escalar_reflectancia,
    )
except ImportError:
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

    'cobertura_valida' es la fraccion del vaso que quedo visible tras la
    mascara de nubes. NO ES OPCIONAL FILTRAR POR ELLA: los pixeles
    enmascarados se cuentan como "no agua", asi que un mes nublado
    SUBESTIMA el embalse sin avisar. core_lag.py descarta los meses con
    cobertura < 0.60, y aun asi pierde el 36% de la serie.

    Un mes sin escenas devuelve agua_ha = 0 y cobertura_valida = 0. Ese
    cero NO significa "embalse vacio": significa "no observado". Es otra
    razon para filtrar siempre por cobertura antes de usar la serie.

    El indice se calcula sobre el compuesto mediano del mes, no como
    mediana de los indices diarios. Para deteccion de agua la diferencia
    es menor, pero conviene saberlo: la serie describe el estado tipico
    del mes, no un dia concreto.
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

        # Agua: MNDWI sobre umbral. Los pixeles enmascarados cuentan como 0,
        # es decir, como "no agua". Por eso 'cobertura_valida' es
        # imprescindible: sin ella un mes nublado parece un embalse vacio.
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