from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
import os

# Anclada al archivo, no al directorio de trabajo. api/ vive dentro de
# backend/, asi que subimos un nivel para llegar a backend/data/.
CARPETA_MAPAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "salidas", "mapas",
)

router = APIRouter()


@router.get("/indice")
def get_indice_mapas():
    """
    Indice de mapas pre-generados, enriquecido con la URL publica.

    POR QUE DEVOLVEMOS 'url' Y NO SOLO 'archivo'
    --------------------------------------------
    El frontend hacia `archivo.split(/[/\\]/).pop()` para recortar la ruta
    de disco y quedarse con el nombre del PNG. Eso obligaba al navegador a
    conocer como estan organizados los ficheros en el servidor: un
    acoplamiento que se rompe solo el dia que cambia la carpeta — que es
    exactamente lo que paso al migrar de Streamlit a FastAPI.

    El backend es quien sabe donde estan los archivos. Que publique la URL.
    """
    ruta = os.path.join(CARPETA_MAPAS, "indice.json")
    if not os.path.exists(ruta):
        return JSONResponse(content={})

    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    for item in data.values():
        archivo = item.get("archivo")
        if not archivo:
            item["url"] = None
            continue

        # basename() tolera los dos formatos: el viejo con ruta completa
        # ("salidas/mapas/X.png") y el nuevo con nombre suelto ("X.png").
        # Asi no hace falta regenerar el indice para que esto funcione.
        nombre = os.path.basename(archivo.replace("\\", "/"))

        # Solo publicamos lo que EXISTE. Un indice que apunta a un PNG
        # borrado produce un 404 dentro de un <img>: la imagen no carga y
        # nadie sabe por que. Mejor decirlo aqui, en el JSON.
        if os.path.exists(os.path.join(CARPETA_MAPAS, nombre)):
            item["url"] = f"/static/mapas/{nombre}"
        else:
            item["url"] = None
            item["error"] = "archivo ausente en disco"

    return JSONResponse(content=data)


@router.get("/salud")
def salud_mapas():
    """
    Diagnostico rapido: cuantos mapas hay realmente disponibles.

    Existe para poder comprobar el estado desde fuera (curl, un check del
    cron) sin abrir el navegador ni leer el JSON completo.
    """
    ruta = os.path.join(CARPETA_MAPAS, "indice.json")
    if not os.path.exists(ruta):
        return {"indice": False, "disponibles": 0, "total": 0, "faltan": []}

    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    faltan = []
    disponibles = 0
    for clave, item in data.items():
        archivo = item.get("archivo")
        nombre = os.path.basename(archivo.replace("\\", "/")) if archivo else None
        if nombre and os.path.exists(os.path.join(CARPETA_MAPAS, nombre)):
            disponibles += 1
        else:
            faltan.append(clave)

    return {
        "indice": True,
        "disponibles": disponibles,
        "total": len(data),
        "faltan": faltan,
    }
