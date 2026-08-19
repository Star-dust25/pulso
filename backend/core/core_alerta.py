# core_alerta.py   (v3 - MOTOR DE DOS ETAPAS)
# ============================================================
# EL NUCLEO DE Pulso
#
#   python core_alerta.py
#
# ============================================================
# EL PROBLEMA
#
# El ICEN oficial exige 3 MESES consecutivos sobre umbral. Por esa regla,
# en 2017 la alerta se habria emitido el 1 de abril. El rio Piura se
# desbordo el 27 de marzo. CINCO DIAS TARDE.
#
# No es un defecto de nuestra implementacion: es una limitacion estructural
# del ICEN, que es un indice de DIAGNOSTICO (declara que hubo un Niño
# costero), no de ALERTA. El propio ENFEN lo reconocio y en 2015 creo un
# Sistema de Alerta separado, "para alertar mas oportunamente sin esperar
# el cumplimiento del criterio de los 3 meses".
#
# ============================================================
# EL HALLAZGO QUE SOSTIENE TODO EL PROYECTO
#
#   El Niño 2015-16 fue MAS FUERTE en el mar que el de 2017.
#   Y su peor mes de daño fue 12 VECES MENOR.
#
#   OJO: el episodio de 2015-16 abarca DOS temporadas de lluvias, y el
#   registro SINPAD las separa:
#
#     mar-2015   5,788 damnificados  -> ANTES de que la Etapa 1 alertara
#                                       (17-abr-2015). Queda fuera de la
#                                       ventana del episodio: es un evento
#                                       NO ANTICIPADO que la matriz no
#                                       contabiliza. Se declara aparte.
#     mar-2016   3,214 damnificados  -> dentro de la ventana. Es el valor
#                                       que usa la matriz de confusion.
#
#                    pico SST    z(MSAVI)   peor mes   veredicto SINPAD
#   2015-16          +2.51 C       1.37        5,788   DESASTRE MENOR
#   2017             +2.03 C       3.35       72,965   DESASTRE MAYOR
#
#   El oceano midio mal la magnitud. El territorio la midio bien.
#
# Un sistema basado solo en la anomalia oceanica habria gritado MAS FUERTE
# en 2015 (daño menor) que en 2017 (cuando el rio se llevo Piura).
#
#   EL MAR DICE "VIENE". EL BOSQUE SECO CONFIRMA "ESTA AQUI".
#
# OJO CON LA FORMULACION: NO decimos "en 2015 no paso nada". Si paso: el
# registro SINPAD del INDECI documenta miles de damnificados en Piura. Lo
# que cambia entre ambos años es la ESCALA del daño, y esa escala la
# anticipa el bosque seco, no el oceano. Afirmar "sin desastre" para 2015
# seria contradecir al registro oficial del Estado.
#
# ============================================================
# CORRECCIONES DE LA v3 (todas son honestidad, no cosmetica)
#
# 1. EPISODIO EN CURSO. El episodio de 2026 sigue abierto: la temporada de
#    lluvias empieza en setiembre. Clasificarlo como "falsa alarma" seria
#    AFIRMAR que no pasara nada, y eso no lo sabemos. Se excluye de la
#    matriz de confusion y se reporta aparte.
#
# 2. LA n REAL DE LA ETAPA 2. Landsat 8 arranca en 2013, asi que 1983 y
#    1998 NO tienen Etapa 2. Nuestro aporte original solo se probo sobre
#    DOS eventos: 2015 y 2017. Es n=2, no n=5. Lo decimos.
#
# 3. YAKU NO DIO ANTICIPACION EN ETAPA 2. Confirmo en abril; el desastre
#    fue el 15 de marzo. Confirmo DESPUES. Se reporta como tal.
#
# 4. EL VEREDICTO LO PONE EL INDECI, NO NOSOTROS. Ver core_impacto.py.
# ============================================================

import os

import numpy as np
import pandas as pd

