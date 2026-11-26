# UPSpotify - Division de Trabajo Backend

## Stack Tecnologico
- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI — framework moderno y rapido para construir APIs en Python.
  Genera documentacion automatica en `/docs` (Swagger UI) al correr el servidor.
- **Base de datos:** MongoDB — base de datos NoSQL orientada a documentos JSON.
- **Cliente MongoDB:** Motor (cliente asincrono de MongoDB para Python)
- **Validacion de datos:** Pydantic — viene incluido con FastAPI, se usa para definir
  la estructura de los datos que entran y salen de cada endpoint.
- **Operaciones matriciales:** Numpy — para calcular TF-IDF y similitud coseno
  de forma eficiente sin usar sklearn.
- **Variables de entorno:** python-dotenv — para leer credenciales desde un archivo .env

## Como correr el servidor localmente
```
uvicorn main:app --reload
```
Esto levanta el servidor en http://localhost:8000
La documentacion interactiva estara en http://localhost:8000/docs

---

## Dependencias de orden (hacer en este orden)
1. Kevin configura el proyecto completo (estructura, .env, CORS, requirements.txt)
2. Kenneth define los modelos de datos (schemas) y la conexion a MongoDB
3. Nicole construye el modelo TF-IDF clasico
4. Sebas construye el modelo de embeddings LLM
5. Todos pueden trabajar en paralelo una vez que Kevin y Kenneth terminan

---

## Kevin — Cancion individual y configuracion del proyecto

### Endpoint
| Metodo | Endpoint     | Descripcion                                                |
|--------|--------------|------------------------------------------------------------|
| GET    | /song/{id}   | Devuelve todos los campos de una cancion incluida la letra |

**Como funciona el endpoint:**
- Recibe el ID de la cancion como parametro en la URL: `/song/abc123`
- Consulta MongoDB buscando el documento con ese `_id`
- Devuelve el documento completo incluyendo la letra completa
- La letra completa SOLO se devuelve en este endpoint, no en los listados
- Si el ID no existe, devuelve error 404 con mensaje "Cancion no encontrada"

**Ejemplo de respuesta exitosa:**
```json
{
  "id": "abc123",
  "titulo": "Bohemian Rhapsody",
  "artista": "Queen",
  "album": "A Night at the Opera",
  "genero": "Rock",
  "letra": "Is this the real life? Is this just fantasy?...",
  "fragmento": "Is this the real life?",
  "youtube_id": "dQw4w9WgXcQ"
}
```

**Ejemplo de respuesta de error:**
```json
{
  "detail": "Cancion no encontrada"
}
```

### Configuracion del proyecto (hacer primero, antes que todos)

**1. Estructura de carpetas que debe crear:**
```
ml-backend/
  main.py                  <- archivo principal, arranca FastAPI
  .env                     <- variables de entorno, NO subir a git
  .gitignore               <- agregar .env y __pycache__ aqui
  requirements.txt         <- lista de dependencias
  /routers                 <- cada archivo es un grupo de endpoints
    search.py              <- endpoints de Nicole
    recommend.py           <- endpoints de Sebas
    songs.py               <- endpoints de Kenneth y Kevin
  /models
    cancion.py             <- modelos de datos que define Kenneth
  /services
    tfidf.py               <- logica del modelo TF-IDF (Nicole trabaja aqui)
    embedding.py           <- logica del modelo LLM (Sebas trabaja aqui)
    mongo.py               <- conexion a MongoDB (Kenneth trabaja aqui)
```

**2. Archivo .env que debe crear:**
```
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGO_DB_NAME=upspotify
LLM_API_KEY=clave_del_llm_que_elijamos
```

**3. Archivo requirements.txt que debe crear:**
```
fastapi
uvicorn
motor
pymongo
python-dotenv
numpy
pydantic
```

**4. Configurar CORS en main.py:**
CORS es necesario para que el frontend Angular (que corre en un puerto diferente
o en otro dominio) pueda hacer peticiones al backend sin ser bloqueado por el navegador.
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en produccion cambiar por la URL real del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**5. Registrar los routers en main.py:**
Cada router es el archivo de endpoints de cada integrante. Kevin los conecta todos:
```python
from routers import search, recommend, songs

app.include_router(search.router)
app.include_router(recommend.router)
app.include_router(songs.router)
```

**6. Despliegue:**
El sistema debe funcionar en un servidor publico, no solo local.
Opciones recomendadas: Railway, Render, o un VPS.
Coordinar con el equipo la URL final para que el frontend apunte a ella.

