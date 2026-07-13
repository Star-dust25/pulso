# ui_manager.py
# ============================================================
# SISTEMA DE DISEÑO DE P.A.L.M.A.
#
# Estetica: institucional peruana. Sobria, densa en informacion,
# sin decoracion. Referencias: gob.pe, SENAMHI, ENFEN.
#
# REGLAS DURAS:
#   - Cero emojis. Iconos SVG vectoriales, siempre.
#   - Cero sombras, cero gradientes, cero bordes redondeados grandes.
#   - Reglas finas (1px) para separar. El espacio en blanco separa.
#   - Los NUMEROS van en monoespaciada. Un dato es un dato.
#   - El color solo significa estado. Nunca decora.
#
# ============================================================
# REGLA TECNICA CRITICA (esto rompio la app la primera vez):
#
# Streamlit pasa el string por el parser de Markdown ANTES de renderizar
# el HTML. Markdown tiene dos reglas que destruyen el resultado:
#
#   1. Una LINEA EN BLANCO cierra el bloque HTML -> lo que sigue se
#      imprime como texto plano.
#   2. Una INDENTACION de 4+ espacios -> se interpreta como bloque de
#      codigo y se muestra el HTML crudo.
#
# Por eso TODO el HTML de este archivo se emite PEGADO A LA IZQUIERDA
# y SIN LINEAS EN BLANCO. No es descuido de formato: es obligatorio.
# ============================================================

# ------------------------------------------------------------
# TOKENS
# ------------------------------------------------------------

OLIVA_PROFUNDO = '#1A2517'      # fondo
SALVIA_SUAVE = '#ACC8A2'        # acento primario

SUPERFICIE = '#212E1D'          # tarjetas
SUPERFICIE_ALTA = '#2A3826'
BORDE = '#33422D'
BORDE_FUERTE = '#4A5C42'

TEXTO = '#E8F0E4'
TEXTO_TENUE = '#9AAF93'
TEXTO_DEBIL = '#6B7A66'

# Semanticos: el color SOLO comunica estado
ROJO = '#C0392B'                # alerta / critico
AMBAR = '#D68910'               # vigilancia
VERDE = SALVIA_SUAVE            # normal / confirmado
AZUL = '#5B8FA8'                # dato oceanico

# ------------------------------------------------------------
# TIPOGRAFIA
# ------------------------------------------------------------
# Tres familias, cada una con un trabajo:
#
#   DISPLAY  Space Grotesk  -> titulos. Grotesca tecnica, con caracter.
#                             No es una fuente de sistema mas: se lee como
#                             instrumento, no como pagina web generica.
#   SANS     IBM Plex Sans  -> cuerpo. Diseñada por IBM para productos
#                             tecnicos e institucionales: tiene voz propia
#                             sin dejar de ser sobria.
#   MONO     IBM Plex Mono  -> datos. Misma familia: coherencia total.
#
# Se descarto Inter: es excelente, pero deliberadamente neutro, y por eso
# esta en todas partes. Un sistema de alerta necesita identidad.

DISPLAY = "'Space Grotesk','Segoe UI',system-ui,sans-serif"
SANS = "'IBM Plex Sans','Segoe UI',system-ui,sans-serif"
MONO = "'IBM Plex Mono','SF Mono','Consolas',monospace"

# ------------------------------------------------------------
# ESCALA TIPOGRAFICA
# ------------------------------------------------------------
# Calibrada para LECTURA A DISTANCIA. En una feria el jurado esta de pie,
# a uno o dos metros de la pantalla. Un dato que no se lee desde ahi no
# existe. Todos los tamaños subieron ~25% respecto a la version anterior.

T_TITULO = '34px'       # titular de la plataforma
T_SUBTITULO = '16px'    # bajada del titular
T_SECCION = '19px'      # titulo de seccion
T_BAJADA = '15.5px'     # texto bajo un titulo de seccion
T_CIFRA_XL = '46px'     # el numero protagonista de una etapa
T_CIFRA_L = '28px'      # cifra de una tarjeta de dato
T_CUERPO = '15px'       # parrafos
T_CUERPO_S = '14.5px'   # parrafos densos (notas, ODS)
T_ETIQUETA = '11.5px'   # etiquetas en monoespaciada (mayusculas)
T_SELLO = '12px'        # sello institucional
T_PIE = '11px'


