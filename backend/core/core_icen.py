# backend/core/core_icen.py
# ============================================================
# RECONSTRUCCION DEL ICEN — con filtro de cobertura y correccion de sesgo
#
# Este modulo existe porque la reconstruccion cruda daba +2.88 donde el
# IGP publicaba +1.98, casi una categoria entera de diferencia. Al
# desglosarlo resultaron ser TRES problemas apilados, y solo el tercero
# era real. Los tres estan resueltos aqui, y conviene entenderlos porque
# cada uno se puede volver a colar.
#
# ------------------------------------------------------------
# PROBLEMA 1 — SE COMPARABAN MESES DISTINTOS
#
# El IGP publica con retraso. Su serie terminaba en mayo-2026 mientras
# la reconstruccion ya tenia junio. Comparar junio contra mayo en pleno
# calentamiento no mide el error del metodo: mide el retraso editorial
# del IGP.
#
#   mismo mes (mayo-2026):  IGP +1.98  |  Pulso +2.17  -> dif +0.19
#   meses distintos:        IGP +1.98  |  Pulso +2.88  -> dif +0.90
#
# Dos tercios de la "discrepancia" eran un artefacto de la comparacion.
# Por eso comparar_con_oficial() SOLO usa el solape real de ambas series.
#
# ------------------------------------------------------------
# PROBLEMA 2 — UN MES INCOMPLETO ENVENENABA LA MEDIA MOVIL
#
# El ICEN es una media de tres meses. El ICEN CENTRADO de junio incluye
# julio; y julio, al calcularse a mitad de mes, tenia 10 dias de dato.
# Su anomalia parcial (+3.77) era la mas alta de toda la serie de 44
# años, y arrastraba la media hacia arriba.
#
#   centrado  junio = media(may, jun, jul) = 2.875   <- julio con 10 dias
#   operativo junio = media(abr, may, jun) = 2.168   <- meses completos
#
# La causa de raiz es sutil: rolling(3, min_periods=3) cuenta valores NO
# NULOS, no cobertura. Un mes con 10 dias entra con el mismo peso que uno
# con 31. La solucion no es bajar min_periods sino ANULAR la anomalia de
# los meses mal cubiertos ANTES de la media movil, para que el rolling
# los vea como lo que son: ausencia de dato.
#
# ------------------------------------------------------------
# PROBLEMA 3 — SESGO POR USAR OTRO PRODUCTO DE TSM (Y OTRA CLIMATOLOGIA)
#
# Este si es real, y no es ruido. Tiene DOS causas superpuestas, y es
# importante no atribuirselo todo a una sola:
#
#   (a) El producto de datos.
#       ICEN oficial -> ERSST v5   (reconstruccion in-situ, desde 1854)
#       Pulso        -> OISST v2.1 (satelital, desde 1982)
#       Tienen tendencias distintas en Niño 1+2.
#
#   (b) La climatologia de referencia.
#       Nosotros usamos una sola, 1991-2020. El ENFEN NO: segun la Nota
#       Tecnica ENFEN 01-2024 el ICEN historico se calcula con una
#       climatologia distinta cada 5 años (1976-2005 para el quinquenio
#       1991-1995, 1981-2010 para 1996-2000, etc.), y 1991-2020 solo rige
#       de 2006 en adelante. Es decir: cuanto mas atras vamos, mas
#       diferimos tambien en la referencia, no solo en el producto.
#
# El sesgo observado DERIVA con el tiempo y hasta cambia de signo:
#
#   1980s  -0.35  |  1990s  -0.21  |  2000s  +0.09
#   2010s  +0.03  |  2020s  +0.18
#
# Son unos +0.014 C por año, +0.61 acumulados en 44 años. NO esta separado
# cuanto de esa deriva viene de (a) y cuanto de (b); ambas empujan en el
# mismo sentido temporal. Lo que si es seguro es la consecuencia practica:
# un sesgo que deriva no se arregla con una constante escrita a mano, hay
# que recalcularlo contra la serie oficial cada vez que el IGP publique.
#
# POR QUE IMPORTA TANTO: el umbral de FUERTE esta en +2.1. En mayo-2026
# la reconstruccion cruda daba 2.17 (FUERTE) y el IGP 1.98 (MODERADA).
# El sesgo de +0.18 era EXACTAMENTE lo que cruzaba el umbral. Sin
# corregir, el sistema anuncia una categoria de mas.
#
# ------------------------------------------------------------
# VALIDACION FUERA DE MUESTRA (ajuste 1982-2022, prueba 2023-2026)
#
# El acierto de categoria se mide comparando la categoria completa que
# devuelve config_icen.clasificar() —condicion Y magnitud, ramas fria,
# neutra y calida— para la reconstruccion y para el ICEN oficial.
#
# ATENCION: las cifras de EAM y de acierto deben releerse de la salida de
# informe() cada vez que se cambie la tabla o el metodo de correccion. No
# se citan aqui para no dejar numeros congelados que envejezcan mal.
#
# La correccion lineal rinde algo mejor que el offset, pero EXTRAPOLA una
# tendencia fuera del rango de ajuste y eso envejece mal: dentro de cinco
# años estaria restando un numero que nadie verifico. El offset sobre la
# ventana reciente rinde casi igual, no extrapola nada y se recalcula
# solo. Es el que va por defecto.
#
# ------------------------------------------------------------
# COMO PRESENTAR ESTO
#
# La reconstruccion NO compite con el ICEN oficial: lo ANTICIPA. El IGP
# publica con uno o dos meses de retraso; nosotros tenemos el mes en
# curso. La pregunta correcta no es "¿coincide con el ICEN?" sino
# "¿predice el ICEN que el IGP publicara?". Con r=0.97 sobre 532 meses,
# esa respuesta se sostiene — y convierte el desfase en la contribucion,
# no en el error.
# ============================================================

