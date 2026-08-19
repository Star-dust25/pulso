# core_impacto.py
# ============================================================
# EL VEREDICTO DEJA DE SER NUESTRO
#
# ------------------------------------------------------------
# EL PROBLEMA QUE RESUELVE
#
# Hasta ahora, "desastre" era un diccionario escrito a mano con cuatro
# fechas que elegimos nosotros. Eso tiene dos consecuencias feas:
#
#   1. Cualquiera puede preguntar "¿y por que esos cuatro y no otros?"
#      y la unica respuesta honesta seria "porque los elegimos asi".
#
#   2. Nos obligaba a un veredicto BINARIO. Un episodio pasaba o no
#      pasaba. Y la realidad no funciona asi: en marzo de 2015 hubo
#      5,788 damnificados en Piura. Llamarlo "sin desastre" —como
#      haciamos— era sencillamente falso.
#
# Este modulo sustituye ese diccionario por el registro oficial de
# emergencias del INDECI. El veredicto deja de ser una opinion nuestra y
# pasa a ser un dato del Estado que cualquiera puede descargar y verificar.
#
# ------------------------------------------------------------
# FUENTE
#
#   INDECI — Emergencias historicas registradas en el SINPAD
#   (Sistema de Informacion Nacional para la Respuesta y Rehabilitacion)
#   Plataforma Nacional de Datos Abiertos, datosabiertos.gob.pe
#   Cobertura utilizada: 2003-2023, departamento de Piura.
#
# Se conservan solo los fenomenos HIDROMETEOROLOGICOS: lluvias intensas,
# inundacion, huaicos, riadas, deslizamientos, derrumbes y granizo. Un
# incendio urbano tambien es una emergencia registrada en SINPAD, pero no
# tiene nada que ver con que el agua haya aterrizado en el territorio.
#
# ------------------------------------------------------------
# LOS CORTES, Y DE DONDE SALEN
#
# No los elegimos "a ojo": son PERCENTILES de la propia distribucion de
# damnificados mensuales de la serie 2003-2023 (252 meses).
#
#   P99 = 10,250.8 damnificados  -> redondeado a 10,000 (MAYOR)
#   P95 =  1,886.3 damnificados  -> redondeado a  2,000 (MENOR)
#
# Con los umbrales REDONDEADOS que usa el codigo:
#   >= 10,000 -> 3 meses en 21 años
#   >=  2,000 -> 12 meses en 21 años
#
# (Con el P95 exacto de 1,886 serian 13. La diferencia esta en un solo mes
# que cae entre 1,886 y 2,000. Se documenta el numero que corresponde a
# los umbrales realmente aplicados, no al percentil sin redondear.)
#
# Reproducible con:
#   python core/core_impacto.py
#
# Esto no elimina la arbitrariedad —elegir P95 tambien es una eleccion—
# pero la vuelve DECLARABLE y REPRODUCIBLE, que es lo que se puede
# defender. Y por eso existe barrer_umbrales().
#
# OJO CON COMO SE LEE EL BARRIDO: en la ultima corrida, el numero de
# episodios con daño va de 5 a 1 segun el corte. NO es estable. La lectura
# honesta no es "la conclusion no depende del corte", sino "entre 1,000 y
# 2,000 el reparto se mantiene, y por eso el P95 redondeado es una
# eleccion razonable". Decirlo de mas seria sobrevender el resultado.
#
# ------------------------------------------------------------
# LO QUE ESTE MODULO NO PUEDE HACER, Y HAY QUE DECIRLO
#
# 1. SINPAD arranca en 2003. Los eventos de 1983 y 1998 quedan fuera y
#    siguen dependiendo del registro documental. Se declaran aparte.
#
# 2. SINPAD tiene SESGO DE REPORTE. Una emergencia existe en el registro
#    si alguien la reporto, y la cobertura administrativa mejora con los
#    años. "Cero damnificados" significa "sin registro", no "no ocurrio".
#
# 3. La granularidad es MENSUAL. Un desastre a fin de mes y otro a
#    principios del siguiente se reparten en dos filas.
#
# 4. LA VENTANA DEL EPISODIO PUEDE DEJAR DAÑO FUERA. El veredicto solo mira
#    dentro de la ventana del episodio mas dos meses de margen. Si el daño
#    ocurrio ANTES de que el sistema alertara, no se contabiliza. Caso
#    real: el episodio de 2015-16 arranca el 17-abr-2015, asi que los
#    5,788 damnificados de marzo de 2015 quedan fuera y el veredicto se
#    apoya en los 3,214 de marzo de 2016. Ese daño no anticipado existe y
#    hay que declararlo por separado.
# ============================================================