from core import core_impacto as impacto

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'datos')
CARPETA_SALIDA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'salidas')
CSV_DIARIO = os.path.join(CARPETA_DATOS, 'serie_sst_diaria.csv')
CSV_VEG = os.path.join(CARPETA_DATOS, 'serie_vegetacion.csv')

CLIM_INICIO, CLIM_FIN = 1991, 2020

# --- ETAPA 1: precursor oceanico ---
VENTANA_PERSISTENCIA = 30      # dias de media movil
UMBRAL_PRECURSOR = 0.4         # C - parametro operativo de Pulso sobre la
                               # anomalia DIARIA. NO es el criterio del ICEN,
                               # que opera sobre la media movil mensual.
DIAS_CONFIRMACION = 15         # dias seguidos sobre umbral para emitir
UMBRAL_MAGNITUD = 2.0          # C - pico minimo para escalar a Etapa 2

# --- ETAPA 2: confirmacion territorial ---
UMBRAL_MSAVI = 1.5             # desviaciones estandar

ANIO_INICIO_MSAVI = 2013       # Landsat 8
DIAS_EN_CURSO = 30             # margen para considerar un episodio abierto

# Registro DOCUMENTAL, solo para lo que SINPAD no cubre (arranca en 2003).
# De 2003 en adelante el veredicto lo pone el registro oficial del INDECI,
# no esta lista. Ver core_impacto.py.
DESASTRES = {
    'FEN 1982-83': pd.Timestamp('1983-05-01'),
    'FEN 1997-98': pd.Timestamp('1998-03-01'),
    'Niño costero 2017': pd.Timestamp('2017-03-27'),
    'Ciclon Yaku 2023': pd.Timestamp('2023-03-15'),
}

TOLERANCIA_DIAS = 45


# ------------------------------------------------------------
# ETAPA 1
# ------------------------------------------------------------

def cargar_diario():
    df = pd.read_csv(CSV_DIARIO, parse_dates=['fecha'])
    return df.dropna(subset=['sst_nino12']).sort_values('fecha').set_index('fecha')


def anomalia_diaria(df):
    """Climatologia por dia del anio (1991-2020), suavizada 31 dias."""
    df = df.copy()
    df['doy'] = df.index.dayofyear

    base = df.loc[str(CLIM_INICIO):str(CLIM_FIN)]
    clim = base.groupby('doy')['sst_nino12'].mean()

    # Suavizado circular: se triplica la serie para que diciembre y enero
    # empalmen. Sin esto, la media movil de 31 dias se queda sin datos en
    # los extremos del anio y produce un escalon artificial el 1 de enero.
    triple = pd.concat([clim, clim, clim])
    suave = triple.rolling(31, center=True, min_periods=1).mean()
    clim_suave = suave.iloc[len(clim):2 * len(clim)]
    clim_suave.index = clim.index

    df['clim'] = df['doy'].map(clim_suave)
    df['anomalia'] = df['sst_nino12'] - df['clim']

    # Media movil RETRASADA -> disponible en tiempo real, sin mirar al futuro
    df['precursor'] = df['anomalia'].rolling(
        VENTANA_PERSISTENCIA, min_periods=VENTANA_PERSISTENCIA).mean()
    return df


def emitir_episodios(df):
    sobre = (df['precursor'] > UMBRAL_PRECURSOR).fillna(False)
    grupos = (~sobre).cumsum()
    racha = sobre.groupby(grupos).cumsum()

    df = df.copy()
    df['etapa1'] = racha >= DIAS_CONFIRMACION

    episodios, inicio = [], None
    for fecha, activo in df['etapa1'].items():
        if activo and inicio is None:
            inicio = fecha
        elif not activo and inicio is not None:
            episodios.append((inicio, fecha))
            inicio = None
    if inicio is not None:
        episodios.append((inicio, df.index[-1]))

    return df, episodios


# ------------------------------------------------------------
# ETAPA 2
# ------------------------------------------------------------