import os

import numpy as np
import pandas as pd

try:
    from config import config_icen as icen
except ImportError:                      # ejecucion suelta del modulo
    import config_icen as icen


# ------------------------------------------------------------
# CONSTANTES
# ------------------------------------------------------------

CLIMATOLOGIA_INICIO = 1991
CLIMATOLOGIA_FIN = 2020

# Dias minimos de OISST para que un mes cuente como observado.
#
# 25 no es arbitrario: los meses cortos tienen 28, asi que 25 tolera
# hasta tres dias sueltos perdidos pero rechaza un mes a medio construir.
# El caso que motivo esto tenia 10.
DIAS_MINIMOS_MES = 25

# Ventana sobre la que se estima el sesgo, en años hacia atras desde el
# ultimo dato oficial. Diez años es un compromiso: suficiente para
# promediar el ruido (unos 120 meses), corto para no arrastrar el sesgo
# de decadas cuyo signo ya no aplica.
VENTANA_SESGO_ANIOS = 10

# Bajo este numero de meses solapados no estimamos nada: devolvemos 0.0 y
# lo declaramos. Preferimos un valor sin corregir y avisado a uno
# corregido con una muestra que no lo sostiene.
MINIMO_MESES_SESGO = 24


# ------------------------------------------------------------
# 1. RECONSTRUCCION
# ------------------------------------------------------------

def _anomalia_mensual(df):
    """
    Anomalia de TSM en Niño 1+2 contra la climatologia 1991-2020.

    Anula los meses con cobertura diaria insuficiente. Ese paso es el que
    impide que un mes a medias contamine la media movil de tres meses.
    """
    base = df.loc[str(CLIMATOLOGIA_INICIO):str(CLIMATOLOGIA_FIN)]
    clim = base.groupby(base.index.month)['sst_nino12'].mean()
    anom = df['sst_nino12'] - df.index.month.map(clim)

    if 'n_dias_sst' in df.columns:
        insuficiente = df['n_dias_sst'] < DIAS_MINIMOS_MES
        # NaN, no el valor parcial. Asi rolling(min_periods=3) lo trata
        # como el hueco que es, en vez de promediarlo como si fuera un
        # mes entero.
        anom = anom.where(~insuficiente, np.nan)

    return anom


