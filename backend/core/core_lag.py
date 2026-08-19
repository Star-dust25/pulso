# core_lag.py
# ============================================================
# EL MOTOR DE ACOPLAMIENTO DE Pulso  (v2)
#
# Reemplaza a simular_efecto_cascada(), donde los desfases estaban
# escritos a mano. Aqui los desfases NO se asumen: se miden.
#
# Cadena evaluada:
#   anomalia SST  ->  llenado de Poechos  ->  respuesta del bosque seco
#
# ------------------------------------------------------------
# LO QUE LOS DATOS DICEN (y no es lo que esperabamos)
#
# La cadena de tres eslabones NO se sostiene. Lo que se sostiene es el
# vinculo DIRECTO. Resultados de la ultima corrida:
#
#   Litoral -> Poechos    r = -0.235  p = 0.013   NO significativo
#   Poechos -> Montes     r = -0.336  p = 0.0003  significativo pero de
#                                                 SIGNO NEGATIVO
#   Litoral -> Montes     r = +0.499  lag 1 mes   SIGNIFICATIVO
#   Litoral -> Andes      r = -0.135  p = 0.088   NO significativo
#
# Interpretacion honesta:
#
# 1. El embalse NO actua como intermediario detectable. Poechos se opera
#    con criterios humanos (descargas programadas, cotas de seguridad), no
#    como un reservorio natural que integre la señal climatica. Ademas el
#    36% de sus meses se descartan por nubosidad, asi que la serie llega
#    mermada al analisis.
#
# 2. El eslabon Poechos -> Montes sale NEGATIVO: mas agua en el vaso
#    precede a MENOS verdor cinco meses despues. Eso no describe un
#    mecanismo causal plausible; lo mas probable es que ambas series
#    compartan una tendencia comun. Se reporta, no se interpreta como
#    causalidad.
#
# 3. El vinculo que Pulso USA es el DIRECTO (mar -> bosque seco, lag de un
#    mes). Ese es fuerte, positivo y estable a lo largo de varios lags.
#
# 4. EL CONTROL FUNCIONA. Litoral -> Andes NO es significativo: el paramo
#    andino no responde al calentamiento costero. Si todo correlacionara
#    con todo, seria ruido. Que el control salga nulo es lo que da valor
#    al resultado positivo.
#
# ------------------------------------------------------------
# CONTROLES DE RIGOR APLICADOS
#
# 1. DESESTACIONALIZACION. NDMI, MSAVI y el nivel de embalse tienen un
#    ciclo anual fortisimo. Correlacionar series estacionales fabrica lags
#    espurios. Restamos la climatologia mensual de cada serie.
#    (La SST ya viene como anomalia: banda 'anom' de OISST.)
#
# 2. FILTRO DE COBERTURA. Un mes nublado sobre Poechos devuelve agua_ha=0
#    porque la nube se lee como "no agua". Ese cero es FALSO. Descartamos
#    los meses con menos del 60% del vaso visible.
#
# 3. CORRECCION POR COMPARACIONES MULTIPLES. Probamos 13 desfases por par.
#    Un p=0.04 entre 13 pruebas es ruido, no hallazgo. Aplicamos Bonferroni:
#    el umbral real es 0.05/13 = 0.0038.
#
# ------------------------------------------------------------
# EL CONTROL QUE NO APLICAMOS, Y HAY QUE DECIRLO
#
# 4. AUTOCORRELACION SERIAL — NO CORREGIDA.
#
#    El test t de Pearson asume observaciones INDEPENDIENTES. Las
#    anomalias mensuales de SST y de vegetacion no lo son: el valor de un
#    mes predice buena parte del siguiente. Con n=162 meses, el numero
#    EFECTIVO de observaciones independientes puede ser de apenas 20 a 30.
#
#    Consecuencia: los p-valores de esta tabla estan SUBESTIMADOS, y no
#    por poco. Bonferroni corrige por comparaciones multiples; no corrige
#    esto.
#
#    Que sigue siendo defendible:
#      - El coeficiente r en si (mide asociacion, no depende del test).
#      - La FORMA del correlograma: el pico en lag 1 y el decaimiento
#        monotono hasta lag 12 es un patron, no un valor suelto.
#      - El contraste con el control (Andes), que sufre exactamente el
#        mismo problema y aun asi no correlaciona.
#
#    Que NO se debe afirmar: "p < 0.0001, luego es seguro". La forma
#    correcta de decirlo es: "la asociacion es fuerte y consistente; el
#    p-valor esta calculado asumiendo independencia, que en series
#    mensuales autocorrelacionadas es optimista".
#
#    Corregirlo requiere n efectivo (Bartlett/Quenouille) o bloques
#    bootstrap. Queda declarado como limitacion, no implementado.
#
# NO DEPENDE DE INTERNET. Solo pandas + numpy.
# ============================================================

