# Pulso

**Plataforma Analítica del Litoral, Montes y Andes**
Sistema de Alerta Temprana ante El Niño Costero — Región Piura, Perú

---

## Qué es

Un sistema de alerta temprana que acopla el monitoreo satelital de la costa y
el bosque seco de Piura para anticipar los efectos del Fenómeno El Niño
Costero.

Construido íntegramente sobre **datos abiertos**: NOAA OISST, USGS Landsat 8,
la cartografía de ecosistemas del MINAM y el registro de emergencias del
INDECI publicado en la Plataforma Nacional de Datos Abiertos.

---

## El hallazgo

**El Niño de 2015-16 calentó más el mar que el de 2017. El daño fue veinte
veces menor.**

| Evento | Pico SST | z(MSAVI) bosque seco | Damnificados | Resultado |
|---|---|---|---|---|
| El Niño 2015-16 | **+2.51 °C** | 1.36 | 3,214 | Desastre menor |
| Niño costero 2017 | +2.03 °C | **3.34** | 72,965 | Catástrofe · 3,468 m³/s |

El índice oficial (ICEN) clasificó 2015-16 como **FUERTE** (2.23, pico de
octubre 2015) y a 2017 como **MODERADO** (1.31, pico de marzo 2017). Gritó más
fuerte el año equivocado.

El contraste es de magnitud, no de ocurrencia: en 2015 sí hubo daño. Lo que
ningún indicador puramente oceánico anticipa es la **escala** de ese daño.
**La confirmación territorial sí.**

---

## Arquitectura: alerta en dos etapas

**ETAPA 1 — Precursor oceánico** *(diario)*
Anomalía de TSM en la región Niño 1+2 (NOAA OISST, 1982–2026) con criterio de
persistencia: 15 días sostenidos sobre +0.4 °C. Es un parámetro operativo
propio de Pulso sobre la anomalía diaria — **no es el criterio del ICEN
oficial**, que opera sobre medias móviles mensuales.

Sola, la Etapa 1 es un mal predictor: **16 % de precisión**, con 27 falsas
alarmas sobre 32 episodios evaluables.

**ETAPA 2 — Confirmación territorial** *(mensual)*
El vigor vegetal del bosque seco (MSAVI, Landsat 8) responde a la anomalía
oceánica con un desfase de **+1 mes** (r = 0.512 · n = 160 · p < 0.0001). El
desfase no se asumió: se obtuvo probando trece desfases y conservando el de
relación más fuerte. Mide si el agua **efectivamente aterrizó** en el
territorio.

> El mar dice "viene". El bosque seco confirma "está aquí".

### Matriz de confusión (36 episodios: 32 evaluables, 1 en curso, 3 excluidos)

| | Aciertos | Falsas alarmas | Perdidos | Precisión |
|---|---|---|---|---|
| Solo Etapa 1 (océano) | 5 | 27 | 0 | **16 %** |
| Etapa 1 + Etapa 2 | 3 | 0 | 2 | **100 %** |

La Etapa 2 rechazó las 27 falsas alarmas, **pero perdió 2 eventos con daño
registrado**. Es el intercambio de todo umbral: subirlo compra precisión y
paga con eventos no detectados. Se declara, no se esconde.

---

## Validación

**Contra el índice oficial.** Reconstruimos el ICEN desde datos satelitales
crudos aplicando el mismo criterio de cálculo (media móvil de 3 meses de la
anomalía de TSM en Niño 1+2) y lo contrastamos contra la serie del IGP:
**r = 0.9713** sobre **532 meses**.

*Nota metodológica:* el ENFEN calcula el ICEN oficial con ERSSTv5; Pulso lo
reconstruye con OISST v2.1, de resolución diaria. Es una reconstrucción
independiente, no una réplica. La correlación mide precisamente cuánto se
aproxima una a la otra.

**Backtest sobre eventos reales.** Anticipación de cada etapa respecto a la
fecha del desastre:

| Evento | Etapa 1 | Etapa 2 |
|---|---|---|
| FEN 1982-83 (01-may-1983) | +244 días | sin dato — Landsat 8 arranca en 2013 |
| FEN 1997-98 (01-mar-1998) | +320 días | sin dato — Landsat 8 arranca en 2013 |
| **Niño costero 2017** (27-mar-2017) | **+68 días** | **+26 días** (z = 3.34) |
| Ciclón Yaku 2023 (15-mar-2023) | +12 días | −17 días (confirmó después) |

Para 2017, el caso completo, el contraste con la regla oficial:

| | Anticipación |
|---|---|
| Regla ICEN (3 meses consecutivos) | **−5 días** (habría llegado tarde) |
| Etapa 1 · precursor diario | **+68 días** (alerta el 18-ene-2017) |
| Etapa 2 · confirmación territorial | **+26 días** (compuesto de feb-2017) |

Esta comparación **no es contra el ENFEN**. El ICEN es un índice de
diagnóstico, no de alerta: sirve para declarar oficialmente que hubo un Niño
costero. El propio ENFEN reconoció esa limitación y en 2015 creó un sistema de
alerta separado para no depender del criterio de los tres meses.