def construir_icen(csv_sst):
    """
    Serie mensual del ICEN reconstruido a partir de OISST.

    Devuelve un DataFrame indexado por fecha con:
        anomalia        anomalia mensual (NaN si el mes esta mal cubierto)
        icen            media movil CENTRADA de 3 meses. Es la definicion
                        oficial, pero NO existe en tiempo real: para
                        conocer el valor de junio hace falta julio entero.
        icen_operativo  media movil RETRASADA de 3 meses. Es lo unico
                        disponible en vivo, y por eso es el que la app
                        debe mostrar como estado actual.
        mes_completo    si el mes tiene cobertura diaria suficiente
        categoria       magnitud segun la tabla ENFEN 2024
    """
    df = pd.read_csv(csv_sst)
    df['fecha'] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    df = df.sort_values('fecha').set_index('fecha')
    df['sst_nino12'] = pd.to_numeric(df['sst_nino12'], errors='coerce')

    df['anomalia'] = _anomalia_mensual(df)
    df['mes_completo'] = (
        df['n_dias_sst'] >= DIAS_MINIMOS_MES
        if 'n_dias_sst' in df.columns
        else df['anomalia'].notna()
    )

    df['icen'] = df['anomalia'].rolling(3, center=True, min_periods=3).mean()
    df['icen_operativo'] = df['anomalia'].rolling(3, min_periods=3).mean()
    df['categoria'] = df['icen'].map(lambda v: icen.clasificar(v)[1])

    return df


# ------------------------------------------------------------
# 2. SERIE OFICIAL
# ------------------------------------------------------------

def leer_oficial(ruta):
    """
    Lee ICEN.txt del IGP: lineas 'anio mes valor', comentarios con '%'.

    Devuelve DataFrame indexado por fecha con la columna 'icen_igp', o
    None si el archivo no existe. Que falte no es un error fatal: sin el
    la reconstruccion sigue siendo utilizable, solo que sin corregir.
    """
    if not os.path.exists(ruta):
        return None

    filas = []
    with open(ruta, encoding='utf-8', errors='replace') as f:
        for linea in f:
            if linea.lstrip().startswith('%'):
                continue
            partes = linea.split()
            if len(partes) != 3:
                continue
            try:
                filas.append((int(partes[0]), int(partes[1]), float(partes[2])))
            except ValueError:
                continue

    if not filas:
        return None

    d = pd.DataFrame(filas, columns=['anio', 'mes', 'icen_igp'])
    d['fecha'] = pd.to_datetime(dict(year=d.anio, month=d.mes, day=1))
    return d.set_index('fecha').sort_index()[['icen_igp']]


# ------------------------------------------------------------
# 3. SESGO
# ------------------------------------------------------------

def estimar_sesgo(recon, oficial, ventana_anios=VENTANA_SESGO_ANIOS):
    """
    Sesgo medio de la reconstruccion contra el ICEN oficial.

    Se estima SOLO sobre la ventana reciente, no sobre las cuatro decadas,
    porque el sesgo deriva y cambia de signo: promediar 1982-2026 daria
    -0.06 (casi nada) y ocultaria el +0.18 que aplica hoy. Un sesgo que
    cambia con el tiempo no se resume en un numero global.

    Devuelve un dict con el offset y su incertidumbre; el offset es 0.0 si
    no hay muestra suficiente, y 'suficiente' lo dice el propio dict.
    """
    vacio = {
        'offset': 0.0, 'n': 0, 'sd': None, 'ic95': None,
        'desde': None, 'hasta': None, 'suficiente': False,
    }
    if oficial is None:
        return vacio

    m = recon[['icen']].join(oficial, how='inner').dropna()
    if m.empty:
        return vacio

    corte = m.index.max() - pd.DateOffset(years=ventana_anios)
    v = m.loc[m.index >= corte]
    if len(v) < MINIMO_MESES_SESGO:
        return vacio

    dif = v['icen'] - v['icen_igp']
    sd = float(dif.std())
    return {
        'offset': float(dif.mean()),
        'n': int(len(v)),
        'sd': sd,
        'ic95': float(1.96 * sd / np.sqrt(len(v))),
        'desde': v.index.min().strftime('%Y-%m'),
        'hasta': v.index.max().strftime('%Y-%m'),
        'suficiente': True,
    }