# ------------------------------------------------------------
# ICONOS SVG (stroke, 24x24). Nunca emojis.
# ------------------------------------------------------------

_ICONOS = {
    'oceano': '<path d="M2 12c2 0 3-2 5-2s3 2 5 2 3-2 5-2 3 2 5 2M2 17c2 0 3-2 5-2s3 2 5 2 3-2 5-2 3 2 5 2M2 7c2 0 3-2 5-2s3 2 5 2 3-2 5-2 3 2 5 2"/>',
    'bosque': '<path d="M12 2L7 10h3l-4 6h5v6h2v-6h5l-4-6h3z"/>',
    'alerta': '<path d="M12 3L2 20h20L12 3z"/><path d="M12 9v5M12 17h.01"/>',
    'confirmado': '<path d="M20 6L9 17l-5-5"/>',
    'reloj': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'escudo': '<path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/>',
    'grafico': '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    'mapa': '<path d="M9 4L3 7v13l6-3 6 3 6-3V4l-6 3z"/><path d="M9 4v13M15 7v13"/>',
    'satelite': '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    'flecha': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'punto': '<circle cx="12" cy="12" r="5"/>',
}


def icono(nombre, color='currentColor', tam=18, grosor=1.6):
    cuerpo = _ICONOS.get(nombre, _ICONOS['punto'])
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" '
            f'stroke-linejoin="round" style="vertical-align:-3px;">{cuerpo}</svg>')


# ------------------------------------------------------------
# CSS GLOBAL
# ------------------------------------------------------------

def estilos_globales():
    """
    Inyectar UNA sola vez, al inicio de app_palma.py.

    LECCION APRENDIDA (tres intentos fallidos, documentados para no repetirlos):

      1. 'header{visibility:hidden}'  -> mata el boton de la barra lateral.
      2. 'header{height:0}'           -> lo mismo, ademas tapa el contenido.
      3. '[data-testid="stToolbar"]{display:none}' -> el toolbar CONTIENE el
         boton de la barra lateral junto al de Deploy. Ocultarlo se los lleva
         a los tres por delante.

    REGLA: no se oculta NINGUN contenedor del header. Se camufla con el color
    del fondo y se ocultan SOLO los elementos concretos que sobran.
    """
    css = (
        f'html,body,[class*="css"]{{font-family:{SANS};}}'
        f'h1,h2,h3{{font-family:{DISPLAY};}}'
        f'.block-container{{padding-top:3.6rem;max-width:1400px;}}'
        f'header[data-testid="stHeader"]{{background:{OLIVA_PROFUNDO};}}'
        f'[data-testid="stDecoration"]{{display:none;}}'
        f'[data-testid="stAppDeployButton"]{{display:none;}}'
        f'#MainMenu{{visibility:hidden;}}'
        f'footer{{visibility:hidden;}}'
        f'[data-testid="stSidebarCollapsedControl"],'
        f'[data-testid="collapsedControl"]{{display:flex !important;'
        f'visibility:visible !important;opacity:1 !important;}}'
        f'[data-testid="stSidebarCollapsedControl"] svg,'
        f'[data-testid="collapsedControl"] svg{{color:{SALVIA_SUAVE} !important;'
        f'fill:{SALVIA_SUAVE} !important;}}'
        # Pestañas: mas grandes, legibles a distancia
        f'.stTabs [data-baseweb="tab-list"]{{gap:0;'
        f'border-bottom:1px solid {BORDE};background:transparent;}}'
        f'.stTabs [data-baseweb="tab"]{{height:50px;padding:0 24px;'
        f'background:transparent;border-bottom:2px solid transparent;'
        f'border-radius:0;color:{TEXTO_TENUE};font-family:{DISPLAY};'
        f'font-size:15px;font-weight:600;letter-spacing:0.03em;}}'
        f'.stTabs [aria-selected="true"]{{color:{SALVIA_SUAVE};'
        f'border-bottom:2px solid {SALVIA_SUAVE};background:transparent;}}'
        f'.num{{font-family:{MONO};font-variant-numeric:tabular-nums;}}'
        # Barra lateral: etiquetas y opciones legibles
        f'section[data-testid="stSidebar"]{{background:{OLIVA_PROFUNDO};'
        f'border-right:1px solid {BORDE};}}'
        f'section[data-testid="stSidebar"] label{{font-size:14.5px !important;}}'
        f'section[data-testid="stSidebar"] .stRadio label p{{'
        f'font-size:14.5px !important;}}'
        f'.stButton>button{{border-radius:2px;border:1px solid {BORDE_FUERTE};'
        f'background:transparent;color:{TEXTO};font-family:{DISPLAY};'
        f'font-weight:600;font-size:13px;letter-spacing:0.05em;padding:8px 0;}}'
        f'.stButton>button:hover{{border-color:{SALVIA_SUAVE};'
        f'color:{SALVIA_SUAVE};}}'
        # Tablas anchas: scroll horizontal en vez de desbordar
        f'.tabla-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;}}'
        # --------------------------------------------------------
        # RESPONSIVE
        # Streamlit apila solas las st.columns por debajo de ~640px, pero
        # NUESTRO html (flex) no: hay que decirle que envuelva. Y los tamaños
        # calibrados para leer a 2 m en una pantalla grande son excesivos en
        # un movil de 6 pulgadas sostenido a 30 cm.
        # --------------------------------------------------------
        f'@media (max-width:820px){{'
        f'.block-container{{padding-left:1rem;padding-right:1rem;}}'
        f'.stTabs [data-baseweb="tab"]{{padding:0 14px;font-size:13px;'
        f'height:44px;}}'
        f'.fila-flex{{flex-wrap:wrap;}}'
        f'.col-dato{{min-width:100% !important;text-align:left !important;'
        f'margin-top:8px;}}'
        f'.pie-flex{{flex-direction:column;align-items:flex-start;gap:6px;}}'
        f'}}'
    )
    fuentes = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
               '<link href="https://fonts.googleapis.com/css2?'
               'family=Space+Grotesk:wght@500;600;700&'
               'family=IBM+Plex+Sans:wght@400;500;600;700&'
               'family=IBM+Plex+Mono:wght@400;500;600&display=swap" '
               'rel="stylesheet">')
    return f'{fuentes}<style>{css}</style>'


