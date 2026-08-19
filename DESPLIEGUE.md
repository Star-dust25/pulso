# DESPLIEGUE — Pulso

Estado actual: **el sistema se ejecuta localmente**. No hay despliegue público.
Esta guía cubre cómo levantarlo, cómo regenerar los datos y cómo demostrarlo.

---

## Arquitectura

Dos servicios independientes:

| Servicio | Tecnología | Puerto |
|---|---|---|
| Backend | FastAPI (Python) | 8000 |
| Frontend | SvelteKit (Node) | 5173 |

El frontend consume el backend. Si el backend no está levantado, la interfaz
carga pero muestra el error de conexión: no se rompe, avisa.

---

## PASO 1 — Levantar el backend

```powershell
cd backend
python -m uvicorn main:app --reload
```

**Usa solo esta forma.** `python main.py` hace lo mismo (el archivo levanta
uvicorn al final), pero si lanzas las dos a la vez no sabrás cuál te está
respondiendo el navegador.

Al arrancar debe imprimir una línea como esta:

```
[static] /static/mapas -> ...\data\salidas\mapas  (11 PNG)
```

Si en su lugar dice `AVISO: no existe`, las imágenes darán 404. Ejecuta
`python scripts/construir_mapas.py`.

Comprueba que responde antes de seguir:

```
http://127.0.0.1:8000/api/alerta/estado
```

Debe devolver un JSON con `precursor`, `z_msavi`, `etapa1_activa` y
`ultimo_dato`. Mira esa última fecha: es hasta cuándo llegan los datos.

### El backend solo escucha en 127.0.0.1

Es lo correcto para desarrollo. Si necesitas verlo desde el móvil o desde otro
equipo durante una demostración:

```powershell
$env:PULSO_HOST="0.0.0.0"
python main.py
```

---

## PASO 2 — Levantar el frontend

