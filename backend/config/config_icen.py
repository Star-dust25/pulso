# config_icen.py
# ============================================================
# CATEGORIAS OFICIALES DEL ICEN — FUENTE UNICA DE VERDAD
#
# ------------------------------------------------------------
# POR QUE EXISTE ESTE ARCHIVO
#
# Los umbrales del ICEN no deben vivir repetidos en varios modulos. La
# tabla ANTIGUA (ENFEN 2012 / Takahashi et al. 2014) era:
#
#       EXTRAORDINARIO > 3.0 | FUERTE > 1.7 | MODERADO > 1.0 | DEBIL > 0.4
#
# Esa tabla YA NO ESTA VIGENTE. En diciembre de 2024 el ENFEN actualizo la
# metodologia (Nota Tecnica ENFEN 01-2024) y con ella los intervalos.
#
# Consecuencia real de usar la tabla vieja: el episodio de 2023 (ICEN
# reconstruido = 3.15) se clasificaba como EXTRAORDINARIO. Con la tabla
# vigente es FUERTE, y la cronologia oficial del ENFEN (Tabla 3 de la nota
# tecnica) lo registra como "Niño Fuerte" (marzo 2023 - febrero 2024).
# El ICEN oficial ademas no llego a 3.15. El sistema estaba declarando un
# Niño extraordinario que oficialmente no existio.
#
# Un umbral copiado en tres archivos es un umbral que envejece mal.
# Aqui vive una sola vez.
#
# ------------------------------------------------------------
# FUENTE
#
#   ENFEN (2024). Definicion operacional de los eventos El Niño Costero y
#   La Niña Costera en el Peru. Nota Tecnica ENFEN 01-2024, 7p.
#   Diciembre 2024. Reemplaza a la Nota Tecnica ENFEN de abril 2012.
#
#   Publicacion vigente: SIOFEN / IMARPE
#   https://siofen.imarpe.gob.pe/nivel2/indice-costero-el-nino-icen
#
#   Producto: ICEN (ENFEN, 2024) · Datos: NOAA ERSST v5
#
# El ICEN es la media movil de TRES MESES de la anomalia mensual de TSM en
# la region Niño 1+2 (90°-80°W, 10°S-0°).
#
# NOTA SOBRE LA CLIMATOLOGIA: SIOFEN resume la referencia como "climatologia
# 1991-2020", y esa es la cadena que usamos en FUENTE_CORTA. La nota tecnica
# es mas precisa: el ICEN historico se calcula con una climatologia distinta
# cada 5 años (1931-1960 para el quinquenio 1946-1950, 1936-1965 para el
# siguiente, y asi sucesivamente). La climatologia 1991-2020 rige de 2006 en
# adelante. Nuestra serie reconstruida no replica ese escalonamiento; por eso
# se valida por correlacion contra la serie oficial y NO se presenta como el
# ICEN oficial.
#
# ------------------------------------------------------------
# ADVERTENCIA QUE HAY QUE DECIR EN VOZ ALTA
#
# El pico oficial de 2017 fue ICEN = 1.31, y el umbral de la categoria
# MODERADA arranca en 1.3. Esta UNA CENTESIMA por encima.
#
# La frase honesta no es "2017 fue moderado". Es:
#
#   "2017 alcanzo la categoria MODERADA, en el limite inferior del
#    intervalo (1.31 sobre un umbral de 1.30)."
#
# Decirlo asi es mas fuerte que ocultarlo: demuestra que conoces el dato
# hasta la centesima. Para eso existe la funcion en_el_limite().
#
# ------------------------------------------------------------
# PENDIENTE CONOCIDO (documentado a proposito, no corregido)
#
# La figura 1_icen_historico.png, generada por backtest_fen.py, lleva el
# rotulo "Metodologia ENFEN 2012" y el umbral "+0.4 °C", que corresponden a
# la tabla derogada y contradicen este archivo. No se regenero la imagen
# porque no se muestra en la web. Si alguna vez se publica, hay que
# regenerarla contra esta tabla.
# ============================================================

import math

# ------------------------------------------------------------
# LA TABLA
# ------------------------------------------------------------
# (limite_inferior, limite_superior, cerrado_abajo, cerrado_arriba,
#  condicion, magnitud)
#
# IMPORTANTE: el ENFEN NO usa la misma convencion en las dos ramas.
# Segun la Tabla 2 de la Nota Tecnica ENFEN 01-2024:
#
#   - Rama FRIA : cerrada por abajo, abierta por arriba  ->  [inf, sup)
#       "Moderada: mayor o igual que -1.3 y menor que -1.1"
#   - Banda NEUTRA: cerrada por ambos lados              ->  [inf, sup]
#       "mayor o igual que -0.7 y menor o igual que 0.5"
#   - Rama CALIDA: abierta por abajo, cerrada por arriba ->  (inf, sup]
#       "Moderada: mayor que 1.3 y menor o igual que 2.1"
#
# Aplicar una sola convencion a toda la tabla clasifica mal exactamente los
# valores -1.3, -1.1 y -0.7, siempre exagerando la severidad. Por eso cada
# fila lleva sus propios marcadores de borde.
#
# El orden va de mas frio a mas calido para poder recorrerlo linealmente.

