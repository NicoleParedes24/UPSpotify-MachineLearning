from pydantic import BaseModel
from typing import Optional


# Modelo completo (usado en GET /song/{id})
class CancionCompleta(BaseModel):
    id: str
    titulo: str
    artista: str
    album: str
    genero: str
    letra: str
    fragmento: str
    youtube_id: str


# Modelo para listados (usado en /search, /popular, /recommend)
# No incluye letra completa para no sobrecargar la respuesta
class CancionResumen(BaseModel):
    id: str
    titulo: str
    artista: str
    album: str
    genero: str
    fragmento: str
    youtube_id: str
    similitud: Optional[float] = None
