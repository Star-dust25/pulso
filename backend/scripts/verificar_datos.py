# verificar_datos.py
# ============================================================
#   python verificar_datos.py
#
# Audita los CSV antes de analizarlos. Detecta el problema clasico:
# filas duplicadas por haber lanzado el descargador mas de una vez.
#
# Si encuentra duplicados, los elimina y reescribe el CSV limpio.
# Un duplicado no es cosmetico: infla la n, estrecha los intervalos de
# confianza y puede fabricar correlaciones que no existen.
# ============================================================

import os
import sys

import pandas as pd

CARPETA = 'datos'

ESPERADO = {
    'serie_sst.csv': (['anio', 'mes'], 1982, 'SST'),
    'serie_vegetacion.csv': (['anio', 'mes'], 2013, 'VEGETACION'),
    'serie_reservorios.csv': (['reservorio', 'anio', 'mes'], 2013, 'RESERVORIOS'),
}


def auditar(nombre, claves, anio_inicio, etiqueta):
    ruta = os.path.join(CARPETA, nombre)
    if not os.path.exists(ruta):
        print(f'[{etiqueta}] no existe todavia ({ruta}). Se omite.\n')
        return

    df = pd.read_csv(ruta)
    filas = len(df)

    duplicados = df.duplicated(subset=claves).sum()
    anios = sorted(df['anio'].dropna().astype(int).unique())
    faltantes = [a for a in range(anio_inicio, max(anios) + 1) if a not in anios]

    print(f'[{etiqueta}]  {ruta}')
    print(f'   filas        : {filas}')
    print(f'   duplicados   : {duplicados}')
    print(f'   rango anios  : {min(anios)} - {max(anios)}')
    if faltantes:
        print(f'   AÑOS FALTANTES: {faltantes}')

    if duplicados:
        limpio = df.drop_duplicates(subset=claves, keep='first')
        limpio = limpio.sort_values(claves)
        limpio.to_csv(ruta, index=False)
        print(f'   -> LIMPIADO: {filas} filas -> {len(limpio)} filas')
        df = limpio

    # Cobertura real de datos (cuantos meses traen valor, no null)
    for col in df.columns:
        if col in ('anio', 'mes', 'reservorio'):
            continue
        validos = df[col].notna().sum()
        pct = 100 * validos / len(df) if len(df) else 0
        marca = '  <-- REVISAR' if pct < 50 else ''
        print(f'   {col:20s}: {validos:4d}/{len(df)} con dato ({pct:5.1f}%){marca}')
    print()


def main():
    if not os.path.isdir(CARPETA):
        sys.exit(f'No existe la carpeta {CARPETA}/. ¿Corriste construir_series.py?')

    print('=== AUDITORIA DE DATOS ===\n')
    for nombre, (claves, anio, etiqueta) in ESPERADO.items():
        auditar(nombre, claves, anio, etiqueta)
    print('Listo.')


if __name__ == '__main__':
    main()
