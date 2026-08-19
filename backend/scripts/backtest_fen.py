# backtest_fen.py   (v3)
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/backtest_fen.py
#
#   Requiere que backend/ este en el PYTHONPATH para resolver
#   'config' y 'core'. En PowerShell:
#       $env:PYTHONPATH="<ruta>\backend"
#
# Reconstruye el INDICE COSTERO EL NIÑO (ICEN) con el pipeline de Pulso y
# lo valida contra los eventos historicos de Piura.
#
# ------------------------------------------------------------
# QUE SE CORRIGIO RESPECTO A LA v1 (y por que importa):
#
# La v1 reportaba 482 dias de anticipacion para 2017. ERA FALSO.
# Buscaba la PRIMERA racha de alerta en una ventana de 18 meses, y
# enganchaba el Niño de 2015-16 -- un evento DISTINTO que no causo el
# desastre. Implicaba que el sistema llevaba mas de un año en alerta.
#
# La v2 exige que la racha de alerta este VIGENTE en el momento del
# desastre (o haya cerrado como mucho 2 meses antes). Si la alerta
# pertenece a otro evento, no cuenta.
#
# Un numero espectacular pero falso destruye un proyecto. Uno modesto
# y verdadero lo sostiene.
#
# ------------------------------------------------------------
# QUE SE CORRIGIO EN LA v3: EL UMBRAL DE DETECCION
#
# Este script detectaba eventos con ICEN > +0.4 C y lo rotulaba como
# "metodologia ENFEN 2012". Ese rotulo ya no vale:
#
#   - La Nota Tecnica ENFEN 01-2024 (diciembre 2024) reemplaza a la de
#     abril de 2012. En la tabla vigente, las condiciones CALIDAS empiezan
#     por encima de +0.5, no de +0.4. La banda neutra llega hasta +0.5.
#   - El archivo ademas MEZCLABA tablas: usaba config_icen (2024) para las
#     magnitudes y el umbral de 2012 para detectar los eventos.
#
# DECISION: el valor +0.4 SE MANTIENE, pero deja de presentarse como
# criterio del ENFEN. Es el UMBRAL OPERATIVO DE PULSO, deliberadamente mas
# bajo que el oficial.
#
# El motivo no es cosmetico y conviene poder defenderlo: el ICEN es un
# indice de DIAGNOSTICO —sirve para declarar oficialmente que hubo un Niño
# costero— mientras que Pulso es un sistema de ALERTA. Un sistema de
# alerta dispara antes y acepta mas falsas alarmas a cambio de no llegar
# tarde. Bajar el umbral es esa eleccion, hecha a proposito y declarada.
#
# Lo que NO se puede decir es "asi lo define el ENFEN". No lo define asi.
#
# NOTA para quien retome esto: subir el umbral a +0.5 alinearia el script
# con la tabla vigente, pero cambiaria que rachas se detectan y con ello
# los conteos, la anticipacion y el CSV de salida. No se hizo porque
# obligaria a revalidar todas las cifras publicadas.
#
# ------------------------------------------------------------
# METODOLOGIA
#   ICEN = media movil de 3 meses de la anomalia mensual de TSM
#          en la region Niño 1+2 (90W-80W, 10S-0)
#   Criterio ENFEN vigente : condiciones calidas (ICEN > +0.5) durante
#                            >= 3 meses consecutivos
#   Criterio operativo Pulso: ICEN > +0.4 durante >= 3 meses consecutivos
#
# HONESTIDAD METODOLOGICA:
#   ENFEN usa ERSSTv5 con climatologias escalonadas cada 5 años.
#   Nosotros usamos OISST v2.1 con una sola climatologia 1991-2020.
#   Esto es una RECONSTRUCCION, no una replica del indice oficial.
#
# ------------------------------------------------------------
# ESTE SCRIPT Y core_alerta.py NO CUENTAN LO MISMO
#
# Los dos detectan episodios, pero con detectores distintos, asi que sus
# numeros NO tienen por que coincidir y no es un error que difieran:
#
#   backtest_fen.py : ICEN MENSUAL (media movil de 3 meses).
#                     Menos episodios, mas largos.
#   core_alerta.py  : precursor DIARIO (media movil de 30 dias).
#                     Mas episodios, mas cortos, y detecta antes.
#
# Por eso la anticipacion de 2017 sale -5 dias aqui y +68 dias alli. Esa
# diferencia NO es una inconsistencia: es exactamente el argumento del
# proyecto. La regla mensual llega tarde; la cadencia diaria recupera
# semanas. Ambas cifras se muestran juntas en la web por ese motivo.
#
# Si se citan conteos de episodios o precisiones, hay que decir de cual de
# los dos detectores salen.
# ============================================================

