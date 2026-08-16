import sys
import os

# Ensure the backend directory is in the path to allow core imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from api import alerta, mapas

app = FastAPI(title="Pulso API")

# Setup CORS for the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static maps
mapas_dir = os.path.join(os.path.dirname(__file__), "data", "salidas", "mapas")
if os.path.exists(mapas_dir):
    app.mount("/static/mapas", StaticFiles(directory=mapas_dir), name="mapas")

app.include_router(alerta.router, prefix="/api/alerta", tags=["Alerta"])
app.include_router(mapas.router, prefix="/api/mapas", tags=["Mapas"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Pulso API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
