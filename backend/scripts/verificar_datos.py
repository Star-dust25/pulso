# verificar_datos.py
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/verificar_datos.py
#
# AUDITORIA DE SOLO LECTURA. Este script NO modifica nada.
#
# ------------------------------------------------------------
# QUE HACE
#
# Revisa los CSV de data/datos/ y reporta:
#   - filas duplicadas por clave
#   - años ausentes dentro del rango esperado
#   - hasta que mes llega cada serie
#   - que porcentaje de cada columna trae dato real (no nulo)
#
# ------------------------------------------------------------
# POR QUE YA NO ESCRIBE
#
# La version anterior, al encontrar duplicados, los eliminaba y
# reescribia el CSV con drop_duplicates(keep='first').
#
# Eso hoy seria DAÑINO. Los scripts de descarga deduplican con
# keep='last', y no es un capricho: OISST y Landsat publican valores
# preliminares que luego corrigen, asi que la lectura mas reciente es la
# buena. Un keep='first' revertiria valores corregidos a sus versiones
# preliminares, en silencio y sin dejar rastro.
#
# Ademas ya no hace falta: construir_serie_diaria.py, construir_series.py
# y construir_reservorios.py deduplican al escribir, asi que el problema
# que este script resolvia no puede volver a producirse por esa via.
#
# Si esta auditoria encuentra duplicados, la respuesta correcta NO es
# limpiarlos aqui: es volver a ejecutar el descargador correspondiente,
# que reescribe el archivo entero y deduplica con el criterio correcto.
#
# ------------------------------------------------------------
# BUG CORREGIDO: LA CARPETA NO EXISTIA
#
# CARPETA valia 'datos'. La ruta real es 'data/datos'. El script salia
# SIEMPRE por el sys.exit con el mensaje "¿Corriste construir_series.py?",
# que ademas culpaba al descargador de un fallo de ruta. Nadie lo noto
# porque este script llevaba tiempo sin usarse.
# ============================================================

import os
import sys

import pandas as pd

# Anclado al archivo, no al directorio de trabajo.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(CARPETA_BACKEND, 'data', 'datos')

# nombre -> (claves de unicidad, primer año esperado, etiqueta)
ESPERADO = {
    'serie_sst.csv': (['anio', 'mes'], 1982, 'SST'),
    'serie_vegetacion.csv': (['anio', 'mes'], 2013, 'VEGETACION'),
    'serie_reservorios.csv': (['reservorio', 'anio', 'mes'], 2013,
                              'RESERVORIOS'),
}

# Columnas que son identificadores, no mediciones: no tiene sentido
# medirles la cobertura de datos.
COLUMNAS_CLAVE = ('anio', 'mes', 'reservorio', 'fecha')


def auditar(nombre, claves, anio_inicio, etiqueta):
    """Revisa un CSV y devuelve True si no encontro problemas."""
    ruta = os.path.join(CARPETA, nombre)
    if not os.path.exists(ruta):
        print(f'[{etiqueta}] no existe todavia ({ruta}). Se omite.\n')
        return True

    df = pd.read_csv(ruta)
    if df.empty:
        print(f'[{etiqueta}] {ruta}')
        print('   ARCHIVO VACIO.\n')
        return False

    limpio = True
    filas = len(df)
    duplicados = int(df.duplicated(subset=claves).sum())
    anios = sorted(df['anio'].dropna().astype(int).unique())
    faltantes = [a for a in range(anio_inicio, max(anios) + 1)
                 if a not in anios]

    print(f'[{etiqueta}]  {ruta}')
    print(f'   filas        : {filas}')
    print(f'   rango anios  : {min(anios)} - {max(anios)}')

    # Hasta que mes llega la serie. Un año presente no significa un año
    # completo: es justo el error que tenian los scripts de descarga.
    ultimo = df.sort_values(['anio', 'mes']).iloc[-1]
    print(f'   ultimo mes   : {int(ultimo["anio"])}-{int(ultimo["mes"]):02d}')

    if duplicados:
        limpio = False
        print(f'   DUPLICADOS   : {duplicados}   <-- vuelve a ejecutar el '
              f'descargador de esta serie.')
        print('                  (este script NO los borra a proposito: '
              'ver el encabezado)')
    else:
        print(f'   duplicados   : 0')

    if faltantes:
        limpio = False
        print(f'   AÑOS FALTANTES: {faltantes}')

    # Cobertura real de datos: cuantas filas traen valor, no nulo.
    for col in df.columns:
        if col in COLUMNAS_CLAVE:
            continue
        validos = int(df[col].notna().sum())
        pct = 100 * validos / len(df) if len(df) else 0
        marca = '  <-- REVISAR' if pct < 50 else ''
        if pct < 50:
            limpio = False
        print(f'   {col:20s}: {validos:4d}/{len(df)} con dato '
              f'({pct:5.1f}%){marca}')
    print()
    return limpio


def main():
    if not os.path.isdir(CARPETA):
        sys.exit(f'No existe {CARPETA}. Ejecuta primero:\n'
                 f'  python scripts/construir_series.py')

    print('=== AUDITORIA DE DATOS (solo lectura) ===\n')
    todo_ok = True
    for nombre, (claves, anio, etiqueta) in ESPERADO.items():
        if not auditar(nombre, claves, anio, etiqueta):
            todo_ok = False

    if todo_ok:
        print('Sin incidencias.')
    else:
        print('Hay incidencias arriba. Este script no las corrige: vuelve a')
        print('ejecutar el descargador correspondiente, que reescribe el')
        print('archivo entero y deduplica con el criterio correcto.')
    # Codigo de salida distinto de cero para poder encadenarlo en CI.
    sys.exit(0 if todo_ok else 1)


if __name__ == '__main__':
    main()