import os

import numpy as np
import pandas as pd

from config import config_icen as icen
from core import core_impacto as impacto

# Anclado al archivo, no al directorio de trabajo. scripts/ vive dentro de
# backend/, asi que subimos un nivel. Con rutas relativas el script solo
# funcionaba si se lanzaba exactamente desde backend/, y fallaba en
# silencio (FileNotFoundError) desde cualquier otro sitio.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.path.join(CARPETA_BACKEND, 'data', 'datos')
CARPETA_SALIDA = os.path.join(CARPETA_BACKEND, 'data', 'salidas')
CSV_SST = os.path.join(CARPETA_DATOS, 'serie_sst.csv')

CLIMATOLOGIA_INICIO = 1991
CLIMATOLOGIA_FIN = 2020

# Dias minimos de OISST para que un mes cuente como observado.
#
# Mismo criterio que core_icen.py, y por la misma razon: sin esta guarda,
# un mes A MEDIO CONSTRUIR entra en la media movil de tres meses con el
# mismo peso que uno completo. En agosto de 2026, con 15 dias de dato,
# este script publicaba ICEN = +3.58 y magnitud EXTRAORDINARIA mientras
# core_icen.py —que si filtraba— reportaba julio y FUERTE. Dos modulos
# del mismo sistema contradiciendose sobre el mes en curso.
DIAS_MINIMOS_MES = 25

# Umbral OPERATIVO de Pulso, no el del ENFEN. Ver la nota de la v3 arriba.
# El ENFEN vigente situa el inicio de condiciones calidas en +0.5.
UMBRAL_EVENTO = 0.4
UMBRAL_ENFEN_CALIDO = 0.5   # solo para poder mostrar la diferencia

MESES_CONSECUTIVOS = 3
TOLERANCIA_CIERRE = 2      # meses que la alerta puede haber cerrado antes

# Las categorias del ICEN ya NO viven aqui.
#
# Estaban copiadas con la tabla ENFEN 2012 (3.0 / 1.7 / 1.0 / 0.4), que fue
# reemplazada por la Nota Tecnica ENFEN 01-2024. Con la tabla vieja, el
# episodio de 2023 se clasificaba como EXTRAORDINARIO cuando oficialmente
# fue FUERTE. Un umbral copiado en varios archivos es un umbral que
# envejece mal, y este envejecio.
#
# Ahora la tabla vive UNA sola vez, en config_icen.py, con su fuente y su
# autocomprobacion contra la serie oficial del IGP.

# Desastres documentados en Piura (fuente: SENAMHI/COEN/prensa).
#
# CORRECCION: faltaba el FEN 1982-83. Sin el, este script clasificaba el
# mega-Niño de 1983 -- uno de los peores desastres de la historia de Piura --
# como FALSA ALARMA, y reportaba una precision distinta a la de core_alerta.py.
# Un jurado piurano lo habria detectado al instante.
DESASTRES = {
    'FEN 1982-83': pd.Timestamp('1983-05-01'),
    'FEN 1997-98 (4,400 m3/s)': pd.Timestamp('1998-03-01'),
    'Niño costero 2017 (3,468 m3/s)': pd.Timestamp('2017-03-27'),
    'Ciclon Yaku 2023 (~1,700 m3/s)': pd.Timestamp('2023-03-15'),
}


def clasificar(valor):
    """
    Magnitud del ICEN segun la tabla vigente (ENFEN, 2024).

    Devuelve solo la MAGNITUD ('FUERTE', 'MODERADA', ...) porque es lo que
    consumen las tablas de este script. Si necesitas ademas la condicion
    (calida / fria / neutra), usa config_icen.clasificar() o .etiqueta().

    OJO: aqui se aplica al maximo del ICEN OPERATIVO (media retrasada). El
    ENFEN define las magnitudes sobre el ICEN centrado. Son cifras
    parecidas pero no identicas; la magnitud reportada por este script es
    la del valor que el sistema habria visto EN VIVO, que es justamente lo
    que interesa en un backtest de alerta.
    """
    if pd.isna(valor):
        return 'S/D'
    _, magnitud = icen.clasificar(valor)
    return magnitud