def serie_msavi():
    """
    z(MSAVI) del bosque seco, mes a mes.

    NOTA: la climatologia y la desviacion estandar se calculan sobre TODA
    la serie disponible, asi que anadir meses nuevos mueve ligeramente los
    z historicos. Es una climatologia movil, no un error, pero implica que
    las cifras citadas fuera del codigo deben releerse tras cada
    actualizacion de datos.
    """
    v = pd.read_csv(CSV_VEG)
    v['fecha'] = pd.to_datetime(dict(year=v.anio, month=v.mes, day=1))
    v = v.sort_values('fecha').set_index('fecha')
    v['msavi_montes'] = pd.to_numeric(v['msavi_montes'], errors='coerce')

    clim = v.groupby(v.index.month)['msavi_montes'].transform('mean')
    anomalia = v['msavi_montes'] - clim
    v['z_msavi'] = anomalia / anomalia.std()
    return v[['z_msavi', 'n_escenas']]


_CACHE_SINPAD = {}


def _sinpad():
    """Carga SINPAD una sola vez. Si falta el CSV, devuelve None y el
    sistema cae al registro documental sin romperse."""
    if 'df' not in _CACHE_SINPAD:
        _CACHE_SINPAD['df'] = impacto.cargar_sinpad()
    return _CACHE_SINPAD['df']


def evaluar_episodio(df, veg, inicio, fin, tope=None):
    pico = df.loc[inicio:fin, 'precursor'].max()

    ventana = veg.loc[inicio - pd.DateOffset(months=1):
                      fin + pd.DateOffset(months=2), 'z_msavi'].dropna()
    z = ventana.max() if len(ventana) else np.nan
    mes_z = ventana.idxmax() if len(ventana) else None

    tiene_etapa2 = inicio.year >= ANIO_INICIO_MSAVI and not np.isnan(z)

    if tiene_etapa2:
        alerta_roja = (pico >= UMBRAL_MAGNITUD) and (z >= UMBRAL_MSAVI)
    else:
        # Antes de Landsat 8 solo existe la Etapa 1.
        alerta_roja = pico >= UMBRAL_MAGNITUD

    # --- VEREDICTO: ya no lo ponemos nosotros ---
    #
    # Antes: 'desastre' salia de un diccionario de cuatro fechas escritas a
    # mano. Ahora sale del registro de emergencias del INDECI (SINPAD).
    # El cambio no es cosmetico: con el diccionario, 2015 figuraba como
    # "sin desastre" cuando el Estado si registra damnificados en Piura
    # durante ese episodio.
    sinpad = _sinpad()
    ultimo_dato = df.index[-1]
    # 'tope' = inicio del episodio siguiente. Sin el, el margen de dos
    # meses invade el episodio que viene detras y le roba su daño: el
    # episodio de sep-2016 (pico +0.61 C, oceano casi neutro) se acreditaba
    # los damnificados de enero de 2017, que son del Niño costero.
    veredicto, detalle = impacto.veredicto(sinpad, inicio, fin, ultimo_dato,
                                           tope=tope)

    # Antes de 2003 SINPAD no llega: se resuelve con el registro documental.
    if veredicto == 'FUERA DE COBERTURA':
        doc = next((n for n, f in DESASTRES.items()
                    if inicio <= f <= fin + pd.Timedelta(days=TOLERANCIA_DIAS)),
                   None)
        veredicto = 'DESASTRE MAYOR' if doc else 'SIN DAÑO REGISTRADO'
        detalle = {'documental': doc}

    nombre_doc = next((n for n, f in DESASTRES.items()
                       if inicio <= f <= fin + pd.Timedelta(days=TOLERANCIA_DIAS)),
                      None)
    # 'desastre' se conserva para no romper lo que ya lo consume, pero
    # ahora es DERIVADO del veredicto, no la fuente de verdad.
    desastre = nombre_doc if impacto.hubo_dano(veredicto) else None
    if impacto.hubo_dano(veredicto) and desastre is None:
        desastre = f'{veredicto.title()} ({inicio:%Y})'

    # --- CORRECCION CLAVE ---
    # Un episodio todavia abierto NO se puede clasificar. La temporada de
    # lluvias aun no ha ocurrido. Contarlo como falsa alarma seria afirmar
    # que no pasara nada, y eso no lo sabemos.
    ultimo_dato = df.index[-1]
    en_curso = fin >= ultimo_dato - pd.Timedelta(days=DIAS_EN_CURSO)

    return {
        'inicio': inicio, 'fin': fin, 'dias': (fin - inicio).days,
        'pico': pico, 'z_msavi': z, 'mes_z': mes_z,
        'alerta_roja': alerta_roja, 'desastre': desastre,
        'veredicto': veredicto,
        'damnificados': (detalle or {}).get('damni_pico_mes'),
        'evaluable': impacto.evaluable(veredicto),
        'tiene_etapa2': tiene_etapa2, 'en_curso': en_curso,
    }