---

## Kenneth — Datos, modelos y canciones populares

### Endpoint
| Metodo | Endpoint  | Descripcion                                       |
|--------|-----------|---------------------------------------------------|
| GET    | /popular  | Devuelve las primeras 20 canciones de la coleccion |

**Como funciona el endpoint:**
- Consulta MongoDB la coleccion `canciones`
- Devuelve los primeros 20 documentos en orden de insercion (sin letra completa)
- Se usa en el Home cuando el usuario no tiene historial guardado

**Ejemplo de respuesta:**
```json
[
  {
    "id": "abc123",
    "titulo": "Bohemian Rhapsody",
    "artista": "Queen",
    "album": "A Night at the Opera",
    "genero": "Rock",
    "fragmento": "Is this the real life?",
    "youtube_id": "dQw4w9WgXcQ",
    "similitud": null
  },
  {
    "id": "def456",
    "titulo": "Blinding Lights",
    "artista": "The Weeknd",
    "album": "After Hours",
    "genero": "Pop",
    "fragmento": "I been tryna call...",
    "youtube_id": "4NRXx6U8ABQ",
    "similitud": null
  }
]
```

### Modelos de datos (schemas con Pydantic)
Kenneth debe definir estas clases en `/models/cancion.py`.
Todos los demas integrantes las importan desde ahi.

```python
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
```

### Conexion a MongoDB
Kenneth debe crear la conexion en `/services/mongo.py`.
Todos los demas la importan desde ahi para hacer consultas.

```python
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
coleccion_canciones = db["canciones"]
```

---

## Nicole — Busqueda y recomendacion clasica (TF-IDF + coseno)

### Endpoints
| Metodo | Endpoint           | Descripcion                                            |
|--------|--------------------|--------------------------------------------------------|
| POST   | /search            | Recibe query de texto, devuelve Top 10 canciones       |
| POST   | /recommend         | Recibe ID de cancion, devuelve 3 mas similares         |
| POST   | /recommend/history | Recibe lista de IDs del historial, devuelve sugerencias|

**Como funciona /search:**
- Recibe: `{ "query": "texto que escribio el usuario" }`
- Al arrancar FastAPI, la matriz TF-IDF ya esta construida en memoria
- Calcula el vector TF-IDF de la query
- Calcula similitud coseno entre la query y cada cancion de la matriz
- Aplica la formula ponderada:
  ```
  similitud_total =
      (0.75 * coseno_letra) +
      (0.10 * jaccard_titulo) +
      (0.10 * jaccard_artista) +
      (0.05 * exacto_genero)
  ```
- Ordena por similitud descendente y devuelve Top 10

**Ejemplo de respuesta de /search:**
```json
[
  {
    "id": "abc123",
    "titulo": "Vivo por amarte",
    "artista": "Mana",
    "album": "Cuando los Angeles Lloran",
    "genero": "Rock",
    "fragmento": "Vivo por amarte, muero por tenerte...",
    "youtube_id": "xXxXxXxXxXx",
    "similitud": 0.95
  },
  {
    "id": "def456",
    "titulo": "Te amo",
    "artista": "Ricky Martin",
    "album": "...",
    "genero": "Balada",
    "fragmento": "Te amo, te amo...",
    "youtube_id": "yYyYyYyYyYy",
    "similitud": 0.87
  }
]
```

**Como funciona /recommend:**
- Recibe: `{ "id": "id_de_la_cancion", "excluir": ["id1", "id2", ...] }`
- El campo `excluir` contiene los IDs del Top 10 ya mostrado para no repetirlos
- Toma el vector TF-IDF de esa cancion desde la matriz en memoria
- Calcula similitud coseno con todas las demas canciones
- Excluye las canciones del campo `excluir`
- Devuelve las 3 mas similares

**Ejemplo de respuesta de /recommend:**
```json
[
  {
    "id": "ghi789",
    "titulo": "Cuando me enamoro",
    "artista": "Enrique Iglesias",
    "album": "...",
    "genero": "Balada",
    "fragmento": "Cuando me enamoro...",
    "youtube_id": "zZzZzZzZzZz",
    "similitud": 0.82
  }
]
```

**Como funciona /recommend/history:**
- Recibe: `{ "ids": ["id1", "id2", "id3"] }` (historial del localStorage del frontend)
- Toma los vectores TF-IDF de todas esas canciones
- Calcula el vector promedio del historial
- Calcula similitud coseno del vector promedio con todas las canciones
- Devuelve sugerencias personalizadas

