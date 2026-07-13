# --- ID del proyecto de Google Earth Engine ---
PROYECTO_ID = 'monitor-bosqueseco'

RUTAS_ASSETS = {
    # --- Base de Datos Oficial (ZEE 2013) ---
    'limite': 'projects/monitor-bosqueseco/assets/limite_piura_corregido',
    'vegetacion': 'projects/monitor-bosqueseco/assets/cobertura_vegetal',
    'rios': 'projects/monitor-bosqueseco/assets/red_hidrografica',
    'reservorios': 'projects/monitor-bosqueseco/assets/reservorios_piura',
    'peligros_fen': 'projects/monitor-bosqueseco/assets/peligros_multiples',
    'inundaciones': 'projects/monitor-bosqueseco/assets/inundacion_historica',
    'zee_oficial': 'projects/monitor-bosqueseco/assets/zee_macrozonificacion',
    
    # --- Base de Datos MINAM (Ecosistemas 2022) ---
    'ecosistemas_2022': 'projects/monitor-bosqueseco/assets/ecosistemas_piura_2022'
}

# --- Zonas Estratégicas: (latitud, longitud, nivel_zoom) ---
ZONAS_ESTRATEGICAS = {
    'LITORAL': {
        'Paita':    (-5.0892, -81.1144, 11),
        'Sechura':  (-5.5570, -80.8222, 11),
        'Talara':   (-4.5806, -81.2703, 11),
        'Colán':    (-5.0167, -81.0833, 12),
    },
    'MONTES': {
        'Morropón':  (-5.1892, -79.9767, 11),
        'Chulucanas':(-5.0942, -80.1614, 11),
        'La Matanza':(-5.1667, -80.1833, 12),
        'Tambo Grande': (-4.9500, -80.3333, 11),
    },
    'ANDES': {
        'Ayabaca':      (-4.6367, -79.7167, 11),
        'Huancabamba':  (-5.2333, -79.4500, 11),
        'Pacaipampa':   (-4.9500, -79.5667, 11),
        'Canchaque':    (-5.3667, -79.6167, 12),
    },
}