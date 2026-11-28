from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search, recommend, songs

app = FastAPI(title="UPSpotify API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(recommend.router)
app.include_router(songs.router)

@app.get("/")
def root():
    return {"status": "UPSpotify Backend funcionando"}