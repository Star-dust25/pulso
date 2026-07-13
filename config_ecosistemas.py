# ============================================================
# BLOQUE A AÑADIR AL FINAL DE config.py
# ============================================================
# Valores tomados literalmente del campo ECO_REGION del asset
# 'ecosistemas_piura_2022' (MINAM). Verificados con inspeccionar.py.
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
# NINO_1_2 es la region oficial que usa NOAA y que sustenta el ICEN de ENFEN
# (indice costero El Nino, el estandar peruano). Usarla nos alinea con la
# autoridad nacional en vez de inventar una caja arbitraria.
REGION_NINO_1_2 = (-90.0, -10.0, -80.0, 0.0)   # (oeste, sur, este, norte)

# Caja local frente a Piura: senal costera de alta resolucion.
REGION_MAR_PIURA = (-81.6, -6.2, -80.5, -4.0)

# Escala nativa de OISST (0.25 grados ~ 27.8 km)
ESCALA_SST = 25000

# Escalas de muestreo para las series de vegetacion.
# Paramo es pequeno -> escala fina. Bosque seco es enorme -> escala gruesa
# para que la serie de ~150 meses no reviente el presupuesto de EE.
ESCALA_ANDES = 60
ESCALA_MONTES = 200

# Tolerancia de simplificacion de geometrias (metros).
# Reduce vertices sin alterar la media regional de forma apreciable.
TOLERANCIA_SIMPLIFICACION = 500