# config_icen.py
# ============================================================
# CATEGORIAS OFICIALES DEL ICEN — FUENTE UNICA DE VERDAD
#
# ------------------------------------------------------------
# POR QUE EXISTE ESTE ARCHIVO
#
# Los umbrales del ICEN estaban copiados dentro de backtest_fen.py con los
# valores de la tabla ANTIGUA (ENFEN 2012 / Takahashi et al. 2014):
#
#       EXTRAORDINARIO > 3.0 | FUERTE > 1.7 | MODERADO > 1.0 | DEBIL > 0.4
#
# Esa tabla YA NO ESTA VIGENTE. En diciembre de 2024 el ENFEN actualizo la
# metodologia (Nota Tecnica ENFEN 01-2024) y con ella los intervalos.
#
# Consecuencia real del error: con la tabla vieja, el episodio de 2023
# (ICEN reconstruido = 3.15) se clasificaba como EXTRAORDINARIO. Con la
# tabla vigente es FUERTE — y el ICEN oficial ni siquiera llego a 3.15,
# se quedo en 2.92. El sistema estaba declarando un Niño extraordinario
# que oficialmente no existio.
#
# Un umbral copiado en tres archivos es un umbral que envejece mal.
# Aqui vive una sola vez.
#
# ------------------------------------------------------------
# FUENTE
#
#   ENFEN (2024). Definicion operacional de los eventos El Niño Costero y
#   La Niña Costera en el Peru. Nota Tecnica ENFEN 01-2024.
#
#   Publicacion vigente: SIOFEN / IMARPE
#   https://siofen.imarpe.gob.pe/nivel2/indice-costero-el-nino-icen
#
#   Producto: ICEN (ENFEN, 2024) · Datos: NOAA ERSST v5
#   Climatologia: 1991-2020 · Procesamiento: LHFM/AFIOF/DGIOCC/IMARPE
#
# El ICEN es la media movil de TRES MESES de la anomalia mensual de TSM en
# la region Niño 1+2 (90°-80°W, 10°S-0°).
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
# ============================================================

import math

# ------------------------------------------------------------
# LA TABLA
# ------------------------------------------------------------
# (limite_inferior, limite_superior, condicion, magnitud)
# Intervalos abiertos por abajo, cerrados por arriba: (inf, sup]
# El orden va de mas frio a mas calido para poder recorrerlo linealmente.

TABLA_ICEN = [
    (-math.inf, -1.3, 'fria',   'FUERTE'),
    (-1.3,      -1.1, 'fria',   'MODERADA'),
    (-1.1,      -0.7, 'fria',   'DEBIL'),
    (-0.7,       0.5, 'neutra', 'NEUTRO'),
    (0.5,        1.3, 'calida', 'DEBIL'),
    (1.3,        2.1, 'calida', 'MODERADA'),
    (2.1,        3.5, 'calida', 'FUERTE'),
    (3.5,  math.inf,  'calida', 'EXTRAORDINARIA'),
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
    'La Niña Costera en el Peru. Nota Tecnica ENFEN 01-2024. '
    'Publicacion vigente en SIOFEN/IMARPE.'
)


# ------------------------------------------------------------
# CLASIFICACION
# ------------------------------------------------------------

def clasificar(valor):
    """
    Devuelve (condicion, magnitud) segun la tabla ENFEN 2024.

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

    for inferior, superior, condicion, magnitud in TABLA_ICEN:
        if inferior < v <= superior:
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
    for inferior, superior, _, _ in TABLA_ICEN:
        if inferior < v <= superior:
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
    for inferior, superior, _, _ in TABLA_ICEN:
        if inferior < v <= superior:
            return inferior if math.isfinite(inferior) else None
    return None


# ------------------------------------------------------------
# AUTOCOMPROBACION
# ------------------------------------------------------------
# Casos verificados contra la serie oficial del IGP. Si alguien vuelve a
# tocar los umbrales, esto revienta antes que la presentacion.

_CASOS = [
    (4.08, 'calida', 'EXTRAORDINARIA'),   # 1997-98, pico nov-1997
    (2.92, 'calida', 'FUERTE'),           # 2023,    pico jul-2023
    (2.23, 'calida', 'FUERTE'),           # 2015-16, pico oct-2015
    (1.98, 'calida', 'MODERADA'),         # 2026,    may-2026
    (1.31, 'calida', 'MODERADA'),         # 2017,    pico mar-2017 (al filo)
    (0.90, 'calida', 'DEBIL'),
    (0.10, 'neutra', 'NEUTRO'),
    (-0.90, 'fria',  'DEBIL'),
    (-1.20, 'fria',  'MODERADA'),
    (-1.64, 'fria',  'FUERTE'),
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
    for inferior, superior, condicion, magnitud in reversed(TABLA_ICEN):
        lo = '-inf' if inferior == -math.inf else f'{inferior:+.1f}'
        hi = '+inf' if superior == math.inf else f'{superior:+.1f}'
        nombre = magnitud if condicion != 'fria' else f'{magnitud} (fria)'
        print(f'{nombre:<18}{lo + " a " + hi:>20}')
    print('\nComprobacion contra la serie oficial del IGP:\n')
    autocomprobar(verboso=True)
    print('\nTodo correcto.')
