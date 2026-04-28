from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

from services.conversation_importer import ConversationImporter, ImportOptions
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig, IMPORTS_DIR
from api.schemas.conversation import (
    ConversationPreview, ImportRequest, ImportResult, DeleteSessionRequest,
)

router = APIRouter(prefix="/api/import", tags=["import"])
config = AppConfig()
vector_store = VectorStore()
ollama_svc = OllamaService(config)
importer = ConversationImporter(vector_store, ollama_svc, config)


@router.get("/preview", response_model=list[ConversationPreview])
async def preview_import(source_type: str, source_path: Optional[str] = None):
    results = importer.preview_import(source_type, source_path)
    return [ConversationPreview(**r) for r in results]


@router.post("/conversations", response_model=list[ImportResult])
async def import_conversations(request: ImportRequest):
    options = ImportOptions(
        extract_memories=request.extract_memories,
        extract_dimensions=request.extract_dimensions,
    )
    results = importer.import_conversations(
        source_type=request.source_type,
        source_path=request.source_path,
        options=options,
    )
    return [ImportResult(**r) for r in results]


@router.post("/upload")
async def upload_file(
    source_type: str,
    file: UploadFile = File(...),
    extract_memories: bool = True,
):
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = IMPORTS_DIR / file.filename

    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    options = ImportOptions(extract_memories=extract_memories)
    results = importer.import_conversations(
        source_type=source_type,
        source_path=str(file_path),
        options=options,
    )

    return results


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, delete_memories: bool = False):
    result = importer.delete_session(session_id, delete_memories)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result