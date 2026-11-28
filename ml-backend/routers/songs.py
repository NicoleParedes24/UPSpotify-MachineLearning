from fastapi import APIRouter, HTTPException
from typing import List
from models.cancion import CancionCompleta, CancionResumen
from services.mongo import coleccion_canciones

router = APIRouter()


# ─────────────────────────────────────────────
# GET /popular
# Devuelve las primeras 20 canciones (sin letra)
# ─────────────────────────────────────────────
@router.get("/popular", response_model=List[CancionResumen])
async def get_popular():
    cursor = coleccion_canciones.find({}, {"letra": 0}).limit(20)
    canciones = []
    async for doc in cursor:
        canciones.append(CancionResumen(
            id=doc["id"],
            titulo=doc["titulo"],
            artista=doc["artista"],
            album=doc["album"],
            genero=doc["genero"],
            fragmento=doc["fragmento"],
            youtube_id=doc["youtube_id"],
            similitud=None,
        ))
    return canciones


# ─────────────────────────────────────────────
# GET /song/{id}
# Devuelve una cancion completa con letra
# ─────────────────────────────────────────────
@router.get("/song/{id}", response_model=CancionCompleta)
async def get_song(id: str):
    doc = await coleccion_canciones.find_one({"id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Cancion no encontrada")
    return CancionCompleta(
        id=doc["id"],
        titulo=doc["titulo"],
        artista=doc["artista"],
        album=doc["album"],
        genero=doc["genero"],
        letra=doc["letra"],
        fragmento=doc["fragmento"],
        youtube_id=doc["youtube_id"],
    )