# ------------------------------------------------------------
# COMPONENTES
# ------------------------------------------------------------

def cabecera(titulo, subtitulo,
             sello='PLATAFORMA ANALITICA DEL LITORAL, MONTES Y ANDES'):
    return (
        f'<div style="border-bottom:1px solid {BORDE};padding-bottom:18px;'
        f'margin-bottom:24px;">'
        f'<div style="font-family:{MONO};font-size:{T_SELLO};'
        f'letter-spacing:0.18em;color:{TEXTO_DEBIL};text-transform:uppercase;'
        f'margin-bottom:10px;font-weight:500;">{sello}</div>'
        f'<div style="font-family:{DISPLAY};font-size:clamp(24px,4.5vw,{T_TITULO});'
        f'font-weight:700;color:{TEXTO};letter-spacing:-0.015em;'
        f'line-height:1.12;">{titulo}</div>'
        f'<div style="font-size:{T_SUBTITULO};color:{TEXTO_TENUE};'
        f'margin-top:8px;max-width:860px;line-height:1.55;">{subtitulo}</div>'
        f'</div>'
    )


def banda_alerta(nivel, titulo, detalle):
    """nivel: 'rojo' | 'ambar' | 'verde'"""
    mapa = {
        'rojo': (ROJO, 'alerta', 'ALERTA'),
        'ambar': (AMBAR, 'reloj', 'VIGILANCIA'),
        'verde': (VERDE, 'confirmado', 'NORMAL'),
    }
    color, ic, etiqueta = mapa.get(nivel, mapa['ambar'])
    return (
        f'<div style="border:1px solid {color};border-left:4px solid {color};'
        f'background:{SUPERFICIE};padding:20px 24px;margin-bottom:20px;">'
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'margin-bottom:8px;">'
        f'{icono(ic, color, 20)}'
        f'<span style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.18em;color:{color};font-weight:600;">{etiqueta}</span>'
        f'</div>'
        f'<div style="font-family:{DISPLAY};font-size:21px;font-weight:600;'
        f'color:{TEXTO};margin-bottom:6px;line-height:1.25;">{titulo}</div>'
        f'<div style="font-size:{T_CUERPO};color:{TEXTO_TENUE};'
        f'line-height:1.6;">{detalle}</div></div>'
    )