def aplicar_correccion(recon, sesgo):
    """
    Añade icen_corregido e icen_operativo_corregido.

    La correccion es una resta simple, pero tiene una consecuencia que hay
    que decir en voz alta: a partir de aqui la reconstruccion YA NO es
    independiente del IGP. Es un proxy CALIBRADO contra la serie oficial.
    Sigue siendo util —anticipa el valor uno o dos meses— pero no puede
    presentarse como una medicion independiente que "confirma" al IGP.
    """
    d = recon.copy()
    off = sesgo['offset']
    d['icen_corregido'] = d['icen'] - off
    d['icen_operativo_corregido'] = d['icen_operativo'] - off
    d['categoria_corregida'] = d['icen_corregido'].map(
        lambda v: icen.clasificar(v)[1])
    return d


# ------------------------------------------------------------
# 4. COMPARACION Y VALIDACION
# ------------------------------------------------------------

def comparar_con_oficial(recon, oficial):
    """
    Compara mes contra mes SOLO en el solape real de ambas series.

    El how='inner' es el corazon del arreglo del problema 1: hace
    imposible comparar el junio de uno contra el mayo del otro.
    """
    if oficial is None:
        return None
    m = recon[['icen']].join(oficial, how='inner').dropna()
    if m.empty:
        return None
    m['dif'] = m['icen'] - m['icen_igp']
    return m


def validar(recon, oficial, anio_corte=2023):
    """
    Validacion FUERA DE MUESTRA: estima el sesgo con datos anteriores al
    corte y mide el acierto despues.

    Validar con los mismos datos que se usaron para estimar el sesgo daria
    un numero bonito y sin valor. Este si se puede defender ante un jurado.

    El acierto de categoria compara la categoria COMPLETA (condicion y
    magnitud) que devuelve config_icen.clasificar(). Una version anterior
    usaba np.digitize sobre los cuatro umbrales calidos, lo que metia en
    un mismo cajon todos los meses neutros y todos los frios: dos meses de
    La Niña de magnitudes distintas contaban como acierto. Eso inflaba el
    porcentaje.
    """
    m = comparar_con_oficial(recon, oficial)
    if m is None or m.empty:
        return None

    entrena = m[m.index.year < anio_corte]
    prueba = m[m.index.year >= anio_corte]
    if len(entrena) < MINIMO_MESES_SESGO or prueba.empty:
        return None

    corte_v = entrena.index.max() - pd.DateOffset(years=VENTANA_SESGO_ANIOS)
    off = float((entrena.loc[entrena.index >= corte_v, 'dif']).mean())

    cat_oficial = [icen.clasificar(x) for x in prueba['icen_igp']]

    def medir(pred):
        err = pred - prueba['icen_igp']
        cat_pred = [icen.clasificar(x) for x in pred]
        acierto = float(np.mean(
            [a == b for a, b in zip(cat_pred, cat_oficial)]))
        return {'sesgo': float(err.mean()),
                'eam': float(err.abs().mean()),
                'acierto_categoria': acierto}

    return {
        'n_entrenamiento': int(len(entrena)),
        'n_prueba': int(len(prueba)),
        'anio_corte': anio_corte,
        'offset_estimado': off,
        'sin_correccion': medir(prueba['icen']),
        'con_correccion': medir(prueba['icen'] - off),
        'r': float(np.corrcoef(m['icen'], m['icen_igp'])[0, 1]),
        'n_total': int(len(m)),
    }


# ------------------------------------------------------------
# 5. ESTADO ACTUAL — lo que consume la app
# ------------------------------------------------------------