En **otra** terminal, sin cerrar la anterior:

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`.

### Variable de entorno

El frontend necesita saber dónde está el backend. Copia `.env.example` a
`.env`:

```
PUBLIC_API_URL=http://127.0.0.1:8000
```

Si la variable falta, `src/lib/api.ts` cae de vuelta a `127.0.0.1:8000`, así
que en local funciona igual. Para cualquier otra máquina, hay que ponerla.

**SvelteKit no recarga el `.env` en caliente.** Si lo cambias, detén el
servidor y vuelve a levantarlo.

Si Vite arranca en un puerto distinto al 5173 (porque estaba ocupado), el CORS
del backend admite hasta el 5176. Más allá de eso hay que añadirlo en
`main.py`.

---

## Regenerar los datos

Requiere una cuenta de Google Earth Engine autenticada
(`earthengine authenticate`).

### Antes de nada: PYTHONPATH

**Ningún script del proyecto arranca sin esto.** Los encabezados dicen
`python construir_series.py`, pero ese comando falla desde cualquier
directorio: Python no encuentra `config`, `core` ni `config_ecosistemas`.

En PowerShell, **en cada ventana nueva**:

```powershell
$env:PYTHONPATH="C:\Users\<usuario>\pulso\backend;C:\Users\<usuario>\pulso\backend\config;C:\Users\<usuario>\pulso\backend\core"
```

Comprueba que funcionó:

```powershell
python -c "import ee; ee.Initialize(project='monitor-bosqueseco'); print(ee.Number(1).getInfo())"
```

Debe imprimir `1`.

### Si `pip` falla con "Unable to create process"

El `pip.exe` del entorno virtual lleva grabada la ruta con la que se creó. Si
renombraste la carpeta del proyecto, deja de funcionar. Solución:

```powershell
python -m pip install ...
```

`python -m pip` no depende de ese lanzador y funciona siempre.

### Orden de ejecución

Desde `backend/`, y **en este orden**, porque cada paso depende del anterior:

```powershell
python scripts/construir_series.py          # serie_sst.csv, serie_vegetacion.csv
python scripts/construir_serie_diaria.py    # serie_sst_diaria.csv
python scripts/construir_reservorios.py     # serie_reservorios.csv
python scripts/verificar_datos.py           # auditoría (solo lectura)
python scripts/backtest_fen.py              # icen_reconstruido.csv + figuras 1 y 2
python scripts/validar_icen.py --refrescar  # icen_oficial.txt + figura 3
python -c "from core import core_alerta; core_alerta.main()"   # figuras 5 y 6
python scripts/construir_mapas.py           # los 9 mapas + indice.json
```

`--refrescar` en `validar_icen.py` **no es opcional antes de presentar**: sin
él, el script reutiliza la copia local del ICEN oficial aunque tenga meses, y
el retraso del IGP que muestra el sistema saldría inflado.

### ⚠️ Copiar las figuras que la web muestra

Dos figuras se generan en `data/salidas/` pero la web las sirve desde
`data/salidas/mapas/`. **Hay que copiarlas a mano después de regenerarlas:**

```powershell
Copy-Item data\salidas\3_validacion_icen.png data\salidas\mapas\ -Force
Copy-Item data\salidas\5_dos_etapas_2015_vs_2017.png data\salidas\mapas\ -Force
```

Si se olvida, la web muestra la versión antigua **sin ningún error visible**.
Como la copia ya existe, no hay 404 que avise. Verifica la fecha:

```powershell
Get-ChildItem data\salidas\mapas\*.png | Select-Object Name, LastWriteTime
```

### ⚠️ El caché de 30 minutos

`api/alerta.py` cachea la serie 30 minutos y la vegetación 1 hora. Si
regeneras los CSV con el servidor encendido, **la web sigue mostrando lo viejo
sin avisar**. Reinicia uvicorn (Ctrl+C y volver a levantarlo) después de
cualquier actualización de datos.

---

## PASO 3 — Verificación antes de presentar

Recorre las cuatro pestañas y confirma:

- [ ] **Resumen** — el banner muestra estado, y las dos barras traen número y fecha
- [ ] **Monitoreo Satelital** — los tres ecosistemas cargan mapa, y los tres periodos también (9 mapas en total)
- [ ] **Backtest** — las tres tarjetas de anticipación y el gráfico comparativo
- [ ] **Validación** — las tres métricas y el gráfico de validación del ICEN

Si un gráfico no aparece, revisa el aviso `[static]` del arranque del backend.

Y comprueba la frescura de los datos:

```powershell
python -c "import urllib.request,json; d=json.load(urllib.request.urlopen('http://localhost:8000/api/alerta/estado')); print('ultimo dato:', d['ultimo_dato'])"
```

OISST se publica con retraso: que el último día sea de hace dos a cuatro días
es normal. Si es de hace semanas, hay que regenerar las series.

---

## PASO 4 — Antes de salir de casa

- [ ] Los dos servicios arrancan desde cero (cierra todo y vuelve a empezar)
- [ ] Existe `frontend/.env`
- [ ] Las dependencias están instaladas (`pip` y `npm`) — **no confíes en tener wifi en el local**
- [ ] `ultimo_dato` es de hace pocos días
- [ ] Las figuras de `data/salidas/mapas/` tienen fecha reciente
- [ ] Batería y cargador
- [ ] Adaptador de vídeo para el proyector

---

## Plan B si algo falla en vivo

Los resultados están en `backend/data/salidas/` como imágenes PNG ya
generadas. Ábrelas directamente desde el explorador de archivos:

| Archivo | Qué muestra |
|---|---|
| `5_dos_etapas_2015_vs_2017.png` | El hallazgo central |
| `6_estado_actual.png` | El estado del sistema hoy |
| `3_validacion_icen.png` | La validación contra el índice oficial |
| `2_backtest_2017.png` | La anticipación en 2017 |
| `mapas/*.png` | Los nueve mapas por ecosistema y periodo |

El argumento del proyecto no depende de que la web arranque.

Y si hay terminal pero no navegador, esto imprime el diagnóstico completo:

```powershell
python -c "from core import core_alerta; core_alerta.main()"
python -c "from core import core_icen; core_icen.informe('data/datos/serie_sst.csv','data/salidas/icen_oficial.txt')"
```

---

## Automatización: qué corre solo y qué no

| Tarea | ¿Automática? |
|---|---|
| Regenerar los 9 mapas | Sí — GitHub Actions, cron diario |
| Actualizar `serie_sst_diaria.csv` | **No** — a mano |
| Actualizar `serie_sst.csv` / `serie_vegetacion.csv` | **No** — a mano |
| Actualizar `serie_reservorios.csv` | **No** — a mano |
| Regenerar las figuras PNG | **No** — a mano |
| Copiar las figuras a `mapas/` | **No** — a mano |

GitHub **desactiva los workflows programados tras 60 días sin actividad** en el
repositorio. No falla: deja de correr en silencio. Revisa la pestaña Actions
si los mapas envejecen sin que nada aparezca en rojo.

---

## Pendiente: despliegue público

Un despliegue con URL pública requiere alojar los dos servicios por separado
(backend con Python, frontend estático o en Node) y apuntar `PUBLIC_API_URL`
a la dirección pública del backend.

No está hecho ni probado. Documentarlo aquí sin haberlo verificado sería
describir algo que no existe.