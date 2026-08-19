# ============================================================
# config_ecosistemas.py
# ============================================================
# Parametros de seleccion de ecosistemas y de muestreo espacial.
#
# Los valores de ECO_ANDES, ECO_MONTES y ECO_EXCLUIDOS_MONTES estan
# copiados literalmente del campo ECO_REGION del asset
# 'ecosistemas_piura_2022', leidos directamente de la tabla de
# atributos del shapefile original (20221129_MINAM_ECOSISTEMAS.shp).
#
# Fuente del mapa: Gobierno Regional de Piura, elaborado en 2022 con la
# metodologia y asistencia tecnica del MINAM. Aprobado por Ordenanza
# Regional N° 492-2023/GRP-CR.
#
# Cualquier cambio en estas cadenas debe verificarse contra el asset:
# si un nombre no coincide exactamente (incluidas las tildes), el filtro
# devuelve una coleccion vacia sin lanzar error.
# ============================================================

CAMPO_ECOSISTEMA = 'ECO_REGION'

# --- ANDES: unidad hidrológica de cabecera ---
# Incluimos Bofedal ademas de Paramo: el bofedal es el humedal altoandino
# que regula el almacenamiento hidrico. Excluirlo de un analisis de
# "retencion hidrica" seria un error metodologico.
ECO_ANDES = [
    'Páramo',
    'Bofedal',
]

# --- ANDES ampliado (opcional, zona de amortiguamiento) ---
ECO_ANDES_AMPLIADO = ECO_ANDES + [
    'Pastizal',
    'Matorral andino',
]

# --- MONTES: bosque seco de la vertiente occidental ---
# EXCLUIMOS deliberadamente 'Bosque estacionalmente seco interandino
# (Chinchipe)': pertenece a la vertiente oriental y responde a un regimen
# climatico distinto (cuenca amazonica), no al pulso pluvial del FEN costero.
# Incluirlo contaminaria la serie temporal.
ECO_MONTES = [
    'Bosque estacionalmente seco de llanura',
    'Bosque estacionalmente seco de lomadas',
    'Bosque estacionalmente seco de colina',
    'Bosque estacionalmente seco de montaña',
    'Bosque estacionalmente seco ribereño (Algarrobal)',
]

ECO_EXCLUIDOS_MONTES = [
    'Bosque estacionalmente seco interandino (Chinchipe)',  # vertiente oriental
]

# --- LITORAL: regiones oceanicas de referencia ---
# Niño 1+2 (90°-80°W, 10°S-0°) es la region sobre la que se calcula el
# ICEN (Indice Costero El Niño), el indice que el ENFEN usa oficialmente
# para el monitoreo de El Niño y La Niña frente a la costa peruana y que
# mantiene el IGP. Usarla nos alinea con la autoridad nacional en vez de
# inventar una caja arbitraria.
REGION_NINO_1_2 = (-90.0, -10.0, -80.0, 0.0)   # (oeste, sur, este, norte)

# Caja local frente a Piura: senal costera de alta resolucion.
# El borde este cae sobre tierra firme en parte del recorrido; no afecta
# el promedio porque OISST enmascara los pixeles continentales.
REGION_MAR_PIURA = (-81.6, -6.2, -80.5, -4.0)

# Escala de muestreo de la SST, en metros.
# OISST tiene resolucion nativa de 0.25 grados (~27.8 km); aqui se usa
# un valor redondeado de 25 km.
ESCALA_SST = 25000

# Escalas de muestreo para las series de vegetacion.
# Paramo es pequeno -> escala fina. Bosque seco es enorme -> escala gruesa
# para que la serie de ~150 meses no reviente el presupuesto de EE.
# Nota: al usar escalas distintas, los valores z de ANDES y MONTES no son
# estrictamente comparables entre si; cada zona se compara con su propia
# climatologia.
ESCALA_ANDES = 60
ESCALA_MONTES = 200

# Tolerancia de simplificacion de geometrias (metros).
# Reduce el numero de vertices para bajar el costo de computo en Earth
# Engine. El efecto de esta simplificacion sobre la media regional no ha
# sido cuantificado; es una decision de rendimiento, no un resultado medido.
TOLERANCIA_SIMPLIFICACION = 500