import os

import pandas as pd

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'data', 'datos')
CSV_SINPAD = os.path.join(CARPETA_DATOS, 'piura_emergencias_hidro_mensual.csv')

# --- Cortes de severidad (percentiles de la serie 2003-2023) ---
UMBRAL_MAYOR = 10000     # ~P99 (exacto: 10,250.8)
UMBRAL_MENOR = 2000      # ~P95 (exacto:  1,886.3)

# Primer año con cobertura SINPAD. Antes de esto, el modulo no opina.
ANIO_INICIO_SINPAD = 2003

# Eventos anteriores a SINPAD. Se mantienen por necesidad, y se marcan
# como lo que son: registro documental, no dato descargable.
DESASTRES_DOCUMENTALES = {
    'FEN 1982-83': pd.Timestamp('1983-05-01'),
    'FEN 1997-98': pd.Timestamp('1998-03-01'),
}

VEREDICTOS = ('DESASTRE MAYOR', 'DESASTRE MENOR', 'SIN DAÑO REGISTRADO',
              'COBERTURA DUDOSA', 'FUERA DE COBERTURA', 'EN CURSO')

# --- Deteccion de años mal publicados ---
#
# El recurso de 2023 del portal trae 10 emergencias hidrometeorologicas en
# Piura y CERO damnificados en todo el año. Eso es imposible: el ciclon
# Yaku toco Piura el 15 de marzo de 2023. El archivo esta incompleto.
#
# Si no lo detectamos, el sistema concluye "en 2023 no hubo daño" y esa
# frase es falsa. Un dato ausente NO es un cero: es un dato ausente, y hay
# que decirlo. Por eso los años bajo este minimo se marcan como COBERTURA
# DUDOSA y quedan FUERA de la matriz de confusion, igual que los episodios
# en curso. Preferimos una n menor a una n contaminada.
MINIMO_EMERGENCIAS_ANUALES = 15


def cargar_sinpad(ruta=CSV_SINPAD):
    """
    Serie mensual de emergencias hidrometeorologicas en Piura.

    Devuelve None si el archivo no esta: el resto del sistema debe poder
    funcionar sin el, degradandose al registro documental. Un modulo de
    impacto que tumba la aplicacion cuando falta un CSV no sirve.
    """
    if not os.path.exists(ruta):
        return None
    df = pd.read_csv(ruta)
    df['fecha'] = pd.PeriodIndex(df['ym'], freq='M').to_timestamp()
    return df.set_index('fecha')[['n', 'damni', 'afect', 'viv_destr']]


def impacto_en_ventana(sinpad, inicio, fin, margen_meses=2, tope=None):
    """
    Daño acumulado dentro de la ventana de un episodio.

    'margen_meses' extiende la ventana por el final: la respuesta del
    territorio no termina el dia que la anomalia oceanica baja del umbral.

    'tope' CORTA esa extension. Sin el, el margen de una racha invade el
    inicio de la siguiente y le roba su daño: la racha de sep-nov 2016
    (ICEN 0.47, neutro) se atribuia los 9,016 damnificados de enero de
    2017, que pertenecen al Niño costero. Un episodio no puede acreditarse
    el desastre del que viene detras.

    NO hay margen por el INICIO, y eso es deliberado: un sistema de alerta
    no puede acreditarse un daño ocurrido antes de que alertara. La
    contrapartida es que ese daño tampoco aparece en la matriz. Ver la
    limitacion 4 del encabezado.
    """
    if sinpad is None:
        return None
    desde = pd.Timestamp(inicio).to_period('M').to_timestamp()
    hasta = (pd.Timestamp(fin) + pd.DateOffset(months=margen_meses))
    hasta = hasta.to_period('M').to_timestamp()
    if tope is not None:
        limite = pd.Timestamp(tope).to_period('M').to_timestamp()
        hasta = min(hasta, limite - pd.DateOffset(months=1))
        if hasta < desde:
            hasta = desde
    tramo = sinpad.loc[desde:hasta]
    if not len(tramo):
        return None
    pico = tramo['damni'].idxmax()
    return {
        'damni_total': float(tramo['damni'].sum()),
        'damni_pico_mes': float(tramo['damni'].max()),
        'mes_pico': pico,
        'afectados': float(tramo['afect'].sum()),
        'viviendas_destruidas': float(tramo['viv_destr'].sum()),
        'n_emergencias': int(tramo['n'].sum()),
    }