TABLA_ICEN = [
    (-math.inf, -1.3, True,  False, 'fria',   'FUERTE'),
    (-1.3,      -1.1, True,  False, 'fria',   'MODERADA'),
    (-1.1,      -0.7, True,  False, 'fria',   'DEBIL'),
    (-0.7,       0.5, True,  True,  'neutra', 'NEUTRO'),
    (0.5,        1.3, False, True,  'calida', 'DEBIL'),
    (1.3,        2.1, False, True,  'calida', 'MODERADA'),
    (2.1,        3.5, False, True,  'calida', 'FUERTE'),
    (3.5,  math.inf,  False, True,  'calida', 'EXTRAORDINARIA'),
]

# Umbrales de la rama calida, por si algun modulo necesita solo el numero.
UMBRAL_DEBIL = 0.5
UMBRAL_MODERADA = 1.3
UMBRAL_FUERTE = 2.1
UMBRAL_EXTRAORDINARIA = 3.5

# Tolerancia para avisar de que un valor cae pegado a un umbral.
MARGEN_LIMITE = 0.05

FUENTE_CORTA = 'ICEN (ENFEN, 2024) · NOAA ERSST v5 · clim. 1991-2020'
FUENTE_LARGA = (
    'ENFEN (2024). Definicion operacional de los eventos El Niño Costero y '
    'La Niña Costera en el Peru. Nota Tecnica ENFEN 01-2024, diciembre 2024. '
    'Publicacion vigente en SIOFEN/IMARPE.'
)


# ------------------------------------------------------------
# CLASIFICACION
# ------------------------------------------------------------

def _dentro(v, inferior, superior, cerrado_abajo, cerrado_arriba):
    """Comprueba la pertenencia respetando el tipo de borde de cada fila."""
    ok_abajo = (v >= inferior) if cerrado_abajo else (v > inferior)
    ok_arriba = (v <= superior) if cerrado_arriba else (v < superior)
    return ok_abajo and ok_arriba


# Alias publico. Cualquier modulo que necesite recorrer TABLA_ICEN debe usar
# esta funcion en vez de escribir a mano su propia comparacion: es lo unico
# que garantiza que los bordes se respeten igual en todo el sistema.
dentro = _dentro


def clasificar(valor):
    """
    Devuelve (condicion, magnitud) segun la Tabla 2 de ENFEN 01-2024.

    condicion: 'calida' | 'neutra' | 'fria'
    magnitud : 'DEBIL' | 'MODERADA' | 'FUERTE' | 'EXTRAORDINARIA' | 'NEUTRO'

    Ante un valor no numerico devuelve ('sin_dato', 'S/D'): un sistema de
    alerta no puede inventarse una categoria cuando le falta el dato.
    """
    if valor is None:
        return 'sin_dato', 'S/D'
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return 'sin_dato', 'S/D'
    if math.isnan(v):
        return 'sin_dato', 'S/D'

    for inferior, superior, cerr_ab, cerr_ar, condicion, magnitud in TABLA_ICEN:
        if _dentro(v, inferior, superior, cerr_ab, cerr_ar):
            return condicion, magnitud
    return 'sin_dato', 'S/D'


def etiqueta(valor):
    """
    Etiqueta legible, tal como la nombraria el ENFEN.

        1.98 -> 'El Niño costero MODERADA'
       -1.20 -> 'La Niña costera MODERADA'
        0.10 -> 'Neutro'
    """
    condicion, magnitud = clasificar(valor)
    if condicion == 'calida':
        return f'El Niño costero {magnitud}'
    if condicion == 'fria':
        return f'La Niña costera {magnitud}'
    if condicion == 'neutra':
        return 'Neutro'
    return 'Sin dato'


def en_el_limite(valor, margen=MARGEN_LIMITE):
    """
    True si el valor cae pegado al borde de su categoria.

    No es un adorno: 2017 cerro en 1.31 con el umbral en 1.30. Una revision
    de la serie por parte del IGP podria moverlo de categoria. Si tu sistema
    afirma 'MODERADA' sin decir que esta al filo, esa afirmacion es fragil.
    """
    condicion, magnitud = clasificar(valor)
    if magnitud == 'S/D':
        return False
    v = float(valor)
    for inferior, superior, cerr_ab, cerr_ar, _, _ in TABLA_ICEN:
        if _dentro(v, inferior, superior, cerr_ab, cerr_ar):
            cerca_abajo = math.isfinite(inferior) and (v - inferior) <= margen
            cerca_arriba = math.isfinite(superior) and (superior - v) <= margen
            return bool(cerca_abajo or cerca_arriba)
    return False


