# UPSpotify - Diseño del Backend

## Stack Tecnologico
- Lenguaje: Python
- Framework: FastAPI
- Base de datos: MongoDB
- Modelo clasico: TF-IDF + similitud coseno vectorial
- Modelo IA: Embeddings LLM (PENDIENTE: definir cual, GPT / LLaMA / DeepSeek)

---

## Coleccion MongoDB: canciones

### Campos del documento
```json
{
  "_id": "ObjectId (generado por Mongo)",
  "titulo": "string - nombre de la cancion",
  "artista": "string - nombre del artista",
  "album": "string - nombre del album",
  "genero": "string - genero musical (una sola palabra, sin tildes)",
  "letra": "string - letra completa de la cancion",
  "fragmento": "string - primeras lineas para mostrar en la interfaz",
  "youtube_id": "string - ID del video de YouTube (ej: dQw4w9WgXcQ)",
  "vector_embedding": "array - vector embedding LLM precalculado (PENDIENTE)"
}
```

### Notas
- La matriz TF-IDF se calcula sobre todo el corpus al arrancar FastAPI y se guarda en memoria
- Cuando llega una query, solo se calcula el TF-IDF de esa query y se compara con la matriz en memoria
- `vector_embedding` se precalcula una sola vez por cancion y se guarda en Mongo (PENDIENTE)
- `fragmento` puede ser las primeras 2-3 lineas de `letra` o un campo separado segun la API usada

---

## Modelo TF-IDF y Similitud Coseno

### Construccion de la matriz (al arrancar FastAPI)
```
FastAPI inicia
      |
      v
Carga todas las letras de MongoDB
      |
      v
Construye la matriz TF-IDF del corpus completo
(filas = canciones, columnas = terminos del vocabulario)
      |
      v
Queda en memoria lista para comparar
```

### Busqueda (por cada query)
```
Query del usuario
      |
      v
Calcula el vector TF-IDF de esa query
      |
      v
Calcula similitud coseno entre el vector query
y CADA fila de la matriz (cada cancion)
      |
      v
Ordena por puntaje descendente
      |
      v
Devuelve Top 10
```

### Recomendaciones (endpoint /recommend)
```
ID de cancion seleccionada
      |
      v
Toma el vector TF-IDF de esa cancion en la matriz
      |
      v
Calcula similitud coseno con todas las demas canciones
      |
      v
Devuelve las 3 mas similares
(excluyendo las canciones del Top 10 ya mostradas)
```

> NOTA: La matriz nunca sale del backend. Se construye una sola vez
> al iniciar y se consulta en cada busqueda sin recalcularse.

---

## Calculo de Similitud Final

Cada campo se compara con una medida apropiada y se combina en un puntaje ponderado:

| Campo    | Medida             | Peso |
|----------|--------------------|------|
| `letra`  | Coseno + TF-IDF    | 0.75 |
| `titulo` | Jaccard            | 0.10 |
| `artista`| Jaccard            | 0.10 |
| `genero` | Exacto (1 o 0)     | 0.05 |

### Formula
```
similitud_total =
    (0.75 * coseno_letra) +
    (0.10 * jaccard_titulo) +
    (0.10 * jaccard_artista) +
    (0.05 * exacto_genero)
```

### Notas
- `coseno_letra`: similitud coseno entre el vector TF-IDF de la query y el de la cancion
- `jaccard_titulo`: interseccion / union de palabras entre el titulo de la query y el de la cancion
- `jaccard_artista`: interseccion / union de palabras entre el artista de la query y el de la cancion
- `exacto_genero`: 1 si el genero coincide exactamente, 0 si no coincide

---

## Dataset

- Fuente: Genius API (letras + metadata)
- 200 canciones, 10 generos x 20 canciones, una palabra por genero, sin tildes
- PENDIENTE: crear script de extraccion (Python)

---

## Reproduccion de Canciones

- Metodo: YouTube embed con ID directo guardado en MongoDB
- El campo `youtube_id` se llena al crear el dataset con el ID correcto del video
- El frontend incrusta directamente: `youtube.com/embed/{youtube_id}`
- Sin busqueda en tiempo real, sin riesgo de video incorrecto, sin API adicional

---

## Endpoints (FastAPI)

### Busqueda clasica (TF-IDF + coseno vectorial)
| Metodo | Endpoint           | Entrada                                            | Salida                        |
|--------|--------------------|----------------------------------------------------|-------------------------------|
| POST   | /search            | { "query": "string" }                              | lista de 10 canciones         |
| POST   | /recommend         | { "id": "string", "excluir": ["string"] }          | lista de 3 canciones          |
| GET    | /popular           | -                                                  | primeras 20 canciones         |
| POST   | /recommend/history | { "ids": ["string"] }                              | lista de canciones            |
| GET    | /song/{id}         | id en la URL                                       | cancion completa con letra    |

### Busqueda con IA (Embedding LLM)
| Metodo | Endpoint                | Entrada                        | Salida                        |
|--------|-------------------------|--------------------------------|-------------------------------|
| POST   | /search/ai              | { "query": "string" }          | lista de 10 canciones         |
| POST   | /recommend/ai           | { "id": "string", "excluir": ["string"] } | lista de 3 canciones |
| POST   | /recommend/history/ai   | { "ids": ["string"] }          | lista de canciones            |

### Estructura de respuesta de una cancion
```json
{
  "id": "string",
  "titulo": "string",
  "artista": "string",
  "album": "string",
  "genero": "string",
  "fragmento": "string",
  "similitud": 0.00
}
```

> NOTA: `letra` completa solo se devuelve en el endpoint `GET /song/{id}`,
> no en los listados de busqueda ni recomendaciones, para no sobrecargar las respuestas.

---

## Pendientes
- [ ] Definir LLM para embeddings
- [ ] Definir generos y cantidad de canciones del dataset
- [ ] Crear script de extraccion con Genius API
