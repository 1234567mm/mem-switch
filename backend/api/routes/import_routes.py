from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

from services.conversation_importer import ConversationImporter, ImportOptions
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from services.batch_import_service import BatchImportService
from config import AppConfig, IMPORTS_DIR
from api.schemas.conversation import (
    ConversationPreview, ImportRequest, ImportResult, DeleteSessionRequest,
)
from api.schemas.import_task import (
    BatchImportRequest,
    TaskStatusResponse,
    TaskListItemResponse,
    RetryTaskRequest,
)

router = APIRouter(prefix="/api/import", tags=["import"])
config = AppConfig()
vector_store = VectorStore()
ollama_svc = OllamaService(config)
importer = ConversationImporter(vector_store, ollama_svc, config)
batch_import_service = BatchImportService(vector_store, ollama_svc, config)


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


@router.post("/batch", response_model=dict)
async def batch_import(request: BatchImportRequest):
    """批量导入文件"""
    result = batch_import_service.import_batch(
        source_type=request.source_type,
        source_path=request.source_path,
        extract_memories=request.extract_memories,
        extract_dimensions=request.extract_dimensions,
        delete_after_import=request.delete_after_import,
    )
    return result


@router.get("/tasks", response_model=list[TaskListItemResponse])
async def list_tasks(limit: int = 20):
    """获取任务列表"""
    tasks = batch_import_service.list_tasks(limit=limit)
    return [TaskListItemResponse(**t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    result = batch_import_service.get_task_status(task_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Task not found"))
    return TaskStatusResponse(**result)


@router.post("/tasks/{task_id}/retry", response_model=dict)
async def retry_task(task_id: str, request: RetryTaskRequest = None):
    """重试失败的文件

    注意：当前实现返回原任务状态，实际重试逻辑需在后续版本实现
    """
    # TODO: 实现重试逻辑 - 重新处理失败的文件
    result = batch_import_service.get_task_status(task_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Task not found"))

    return {
        "task_id": task_id,
        "status": "retry_queued",
        "message": "Retry functionality is not yet implemented"
    }