def umbral_inferior(valor):
    """Limite inferior del intervalo en el que cae el valor (para narrarlo)."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    for inferior, superior, cerr_ab, cerr_ar, _, _ in TABLA_ICEN:
        if _dentro(v, inferior, superior, cerr_ab, cerr_ar):
            return inferior if math.isfinite(inferior) else None
    return None


# ------------------------------------------------------------
# AUTOCOMPROBACION
# ------------------------------------------------------------
# Casos contrastados con la serie oficial del IGP y con la cronologia de
# eventos de la Nota Tecnica ENFEN 01-2024 (Tablas 3 y 4). Si alguien vuelve
# a tocar los umbrales, esto revienta antes que la presentacion.

_CASOS = [
    (4.08, 'calida', 'EXTRAORDINARIA'),   # 1997-98, pico nov-1997
    (2.92, 'calida', 'FUERTE'),           # 2023,    pico jul-2023
    (2.23, 'calida', 'FUERTE'),           # 2015-16, pico oct-2015
    (1.98, 'calida', 'MODERADA'),         # may-2026: ICENtmp (provisional,
                                          #   sujeto a reemplazo por el ICEN
                                          #   definitivo; no es serie cerrada)
    (1.31, 'calida', 'MODERADA'),         # 2017,    pico mar-2017 (al filo)
    (0.90, 'calida', 'DEBIL'),
    (0.10, 'neutra', 'NEUTRO'),
    (-0.90, 'fria',  'DEBIL'),
    (-1.20, 'fria',  'MODERADA'),
    (-1.64, 'fria',  'FUERTE'),

    # --- Casos de BORDE ---
    # No son adorno: con una convencion unica para toda la tabla, los tres
    # primeros salian una categoria mas severa de lo que dice el ENFEN, y
    # ningun otro caso de esta lista lo detectaba.
    (-1.30, 'fria',   'MODERADA'),        # "mayor o igual que -1.3"
    (-1.10, 'fria',   'DEBIL'),           # "mayor o igual que -1.1"
    (-0.70, 'neutra', 'NEUTRO'),          # "mayor o igual que -0.7"
    (0.50,  'neutra', 'NEUTRO'),          # "menor o igual que 0.5"
    (1.30,  'calida', 'DEBIL'),           # "menor o igual que 1.3"
    (2.10,  'calida', 'MODERADA'),        # "menor o igual que 2.1"
    (3.50,  'calida', 'FUERTE'),          # "menor o igual que 3.5"
]


def autocomprobar(verboso=False):
    fallos = []
    for valor, cond_esperada, mag_esperada in _CASOS:
        cond, mag = clasificar(valor)
        ok = (cond, mag) == (cond_esperada, mag_esperada)
        if not ok:
            fallos.append((valor, cond_esperada, mag_esperada, cond, mag))
        if verboso:
            marca = 'OK ' if ok else 'MAL'
            filo = '  <- al filo del umbral' if en_el_limite(valor) else ''
            print(f'  {marca} {valor:>6.2f}  {etiqueta(valor)}{filo}')
    if fallos:
        detalle = '\n'.join(
            f'    {v}: esperado {ce}/{me}, obtenido {co}/{mo}'
            for v, ce, me, co, mo in fallos)
        raise AssertionError(
            'La tabla del ICEN no coincide con los casos oficiales:\n' + detalle)
    return True


if __name__ == '__main__':
    print('=' * 62)
    print('CATEGORIAS DEL ICEN — ENFEN 2024')
    print('=' * 62)
    print(f'\n{FUENTE_CORTA}\n')
    print(f'{"MAGNITUD":<18}{"INTERVALO":>20}')
    for inferior, superior, cerr_ab, cerr_ar, condicion, magnitud in reversed(TABLA_ICEN):
        lo = '-inf' if inferior == -math.inf else f'{inferior:+.1f}'
        hi = '+inf' if superior == math.inf else f'{superior:+.1f}'
        abre = '[' if cerr_ab else '('
        cierra = ']' if cerr_ar else ')'
        nombre = magnitud if condicion != 'fria' else f'{magnitud} (fria)'
        print(f'{nombre:<18}{abre + lo + ", " + hi + cierra:>20}')
    print('\nComprobacion contra los casos oficiales:\n')
    autocomprobar(verboso=True)
    print('\nTodo correcto.')