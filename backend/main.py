# main.py
# ============================================================
# API de Pulso (FastAPI)
#
#   Arrancar DESDE backend/:
#       python -m uvicorn main:app --reload
#
#   Tambien funciona `python main.py`, porque el bloque final levanta
#   uvicorn. Usa UNA de las dos, no las dos a la vez: si ambas apuntan al
#   puerto 8000 no sabras cual te esta respondiendo el navegador.
#
# OJO CON EL CACHE: api/alerta.py cachea la serie 30 minutos. Si
# regeneras los CSV con el servidor encendido, la web sigue mostrando lo
# viejo hasta media hora despues, SIN avisar. Reinicia uvicorn tras
# cualquier actualizacion de datos.
# ============================================================

import os
import sys
# backend/ en el path para poder importar 'api', 'core' y 'config'.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from api import alerta, mapas

app = FastAPI(title="Pulso API")

# --- CORS para el servidor de desarrollo del frontend ---
#
# Vite usa el 5173, pero si ese puerto esta ocupado —tipicamente por otra
# instancia que quedo abierta— salta al 5174, al 5175, etc. Con un solo
# puerto permitido, el frontend deja de poder llamar a la API y el error
# que ve el navegador no menciona CORS de forma evidente. Se permiten
# varios para que ese fallo no ocurra en mitad de una demostracion.
PUERTOS_VITE = (5173, 5174, 5175, 5176)
ORIGENES = [f"http://{host}:{p}"
            for p in PUERTOS_VITE
            for host in ("localhost", "127.0.0.1")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mapas estaticos ---
#
# El montaje era silencioso: si la carpeta no existia, el servidor
# arrancaba igual y TODAS las imagenes daban 404 sin una sola pista en el
# log. Ahora se avisa por consola.
#
# Recuerda que esta carpeta sirve /static/mapas/. Las figuras que la web
# muestra pero que los scripts generan en data/salidas/ (3_validacion_icen
# y 5_dos_etapas) hay que COPIARLAS aqui despues de regenerarlas, o el
# sitio mostrara la version vieja sin avisar.
MAPAS_DIR = os.path.join(os.path.dirname(__file__), "data", "salidas", "mapas")

if os.path.isdir(MAPAS_DIR):
    app.mount("/static/mapas", StaticFiles(directory=MAPAS_DIR), name="mapas")
    n_png = len([f for f in os.listdir(MAPAS_DIR) if f.endswith(".png")])
    print(f"[static] /static/mapas -> {MAPAS_DIR}  ({n_png} PNG)")
else:
    print(f"[static] AVISO: no existe {MAPAS_DIR}")
    print("[static] /static/mapas NO se ha montado: todas las imagenes")
    print("[static] daran 404. Ejecuta: python scripts/construir_mapas.py")

app.include_router(alerta.router, prefix="/api/alerta", tags=["Alerta"])
app.include_router(mapas.router, prefix="/api/mapas", tags=["Mapas"])


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Pulso API is running"}


if __name__ == "__main__":
    # 127.0.0.1 por defecto: el servidor solo acepta conexiones de esta
    # maquina. Antes era 0.0.0.0, que lo expone a toda la red local —en el
    # wifi de un auditorio, a cualquiera que este conectado.
    #
    # Si necesitas abrirlo (por ejemplo para verlo desde el movil durante
    # una demostracion), lanza:  PULSO_HOST=0.0.0.0 python main.py
    host = os.environ.get("PULSO_HOST", "127.0.0.1")
    puerto = int(os.environ.get("PULSO_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=puerto, reload=True)