---

## Limitaciones (declaradas)

**La Etapa 2 solo alcanza a los eventos posteriores a 2013**, cuando Landsat 8
inicia operaciones. De las alertas rojas del histórico, **2017 es el único
desastre mayor donde ambas etapas operaron con dato real**: en 1982-83 y
1997-98 no existía el sensor, y 2023 quedó excluido de la matriz por cobertura
incompleta del registro SINPAD. **Es una prueba de concepto, no una validación
estadística.**

**Los umbrales se calibraron observando estos mismos datos: hay sobreajuste.**
Lo defendible no es el umbral sino el gradiente:

| Categoría | z(MSAVI) |
|---|---|
| Máximo sin daño registrado | 1.09 |
| Mínimo con daño registrado (2015) | 1.36 |
| Desastre mayor (2017) | 3.34 |
| Desastre mayor (2023) | 3.67 |

No hay solape entre los episodios con daño y los que no lo tuvieron. A más
señal, más daño.

**El sistema pierde dos eventos con daño real.** El 100 % de precisión no es
gratis:

| Evento | Pico SST | z(MSAVI) | Damnificados | Por qué se perdió |
|---|---|---|---|---|
| Mar-2008 | +0.90 °C | sin dato | 4,345 | Landsat 8 no existía |
| Abr-2015 | +2.51 °C | 1.36 | 3,214 | Por debajo del umbral de 1.5 |

El primero es una limitación de cobertura satelital; el segundo, una decisión
de umbral: 1.5 está por encima del mínimo observado con daño (1.36). Un
sistema de alerta debe declarar sus dos tipos de error, no solo uno.

**El ciclón Yaku (2023) fue un evento sinóptico rápido**; la Etapa 2 confirmó
después del desastre. El sistema detecta El Niño costero, no ciclones.

---

## Hallazgos negativos

Ambos contradicen la hipótesis inicial del proyecto, y se reportan igual:

1. **El páramo andino no responde** a la anomalía oceánica. Su correlograma es
   plano. La lectura más plausible es que su humedad, saturada durante buena
   parte del año, lo haga funcionar como regulador y no como receptor de la
   señal.
2. **La superficie del reservorio de Poechos no sirve como proxy
   hidrológico**: está dominada por decisiones de operación humana, no por la
   lluvia.

---

## Relación con ENFEN

Pulso **no compite con el ENFEN ni pretende adelantarse a él.** El ENFEN opera
un sistema de alerta propio y mantiene el estado de "Alerta de El Niño
Costero" desde marzo de 2026. Nuestro sistema detectó ese mismo episodio el
1 de marzo de 2026, de forma independiente: **coincidimos con la autoridad
nacional**.

El aporte está en la Etapa 2 — la capa que hoy no existe.

---

## Uso

**Backend** (FastAPI):

```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Frontend** (SvelteKit):

```bash
cd frontend
npm install
npm run dev
```

El frontend necesita saber dónde está el backend. Copia `.env.example` a
`.env` y ajusta:

```
PUBLIC_API_URL=http://127.0.0.1:8000
```

Las series ya están descargadas en `backend/data/datos/` y los mapas
pre-generados en `backend/data/salidas/mapas/`. **La interfaz funciona sin
conexión a Earth Engine**: lee de los CSV y de los PNG ya generados.

Para reconstruir los datos desde cero (requiere una cuenta de Google Earth
Engine), desde `backend/` y en este orden:

```bash
python scripts/construir_series.py        # SST mensual + vegetación
python scripts/construir_serie_diaria.py  # SST diaria (~16,400 días)
python scripts/construir_reservorios.py   # superficie de embalses
python scripts/construir_mapas.py         # mapas por ecosistema y periodo
python scripts/verificar_datos.py         # auditoría de integridad
python scripts/backtest_fen.py            # reconstrucción del ICEN
python scripts/validar_icen.py            # validación vs. índice oficial
```

Los mapas se regeneran a diario de forma automática mediante GitHub Actions
(`.github/workflows/mapas-diarios.yml`).

---

## Fuentes

- **NOAA OISST v2.1** — temperatura superficial del mar, diaria, desde 1981
- **USGS Landsat 8 Collection 2 Level 2** — reflectancia de superficie, 30 m
- **MINAM** — Mapa Nacional de Ecosistemas
- **INDECI (SINPAD)** — registro de emergencias, vía la Plataforma Nacional de
  Datos Abiertos (datosabiertos.gob.pe)
- **IGP / ENFEN** — Índice Costero El Niño (ICEN), serie oficial

Las categorías del ICEN siguen la **Nota Técnica ENFEN 01-2024** (ENFEN, 2024:
*Definición operacional de los eventos El Niño Costero y La Niña Costera en el
Perú*), vigente desde diciembre de 2024. La tabla vive en un único archivo,
`backend/config/config_icen.py`, con autocomprobación contra la serie oficial
del IGP.

---

Proyecto desarrollado para la **Datathon Ambiental Universitaria 2026**
(MINAM · Gobierno Regional de Piura · CIP Piura · Proyecto Bosque Seco).