# ------------------------------------------------------------
# GRAFICOS
# ------------------------------------------------------------

def graficar(df, veg):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print('\n[AVISO] matplotlib no instalado. Sin graficos.')
        return

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    AZUL, ROJO, NARANJA, GRIS = '#1f3a5f', '#c0392b', '#e67e22', '#95a5a6'

    # ===== LAMINA CENTRAL: 2015-16 vs 2017 =====
    # Ventanas IGUALADAS a 15 meses para que la comparacion sea justa.
    #
    # ATENCION: los picos y las cifras de damnificados de los rotulos estan
    # ESCRITOS A MANO. Si se regeneran las series hay que releerlos de la
    # salida de main() y actualizarlos aqui, o el grafico dira una cosa y
    # el terminal otra.
    fig, ejes = plt.subplots(2, 2, figsize=(15, 8), sharey='row')

    casos = [
        ('2015-02', '2016-05', 'EL NIÑO 2015-16 ("Godzilla")',
         'Mar MAS caliente: pico +2.51 °C  →  peor mes 5,788 damnificados',
         None, 'DAÑO MENOR'),
        ('2016-07', '2017-10', 'NIÑO COSTERO 2017',
         'Mar MENOS caliente: pico +2.03 °C  →  peor mes 72,965 damnificados',
         DESASTRES['Niño costero 2017'], 'EL BOSQUE CONFIRMA'),
    ]

    for col, (ini, fin, titulo, sub, desastre, veredicto) in enumerate(casos):
        # --- Panel superior: ETAPA 1 ---
        ax = ejes[0][col]
        z = df.loc[ini:fin]
        ax.plot(z.index, z['anomalia'], lw=0.6, color='#d5dbdb',
                label='Anomalia diaria' if col == 0 else None)
        ax.plot(z.index, z['precursor'], lw=2.6, color=AZUL,
                label='Precursor 30d' if col == 0 else None)
        ax.axhline(UMBRAL_PRECURSOR, ls='--', lw=1, color=NARANJA,
                   label=f'Umbral alerta (+{UMBRAL_PRECURSOR})' if col == 0 else None)
        ax.axhline(UMBRAL_MAGNITUD, ls=':', lw=1.3, color=ROJO,
                   label=f'Umbral magnitud (+{UMBRAL_MAGNITUD})' if col == 0 else None)
        ax.axhline(0, lw=0.6, color='gray')
        if desastre is not None:
            ax.axvline(desastre, color=ROJO, lw=2.6)
            ax.text(desastre, ax.get_ylim()[1] * 0.92, ' DESBORDE\n 27-mar',
                    color=ROJO, fontsize=8.5, fontweight='bold', va='top')
        ax.set_title(f'{titulo}\n{sub}', fontsize=11, loc='left',
                     fontweight='bold')
        if col == 0:
            ax.set_ylabel('ETAPA 1\nAnomalia SST (°C)', fontsize=10)
            ax.legend(fontsize=7.5, loc='upper left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
        ax.grid(alpha=0.2)

        # --- Panel inferior: ETAPA 2 ---
        ax = ejes[1][col]
        zv = veg.loc[ini:fin, 'z_msavi'].dropna()
        colores = [ROJO if x >= UMBRAL_MSAVI else GRIS for x in zv]
        ax.bar(zv.index, zv.values, width=22, color=colores)
        ax.axhline(UMBRAL_MSAVI, ls='--', lw=1.3, color=ROJO,
                   label=f'Umbral confirmacion (z={UMBRAL_MSAVI})'
                   if col == 0 else None)
        ax.axhline(0, lw=0.6, color='gray')
        if desastre is not None:
            ax.axvline(desastre, color=ROJO, lw=2.6)

        color_v = ROJO if desastre is not None else '#7f8c8d'
        ax.text(0.98, 0.94, veredicto, transform=ax.transAxes,
                ha='right', va='top', fontsize=11, fontweight='bold',
                color=color_v,
                bbox=dict(boxstyle='round,pad=0.4', fc='white',
                          ec=color_v, lw=1.2))

        if col == 0:
            ax.set_ylabel('ETAPA 2\nz(MSAVI) bosque seco', fontsize=10)
            ax.legend(fontsize=7.5, loc='lower left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
        ax.grid(alpha=0.2)

    fig.suptitle('POR QUE LA ANOMALIA OCEANICA NO BASTA\n'
                 'El mar grito mas fuerte en 2015 y su peor mes de daño fue '
                 '12 veces menor (registro SINPAD - INDECI).',
                 fontsize=13.5, fontweight='bold', x=0.01, ha='left')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(CARPETA_SALIDA, '5_dos_etapas_2015_vs_2017.png'),
                dpi=160)
    plt.close(fig)

    # ===== ESTADO ACTUAL =====
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    z = df.loc['2025-01':]

    ax1.plot(z.index, z['anomalia'], lw=0.6, color='#d5dbdb',
             label='Anomalia diaria')
    ax1.plot(z.index, z['precursor'], lw=2.4, color=AZUL, label='Precursor 30d')
    ax1.fill_between(z.index, UMBRAL_PRECURSOR, z['precursor'],
                     where=z['precursor'] > UMBRAL_PRECURSOR,
                     color=ROJO, alpha=0.25)
    ax1.axhline(UMBRAL_PRECURSOR, ls='--', color=NARANJA, label='Umbral alerta')
    ax1.axhline(UMBRAL_MAGNITUD, ls=':', color=ROJO, label='Umbral magnitud')
    ax1.axhline(0, lw=0.6, color='gray')
    ax1.set_ylabel('ETAPA 1 — SST (°C)')
    ax1.legend(fontsize=8, loc='upper left')
    ax1.grid(alpha=0.2)

    zv = veg.loc['2025-01':, 'z_msavi'].dropna()
    colores = [ROJO if x >= UMBRAL_MSAVI else GRIS for x in zv]
    ax2.bar(zv.index, zv.values, width=22, color=colores)
    ax2.axhline(UMBRAL_MSAVI, ls='--', color=ROJO, label='Umbral confirmacion')
    ax2.axhline(0, lw=0.6, color='gray')
    ax2.set_ylabel('ETAPA 2 — z(MSAVI)')
    ax2.legend(fontsize=8, loc='upper left')
    ax2.grid(alpha=0.2)

    ultimo = df.dropna(subset=['precursor']).iloc[-1]
    zs = veg['z_msavi'].dropna()
    z_act = zs.iloc[-1]
    mes_act = zs.index[-1]
    e1 = 'EN ALERTA' if ultimo['etapa1'] else 'vigilancia'
    e2 = 'CONFIRMA' if z_act >= UMBRAL_MSAVI else 'NO confirma'

    fig.suptitle(
        f'ESTADO ACTUAL — {ultimo.name:%d-%b-%Y}   [EPISODIO EN CURSO]\n'
        f'ETAPA 1: {e1} (precursor {ultimo["precursor"]:+.2f} °C)   |   '
        f'ETAPA 2: {e2} (z = {z_act:+.2f}, {mes_act:%b-%Y})',
        fontsize=12, fontweight='bold', x=0.01, ha='left')
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(os.path.join(CARPETA_SALIDA, '6_estado_actual.png'), dpi=160)
    plt.close(fig)

    print(f'\nGraficos: {CARPETA_SALIDA}/5_dos_etapas_2015_vs_2017.png')
    print(f'          {CARPETA_SALIDA}/6_estado_actual.png')
    print('  RECUERDA: si la web los muestra, copialos tambien a '
          'data/salidas/mapas/')


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    for ruta in (CSV_DIARIO, CSV_VEG):
        if not os.path.exists(ruta):
            raise SystemExit(f'Falta {ruta}')

    df = anomalia_diaria(cargar_diario())
    df, episodios = emitir_episodios(df)
    veg = serie_msavi()

    resultados = [
        evaluar_episodio(df, veg, a, b,
                         tope=episodios[i + 1][0] if i + 1 < len(episodios)
                         else None)
        for i, (a, b) in enumerate(episodios)
    ]

    # Los episodios abiertos NO se clasifican. Tampoco los que caen en un
    # año cuyo recurso SINPAD viene incompleto: un dato ausente no es un
    # cero. Reducir la n es el precio de no contaminarla.
    cerrados = [r for r in resultados if not r['en_curso'] and r['evaluable']]
    activos = [r for r in resultados if r['en_curso']]
    excluidos = [r for r in resultados
                 if not r['en_curso'] and not r['evaluable']]

    # ---------- 1. El hallazgo ----------
    print('=' * 68)
    print('Pulso — MOTOR DE ALERTA TEMPRANA DE DOS ETAPAS')
    print('=' * 68)
    print('\n### EL HALLAZGO: la anomalia oceanica sola NO BASTA\n')
    print(f'{"EVENTO":<22}{"pico SST":>10}{"z(MSAVI)":>10}{"DAMNIFICADOS":>14}'
          f'   VEREDICTO')
    for r in resultados:
        if r['inicio'].year in (2015, 2017):
            etq = ('Niño 2015-16' if r['inicio'].year == 2015
                   else 'Niño costero 2017')
            dam = ('—' if r['damnificados'] is None
                   else f'{int(r["damnificados"]):,}')
            print(f'{etq:<22}{r["pico"]:>+9.2f}C{r["z_msavi"]:>10.2f}'
                  f'{dam:>14}   {r["veredicto"]}')
    print()
    print('EL CONTRASTE ES DE MAGNITUD, NO DE OCURRENCIA.')
    print('En 2015 SI hubo daño: el registro SINPAD del INDECI documenta')
    print('miles de damnificados en Piura. Decir "no paso nada" era falso.')
    print('Lo que cambia entre los dos años es la ESCALA del daño, y esa')
    print('escala la anticipa el bosque seco, no el oceano:')
    print('  el mar grito MAS FUERTE en 2015 y el daño fue mucho MENOR.\n')

    # ---------- 2. Backtest ----------
    print('=' * 68)
    print('### BACKTEST: ANTICIPACION SOBRE EVENTOS REALES\n')
    for nombre, fecha in DESASTRES.items():
        r = next((x for x in resultados
                  if x['inicio'] <= fecha
                  <= x['fin'] + pd.Timedelta(days=TOLERANCIA_DIAS)), None)
        print(f'--- {nombre}   (desastre: {fecha:%d-%b-%Y})')
        if r is None:
            print('    NO alerta.\n')
            continue

        dias = (fecha - r['inicio']).days
        print(f'    ETAPA 1 alerta : {r["inicio"]:%d-%b-%Y}   '
              f'-> {dias:+d} dias')

        if not r['tiene_etapa2']:
            print('    ETAPA 2        : NO DISPONIBLE (Landsat 8 arranca en 2013)')
        else:
            d2 = (fecha - r['mes_z']).days
            estado = 'CONFIRMA' if r['z_msavi'] >= UMBRAL_MSAVI else 'no confirma'
            cola = (f'-> {d2:+d} dias (ANTES del desastre)' if d2 > 0
                    else f'-> {d2:+d} dias (DESPUES: sin anticipacion)')
            print(f'    ETAPA 2 {estado:<11}: {r["mes_z"]:%b-%Y}  '
                  f'z={r["z_msavi"]:+.2f}  {cola}')
        print()

    # ---------- 3. Matriz de confusion ----------
    print('=' * 68)
    print('### MATRIZ DE CONFUSION — solo episodios CERRADOS\n')
    print(f'Episodios totales : {len(resultados)}')
    print(f'  evaluables      : {len(cerrados)}')
    print(f'  EN CURSO        : {len(activos)}  (no clasificables aun)')
    print(f'  no evaluables   : {len(excluidos)}  (cobertura SINPAD dudosa)\n')

    tp1 = sum(1 for r in cerrados if r['desastre'])
    fp1 = len(cerrados) - tp1

    rojas = [r for r in cerrados if r['alerta_roja']]
    tp2 = sum(1 for r in rojas if r['desastre'])
    fp2 = len(rojas) - tp2
    fn2 = sum(1 for r in cerrados if r['desastre'] and not r['alerta_roja'])

    print(f'{"":<26}{"aciertos":>9}{"falsas":>8}{"perdidos":>10}{"precision":>11}')
    print(f'{"Solo ETAPA 1 (oceano)":<26}{tp1:>9}{fp1:>8}{0:>10}'
          f'{100 * tp1 / max(1, tp1 + fp1):>10.0f}%')
    print(f'{"ETAPA 1 + ETAPA 2":<26}{tp2:>9}{fp2:>8}{fn2:>10}'
          f'{100 * tp2 / max(1, tp2 + fp2):>10.0f}%')
    # La coletilla "sin perder eventos" era cierta cuando "desastre" lo
    # definiamos nosotros. Contra el registro del INDECI ya no lo es, y
    # dejarla puesta seria contradecir la limitacion 4 en la misma pantalla.
    if fn2:
        print(f'\nLa Etapa 2 rechazo {fp1 - fp2} falsas alarmas, pero perdio '
              f'{fn2} evento(s) con daño registrado.')
        print('Es el intercambio de todo umbral: subirlo compra precision y')
        print('paga con eventos no detectados. Se declara, no se esconde.')
    else:
        print(f'\nLa Etapa 2 rechazo {fp1 - fp2} falsas alarmas sin perder '
              f'eventos.')

    descartadas = sorted(
        [r for r in cerrados if not r['desastre']
         and r['pico'] >= UMBRAL_MAGNITUD and r['tiene_etapa2']],
        key=lambda r: -r['pico'])
    if descartadas:
        print('\n--- Falsas alarmas que la Etapa 2 rechazo ---')
        for r in descartadas:
            print(f'  {r["inicio"]:%Y-%m}  pico {r["pico"]:+.2f}C  '
                  f'z(MSAVI) {r["z_msavi"]:+.2f}  -> el agua nunca aterrizo')

    # ---------- 4. Honestidad ----------
    print('\n' + '=' * 68)
    print('### LIMITACIONES QUE DECLARAMOS NOSOTROS MISMOS\n')

    con_etapa2 = [r for r in cerrados if r['desastre'] and r['tiene_etapa2']]
    n_etapa2 = len(con_etapa2)
    anios = ', '.join(f'{r["inicio"]:%Y}' for r in con_etapa2) or 'ninguno'
    print(f'1. LA n REAL DE LA ETAPA 2 ES {n_etapa2}, NO {tp1}.')
    print('   Landsat 8 arranca en 2013: 1983 y 1998 no tienen Etapa 2, y el')
    print('   recurso SINPAD de 2023 esta incompleto, asi que Yaku tampoco')
    print('   entra en la matriz.')
    print(f'   Eventos con daño Y con Etapa 2 disponible: {anios}.')
    print('   Es una PRUEBA DE CONCEPTO, no una validacion estadistica.\n')

    print('2. HAY SOBREAJUSTE. Los umbrales (2.0 C, z=1.5) se eligieron')
    print('   observando estos mismos datos. Lo decimos antes de que')
    print('   nos lo pregunten.\n')

    zs_no = [r['z_msavi'] for r in cerrados
             if not r['desastre'] and r['tiene_etapa2']
             and not np.isnan(r['z_msavi'])]
    zs_si = [r['z_msavi'] for r in cerrados
             if r['desastre'] and r['tiene_etapa2']
             and not np.isnan(r['z_msavi'])]
    if zs_no and zs_si:
        print('3. EL MARGEN DEL UMBRAL z=1.5 ES ESTRECHO.')
        print(f'   z(MSAVI) maximo SIN daño registrado : {max(zs_no):.2f}')
        print(f'   z(MSAVI) minimo CON daño registrado : {min(zs_si):.2f}')
        if min(zs_si) <= max(zs_no):
            print('   -> HAY SOLAPE. Contra el registro oficial del INDECI, el')
            print('      umbral no distingue perfectamente. Lo declaramos.\n')
        else:
            print('   -> Sin solape, pero la separacion es de apenas '
                  f'{min(zs_si) - max(zs_no):.2f} desviaciones sobre n=2 '
                  'eventos.')
            print('      No es una frontera robusta: es lo que dan los datos.\n')

    perdidos = [r for r in cerrados if r['desastre'] and not r['alerta_roja']]
    if perdidos:
        print(f'4. LA ETAPA 2 PIERDE {len(perdidos)} EVENTO(S) CON DAÑO REAL:')
        for r in perdidos:
            dam = ('—' if r['damnificados'] is None
                   else f'{int(r["damnificados"]):,} damnificados')
            z_txt = ('sin dato Landsat' if np.isnan(r['z_msavi'])
                     else f'z(MSAVI) {r["z_msavi"]:+.2f}')
            print(f'   {r["inicio"]:%b-%Y}  pico {r["pico"]:+.2f} C  '
                  f'{z_txt}  ({dam})')
        print('   La precision del 100% se paga con eventos NO detectados.')
        print('   Un sistema de alerta debe declarar sus dos errores, no uno.')

    # ---------- 5. Estado actual ----------
    ultimo = df.dropna(subset=['precursor']).iloc[-1]
    zs = veg['z_msavi'].dropna()
    z_act, mes_act = zs.iloc[-1], zs.index[-1]

    print('\n' + '=' * 68)
    print(f'### ESTADO ACTUAL — {ultimo.name:%d-%b-%Y}\n')
    e1 = 'EN ALERTA' if ultimo['etapa1'] else 'vigilancia'
    e2 = 'CONFIRMA' if z_act >= UMBRAL_MSAVI else 'NO confirma'
    print(f'  ETAPA 1 (oceano)    : {e1:<11} precursor = {ultimo["precursor"]:+.2f} °C')
    print(f'  ETAPA 2 (territorio): {e2:<11} z(MSAVI)  = {z_act:+.2f} '
          f'({mes_act:%b-%Y})')

    if activos:
        a = activos[0]
        print(f'\n  Episodio activo desde {a["inicio"]:%d-%b-%Y} '
              f'({a["dias"]} dias). Pico {a["pico"]:+.2f} °C.')
        print('  NO se clasifica: la temporada de lluvias aun no ha ocurrido.')

    print()
    if ultimo['etapa1'] and z_act < UMBRAL_MSAVI:
        print('  DIAGNOSTICO: el precursor oceanico esta ACTIVO, pero el pulso')
        print('  hidrico AUN NO HA ATERRIZADO en el territorio.')
        print('  Consistente con ENFEN: la temporada de lluvias inicia en setiembre.')
    elif ultimo['etapa1']:
        print('  DIAGNOSTICO: ALERTA ROJA. Mar y territorio coinciden.')
    else:
        print('  DIAGNOSTICO: condiciones dentro de rango.')

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    df.to_csv(os.path.join(CARPETA_SALIDA, 'alerta_diaria.csv'))
    pd.DataFrame(resultados).to_csv(
        os.path.join(CARPETA_SALIDA, 'episodios_evaluados.csv'), index=False)

    graficar(df, veg)


if __name__ == '__main__':
    main()