import math
import os

import numpy as np
import pandas as pd

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'datos')
CSV_SST = os.path.join(CARPETA_DATOS, 'serie_sst.csv')
CSV_VEG = os.path.join(CARPETA_DATOS, 'serie_vegetacion.csv')
CSV_RES = os.path.join(CARPETA_DATOS, 'serie_reservorios.csv')

LAG_MAXIMO = 12
MIN_OBSERVACIONES = 24
COBERTURA_MINIMA = 0.60          # fraccion del vaso visible bajo nubes
ALFA = 0.05
ALFA_BONFERRONI = ALFA / (LAG_MAXIMO + 1)

RESERVORIO_PRINCIPAL = 'Poechos'


# ------------------------------------------------------------
# Carga
# ------------------------------------------------------------

def cargar_series():
    """Une SST, vegetacion y reservorio en un DataFrame mensual."""
    sst = pd.read_csv(CSV_SST)
    veg = pd.read_csv(CSV_VEG)

    df = pd.merge(sst, veg, on=['anio', 'mes'], how='outer')

    if os.path.exists(CSV_RES):
        res = pd.read_csv(CSV_RES)
        res = res[res['reservorio'] == RESERVORIO_PRINCIPAL].copy()

        # Control 2: los meses muy nublados no son datos, son ceros falsos.
        if 'cobertura_valida' in res.columns:
            descartados = int((res['cobertura_valida'] < COBERTURA_MINIMA).sum())
            res.loc[res['cobertura_valida'] < COBERTURA_MINIMA, 'agua_ha'] = np.nan
            print(f'[{RESERVORIO_PRINCIPAL}] {descartados}/{len(res)} meses '
                  f'descartados por cobertura < {COBERTURA_MINIMA:.0%}')
        else:
            # Sin la columna no podemos distinguir "vaso seco" de "vaso
            # tapado por nubes". Decirlo es mejor que asumir que todo vale.
            print(f'[{RESERVORIO_PRINCIPAL}] AVISO: falta la columna '
                  f'"cobertura_valida". No se filtran los meses nublados; '
                  f'los ceros pueden ser falsos.')

        res = res[['anio', 'mes', 'agua_ha']].rename(
            columns={'agua_ha': 'agua_poechos'})
        df = pd.merge(df, res, on=['anio', 'mes'], how='outer')

    df['fecha'] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    df = df.sort_values('fecha').set_index('fecha')

    for col in df.columns:
        if col not in ('anio', 'mes'):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def desestacionalizar(serie):
    """Control 1: valor - media historica de ese mes del anio."""
    climatologia = serie.groupby(serie.index.month).transform('mean')
    return serie - climatologia


def preparar(df):
    salida = df.copy()
    salida['anom_ndmi_andes'] = desestacionalizar(salida['ndmi_andes'])
    salida['anom_msavi_montes'] = desestacionalizar(salida['msavi_montes'])
    if 'agua_poechos' in salida.columns:
        salida['anom_poechos'] = desestacionalizar(salida['agua_poechos'])
    return salida


# ------------------------------------------------------------
# Correlacion cruzada
# ------------------------------------------------------------

def _pearson(x, y):
    n = len(x)
    if n < 3:
        return float('nan'), float('nan'), n
    r = float(np.corrcoef(x, y)[0, 1])
    if not np.isfinite(r) or abs(r) >= 1.0:
        return r, 0.0, n
    t = r * math.sqrt((n - 2) / (1 - r ** 2))
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    return r, p, n