def tarjeta_etapa(numero, nombre, icono_id, estado, valor, unidad,
                  umbral, activo, fuente):
    color = ROJO if activo else TEXTO_DEBIL
    borde = ROJO if activo else BORDE
    return (
        f'<div style="border:1px solid {borde};background:{SUPERFICIE};'
        f'padding:22px 24px;height:100%;">'
        f'<div style="display:flex;align-items:center;'
        f'justify-content:space-between;margin-bottom:16px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'{icono(icono_id, SALVIA_SUAVE, 20)}'
        f'<span style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.16em;color:{TEXTO_DEBIL};font-weight:500;">'
        f'ETAPA {numero}</span></div>'
        f'<span style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'font-weight:600;letter-spacing:0.1em;color:{color};'
        f'border:1px solid {color};padding:3px 10px;">{estado}</span></div>'
        f'<div style="font-family:{DISPLAY};font-size:17px;font-weight:600;'
        f'color:{TEXTO};margin-bottom:16px;">{nombre}</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;'
        f'margin-bottom:4px;">'
        f'<span class="num" style="font-size:clamp(34px,6vw,{T_CIFRA_XL});font-weight:600;'
        f'color:{TEXTO};line-height:1;">{valor}</span>'
        f'<span style="font-size:{T_SUBTITULO};color:{TEXTO_TENUE};">'
        f'{unidad}</span></div>'
        f'<div style="font-family:{MONO};font-size:13px;color:{TEXTO_DEBIL};'
        f'margin-bottom:16px;">umbral {umbral}</div>'
        f'<div style="border-top:1px solid {BORDE};padding-top:12px;'
        f'font-size:13px;color:{TEXTO_DEBIL};line-height:1.55;">{fuente}</div>'
        f'</div>'
    )


def dato(etiqueta, valor, nota=''):
    return (
        f'<div style="border-left:3px solid {BORDE};padding:2px 0 2px 14px;">'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.14em;color:{TEXTO_DEBIL};text-transform:uppercase;'
        f'font-weight:500;">{etiqueta}</div>'
        f'<div class="num" style="font-size:{T_CIFRA_L};font-weight:600;'
        f'color:{TEXTO};margin:5px 0 3px;line-height:1.15;">{valor}</div>'
        f'<div style="font-size:13px;color:{TEXTO_TENUE};line-height:1.5;">'
        f'{nota}</div></div>'
    )


def nota_metodologica(texto):
    """Para declarar limitaciones. Se lee como nota al pie oficial."""
    return (
        f'<div style="border-left:3px solid {BORDE_FUERTE};'
        f'padding:12px 0 12px 16px;margin-top:18px;">'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.16em;color:{TEXTO_DEBIL};margin-bottom:7px;'
        f'font-weight:500;">NOTA METODOLOGICA</div>'
        f'<div style="font-size:{T_CUERPO_S};color:{TEXTO_TENUE};'
        f'line-height:1.65;">{texto}</div></div>'
    )


def leyenda(ecosistema):
    escalas = {
        'LITORAL': [
            (ROJO, '28 °C +', 'Anomalia termica (FEN)'),
            (AMBAR, '25 °C', 'Aguas calidas'),
            (AZUL, '23 °C', 'Transicion'),
            ('#2C5D73', '19 °C', 'Corriente de Humboldt'),
        ],
        'MONTES': [
            (SALVIA_SUAVE, '0.60 +', 'Bosque denso'),
            ('#7D9E73', '0.30', 'Vegetacion dispersa'),
            ('#B08D57', '0.10', 'Estres hidrico'),
            ('#8C6D46', '0.00', 'Suelo desnudo'),
        ],
        'ANDES': [
            ('#2C5D73', '0.40', 'Saturacion maxima'),
            (AZUL, '0.20', 'Humedad optima'),
            (AMBAR, '0.00', 'Suelo seco'),
            (ROJO, '-0.20', 'Estres severo'),
        ],
    }
    filas = ''
    for color, valor, desc in escalas.get(ecosistema, []):
        filas += (
            f'<div style="display:flex;align-items:center;gap:11px;'
            f'margin-bottom:9px;">'
            f'<div style="width:14px;height:14px;background:{color};'
            f'flex-shrink:0;"></div>'
            f'<span class="num" style="font-size:13.5px;color:{TEXTO};'
            f'min-width:58px;font-weight:600;">{valor}</span>'
            f'<span style="font-size:13px;color:{TEXTO_TENUE};">{desc}</span>'
            f'</div>'
        )
    return (
        f'<div style="border:1px solid {BORDE};background:{SUPERFICIE};'
        f'padding:16px;">'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.16em;color:{TEXTO_DEBIL};margin-bottom:12px;'
        f'font-weight:500;">ESCALA ESPECTRAL</div>{filas}</div>'
    )


