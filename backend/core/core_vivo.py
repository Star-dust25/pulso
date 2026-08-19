# core_vivo.py
# ============================================================
# DATOS EN VIVO — la Etapa 1 deja de ser una foto
#
# ------------------------------------------------------------
# ESTADO: ESCRITO Y PROBADO, PERO NO CONECTADO
#
# Este modulo NO se usa todavia. api/alerta.py lo tiene marcado como TODO
# y sirve el estado leyendo unicamente el CSV historico, declarandolo en
# el campo 'motivo' de la respuesta.
#
# Se deja aqui, funcional y documentado, porque es el siguiente paso del
# proyecto — no porque ya este operando. Un modulo que promete tiempo real
# y no se ejecuta es peor que no tenerlo: hace creer que el sistema hace
# algo que no hace.
#
# Para conectarlo haria falta, en get_alerta_data() de api/alerta.py:
#   try:
#       reciente = core_vivo.sst_reciente()
#       historico = core_vivo.fusionar(historico, reciente)
#       en_vivo, motivo = True, 'Dato de OISST via Earth Engine.'
#   except Exception as e:
#       en_vivo, motivo = False, f'Sin conexion a Earth Engine: {e}'
#
# ------------------------------------------------------------
# EL PROBLEMA QUE RESOLVERIA
#
# Los CSV del repositorio estan congelados en la fecha en que se
# descargaron. Un "sistema de alerta temprana" que muestra el estado del
# mar de hace un mes no es un sistema operativo: es una captura.
#
# ------------------------------------------------------------
# QUE SIGNIFICA "EN VIVO" AQUI, CON PRECISION
#
# NO significa "hoy". OISST se publica con retraso: entre uno y cuatro
# dias segun el momento, contando la latencia de la NOAA y la de la
# ingesta en Earth Engine. Lo mas fresco que este modulo puede devolver
# son datos de hace dos a cuatro dias.
#
# "En vivo" aqui quiere decir: la ultima observacion disponible en la
# fuente, en vez de la que quedo congelada en el CSV. Esa es la mejora
# real, y conviene enunciarla asi y no como "tiempo real".
#
# ------------------------------------------------------------
# EL LIMITE POR SENSOR
#
# ETAPA 1 (oceano) SI puede actualizarse a diario. OISST es diario y solo
# hacen falta los ultimos ~150 dias para calcular el precursor de 30 dias.
# Son unas pocas decenas de lecturas: rapido y barato.
#
# ETAPA 2 (territorio) NO puede, y decirlo importa. Landsat 8 revisita
# cada 16 dias y el MSAVI se compone por mes. "Diario" no significa nada
# para un indice mensual. Se declara como lo que es: actualizacion
# mensual.
#
# Un precursor oceanico diario y una confirmacion territorial mensual.
# Eso no es una limitacion del sistema: es la fisica de los sensores.
#
# ------------------------------------------------------------
# REGLA DE ORO (cuando se conecte)
#
# Si Earth Engine responde -> dato de la fuente.
# Si no responde           -> se cae al CSV local, sin romperse.
#
# El sistema nunca deja de dar un diagnostico. Solo cambia la frescura del
# dato, y lo dice en pantalla.
# ============================================================

import pandas as pd

# Imports tolerantes a las dos formas de ejecucion: como paquete
# (backend/ en el path) o como modulo suelto dentro de su carpeta. Sin
# esto, conectar el modulo desde api/alerta.py falla con
# ModuleNotFoundError, que es exactamente el problema que ya rompio los
# scripts de descarga.
try:
    from config.config_ecosistemas import REGION_NINO_1_2, ESCALA_SST
except ImportError:
    from config_ecosistemas import REGION_NINO_1_2, ESCALA_SST

DIAS_HISTORIA = 150      # suficiente para el precursor de 30 dias, con margen


def _importar_series():
    """core_series segun como se haya cargado el paquete."""
    try:
        from core.core_series import COL_OISST, FACTOR_ESCALA_OISST, caja
    except ImportError:
        from core_series import COL_OISST, FACTOR_ESCALA_OISST, caja
    return COL_OISST, FACTOR_ESCALA_OISST, caja


def sst_reciente(dias=DIAS_HISTORIA):
    """
    Ultimos N dias de TSM en la region Niño 1+2, leidos de OISST.

    Devuelve un DataFrame indexado por fecha con la columna 'sst_nino12',
    en el mismo formato que serie_sst_diaria.csv, para que el motor de
    alerta no tenga que distinguir de donde viene el dato.

    La ventana pedida llega hasta hoy, pero la fuente publica con retraso:
    en la practica la ultima fila sera de hace dos a cuatro dias. No es un
    fallo, es la latencia de OISST.

    Lanza excepcion si Earth Engine no responde: el llamante decide si
    cae al respaldo local. Asume que ee.Initialize() ya se ejecuto.
    """
    import ee
    COL_OISST, FACTOR_ESCALA_OISST, caja = _importar_series()

    # Se usa caja() de core_series, no una copia local: dos definiciones
    # de la misma geometria acaban divergiendo y produciendo series que
    # no son comparables entre si.
    region = caja(REGION_NINO_1_2)

    hoy = pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d')
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

    Los dias presentes en ambos se resuelven a favor del dato de la
    FUENTE: OISST publica una version preliminar y luego la corrige, asi
    que la lectura mas reciente siempre gana a la que quedo congelada en
    el CSV.

    OJO: solo conserva 'sst_nino12'. La columna 'sst_piura' del CSV se
    pierde, porque sst_reciente() no la descarga. El motor de alerta no la
    usa (anomalia_diaria solo lee sst_nino12), pero cualquier consumidor
    que la necesite dejaria de encontrarla al conectar este modulo.
    """
    columnas = ['sst_nino12']
    hist = historico[columnas].copy()
    nuevo = reciente[columnas].copy()

    unido = pd.concat([hist, nuevo])
    unido = unido[~unido.index.duplicated(keep='last')]
    return unido.sort_index()