def construir_icen():
    df = pd.read_csv(CSV_SST)
    df['fecha'] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    df = df.sort_values('fecha').set_index('fecha')
    df['sst_nino12'] = pd.to_numeric(df['sst_nino12'], errors='coerce')

    base = df.loc[str(CLIMATOLOGIA_INICIO):str(CLIMATOLOGIA_FIN)]
    clim = base.groupby(base.index.month)['sst_nino12'].mean()
    df['anomalia'] = df['sst_nino12'] - df.index.month.map(clim)

    # Los meses mal cubiertos se anulan ANTES de la media movil. Poner NaN
    # (y no el valor parcial) hace que rolling(min_periods=3) los trate
    # como el hueco que son, en vez de promediarlos como si fueran un mes
    # entero. Ver la nota de DIAS_MINIMOS_MES.
    if 'n_dias_sst' in df.columns:
        incompletos = df['n_dias_sst'] < DIAS_MINIMOS_MES
        n_desc = int((incompletos & df['anomalia'].notna()).sum())
        if n_desc:
            ultimos = df.index[incompletos & df['anomalia'].notna()][-3:]
            print(f'[cobertura] {n_desc} mes(es) descartados por tener menos '
                  f'de {DIAS_MINIMOS_MES} dias de OISST.')
            for f in ultimos:
                print(f'            {f:%Y-%m} '
                      f'({int(df.loc[f, "n_dias_sst"])} dias)')
        df['anomalia'] = df['anomalia'].where(~incompletos, np.nan)

    # ICEN oficial: media movil CENTRADA -> no existe en tiempo real
    df['icen'] = df['anomalia'].rolling(3, center=True, min_periods=3).mean()

    # ICEN operativo: media movil RETRASADA -> lo unico usable en vivo
    df['icen_operativo'] = df['anomalia'].rolling(3, min_periods=3).mean()

    df['categoria'] = df['icen'].apply(clasificar)
    return df


def extraer_rachas(serie):
    """Devuelve todas las rachas de >= MESES_CONSECUTIVOS sobre el umbral."""
    sobre = (serie > UMBRAL_EVENTO).fillna(False)
    rachas, inicio = [], None

    for fecha, activo in sobre.items():
        if activo and inicio is None:
            inicio = fecha
        elif not activo and inicio is not None:
            tramo = serie.loc[inicio:fecha].iloc[:-1]
            if len(tramo) >= MESES_CONSECUTIVOS:
                rachas.append(tramo)
            inicio = None

    if inicio is not None:
        tramo = serie.loc[inicio:]
        if len(tramo) >= MESES_CONSECUTIVOS:
            rachas.append(tramo)

    return rachas


def anticipacion(df, fecha_desastre):
    """
    CORREGIDO: solo cuenta la racha de alerta VIGENTE en el desastre.

    Una alerta que pertenece a un evento anterior y ya cerrado NO se
    acredita como anticipacion. Ese era el error de la v1.
    """
    rachas = extraer_rachas(df['icen_operativo'])
    mes_desastre = fecha_desastre.to_period('M').to_timestamp()

    for tramo in rachas:
        inicio, fin = tramo.index[0], tramo.index[-1]
        cierre_tolerado = fin + pd.DateOffset(months=TOLERANCIA_CIERRE)

        # La alerta debe estar viva (o recien cerrada) cuando ocurre el desastre
        if inicio <= mes_desastre <= cierre_tolerado:
            confirmacion = tramo.index[MESES_CONSECUTIVOS - 1]
            # La alerta se emite al CIERRE de ese tercer mes
            emision = confirmacion + pd.DateOffset(months=1)
            dias = (fecha_desastre - emision).days
            return {
                'inicio_racha': inicio,
                'emision': emision,
                'dias': dias,
                'icen_max': tramo.max(),
                'magnitud': clasificar(tramo.max()),
                'valida': dias > 0,
            }

    return None


