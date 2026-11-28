"""
Script para cargar los JSON de canciones a MongoDB Atlas.
Mantiene la estructura definida en DISEÑO_BACKEND.md.
"""
import json
import os
import asyncio
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

CANCIONES_DIR = Path(__file__).parent.parent / "Canciones"


async def main():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DB_NAME")]
    coleccion = db["canciones"]

    # Limpiar coleccion antes de reinsertar
    resultado = await coleccion.delete_many({})
    print(f"Coleccion limpiada: {resultado.deleted_count} documentos eliminados")

    archivos = list(CANCIONES_DIR.glob("*.json"))
    if not archivos:
        print(f"No se encontraron archivos JSON en {CANCIONES_DIR}")
        return

    print(f"Archivos encontrados: {[a.name for a in archivos]}\n")

    total_insertadas = 0
    total_duplicadas = 0

    for archivo in archivos:
        print(f"Procesando: {archivo.name}")
        # Forzar UTF-8 explicitamente
        with open(archivo, "r", encoding="utf-8") as f:
            canciones = json.load(f)

        for cancion in canciones:
            existe = await coleccion.find_one({
                "titulo": cancion["titulo"],
                "artista": cancion["artista"]
            })

            if existe:
                print(f"  [DUPLICADO] {cancion['titulo']} - {cancion['artista']}")
                total_duplicadas += 1
                continue

            from bson import ObjectId
            oid = ObjectId()
            documento = {
                "_id":              oid,
                "id":               str(oid),
                "titulo":           cancion.get("titulo", ""),
                "artista":          cancion.get("artista", ""),
                "album":            cancion.get("album", ""),
                "genero":           cancion.get("genero", ""),
                "letra":            cancion.get("letra", ""),
                "fragmento":        cancion.get("fragmento", ""),
                "youtube_id":       cancion.get("youtube_id", ""),
                "vector_embedding": None,
            }

            await coleccion.insert_one(documento)
            print(f"  [OK] {cancion['titulo']} - {cancion['artista']}")
            total_insertadas += 1

    print(f"\n{'='*50}")
    print(f"Insertadas:  {total_insertadas}")
    print(f"Duplicadas:  {total_duplicadas}")
    print(f"Total:       {total_insertadas + total_duplicadas}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
