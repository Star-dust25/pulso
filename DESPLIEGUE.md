# DESPLIEGUE — P.A.L.M.A.

Objetivo: una URL publica para el codigo QR del stand.

---

## PASO 0 — Comprueba que los datos entran al repositorio

Streamlit Cloud NO ejecuta los scripts de descarga. Los CSV **tienen que
viajar dentro del repo**, o cuatro de las cinco pestañas quedan vacias.

```powershell
git check-ignore datos/serie_sst.csv salidas/icen_reconstruido.csv
```

Si imprime algo, esos archivos estan siendo ignorados y hay que arreglarlo.
Si no imprime nada, entran. Correcto.

Peso total de `datos/` + `salidas/`: unos pocos MB. Sin problema.

---

## PASO 1 — Repositorio en GitHub

```powershell
git init
git add .
git commit -m "P.A.L.M.A. - Sistema de Alerta Temprana ante El Nino Costero"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/palma.git
git push -u origin main
```

Antes de hacer push, VERIFICA que no sube basura:

```powershell
git status --short
```

No debe aparecer `venv/`, ni `__pycache__/`, ni ningun `.json`.
Si aparece un `.json`, PARA: puede ser una credencial.

---

## PASO 2 — Cuenta de servicio de Earth Engine

Este es el paso que puede fallar. Tu portatil usa OAuth personal (tu
navegador). **Un servidor no tiene navegador.** Necesita una cuenta de
servicio.

1. Entra a `console.cloud.google.com`, proyecto **monitor-bosqueseco**.
2. `IAM y administracion` -> `Cuentas de servicio` -> **Crear**.
   - Nombre: `palma-streamlit`
   - Rol: `Earth Engine Resource Viewer` (o `Editor` si da problemas)
3. Abre la cuenta creada -> pestaña `Claves` -> `Agregar clave` ->
   `Crear clave nueva` -> **JSON**. Se descarga un archivo.
   **Ese archivo NO va al repositorio. Nunca.**
4. Registra la cuenta en Earth Engine:
   `https://code.earthengine.google.com/register`
   -> registra el correo de la cuenta de servicio
   (`palma-streamlit@monitor-bosqueseco.iam.gserviceaccount.com`)

---

## PASO 3 — Streamlit Cloud

1. `share.streamlit.io` -> inicia sesion con GitHub.
2. `New app` -> elige el repo -> archivo principal: `app_palma.py`.
3. Antes de desplegar: `Advanced settings` -> **Secrets**.
   Pega el contenido del JSON traducido a formato TOML:

```toml
[gee_service_account]
type = "service_account"
project_id = "monitor-bosqueseco"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
client_email = "palma-streamlit@monitor-bosqueseco.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

CUIDADO con `private_key`: debe ir entre comillas dobles y conservar los
`\n` literales tal como aparecen en el JSON.

4. `Deploy`. Tarda unos minutos.

---

## SI EL PASO 2 O 3 FALLA

No es una catastrofe. **Despliega igual.**

Sin cuenta de servicio, la pestaña de MONITOREO mostrara la banda ambar
"Sin conexion a Google Earth Engine", y las otras CUATRO pestañas —Estado,
Backtest, Validacion e Impacto— funcionaran perfectamente, porque leen de
los CSV del repositorio.

El QR seguiria dando acceso al 80% del sistema, y el mapa satelital lo
demuestras en vivo desde el portatil.

No es un plan B improvisado: es la misma arquitectura de degradacion con
gracia que ya probamos con el wifi.

---

## PASO 4 — El codigo QR

Con la URL final (`https://TU-APP.streamlit.app`):

- `qr-code-generator.com` o similar
- Descarga en PNG, alta resolucion
- Imprimelo GRANDE (minimo 10x10 cm) para que se escanee de lejos
- Debajo, el texto: **"P.A.L.M.A. — Sistema en vivo"** y la URL escrita

Pruebalo con TU PROPIO movil antes de imprimir.

---

## PASO 5 — Prueba en movil

Abre la URL en el telefono y revisa:

- [ ] El titulo no se corta
- [ ] Las tarjetas de Etapa 1 y 2 se apilan, no se aplastan
- [ ] La tabla 2015 vs 2017 permite scroll horizontal
- [ ] Las pestañas caben (o hacen scroll)
- [ ] Las cifras grandes siguen legibles