def clasificar_rachas(df):
    """
    Clasifica cada racha de alerta contra el registro OFICIAL del INDECI.

    ------------------------------------------------------------
    QUE SE CORRIGIO AQUI, Y POR QUE IMPORTA

    La version anterior comparaba cada racha contra un diccionario de
    cuatro fechas escrito a mano, y todo lo que no coincidia era "falsa
    alarma". Eso producia dos errores graves:

    1. EL EPISODIO EN CURSO SE CONTABA COMO FALLO. La racha de 2026 sigue
       abierta —la temporada de lluvias empieza en setiembre— y aparecia
       en la lista de falsas alarmas. Es decir, el sistema AFIRMABA que
       este año no va a pasar nada. No lo sabemos. core_alerta.py ya
       excluia los episodios abiertos; este script no lo hacia.

    2. 2015 SE CONTABA COMO FALLO. El registro SINPAD documenta 5,788
       damnificados en Piura en marzo de 2015. No fue una falsa alarma:
       fue un evento de MENOR magnitud. Llamarlo "no paso nada" era falso
       y, ante un jurado piurano, indefendible.

    Devuelve una lista de dicts, uno por racha, con su veredicto.
    """
    rachas = extraer_rachas(df['icen_operativo'])
    sinpad = impacto.cargar_sinpad()
    ultimo_dato = df['icen_operativo'].dropna().index[-1]

    dudosos = impacto.anios_dudosos(sinpad)

    salida = []
    for i, tramo in enumerate(rachas):
        inicio, fin = tramo.index[0], tramo.index[-1]
        # El margen de una racha no puede invadir la siguiente.
        tope = rachas[i + 1].index[0] if i + 1 < len(rachas) else None
        v, detalle = impacto.veredicto(sinpad, inicio, fin, ultimo_dato,
                                       tope=tope, dudosos=dudosos)

        # Antes de 2003 no hay SINPAD: 1983 y 1998 se resuelven con el
        # registro documental, que es lo unico que existe para esos años.
        if v == 'FUERA DE COBERTURA':
            limite = fin + pd.DateOffset(months=TOLERANCIA_CIERRE)
            doc = next((nombre for nombre, f in DESASTRES.items()
                        if inicio <= f.to_period('M').to_timestamp() <= limite),
                       None)
            if doc:
                v, detalle = 'DESASTRE MAYOR', {'documental': doc,
                                                'damni_pico_mes': None}
            else:
                v = 'SIN DAÑO REGISTRADO'

        salida.append({
            'inicio': inicio, 'fin': fin,
            'icen_max': tramo.max(),
            'magnitud': clasificar(tramo.max()),
            'veredicto': v,
            'detalle': detalle,
        })
    return salida


def falsas_alarmas(df):
    """Compatibilidad: (aciertos, falsas) SIN contar los episodios abiertos."""
    rachas = clasificar_rachas(df)
    evaluables = [r for r in rachas if impacto.evaluable(r['veredicto'])]
    aciertos = [r for r in evaluables if impacto.hubo_dano(r['veredicto'])]
    falsas = [r for r in evaluables if not impacto.hubo_dano(r['veredicto'])]
    return aciertos, falsas