def anios_dudosos(sinpad, minimo=MINIMO_EMERGENCIAS_ANUALES):
    """Años cuyo recurso publicado esta manifiestamente incompleto."""
    if sinpad is None:
        return set()
    por_anio = sinpad.groupby(sinpad.index.year)['n'].sum()
    return set(por_anio[por_anio < minimo].index)


def veredicto(sinpad, inicio, fin, ultimo_dato=None, meses_en_curso=3,
              umbral_mayor=UMBRAL_MAYOR, umbral_menor=UMBRAL_MENOR,
              tope=None, dudosos=None):
    """
    Clasifica un episodio. Devuelve (veredicto, detalle).

    El orden de las comprobaciones IMPORTA:

      1. ¿Sigue abierto? Entonces NO se clasifica. Contar como falsa
         alarma un episodio cuya temporada de lluvias todavia no ha
         ocurrido es AFIRMAR que no va a pasar nada, y eso no lo sabemos.
         Es el mismo error que ya se corrigio en core_alerta.py.

      2. ¿Cae antes de 2003? Entonces SINPAD no lo cubre y se resuelve
         con el registro documental.

      3. Solo entonces se mira el daño.

    NOTA sobre 'meses_en_curso': aqui son 3, pero core_alerta.py usa 30
    DIAS para su propio marcador 'en_curso'. Son criterios distintos a
    proposito —uno cierra el veredicto de impacto, el otro solo etiqueta
    el episodio— pero conviene saberlo: un episodio cerrado hace dos meses
    es 'EN CURSO' para este modulo y no lo es para core_alerta.
    """
    inicio = pd.Timestamp(inicio)
    fin = pd.Timestamp(fin)
    if dudosos is None:
        dudosos = anios_dudosos(sinpad)

    # --- 1. En curso: no clasificable ---
    if ultimo_dato is not None:
        limite = pd.Timestamp(ultimo_dato) - pd.DateOffset(months=meses_en_curso)
        if fin >= limite:
            return 'EN CURSO', {
                'nota': 'Episodio abierto o recien cerrado. La temporada de '
                        'lluvias aun no ha concluido: clasificarlo seria '
                        'afirmar un resultado que todavia no se conoce.'
            }

    # --- 2. Anterior a la cobertura de SINPAD ---
    if fin.year < ANIO_INICIO_SINPAD:
        nombre = next(
            (n for n, f in DESASTRES_DOCUMENTALES.items()
             if inicio <= f <= fin + pd.DateOffset(months=2)), None)
        return 'FUERA DE COBERTURA', {
            'documental': nombre,
            'nota': 'SINPAD arranca en 2003. Este episodio se resuelve con '
                    'registro documental, no con dato descargable.'
        }

    # --- 3. ¿El año esta bien publicado? ---
    # Si CUALQUIER año de la ventana viene incompleto, no podemos afirmar
    # "no hubo daño": no lo sabemos.
    abarcados = set(range(inicio.year, fin.year + 1))
    if abarcados & set(dudosos):
        return 'COBERTURA DUDOSA', {
            'anios': sorted(abarcados & set(dudosos)),
            'nota': 'El recurso publicado de ese año esta incompleto. '
                    'Ausencia de registro no equivale a ausencia de daño.'
        }

    # --- 4. Veredicto por daño registrado ---
    imp = impacto_en_ventana(sinpad, inicio, fin, tope=tope)
    if imp is None:
        return 'FUERA DE COBERTURA', {'nota': 'Sin datos SINPAD en la ventana.'}

    pico = imp['damni_pico_mes']
    if pico >= umbral_mayor:
        return 'DESASTRE MAYOR', imp
    if pico >= umbral_menor:
        return 'DESASTRE MENOR', imp
    return 'SIN DAÑO REGISTRADO', imp