def _umbral_mas_cercano(valor):
    """
    Umbral de categoria mas proximo al valor, MIRANDO EN AMBAS DIRECCIONES.

    Esto no es un detalle. Un valor de +2.01 esta a 0.71 del umbral de
    MODERADA por abajo, pero a solo 0.09 del de FUERTE por arriba. Medir
    unicamente la distancia al limite inferior lo declararia comodamente
    dentro de su categoria cuando en realidad esta al borde de la
    siguiente. Con una incertidumbre de +-0.15, ese valor podria ser
    perfectamente FUERTE.

    La pertenencia se delega en icen.dentro() en vez de escribirla a mano:
    el ENFEN no usa la misma convencion de bordes en la rama fria y en la
    calida, y duplicar la comparacion aqui reintroducia el error.

    Devuelve (umbral, distancia, categoria_vecina).
    """
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None, None, None

    mejor = (None, None, None)
    for inferior, superior, cerr_ab, cerr_ar, _, _ in icen.TABLA_ICEN:
        if not icen.dentro(v, inferior, superior, cerr_ab, cerr_ar):
            continue
        candidatos = []
        if np.isfinite(inferior):
            candidatos.append((abs(v - inferior), inferior))
        if np.isfinite(superior):
            candidatos.append((abs(superior - v), superior))
        if not candidatos:
            return None, None, None
        distancia, umbral = min(candidatos)
        # La categoria del otro lado: a que se convertiria si cruzase.
        epsilon = 1e-9
        otro = umbral - epsilon if umbral <= v else umbral + epsilon
        mejor = (umbral, distancia, icen.clasificar(otro)[1])
        break
    return mejor


def estado_actual(recon, oficial, sesgo):
    """
    Resumen honesto del episodio en curso.

    Reglas que este dict hace cumplir, y que la version anterior violaba:

      1. El valor en vivo es el OPERATIVO (media retrasada), no el
         centrado. El centrado de junio necesita julio entero: publicarlo
         a mitad de julio es publicar un numero que aun no existe.
      2. Solo meses con cobertura completa.
      3. Se reporta el valor corregido Y el crudo, nunca solo uno.
      4. Si la distancia al umbral es menor que la incertidumbre, la
         categoria se declara INDISTINGUIBLE en vez de afirmarse.
    """
    completos = recon[recon['mes_completo'] & recon['icen_operativo'].notna()]
    if completos.empty:
        return None

    fila = completos.iloc[-1]
    crudo = float(fila['icen_operativo'])
    corregido = crudo - sesgo['offset']

    _, magnitud = icen.clasificar(corregido)

    # Incertidumbre: la dispersion mes a mes del sesgo, no el error de su
    # media. Lo que importa no es "cuan bien conozco el sesgo medio" sino
    # "cuanto puede desviarse ESTE mes".
    incert = sesgo['sd'] if sesgo['suficiente'] else None
    umbral, margen, vecina = _umbral_mas_cercano(corregido)
    ambigua = bool(incert is not None and margen is not None
                   and margen < incert)

    ult_oficial = None
    if oficial is not None and not oficial.empty:
        f = oficial.index.max()
        ult_oficial = {
            'mes': f.strftime('%Y-%m'),
            'valor': float(oficial.loc[f, 'icen_igp']),
            'meses_de_retraso': int(
                (fila.name.year - f.year) * 12 + (fila.name.month - f.month)),
        }

    return {
        'mes': fila.name.strftime('%Y-%m'),
        'icen_crudo': round(crudo, 2),
        'icen_corregido': round(corregido, 2),
        'offset_aplicado': round(sesgo['offset'], 3),
        'categoria': magnitud,
        'etiqueta': icen.etiqueta(corregido),
        'categoria_ambigua': ambigua,
        'categoria_vecina': vecina,
        'margen_al_umbral': round(margen, 2) if margen is not None else None,
        'incertidumbre': round(incert, 2) if incert is not None else None,
        'umbral_mas_cercano': umbral,
        'oficial_mas_reciente': ult_oficial,
        'nota': (
            'Valor operativo (media movil retrasada de 3 meses) corregido '
            'por el sesgo OISST-ERSST estimado sobre los ultimos '
            f'{sesgo["n"]} meses. Es una estimacion anticipada del ICEN '
            'que publicara el IGP, no una medicion independiente.'
        ) if sesgo['suficiente'] else (
            'Valor operativo SIN corregir: no hay solape suficiente con la '
            'serie oficial para estimar el sesgo. Puede sobrestimar.'
        ),
    }