def graficar(df):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('\n[AVISO] matplotlib no instalado. Sin graficos.')
        return

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # --- 1. Serie historica completa ---
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df.index, df['icen'], lw=1.0, color='#1f3a5f')
    ax.fill_between(df.index, UMBRAL_EVENTO, df['icen'],
                    where=df['icen'] > UMBRAL_EVENTO,
                    color='#e74c3c', alpha=0.55)
    ax.axhline(UMBRAL_EVENTO, ls='--', lw=1, color='#e67e22',
               label=f'Umbral operativo Pulso (+{UMBRAL_EVENTO} °C)')
    ax.axhline(UMBRAL_ENFEN_CALIDO, ls='-.', lw=1, color='#8e44ad',
               label=f'Inicio condiciones calidas ENFEN 2024 '
                     f'(+{UMBRAL_ENFEN_CALIDO} °C)')
    ax.axhline(icen.UMBRAL_FUERTE, ls=':', lw=1, color='#c0392b',
               label=f'FUERTE (+{icen.UMBRAL_FUERTE} °C)')
    ax.axhline(0, lw=0.6, color='gray')

    for nombre, fecha in DESASTRES.items():
        ax.axvline(fecha, color='black', lw=1.3, alpha=0.75)
        ax.annotate(nombre.split('(')[0].strip(),
                    (fecha, ax.get_ylim()[1]), rotation=90,
                    fontsize=7.5, va='top', ha='right')

    ax.set_title('Pulso — Reconstruccion del Indice Costero El Niño (ICEN)\n'
                 'Region Niño 1+2 | OISST v2.1 | Climatologia 1991-2020 | '
                 'Categorias: Nota Tecnica ENFEN 01-2024',
                 fontsize=11, loc='left')
    ax.set_ylabel('ICEN (°C)')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA_SALIDA, '1_icen_historico.png'), dpi=160)
    plt.close(fig)

    # --- 2. Backtest 2017 (el grafico clave) ---
    zoom = df.loc['2016-06':'2017-10']
    desastre = DESASTRES['Niño costero 2017 (3,468 m3/s)']
    res = anticipacion(df, desastre)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(zoom.index, zoom['icen_operativo'], marker='o', ms=4, lw=1.8,
            color='#1f3a5f', label='ICEN operativo (Pulso)')
    ax.axhline(UMBRAL_EVENTO, ls='--', color='#e67e22',
               label=f'Umbral operativo Pulso (+{UMBRAL_EVENTO} °C)')
    ax.axhline(0, lw=0.6, color='gray')
    ax.axvline(desastre, color='#c0392b', lw=2.2,
               label='Desborde río Piura\n27-mar-2017 · 3,468 m³/s')

    if res and res['valida']:
        ax.axvline(res['emision'], color='#27ae60', lw=2.2,
                   label=f'ALERTA Pulso\n{res["emision"]:%b-%Y}')
        y = zoom['icen_operativo'].max() * 1.15
        ax.annotate('', xy=(desastre, y), xytext=(res['emision'], y),
                    arrowprops=dict(arrowstyle='<->', color='#27ae60', lw=1.6))
        medio = res['emision'] + (desastre - res['emision']) / 2
        ax.text(medio, y * 1.06, f'{res["dias"]} días de anticipación',
                ha='center', color='#27ae60', fontweight='bold', fontsize=11)

    ax.set_title('BACKTEST — El Niño costero 2017\n'
                 'Anticipación real del sistema sobre un evento historico',
                 fontsize=11, loc='left')
    ax.set_ylabel('ICEN operativo (°C)')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA_SALIDA, '2_backtest_2017.png'), dpi=160)
    plt.close(fig)

    print(f'\nGraficos en {CARPETA_SALIDA}')
    print('  RECUERDA: si la web muestra alguno, copialo tambien a '
          'data/salidas/mapas/')


