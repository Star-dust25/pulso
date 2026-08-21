from fastapi import APIRouter
from cachetools import cached, TTLCache
import pandas as pd

from core.core_alerta import (
    cargar_diario, anomalia_diaria, emitir_episodios, serie_msavi,
    UMBRAL_PRECURSOR, UMBRAL_MSAVI, UMBRAL_MAGNITUD,
)

router = APIRouter()

# Cache de 30 min para la serie diaria, 1 h para la vegetacion mensual.
#
# OJO EN DEMOS: si regeneras los CSV con el servidor encendido, la web
# sigue mostrando lo viejo hasta media hora despues, SIN avisar. Reinicia
# uvicorn tras cualquier actualizacion de datos.
cache_alerta = TTLCache(maxsize=1, ttl=1800)
cache_msavi = TTLCache(maxsize=1, ttl=3600)

# Ventana del grafico de evolucion, en dias, RELATIVA al ultimo dato.
#
# Antes era la fecha literal '2025-06'. Dos problemas con eso: el grafico
# crece indefinidamente segun pasa el tiempo, y el dia que la serie
# empiece despues de esa fecha el endpoint devuelve una lista vacia sin
# error. Una constante temporal escrita a mano es una bomba de relojeria.
VENTANA_GRAFICO_DIAS = 420

# Ventana del panel mensual de z(MSAVI), en MESES, no en dias: la serie de
# vegetacion es mensual, asi que medirla en dias no tiene sentido y
# desalinearia el corte respecto a los meses ya calculados. 18 meses da
# año y medio de contexto, similar a la ventana que usan los paneles del
# backtest historico (por ejemplo, el de 2015-16 cubre 16 meses).
VENTANA_MSAVI_MESES = 18


@cached(cache_alerta)
def get_alerta_data():
    """
    Serie diaria + episodios, leidos del CSV historico.

    POR QUE 'en_vivo' ES SIEMPRE False
    ----------------------------------
    core_vivo.fusionar() esta escrito y probado, pero NO esta conectado.
    Es una decision, no un olvido: preferimos servir un dato de fecha
    conocida a depender de una llamada externa que puede caerse en mitad
    de una demostracion.

    El CSV lo actualiza scripts/construir_serie_diaria.py, y el campo
    'ultimo_dato' dice hasta cuando llega. Un sistema de alerta que sirve
    datos congelados sin decirlo es peor que uno caido; por eso la fecha
    viaja en la respuesta.

    NOTA: el mensaje anterior decia "Earth Engine no conectado". Era falso:
    Earth Engine funciona —los scripts de descarga lo usan sin problema—.
    Lo que no existe es la fusion en vivo dentro de la API.
    """
    historico = cargar_diario()
    en_vivo = False
    motivo = ("Fusion en vivo no implementada: la API sirve el CSV "
              "historico, actualizado por scripts/construir_serie_diaria.py. "
              "Ver el campo 'ultimo_dato' para saber hasta cuando llega.")

    df = anomalia_diaria(historico)
    df, episodios = emitir_episodios(df)
    return df, episodios, en_vivo, motivo


@cached(cache_msavi)
def get_msavi_data():
    return serie_msavi()


@router.get("/estado")
def get_estado():
    df, episodios, en_vivo, motivo = get_alerta_data()
    veg = get_msavi_data()

    ultimo = df.dropna(subset=['precursor']).iloc[-1]
    zs = veg['z_msavi'].dropna()
    z_act = zs.iloc[-1]
    mes_z = zs.index[-1]

    etapa1_activa = bool(ultimo['etapa1'])
    etapa2_activa = bool(z_act >= UMBRAL_MSAVI)

    # Ventana relativa al ultimo dato disponible, no a una fecha fija.
    inicio = df.index.max() - pd.Timedelta(days=VENTANA_GRAFICO_DIAS)
    # Solo las dos columnas que el grafico usa. Ademas de aligerar el
    # payload, evita que el .where() de abajo toque la columna booleana
    # 'etapa1': mezclar None con bool provoca un upcast a object y pandas
    # lanza un aviso — o un error, segun la version.
    recent = df.loc[inicio:, ['anomalia', 'precursor']].copy()

    # JSON no tiene NaN. Sin esta conversion, FastAPI serializa el literal
    # NaN, que JSON.parse() del navegador rechaza: el fetch falla entero.
    recent = recent.astype(object).where(pd.notnull(recent), None)

    historico_records = [
        {
            "fecha": fecha.strftime('%Y-%m-%d'),
            "anomalia": fila["anomalia"],
            "precursor": fila["precursor"],
        }
        for fecha, fila in recent.iterrows()
    ]

    # --- Serie mensual de z(MSAVI) para el panel "estado actual" ---
    #
    # Reutiliza 'veg' completo (no solo 'zs', que ya viene sin nulos): los
    # meses futuros del año en curso existen en el CSV con valor nulo, y
    # conservarlos deja huecos visibles en vez de que la barra del mes
    # que aun no ocurrio desaparezca sin explicacion.
    inicio_msavi = veg.index.max() - pd.DateOffset(months=VENTANA_MSAVI_MESES)
    veg_reciente = veg.loc[inicio_msavi:, ['z_msavi']].copy()
    veg_reciente = veg_reciente.astype(object).where(
        pd.notnull(veg_reciente), None)

    msavi_mensual = [
        {
            "mes": fecha.strftime('%Y-%m'),
            "z_msavi": fila["z_msavi"],
        }
        for fecha, fila in veg_reciente.iterrows()
    ]

    return {
        "etapa1_activa": etapa1_activa,
        "etapa2_activa": etapa2_activa,
        "precursor": float(ultimo['precursor']),
        "z_msavi": float(z_act),
        "umbral_precursor": float(UMBRAL_PRECURSOR),
        # Umbral de MAGNITUD (no de alerta): el pico minimo de precursor
        # oceanico que hace falta para escalar a Etapa 2, ademas del criterio
        # de persistencia de 15 dias. Es la segunda linea de referencia que
        # ya se dibuja en los paneles ETAPA 1 del backtest historico
        # (core_alerta.graficar); el grafico de evolucion diaria del Resumen
        # solo tenia la primera.
        "umbral_magnitud": float(UMBRAL_MAGNITUD),
        "umbral_msavi": float(UMBRAL_MSAVI),
        "fecha_precursor": ultimo.name.strftime('%d-%b-%Y'),
        # El compuesto MSAVI del mes EN CURSO se calcula con las escenas
        # que haya hasta la fecha, asi que a mitad de mes es parcial. No se
        # filtra (a diferencia de core_icen.py, que si descarta los meses
        # con menos de 25 dias de OISST): la Etapa 2 se lee como tendencia
        # mensual, no como un valor cerrado. Conviene saberlo si el mes que
        # aparece aqui es el actual.
        "fecha_msavi": mes_z.strftime('%b-%Y'),
        # La frescura del dato es parte del diagnostico, no un detalle
        # tecnico. El frontend debe mostrarla cuando en_vivo es False.
        "en_vivo": en_vivo,
        "motivo": motivo,
        "ultimo_dato": df.index.max().strftime('%Y-%m-%d'),
        "historico": historico_records,
        # Serie mensual de z(MSAVI), para dibujar el mismo tipo de barras
        # que ya usa el panel "Etapa 2" del backtest historico, pero con
        # los meses recientes. 'z_msavi' puede venir null en meses futuros
        # del año en curso o sin escenas utiles: es informacion honesta
        # (mes no observado), no un cero.
        "msavi_mensual": msavi_mensual,
    }