def correlacion_cruzada(df, causa, efecto, lag_maximo=LAG_MAXIMO):
    """
    causa(t) vs efecto(t+k), para k = 0..lag_maximo.

    Devuelve 'p' redondeado para leerlo comodo y 'p_exacto' sin redondear.
    La decision de significancia SIEMPRE usa 'p_exacto': redondear a cuatro
    decimales cerca de un umbral de 0.0038 puede cambiar el veredicto.
    """
    if causa not in df.columns or efecto not in df.columns:
        return pd.DataFrame()

    filas = []
    for k in range(0, lag_maximo + 1):
        par = pd.concat([df[causa], df[efecto].shift(-k)],
                        axis=1, keys=['causa', 'efecto']).dropna()
        if len(par) < MIN_OBSERVACIONES:
            continue
        r, p, n = _pearson(par['causa'].values, par['efecto'].values)
        filas.append({
            'lag': k,
            'r': round(r, 3),
            'p': round(p, 4),
            'p_exacto': p,
            'n': n,
            'sig': 'SI' if p < ALFA_BONFERRONI else '-',
        })
    return pd.DataFrame(filas)


def lag_optimo(df, causa, efecto, lag_maximo=LAG_MAXIMO):
    tabla = correlacion_cruzada(df, causa, efecto, lag_maximo)
    if tabla.empty:
        return None

    mejor = tabla.loc[tabla['r'].abs().idxmax()]
    # p_exacto, no el redondeado: ver la nota de correlacion_cruzada().
    p = float(mejor['p_exacto'])
    return {
        'lag_meses': int(mejor['lag']),
        'lag_dias_aprox': int(mejor['lag'] * 30),
        'r': float(mejor['r']),
        'p_valor': p,
        'n': int(mejor['n']),
        'significativo': p < ALFA_BONFERRONI,   # umbral CORREGIDO
        'sentido': 'positivo' if mejor['r'] > 0 else 'negativo',
        'tabla': tabla.drop(columns=['p_exacto']),
    }


def acoplamiento_completo(df):
    """
    La cadena que sustenta la tesis, mas los controles.

    Los eslabones via Poechos y via paramo se mantienen para poder
    REPORTAR los hallazgos nulos con evidencia, no para esconderlos. Un
    resultado nulo publicado vale mas que un resultado nulo omitido.
    """
    pares = {
        'CADENA 1: Litoral -> Poechos': ('anom_piura', 'anom_poechos'),
        'CADENA 2: Poechos -> Montes':  ('anom_poechos', 'anom_msavi_montes'),
        'DIRECTO:  Litoral -> Montes':  ('anom_piura', 'anom_msavi_montes'),
        'CONTROL:  Litoral -> Andes':   ('anom_piura', 'anom_ndmi_andes'),
    }
    return {nombre: lag_optimo(df, c, e) for nombre, (c, e) in pares.items()}


# ------------------------------------------------------------
# python core_lag.py
# ------------------------------------------------------------

if __name__ == '__main__':
    datos = preparar(cargar_series())

    print('\n=== ACOPLAMIENTO MEDIDO (no asumido) ===')
    print(f'Umbral de significancia corregido (Bonferroni, {LAG_MAXIMO + 1} '
          f'pruebas): p < {ALFA_BONFERRONI:.4f}')
    print('AVISO: los p-valores asumen observaciones independientes. Las '
          'series mensuales estan')
    print('autocorrelacionadas, asi que estos p estan SUBESTIMADOS. Ver la '
          'limitacion 4 del encabezado.\n')

    for eslabon, res in acoplamiento_completo(datos).items():
        print(f'--- {eslabon}')
        if res is None:
            print('    datos insuficientes.\n')
            continue

        marca = 'SIGNIFICATIVO' if res['significativo'] else 'NO significativo'
        print(f'    lag optimo : {res["lag_meses"]} meses '
              f'(~{res["lag_dias_aprox"]} dias)')
        print(f'    r          : {res["r"]:+.3f} ({res["sentido"]})')
        print(f'    p          : {res["p_valor"]:.4f}   [{marca}]')
        print(f'    n          : {res["n"]} meses')
        if res['r'] < 0 and 'CONTROL' not in eslabon:
            print('    NOTA: signo NEGATIVO. No describe un mecanismo causal '
                  'plausible en esta cadena;')
            print('          lo mas probable es una tendencia comun. Se '
                  'reporta, no se interpreta.')
        print('    correlograma:')
        print(res['tabla'].to_string(index=False))
        print()