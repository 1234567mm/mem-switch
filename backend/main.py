from fastapi import FastAPI
from api.routes import health, hardware, ollama, settings
from services.vector_store import VectorStore

app = FastAPI(title="Mem-Switch Backend", version="0.1.0")

app.include_router(health.router)
app.include_router(hardware.router)
app.include_router(ollama.router)
app.include_router(settings.router)

vector_store = VectorStore()


@app.on_event("startup")
async def startup():
    print("Mem-Switch backend starting...")
    print(f"Qdrant collections initialized")
