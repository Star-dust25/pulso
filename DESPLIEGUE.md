# DESPLIEGUE — Pulso

Estado actual: **el sistema se ejecuta localmente**. No hay despliegue público.
Esta guía cubre cómo levantarlo y cómo demostrarlo.

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
python main.py
```

Comprueba que responde antes de seguir. En el navegador:

```
http://127.0.0.1:8000/api/alerta/estado
```

Debe devolver un JSON con `precursor`, `z_msavi` y `etapa1_activa`. Si no
responde, nada más va a funcionar.

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

---

## PASO 3 — Verificación antes de presentar

Recorre las cuatro pestañas y confirma:

- [ ] **Resumen** — el banner muestra estado, y las dos barras traen número y fecha
- [ ] **Monitoreo Satelital** — los tres ecosistemas cargan mapa, y los tres periodos también (9 mapas en total)
- [ ] **Backtest** — las tres tarjetas de anticipación y el gráfico comparativo
- [ ] **Validación** — las tres métricas y el gráfico de validación del ICEN

Si un gráfico no aparece, es que el backend no está sirviendo `/static/mapas/`.
Revisa el PASO 1.

---

## PASO 4 — Antes de salir de casa

- [ ] Los dos servicios arrancan desde cero (cierra todo y vuelve a empezar)
- [ ] Existe `frontend/.env`
- [ ] Las dependencias están instaladas (`pip` y `npm`) — **no confíes en tener wifi en el local**
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

---

## Pendiente: despliegue público

Un despliegue con URL pública requiere alojar los dos servicios por separado
(backend con Python, frontend estático o en Node) y apuntar `PUBLIC_API_URL`
a la dirección pública del backend.

No está hecho ni probado. Documentarlo aquí sin haberlo verificado sería
describir algo que no existe.