def hubo_dano(v):
    """True si el veredicto cuenta como evento con daño."""
    return v in ('DESASTRE MAYOR', 'DESASTRE MENOR')


def evaluable(v):
    """
    True si el episodio puede entrar en una matriz de confusion.

    Quedan FUERA los episodios en curso, los anteriores a SINPAD y los que
    caen en un año mal publicado. Reducir la n es el precio de no
    contaminarla.
    """
    return v in ('DESASTRE MAYOR', 'DESASTRE MENOR', 'SIN DAÑO REGISTRADO')


def barrer_umbrales(sinpad, episodios, ultimo_dato=None,
                    cortes=(500, 1000, 2000, 5000, 10000)):
    """
    ¿Cambia la conclusion si movemos el corte de "desastre"?

    Enseñar este barrido es lo que hay que hacer antes de que alguien
    pregunte por que 2,000 y no 1,500.

    Pero hay que leerlo con honestidad: en la ultima corrida el reparto NO
    es estable en todo el rango (va de 5 a 1 episodios con daño). Lo que
    se sostiene es que entre 1,000 y 2,000 el reparto no cambia, y ahi es
    donde cae el P95. Afirmar "la conclusion no depende del corte" seria
    decir mas de lo que muestran los numeros.

    'episodios' es una lista de tuplas (inicio, fin).
    """
    filas = []
    for corte in cortes:
        con_dano = sin_dano = 0
        for inicio, fin in episodios:
            v, _ = veredicto(sinpad, inicio, fin, ultimo_dato,
                             umbral_mayor=corte * 5, umbral_menor=corte)
            if v == 'SIN DAÑO REGISTRADO':
                sin_dano += 1
            elif hubo_dano(v):
                con_dano += 1
        filas.append({'corte': corte, 'con_dano': con_dano,
                      'sin_dano': sin_dano})
    return pd.DataFrame(filas)


if __name__ == '__main__':
    s = cargar_sinpad()
    if s is None:
        raise SystemExit(f'Falta {CSV_SINPAD}')
    print(f'Serie SINPAD: {len(s)} meses  '
          f'({s.index[0]:%b-%Y} a {s.index[-1]:%b-%Y})')

    # Percentiles reales, para que los umbrales del encabezado sean
    # verificables sin salir del archivo.
    p95 = s['damni'].quantile(0.95)
    p99 = s['damni'].quantile(0.99)
    print(f'Percentiles de damnificados/mes: P95 = {p95:,.1f}   '
          f'P99 = {p99:,.1f}')
    print(f'Cortes aplicados (redondeados): MAYOR >= {UMBRAL_MAYOR:,}  '
          f'MENOR >= {UMBRAL_MENOR:,}')
    print(f'  meses >= {UMBRAL_MAYOR:,}: {int((s.damni >= UMBRAL_MAYOR).sum())}')
    print(f'  meses >= {UMBRAL_MENOR:,}: {int((s.damni >= UMBRAL_MENOR).sum())}\n')

    print('Meses por encima del corte MENOR:')
    top = s[s.damni >= UMBRAL_MENOR].sort_values('damni', ascending=False)
    for f, r in top.iterrows():
        marca = 'MAYOR' if r.damni >= UMBRAL_MAYOR else 'menor'
        print(f'  {f:%Y-%m}  {int(r.damni):>7,} damnificados   {marca}')

    dudosos = anios_dudosos(s)
    if dudosos:
        print(f'\nAños con recurso incompleto (< {MINIMO_EMERGENCIAS_ANUALES} '
              f'emergencias): {sorted(dudosos)}')
        print('Quedan FUERA de la matriz de confusion.')