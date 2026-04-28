from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
from typing import List

from services.knowledge_service import KnowledgeService
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig, DOCUMENTS_DIR
from api.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseResponse,
    DocumentResponse, SearchRequest, SearchResult,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

config = AppConfig()
vector_store = VectorStore()
ollama_svc = OllamaService(config)
knowledge_svc = KnowledgeService(vector_store, ollama_svc, config)


@router.post("/bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(data: KnowledgeBaseCreate):
    kb = knowledge_svc.create_knowledge_base(
        name=data.name,
        description=data.description,
        embedding_model=data.embedding_model,
        chunk_size=data.chunk_size,
        similarity_threshold=data.similarity_threshold,
    )
    return KnowledgeBaseResponse(
        kb_id=kb.kb_id,
        name=kb.name,
        description=kb.description,
        embedding_model=kb.embedding_model,
        chunk_size=kb.chunk_size,
        similarity_threshold=kb.similarity_threshold,
        created_at=kb.created_at,
        document_count=kb.document_count,
    )


@router.get("/bases", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases():
    kbs = knowledge_svc.list_knowledge_bases()
    return [
        KnowledgeBaseResponse(
            kb_id=kb.kb_id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            similarity_threshold=kb.similarity_threshold,
            created_at=kb.created_at,
            document_count=kb.document_count,
        )
        for kb in kbs
    ]


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str):
    kb = knowledge_svc.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBaseResponse(
        kb_id=kb.kb_id,
        name=kb.name,
        description=kb.description,
        embedding_model=kb.embedding_model,
        chunk_size=kb.chunk_size,
        similarity_threshold=kb.similarity_threshold,
        created_at=kb.created_at,
        document_count=kb.document_count,
    )


@router.delete("/bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    success = knowledge_svc.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"status": "deleted", "kb_id": kb_id}


@router.post("/bases/{kb_id}/documents", response_model=DocumentResponse)
async def import_document(kb_id: str, file: UploadFile = File(...)):
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DOCUMENTS_DIR / file.filename

    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        doc = knowledge_svc.import_document(kb_id, file_path)
        return DocumentResponse(
            doc_id=doc.doc_id,
            kb_id=doc.kb_id,
            filename=doc.filename,
            chunks_count=doc.chunks_count,
            imported_at=doc.imported_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import document: {e}")


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(kb_id: str):
    docs = knowledge_svc.list_documents(kb_id)
    return [
        DocumentResponse(
            doc_id=d.doc_id,
            kb_id=d.kb_id,
            filename=d.filename,
            chunks_count=d.chunks_count,
            imported_at=d.imported_at,
        )
        for d in docs
    ]


@router.post("/bases/{kb_id}/search", response_model=list[SearchResult])
async def search_knowledge_base(kb_id: str, request: SearchRequest):
    try:
        results = knowledge_svc.search_knowledge(
            kb_id=kb_id,
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
        )
        return [SearchResult(**r) for r in results]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))