# P.A.L.M.A.

**Plataforma Analítica del Litoral, Montes y Andes**
Sistema de Alerta Temprana ante El Niño Costero — Región Piura, Perú

---

## Qué es

Un sistema de alerta temprana que acopla el monitoreo satelital de tres
ecosistemas de Piura —litoral, bosque seco y páramo andino— para anticipar los
efectos del Fenómeno El Niño Costero.

Construido íntegramente sobre **datos abiertos**: NOAA OISST, USGS Landsat 8 y
la cartografía de ecosistemas del MINAM.

---

## El hallazgo

**El Niño de 2015-16 calentó más el mar que el de 2017. Y no causó desastre.**

| Evento | Pico SST | z(MSAVI) bosque seco | Resultado |
|---|---|---|---|
| El Niño 2015-16 | **+2.51 °C** | 1.36 | Sin desastre |
| Niño costero 2017 | +2.03 °C | **3.34** | Catástrofe · 3,468 m³/s |

El índice oficial (ICEN) clasificó 2015-16 como **FUERTE** y a 2017 como
**MODERADO**. Gritó más fuerte el año equivocado.

Ningún indicador puramente oceánico distingue un Niño peligroso de uno
inofensivo. **La confirmación territorial sí.**

---

## Arquitectura: alerta en dos etapas

**ETAPA 1 — Precursor oceánico** *(diario)*
Anomalía de TSM en la región Niño 1+2 (NOAA OISST, 1982–2026) con criterio de
persistencia. Sola, tiene **11 % de precisión**: 31 falsas alarmas en 35
episodios.

**ETAPA 2 — Confirmación territorial** *(mensual)*
El vigor vegetal del bosque seco (MSAVI, Landsat 8) responde a la anomalía
oceánica con un desfase de **+1 mes** (r = 0.512 · n = 160 · p < 0.0001). Mide
si el agua **efectivamente aterrizó** en el territorio.

> El mar dice "viene". El bosque seco confirma "está aquí".

**Combinadas: 100 % de precisión sobre 35 episodios (1982–2026).**

---

## Validación

- **ICEN reconstruido** desde datos crudos con la metodología oficial de ENFEN.
  Contrastado contra la serie del IGP: **r = 0.9713** (n = 532 meses).
- **Backtest sobre eventos reales**: 1983, 1998, 2017 y 2023.

---

## Limitaciones (declaradas)

- La Etapa 2 solo pudo probarse sobre **dos eventos** (2017 y 2023): Landsat 8
  inicia operaciones en 2013. **Es una prueba de concepto, no una validación
  estadística.**
- Los umbrales se calibraron observando estos mismos datos: **hay sobreajuste**.
  Lo defendible es el margen — los no-desastres alcanzan z = 1.36 y los
  desastres arrancan en z = 3.34, sin solape.
- El ciclón Yaku (2023) fue un evento sinóptico rápido; la Etapa 2 confirmó
  **después** del desastre. El sistema detecta El Niño costero, no ciclones.

## Hallazgos negativos

Ambos contradicen la hipótesis inicial del proyecto, y se reportan igual:

1. **El páramo no responde** a la anomalía oceánica. Su correlograma es plano:
   está saturado todo el año. No es un receptor de la señal, es un **regulador**.
2. **La superficie del reservorio de Poechos no sirve como proxy hidrológico**:
   está dominada por decisiones de operación humana, no por la lluvia.

---

## Relación con ENFEN

P.A.L.M.A. **no compite con el ENFEN ni pretende adelantarse a él.** El ENFEN
opera un sistema de alerta propio y mantiene el estado de "Alerta de El Niño
Costero" desde marzo de 2026. Nuestro sistema detectó ese mismo episodio el
1 de marzo de 2026, de forma independiente: **coincidimos con la autoridad
nacional**.

El aporte está en la Etapa 2 — la capa que hoy no existe.

---

## Uso

```bash
pip install -r requirements.txt
streamlit run app_palma.py
```

Las series ya están descargadas en `datos/`. Para reconstruirlas desde cero:

```bash
python construir_series.py          # SST mensual + vegetación
python construir_serie_diaria.py    # SST diaria (~16,400 días)
python construir_reservorios.py     # superficie de embalses
python verificar_datos.py           # auditoría de integridad
python core_alerta.py               # motor de dos etapas
python backtest_fen.py              # reconstrucción del ICEN
python validar_icen.py              # validación vs. índice oficial
```

Requiere una cuenta de Google Earth Engine para el mapa. **Sin conexión, cuatro
de las cinco pestañas siguen operativas**: leen de los CSV locales.

---

## Fuentes

- **NOAA OISST v2.1** — temperatura superficial del mar, diaria, desde 1981
- **USGS Landsat 8 Collection 2 Level 2** — reflectancia de superficie, 30 m
- **MINAM** — Mapa Nacional de Ecosistemas 2022
- **IGP / ENFEN** — Índice Costero El Niño (ICEN), serie oficial

---

Proyecto desarrollado para la **Feria de Ingeniería de Sistemas e Informática —
ODS e Innovación**, UTP Piura 2026.
