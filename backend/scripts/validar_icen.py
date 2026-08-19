# validar_icen.py
# ============================================================
#   Ejecutar DESDE backend/:
#       python scripts/validar_icen.py
#       python scripts/validar_icen.py --refrescar    (fuerza la descarga)
#
# VALIDACION EXTERNA. La pieza que convierte "hicimos un indice" en
# "reconstruimos el indice oficial y lo demostramos".
#
# Descarga el ICEN oficial del IGP (met.igp.gob.pe/datos/ICEN.txt) y lo
# compara mes a mes con nuestra reconstruccion desde 1982.
#
# ------------------------------------------------------------
# ATENCION: LA COPIA LOCAL SE QUEDA VIEJA
#
# Una version anterior reutilizaba data/salidas/icen_oficial.txt para
# siempre: si el archivo existia, NUNCA volvia a descargarlo. Eso congela
# la serie oficial en la fecha de la primera descarga.
#
# No es un detalle: core_icen.py lee ESE MISMO archivo para calcular
# "cuantos meses de retraso lleva el IGP", que es la base del argumento
# "Pulso anticipa al dato oficial". Con una copia vieja, ese retraso sale
# inflado y la ventaja parece mayor de lo que es.
#
# Ahora el script avisa de la antiguedad del archivo y admite --refrescar.
# ANTES DE PRESENTAR: ejecutar con --refrescar.
#
# ------------------------------------------------------------
# QUE ESPERAMOS ENCONTRAR (declarado de antemano):
#   - Correlacion alta en el periodo historico.
#   - Un SESGO que DERIVA con el tiempo, porque OISST v2.1 y ERSSTv5
#     tienen tendencias distintas en Niño 1+2, y porque el ENFEN usa
#     climatologias escalonadas cada 5 años y nosotros una sola.
#
# EL SESGO GLOBAL ES UNA ESTADISTICA ENGAÑOSA. Promediado sobre 1982-2026
# da casi cero, porque cambia de signo: negativo en los 80-90, positivo
# desde 2010. El numero que importa para el dato de HOY es el de la
# ventana reciente. Por eso este script reporta ambos, y el grafico
# muestra el reciente ademas del global.
#
# SI EL SESGO RECIENTE SE CONFIRMA: NO se presenta el valor crudo actual.
# Se presenta la validacion historica, el valor corregido (core_icen.py) y
# se declara la limitacion. Un jurado perdona una limitacion declarada.
# No perdona un dato inflado.
# ============================================================

import argparse
import datetime as dt
import os
import urllib.request

import numpy as np
import pandas as pd

URL_ICEN_OFICIAL = 'http://met.igp.gob.pe/datos/ICEN.txt'

# Anclado al archivo, no al directorio de trabajo: scripts/ vive dentro de
# backend/. Con rutas relativas el script solo funcionaba lanzandolo desde
# backend/ y fallaba en silencio desde cualquier otro sitio.
CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_SALIDA = os.path.join(CARPETA_BACKEND, 'data', 'salidas')
CSV_RECONSTRUIDO = os.path.join(CARPETA_SALIDA, 'icen_reconstruido.csv')
CSV_OFICIAL = os.path.join(CARPETA_SALIDA, 'icen_oficial.txt')

# Dias tras los cuales la copia local se considera vieja y se avisa.
DIAS_FRESCURA = 30

# Ventana reciente para el sesgo que si aplica al dato de hoy.
# Coincide con VENTANA_SESGO_ANIOS de core_icen.py a proposito: si los dos
# modulos midieran el sesgo sobre ventanas distintas, darian numeros
# distintos para lo mismo.
ANIOS_VENTANA_RECIENTE = 10