# ------------------------------------------------------------
# 6. INFORME
# ------------------------------------------------------------

def informe(csv_sst, txt_oficial):
    recon = construir_icen(csv_sst)
    oficial = leer_oficial(txt_oficial)
    sesgo = estimar_sesgo(recon, oficial)
    recon = aplicar_correccion(recon, sesgo)

    print('=' * 64)
    print('ICEN RECONSTRUIDO — DIAGNOSTICO')
    print('=' * 64)

    # Un mes con 0 dias es un mes futuro, una fila vacia del calendario.
    # Uno con 1-24 dias es un mes EN CURSO, y ese es el peligroso: tiene
    # un valor que parece dato pero no lo es.
    if 'n_dias_sst' in recon.columns:
        parciales = recon[(recon['n_dias_sst'] > 0) & ~recon['mes_completo']]
        print(f'\nMeses parciales descartados (<{DIAS_MINIMOS_MES} dias): '
              f'{len(parciales)}')
        for f, fila in parciales.tail(3).iterrows():
            print(f'   {f:%Y-%m}  ({int(fila["n_dias_sst"])} dias)  '
                  f'-> excluido de la media movil')

    # Sin solape suficiente, sesgo['sd'] es None: hay que decirlo, no
    # intentar formatearlo.
    if sesgo['suficiente']:
        print(f'\nSESGO (ventana {sesgo["desde"]} a {sesgo["hasta"]}, '
              f'n={sesgo["n"]})')
        print(f'   offset {sesgo["offset"]:+.3f}   sd {sesgo["sd"]:.3f}')
    else:
        print('\nSESGO: no estimado. No hay solape suficiente con la serie '
              f'oficial (minimo {MINIMO_MESES_SESGO} meses). Se usa 0.000.')

    v = validar(recon, oficial)
    if v:
        print(f'\nVALIDACION FUERA DE MUESTRA (corte {v["anio_corte"]})')
        print(f'   r = {v["r"]:.4f} sobre {v["n_total"]} meses')
        print(f'   entrenamiento {v["n_entrenamiento"]} meses, '
              f'prueba {v["n_prueba"]} meses')
        for nom, k in [('sin corregir', 'sin_correccion'),
                       ('corregido', 'con_correccion')]:
            r = v[k]
            print(f'   {nom:<14} EAM {r["eam"]:.3f}   '
                  f'categoria correcta {100 * r["acierto_categoria"]:.0f}%')

    e = estado_actual(recon, oficial, sesgo)
    if e:
        print(f'\nESTADO ACTUAL — {e["mes"]}')
        print(f'   crudo {e["icen_crudo"]:+.2f}  ->  '
              f'corregido {e["icen_corregido"]:+.2f}')
        print(f'   {e["etiqueta"]}')
        if e['categoria_ambigua']:
            print(f'   AMBIGUA: a {e["margen_al_umbral"]:.2f} del umbral '
                  f'{e["umbral_mas_cercano"]:+.1f} ({e["categoria_vecina"]}), '
                  f'con incertidumbre +-{e["incertidumbre"]:.2f}.')
            print('   No se puede distinguir entre las dos categorias.')
        if e['oficial_mas_reciente']:
            o = e['oficial_mas_reciente']
            n = o['meses_de_retraso']
            print(f'   IGP va por {o["mes"]} ({o["valor"]:+.2f}): '
                  f'{n} {"mes" if n == 1 else "meses"} de retraso')
    print()
    return recon, sesgo, v, e


if __name__ == '__main__':
    informe(os.path.join('data', 'datos', 'serie_sst.csv'),
            os.path.join('data', 'salidas', 'icen_oficial.txt'))