**Ejemplo de respuesta de /recommend/history:**
```json
[
  {
    "id": "jkl012",
    "titulo": "Oye mi amor",
    "artista": "Mana",
    "album": "...",
    "genero": "Rock",
    "fragmento": "Oye mi amor...",
    "youtube_id": "aAaAaAaAaAa",
    "similitud": 0.78
  }
]
```

**Construccion de la matriz TF-IDF (al arrancar FastAPI):**
Nicole debe construir la matriz en `/services/tfidf.py` usando numpy.
El codigo base ya existe (ml_05_wtf_idf.ipynb), hay que adaptarlo para:
- Leer las letras desde MongoDB en lugar de una lista hardcodeada
- Usar operaciones matriciales de numpy en lugar de loops de Python
- Guardar la matriz en memoria para que todos los endpoints la usen

---

## Sebas — Busqueda y recomendacion con IA (Embeddings LLM)

### Endpoints
| Metodo | Endpoint                | Descripcion                                               |
|--------|-------------------------|-----------------------------------------------------------|
| POST   | /search/ai              | Recibe query de texto, devuelve Top 10 usando embeddings  |
| POST   | /recommend/ai           | Recibe ID de cancion, devuelve 3 mas similares con LLM    |
| POST   | /recommend/history/ai   | Recibe lista de IDs del historial, sugerencias con LLM    |

**Como funciona /search/ai:**
- Recibe: `{ "query": "texto que escribio el usuario" }`
- Genera el embedding de la query usando el LLM elegido
- Calcula similitud coseno entre el embedding de la query y los embeddings
  de cada cancion guardados en MongoDB (campo `vector_embedding`)
- Ordena por similitud descendente y devuelve Top 10

**Ejemplo de respuesta de /search/ai:**
```json
[
  {
    "id": "abc123",
    "titulo": "Vivo por amarte",
    "artista": "Mana",
    "album": "Cuando los Angeles Lloran",
    "genero": "Rock",
    "fragmento": "Vivo por amarte, muero por tenerte...",
    "youtube_id": "xXxXxXxXxXx",
    "similitud": 0.93
  }
]
```

**Como funciona /recommend/ai:**
- Recibe: `{ "id": "id_de_la_cancion", "excluir": ["id1", "id2", ...] }`
- Toma el embedding de esa cancion desde MongoDB
- Calcula similitud coseno con los embeddings de todas las demas canciones
- Excluye las canciones del campo `excluir`
- Devuelve las 3 mas similares

**Ejemplo de respuesta de /recommend/ai:**
```json
[
  {
    "id": "mno345",
    "titulo": "No me queda mas",
    "artista": "Selena",
    "album": "...",
    "genero": "Balada",
    "fragmento": "No me queda mas...",
    "youtube_id": "bBbBbBbBbBb",
    "similitud": 0.89
  }
]
```

**Como funciona /recommend/history/ai:**
- Recibe: `{ "ids": ["id1", "id2", "id3"] }` (historial del localStorage del frontend)
- Toma los embeddings de todas esas canciones desde MongoDB
- Calcula el embedding promedio del historial
- Calcula similitud coseno del embedding promedio con todas las canciones
- Devuelve sugerencias personalizadas

**Ejemplo de respuesta de /recommend/history/ai:**
```json
[
  {
    "id": "pqr678",
    "titulo": "Besame mucho",
    "artista": "Luis Miguel",
    "album": "...",
    "genero": "Balada",
    "fragmento": "Besame, besame mucho...",
    "youtube_id": "cCcCcCcCcCc",
    "similitud": 0.76
  }
]
```

**Logica de embeddings en `/services/embedding.py`:**
- Funcion para generar el embedding de un texto usando el LLM elegido
- Funcion para calcular similitud coseno entre dos vectores de embedding
- PENDIENTE: definir que LLM se usara (GPT, LLaMA, DeepSeek, etc.)

---

## Resumen final

| Integrante | Area                        | Endpoints                                                        |
|------------|-----------------------------|------------------------------------------------------------------|
| Kevin      | Config + cancion individual | GET /song/{id} + setup completo del proyecto                     |
| Kenneth    | Datos y MongoDB             | GET /popular + schemas + conexion MongoDB                        |
| Nicole     | Modelo clasico TF-IDF       | POST /search, POST /recommend, POST /recommend/history           |
| Sebas      | Modelo IA embeddings        | POST /search/ai, POST /recommend/ai, POST /recommend/history/ai  |
