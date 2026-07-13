# core_lag.py
# ============================================================
# EL MOTOR DE ACOPLAMIENTO DE P.A.L.M.A.  (v2)
#
# Reemplaza a simular_efecto_cascada(), donde los desfases estaban
# escritos a mano. Aqui NADA se asume: todo se mide.
#
# Cadena evaluada:
#   anomalia SST  ->  llenado de Poechos  ->  respuesta del bosque seco
#
# TRES CONTROLES DE RIGOR QUE UN JURADO PUEDE EXIGIR:
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
# NO DEPENDE DE INTERNET. Solo pandas + numpy.
# ============================================================

import math
import os

import numpy as np
import pandas as pd

CARPETA_DATOS = 'datos'
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
        descartados = int((res['cobertura_valida'] < COBERTURA_MINIMA).sum())
        res.loc[res['cobertura_valida'] < COBERTURA_MINIMA, 'agua_ha'] = np.nan

        print(f'[{RESERVORIO_PRINCIPAL}] {descartados}/{len(res)} meses '
              f'descartados por cobertura < {COBERTURA_MINIMA:.0%}')

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
    """causa(t) vs efecto(t+k), para k = 0..lag_maximo."""
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
            'n': n,
            'sig': 'SI' if p < ALFA_BONFERRONI else '-',
        })
    return pd.DataFrame(filas)


def lag_optimo(df, causa, efecto, lag_maximo=LAG_MAXIMO):
    tabla = correlacion_cruzada(df, causa, efecto, lag_maximo)
    if tabla.empty:
        return None

    mejor = tabla.loc[tabla['r'].abs().idxmax()]
    p = float(mejor['p'])
    return {
        'lag_meses': int(mejor['lag']),
        'lag_dias_aprox': int(mejor['lag'] * 30),
        'r': float(mejor['r']),
        'p_valor': p,
        'n': int(mejor['n']),
        'significativo': p < ALFA_BONFERRONI,   # umbral CORREGIDO
        'sentido': 'positivo' if mejor['r'] > 0 else 'negativo',
        'tabla': tabla,
    }


def acoplamiento_completo(df):
    """
    La cadena que sustenta la tesis, mas los controles.
    El eslabon via paramo se mantiene para poder REPORTAR el hallazgo nulo
    con evidencia, no para esconderlo.
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
          f'pruebas): p < {ALFA_BONFERRONI:.4f}\n')

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
        print('    correlograma:')
        print(res['tabla'].to_string(index=False))
        print()