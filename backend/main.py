from fastapi import FastAPI
from api.routes import health, hardware, ollama, settings, knowledge, memory
import api.routes.import_routes as import_routes
from services.vector_store import VectorStore

app = FastAPI(title="Mem-Switch Backend", version="0.1.0")

app.include_router(health.router)
app.include_router(hardware.router)
app.include_router(ollama.router)
app.include_router(settings.router)
app.include_router(knowledge.router)
app.include_router(memory.router)
app.include_router(import_routes.router)

vector_store = VectorStore()


@app.on_event("startup")
async def startup():
    print("Mem-Switch backend starting...")
    print(f"Qdrant collections initialized")