def main():
    df = construir_icen()
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    print('=== RECONSTRUCCION DEL ICEN ===')
    print(f'Region Niño 1+2 | climatologia {CLIMATOLOGIA_INICIO}-{CLIMATOLOGIA_FIN}')
    print('Fuente: OISST v2.1 (ENFEN usa ERSSTv5 -> es reconstruccion, '
          'no replica)')
    print(f'Categorias: Nota Tecnica ENFEN 01-2024')
    print(f'Deteccion de rachas: umbral OPERATIVO de Pulso +{UMBRAL_EVENTO} °C '
          f'durante >= {MESES_CONSECUTIVOS} meses.')
    print(f'  (El ENFEN situa el inicio de condiciones calidas en '
          f'+{UMBRAL_ENFEN_CALIDO} °C. Pulso usa un umbral mas bajo a')
    print('   proposito: es un sistema de ALERTA, no de diagnostico.)\n')

    print('=== BACKTEST: ANTICIPACION REAL ===')
    print('Solo cuenta la alerta VIGENTE en el desastre. Una alerta de un\n'
          'evento anterior ya cerrado NO se acredita.\n')

    for nombre, fecha in DESASTRES.items():
        print(f'--- {nombre}')
        print(f'    desastre: {fecha:%d-%b-%Y}')
        res = anticipacion(df, fecha)

        if res is None:
            print('    NO habria alertado.')
            print('    -> Limitacion reportada, no ocultada.\n')
            continue

        if not res['valida']:
            print(f'    Alerta emitida {abs(res["dias"])} dias DESPUES '
                  f'del desastre.')
            print('    -> El sistema llego tarde. Se reporta.\n')
            continue

        print(f'    Racha inicia   : {res["inicio_racha"]:%b-%Y}')
        print(f'    ALERTA emitida : {res["emision"]:%b-%Y}')
        print(f'    ANTICIPACION   : {res["dias"]} dias '
              f'(~{res["dias"] / 30:.1f} meses)')
        print(f'    Magnitud ICEN  : {res["icen_max"]:.2f} ({res["magnitud"]})\n')

    # --- Rachas de alerta contrastadas con el registro del INDECI ---
    rachas = clasificar_rachas(df)
    abiertas = [r for r in rachas if r['veredicto'] == 'EN CURSO']
    evaluables = [r for r in rachas if impacto.evaluable(r['veredicto'])]
    con_dano = [r for r in evaluables if impacto.hubo_dano(r['veredicto'])]
    sin_dano = [r for r in evaluables if not impacto.hubo_dano(r['veredicto'])]

    print('\n=== RACHAS DE ALERTA CONTRASTADAS CON SINPAD (1982-2026) ===')
    print(f'Rachas emitidas   : {len(rachas)}')
    print(f'  evaluables      : {len(evaluables)}')
    print(f'  EN CURSO        : {len(abiertas)}  (no clasificables: la '
          f'temporada de lluvias aun no concluye)')
    print(f'Con daño registrado : {len(con_dano)}')
    print(f'Sin daño registrado : {len(sin_dano)}')
    if evaluables:
        print(f'Precision           : '
              f'{100 * len(con_dano) / len(evaluables):.0f}%  '
              f'(solo sobre rachas evaluables)')

    print('\nLECTURA HONESTA: el ICEN detecta la ANOMALIA OCEANICA, no la')
    print('inundacion. La mayoria de episodios debiles no causa daño. Por eso')
    print('el sistema debe GRADUAR la alerta por magnitud, no ser binario.\n')

    print(f'{"PERIODO":<20}{"ICEN":>7} {"MAGNITUD":<16}'
          f'{"VEREDICTO":<22}{"DAMNIFICADOS":>13}')
    for r in rachas:
        d = r['detalle'] or {}
        pico = d.get('damni_pico_mes')
        if pico is None:
            cifra = 'documental' if d.get('documental') else '—'
        else:
            cifra = f'{int(pico):,}'
        periodo = f'{r["inicio"]:%Y-%m} a {r["fin"]:%Y-%m}'
        print(f'{periodo:<20}{r["icen_max"]:>7.2f} {r["magnitud"]:<16}'
              f'{r["veredicto"]:<22}{cifra:>13}')

    # --- ¿Depende la conclusion del corte que elegimos? ---
    sinpad = impacto.cargar_sinpad()
    if sinpad is not None:
        ultimo_dato = df['icen_operativo'].dropna().index[-1]
        ventanas = [(r['inicio'], r['fin']) for r in rachas]
        barrido = impacto.barrer_umbrales(sinpad, ventanas, ultimo_dato)
        print('\n--- SENSIBILIDAD AL CORTE DE "DESASTRE" ---')
        print('Si el reparto se mantiene estable al mover el corte, la')
        print('conclusion NO depende del numero que elegimos.\n')
        print(f'{"corte (damnif.)":>16}{"con daño":>10}{"sin daño":>10}')
        for _, f in barrido.iterrows():
            print(f'{int(f["corte"]):>16,}{int(f["con_dano"]):>10}'
                  f'{int(f["sin_dano"]):>10}')

    # --- Estado actual ---
    ultimo = df['icen_operativo'].dropna()
    if len(ultimo):
        fecha_ult, valor_ult = ultimo.index[-1], ultimo.iloc[-1]
        print(f'\n=== ESTADO ACTUAL ===')
        print(f'Ultimo dato: {fecha_ult:%b-%Y}   ICEN operativo = {valor_ult:+.2f}'
              f'   [{clasificar(valor_ult)}]')
        print('OJO: este valor es SIN corregir el sesgo OISST-ERSST. El valor '
              'que la app publica')
        print('sale de core_icen.py, que si aplica la correccion. Verificar '
              'contra el ICEN oficial')
        print('en met.igp.gob.pe/elnino/ antes de presentar.')

    df.to_csv(os.path.join(CARPETA_SALIDA, 'icen_reconstruido.csv'))
    graficar(df)


if __name__ == '__main__':
    main()