def separador(alto=16):
    return f'<div style="height:{alto}px;"></div>'


def titulo_seccion(titulo, bajada=''):
    html = (f'<div style="font-family:{DISPLAY};font-size:{T_SECCION};'
            f'font-weight:600;color:{TEXTO};margin-bottom:8px;'
            f'letter-spacing:-0.01em;">{titulo}</div>')
    if bajada:
        html += (f'<div style="font-size:{T_BAJADA};color:{TEXTO_TENUE};'
                 f'margin-bottom:16px;line-height:1.6;max-width:960px;">'
                 f'{bajada}</div>')
    return html


def pie_institucional():
    return (
        f'<div class="pie-flex" style="border-top:1px solid {BORDE};'
        f'margin-top:40px;padding-top:16px;display:flex;'
        f'justify-content:space-between;align-items:center;'
        f'font-family:{MONO};font-size:{T_PIE};letter-spacing:0.12em;'
        f'color:{TEXTO_DEBIL};">'
        f'<span>P.A.L.M.A. · REGION PIURA</span>'
        f'<span>FUENTES: NOAA OISST V2.1 · USGS LANDSAT 8 C2 L2 · '
        f'MINAM ECOSISTEMAS 2022 · IGP/ENFEN</span></div>'
    )


def tabla_comparativa():
    """
    Comparativa 2015 vs 2017. HTML propio en vez de st.dataframe:
    el componente nativo trae su propia paleta y rompe la estetica.
    """
    filas = [
        ('El Niño 2015-16', '+2.51 °C', '1.36', 'NO confirma',
         'Sin desastre', TEXTO_DEBIL),
        ('Niño costero 2017', '+2.03 °C', '3.34', 'CONFIRMA',
         'Catastrofe', ROJO),
    ]
    cab = ''.join(
        f'<th style="text-align:left;padding:12px 16px;font-family:{MONO};'
        f'font-size:{T_ETIQUETA};letter-spacing:0.14em;color:{TEXTO_DEBIL};'
        f'font-weight:500;border-bottom:1px solid {BORDE};">{h}</th>'
        for h in ('EVENTO', 'PICO SST', 'z(MSAVI)', 'ETAPA 2', 'RESULTADO'))
    cuerpo = ''
    for ev, sst, z, e2, res, color in filas:
        cuerpo += (
            f'<tr>'
            f'<td style="padding:14px 16px;font-size:{T_CUERPO};color:{TEXTO};'
            f'border-bottom:1px solid {BORDE};font-weight:500;">{ev}</td>'
            f'<td class="num" style="padding:14px 16px;font-size:{T_CUERPO};'
            f'color:{TEXTO};border-bottom:1px solid {BORDE};">{sst}</td>'
            f'<td class="num" style="padding:14px 16px;font-size:{T_CUERPO};'
            f'color:{TEXTO};border-bottom:1px solid {BORDE};">{z}</td>'
            f'<td style="padding:14px 16px;font-family:{MONO};'
            f'font-size:13px;color:{color};border-bottom:1px solid {BORDE};'
            f'font-weight:600;">{e2}</td>'
            f'<td style="padding:14px 16px;font-size:{T_CUERPO};color:{color};'
            f'border-bottom:1px solid {BORDE};font-weight:600;">{res}</td>'
            f'</tr>')
    return (f'<div class="tabla-wrap">'
            f'<table style="width:100%;min-width:640px;border-collapse:collapse;'
            f'border:1px solid {BORDE};background:{SUPERFICIE};">'
            f'<thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table>'
            f'</div>')