def descargar_oficial(refrescar=False):
    """
    Baja ICEN.txt del IGP.

    Reutiliza la copia local salvo que se pida --refrescar, pero SIEMPRE
    informa de su antiguedad. Si la descarga falla y hay copia, se usa la
    copia y se dice: preferimos un dato viejo declarado a un fallo mudo.
    """
    local_existe = os.path.exists(CSV_OFICIAL)

    if local_existe and not refrescar:
        edad = dt.datetime.now() - dt.datetime.fromtimestamp(
            os.path.getmtime(CSV_OFICIAL))
        dias = edad.days
        aviso = '  <-- VIEJA. Ejecuta con --refrescar.' if dias > DIAS_FRESCURA else ''
        print(f'Usando copia local: {CSV_OFICIAL}')
        print(f'  descargada hace {dias} dia(s).{aviso}')
        with open(CSV_OFICIAL, encoding='utf-8', errors='replace') as f:
            return f.read()

    print(f'Descargando {URL_ICEN_OFICIAL} ...')
    try:
        peticion = urllib.request.Request(
            URL_ICEN_OFICIAL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            texto = respuesta.read().decode('utf-8', errors='replace')
    except Exception as e:
        if local_existe:
            print(f'  FALLO la descarga ({e}). Se usa la copia local, que '
                  f'puede estar desactualizada.')
            with open(CSV_OFICIAL, encoding='utf-8', errors='replace') as f:
                return f.read()
        raise

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    with open(CSV_OFICIAL, 'w', encoding='utf-8') as f:
        f.write(texto)
    print(f'Guardado en {CSV_OFICIAL}')
    return texto


def parsear_oficial(texto, verboso=False):
    """
    El formato de ICEN.txt puede variar. Estrategia robusta: buscar en cada
    linea numeros que parezcan (anio, mes, valor) y quedarnos con eso.
    Las lineas de comentario del IGP empiezan por '%'.
    """
    lineas = [l for l in texto.splitlines() if l.strip()]

    if verboso:
        print('\n--- Primeras 5 lineas del archivo oficial ---')
        for l in lineas[:5]:
            print(f'    {l}')
        print('---\n')

    filas = []
    for linea in lineas:
        if linea.lstrip().startswith('%'):
            continue
        partes = linea.replace(',', ' ').split()
        numeros = []
        for p in partes:
            try:
                numeros.append(float(p))
            except ValueError:
                pass

        # Buscamos: anio (1950-2100), mes (1-12), valor (-5 a 5)
        if len(numeros) >= 3:
            anio, mes, valor = numeros[0], numeros[1], numeros[2]
            if 1950 <= anio <= 2100 and 1 <= mes <= 12 and -6 < valor < 6:
                filas.append({'anio': int(anio), 'mes': int(mes),
                              'icen_oficial': valor})

    if not filas:
        raise SystemExit(
            'No se pudo parsear ICEN.txt. Ejecuta con --verboso para ver las '
            'primeras lineas y ajustar el parseo.')

    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--refrescar', action='store_true',
                    help='Fuerza la descarga del ICEN oficial del IGP.')
    ap.add_argument('--verboso', action='store_true',
                    help='Muestra las primeras lineas del archivo oficial.')
    args = ap.parse_args()

    if not os.path.exists(CSV_RECONSTRUIDO):
        raise SystemExit(f'Falta {CSV_RECONSTRUIDO}. '
                         'Corre primero: python scripts/backtest_fen.py')

    oficial = parsear_oficial(descargar_oficial(args.refrescar), args.verboso)
    ultimo_oficial = oficial.sort_values(['anio', 'mes']).iloc[-1]
    print(f'\nICEN oficial: {len(oficial)} meses, '
          f'{oficial.anio.min()} - {oficial.anio.max()}')
    print(f'  ultimo mes publicado: '
          f'{int(ultimo_oficial.anio)}-{int(ultimo_oficial.mes):02d} '
          f'({ultimo_oficial.icen_oficial:+.2f})')

    nuestro = pd.read_csv(CSV_RECONSTRUIDO)
    nuestro = nuestro[['anio', 'mes', 'icen']].rename(
        columns={'icen': 'icen_pulso'})

    df = pd.merge(nuestro, oficial, on=['anio', 'mes'], how='inner').dropna()
    df['fecha'] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    df = df.sort_values('fecha')
    df['error'] = df['icen_pulso'] - df['icen_oficial']

    print(f'Meses comparables: {len(df)}\n')

    # --- Metricas globales ---
    r = float(np.corrcoef(df['icen_pulso'], df['icen_oficial'])[0, 1])
    sesgo = df['error'].mean()
    rmse = float(np.sqrt((df['error'] ** 2).mean()))

    # --- Sesgo de la ventana reciente: el que aplica al dato de HOY ---
    corte = df['fecha'].max() - pd.DateOffset(years=ANIOS_VENTANA_RECIENTE)
    reciente = df[df['fecha'] >= corte]
    sesgo_reciente = reciente['error'].mean()

    print('=== VALIDACION GLOBAL (1982 - hoy) ===')
    print(f'  Correlacion (r) : {r:.4f}')
    print(f'  Sesgo medio     : {sesgo:+.3f} C   <-- ENGAÑOSO por si solo')
    print(f'  RMSE            : {rmse:.3f} C')
    print(f'\n  Sesgo ULTIMOS {ANIOS_VENTANA_RECIENTE} AÑOS : '
          f'{sesgo_reciente:+.3f} C  (n={len(reciente)})')
    print('  El sesgo global promedia decadas de signo opuesto y sale casi')
    print('  nulo. El de la ventana reciente es el que corrige core_icen.py.\n')

    # --- Metricas por periodo: como deriva el sesgo ---
    print('=== SESGO POR PERIODO ===')
    print(f'{"PERIODO":>12} {"n":>5} {"r":>8} {"sesgo":>8} {"RMSE":>8}')
    cortes = [(1982, 1999), (2000, 2019), (2020, 2024), (2025, 2026)]
    for ini, fin in cortes:
        tramo = df[(df.anio >= ini) & (df.anio <= fin)]
        if len(tramo) < 3:
            continue
        r_t = float(np.corrcoef(tramo['icen_pulso'], tramo['icen_oficial'])[0, 1])
        print(f'{ini}-{fin:>4} {len(tramo):>5} {r_t:>8.3f} '
              f'{tramo["error"].mean():>+8.3f} '
              f'{np.sqrt((tramo["error"] ** 2).mean()):>8.3f}')

    # --- Ultimos 18 meses, mes a mes ---
    print('\n=== ULTIMOS 18 MESES (el detalle que importa) ===')
    print(f'{"FECHA":>8} {"Pulso":>8} {"OFICIAL":>9} {"ERROR":>8}')
    for _, f in df.tail(18).iterrows():
        print(f'{f["fecha"]:%Y-%m} {f["icen_pulso"]:>8.2f} '
              f'{f["icen_oficial"]:>9.2f} {f["error"]:>+8.2f}')

    # --- Grafico de validacion ---
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

        ax1.plot(df['fecha'], df['icen_oficial'], lw=1.6, color='#c0392b',
                 label='ICEN oficial (IGP / ENFEN)')
        ax1.plot(df['fecha'], df['icen_pulso'], lw=1.2, color='#1f3a5f',
                 ls='--', label='ICEN reconstruido (Pulso)')
        # Umbral vigente (Nota Tecnica ENFEN 01-2024): las condiciones
        # calidas empiezan por encima de +0.5. La version anterior dibujaba
        # +0.4 —el umbral derogado de 2012— y ademas sin etiqueta, sobre un
        # grafico que compara justamente contra el indice oficial.
        ax1.axhline(0.5, ls=':', color='gray', lw=1,
                    label='Inicio condiciones calidas ENFEN 2024 (+0.5 °C)')
        ax1.set_ylabel('ICEN (°C)')
        ax1.set_title(
            f'VALIDACION EXTERNA — Pulso vs ICEN oficial\n'
            f'r = {r:.3f}  |  RMSE = {rmse:.2f} °C  |  n = {len(df)} meses\n'
            f'Sesgo global {sesgo:+.2f} °C (promedia decadas de signo '
            f'opuesto)  |  ultimos {ANIOS_VENTANA_RECIENTE} años '
            f'{sesgo_reciente:+.2f} °C',
            fontsize=10.5, loc='left')
        ax1.legend(fontsize=9)
        ax1.grid(alpha=0.2)

        ax2.axhline(0, color='black', lw=0.8)
        ax2.fill_between(df['fecha'], 0, df['error'],
                         color='#e67e22', alpha=0.7)
        ax2.set_ylabel('Error (°C)')
        ax2.set_xlabel('Año')
        ax2.set_title('El error DERIVA y cambia de signo: por eso el sesgo se '
                      'recalcula sobre la ventana reciente, no globalmente.',
                      fontsize=9, loc='left', color='#555555')
        ax2.grid(alpha=0.2)

        fig.tight_layout()
        salida = os.path.join(CARPETA_SALIDA, '3_validacion_icen.png')
        fig.savefig(salida, dpi=160)
        plt.close(fig)
        print(f'\nGrafico: {salida}')
        print('  ESTA FIGURA SE MUESTRA EN LA WEB. Copiala tambien a '
              'data/salidas/mapas/')
    except ImportError:
        pass

    print('\n=== LECTURA ===')
    if r > 0.9 and abs(sesgo_reciente) < 0.3:
        print('La FORMA de la serie coincide con la oficial (r alto) y el')
        print('sesgo reciente es pequeño y corregible. Se puede presentar,')
        print('siempre declarando que es una RECONSTRUCCION con OISST, no el')
        print('ICEN oficial (que usa ERSSTv5).')
    elif r > 0.9:
        print('La FORMA de la serie es correcta (r alto) pero hay SESGO')
        print('reciente relevante. Presenta la correlacion y DECLARA el')
        print('sesgo. No lo escondas.')
    else:
        print('Discrepancia estructural. NO presentar valores absolutos;')
        print('presentar solo la deteccion de eventos, que si es correcta.')


if __name__ == '__main__':
    main()
