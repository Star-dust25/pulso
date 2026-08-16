from fastapi import APIRouter
from cachetools import cached, TTLCache
import pandas as pd

from core.core_alerta import (
    cargar_diario, anomalia_diaria, emitir_episodios, serie_msavi,
    UMBRAL_PRECURSOR, UMBRAL_MSAVI,
)

router = APIRouter()

# Cache de 30 min para la serie diaria, 1 h para la vegetacion mensual.
cache_alerta = TTLCache(maxsize=1, ttl=1800)
cache_msavi = TTLCache(maxsize=1, ttl=3600)

# Ventana del grafico de evolucion, en dias, RELATIVA al ultimo dato.
#
# Antes era la fecha literal '2025-06'. Dos problemas con eso: el grafico
# crece indefinidamente segun pasa el tiempo, y el dia que la serie
# empiece despues de esa fecha el endpoint devuelve una lista vacia sin
# error. Una constante temporal escrita a mano es una bomba de relojeria.
VENTANA_GRAFICO_DIAS = 420


@cached(cache_alerta)
def get_alerta_data():
    """
    Serie diaria + episodios.

    TODO PENDIENTE: aqui va la fusion con el dato vivo de OISST via
    core_vivo.fusionar(). Mientras no este, el sistema opera solo con el
    CSV historico y LO DECLARA en el campo 'motivo'. Un sistema de alerta
    que sirve datos congelados sin decirlo es peor que uno caido.
    """
    historico = cargar_diario()
    en_vivo = False
    motivo = "Earth Engine no conectado: operando solo con el CSV historico."

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

    return {
        "etapa1_activa": etapa1_activa,
        "etapa2_activa": etapa2_activa,
        "precursor": float(ultimo['precursor']),
        "z_msavi": float(z_act),
        "umbral_precursor": float(UMBRAL_PRECURSOR),
        "umbral_msavi": float(UMBRAL_MSAVI),
        "fecha_precursor": ultimo.name.strftime('%d-%b-%Y'),
        "fecha_msavi": mes_z.strftime('%b-%Y'),
        # La frescura del dato es parte del diagnostico, no un detalle
        # tecnico. El frontend debe mostrarla cuando en_vivo es False.
        "en_vivo": en_vivo,
        "motivo": motivo,
        "ultimo_dato": df.index.max().strftime('%Y-%m-%d'),
        "historico": historico_records,
    }