# ------------------------------------------------------------
# COMPONENTES ODS
# ------------------------------------------------------------
# Los colores oficiales de la ONU se usan SOLO como identificador
# institucional (una regla lateral fina), nunca como decoracion.
# Un jurado reconoce el ODS de un vistazo sin que rompamos la paleta.

COLORES_ODS = {
    6: '#26BDE2',    # Agua limpia y saneamiento
    13: '#3F7E44',   # Accion por el clima
    14: '#0A97D9',   # Vida submarina
    15: '#56C02B',   # Vida de ecosistemas terrestres
}


def tarjeta_ods(numero, nombre, meta, contribucion, evidencia,
                principal=False):
    """
    Tarjeta de un ODS.
    'evidencia' debe ser un DATO MEDIDO por el sistema, no una promesa.
    Es lo unico que distingue una alineacion real de una lista de logos.
    """
    color = COLORES_ODS.get(numero, SALVIA_SUAVE)
    etiqueta = 'ODS PRINCIPAL' if principal else 'ODS SECUNDARIO'
    borde = f'2px solid {color}' if principal else f'1px solid {BORDE}'
    return (
        f'<div style="border:{borde};border-left:5px solid {color};'
        f'background:{SUPERFICIE};padding:20px 24px;margin-bottom:14px;'
        f'height:100%;">'
        f'<div style="display:flex;align-items:center;'
        f'justify-content:space-between;margin-bottom:12px;">'
        f'<span style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.16em;color:{TEXTO_DEBIL};font-weight:500;">'
        f'{etiqueta}</span>'
        f'<span class="num" style="font-size:13px;font-weight:600;'
        f'color:{color};border:1px solid {color};padding:2px 9px;">'
        f'ODS {numero}</span></div>'
        f'<div style="font-family:{DISPLAY};font-size:19px;font-weight:600;'
        f'color:{TEXTO};margin-bottom:14px;">{nombre}</div>'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.12em;color:{TEXTO_DEBIL};margin-bottom:5px;">'
        f'META</div>'
        f'<div style="font-size:{T_CUERPO_S};color:{TEXTO_TENUE};'
        f'line-height:1.6;margin-bottom:14px;">{meta}</div>'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.12em;color:{TEXTO_DEBIL};margin-bottom:5px;">'
        f'CONTRIBUCION DE P.A.L.M.A.</div>'
        f'<div style="font-size:{T_CUERPO_S};color:{TEXTO};line-height:1.6;'
        f'margin-bottom:14px;">{contribucion}</div>'
        f'<div style="border-top:1px solid {BORDE};padding-top:12px;">'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.14em;color:{color};margin-bottom:5px;'
        f'font-weight:600;">EVIDENCIA MEDIDA</div>'
        f'<div class="num" style="font-size:{T_CUERPO};color:{TEXTO};'
        f'font-weight:600;line-height:1.5;">{evidencia}</div></div>'
        f'</div>'
    )


def paso_decision(numero, momento, actor, accion, dato):
    """Un eslabon de la cadena de decision. Quien, cuando, con que dato."""
    return (
        f'<div class="fila-flex" style="display:flex;gap:18px;padding:16px 0;'
        f'border-bottom:1px solid {BORDE};">'
        f'<div class="num" style="font-size:26px;font-weight:600;'
        f'color:{SALVIA_SUAVE};min-width:32px;line-height:1.1;">{numero}</div>'
        f'<div style="flex:1;min-width:260px;">'
        f'<div style="font-family:{MONO};font-size:{T_ETIQUETA};'
        f'letter-spacing:0.14em;color:{TEXTO_DEBIL};margin-bottom:5px;">'
        f'{momento}</div>'
        f'<div style="font-family:{DISPLAY};font-size:16px;font-weight:600;'
        f'color:{TEXTO};margin-bottom:4px;">{actor}</div>'
        f'<div style="font-size:{T_CUERPO_S};color:{TEXTO_TENUE};'
        f'line-height:1.6;">{accion}</div></div>'
        f'<div class="col-dato" style="min-width:180px;text-align:right;">'
        f'<div class="num" style="font-size:13.5px;color:{SALVIA_SUAVE};'
        f'font-weight:600;line-height:1.5;">{dato}</div></div>'
        f'</div>'
    )