from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from services.vector_store import VectorStore
from services.document_processor import get_processor
from config import DOCUMENTS_DIR, AppConfig
from services.ollama_service import OllamaService


@dataclass
class KnowledgeBase:
    kb_id: str
    name: str
    description: str
    embedding_model: str
    chunk_size: int
    similarity_threshold: float
    created_at: datetime
    document_count: int = 0


@dataclass
class Document:
    doc_id: str
    kb_id: str
    filename: str
    file_path: str
    chunks_count: int
    imported_at: datetime


class KnowledgeService:
    """知识库服务"""

    def __init__(self, vector_store: VectorStore, ollama_service: OllamaService, config: AppConfig):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.collection_name = "knowledge"

    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        embedding_model: str = None,
        chunk_size: int = 500,
        similarity_threshold: float = 0.7,
    ) -> KnowledgeBase:
        """创建知识库"""
        kb_id = str(uuid4())
        embedding_model = embedding_model or self.config.get("embedding_model", "nomic-embed-text")

        kb = KnowledgeBase(
            kb_id=kb_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            similarity_threshold=similarity_threshold,
            created_at=datetime.now(),
            document_count=0,
        )

        from services.database import get_session, KnowledgeBaseRow
        session = get_session()
        try:
            row = KnowledgeBaseRow(
                kb_id=kb_id,
                name=name,
                description=description,
                embedding_model=embedding_model,
                chunk_size=chunk_size,
                similarity_threshold=similarity_threshold,
            )
            session.add(row)
            session.commit()
        finally:
            session.close()

        return kb

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        """列出所有知识库"""
        from services.database import get_session, KnowledgeBaseRow
        session = get_session()
        try:
            rows = session.query(KnowledgeBaseRow).all()
            return [self._row_to_kb(row) for row in rows]
        finally:
            session.close()

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取知识库详情"""
        from services.database import get_session, KnowledgeBaseRow
        session = get_session()
        try:
            row = session.query(KnowledgeBaseRow).filter_by(kb_id=kb_id).first()
            return self._row_to_kb(row) if row else None
        finally:
            session.close()

    def _row_to_kb(self, row) -> KnowledgeBase:
        return KnowledgeBase(
            kb_id=row.kb_id,
            name=row.name,
            description=row.description,
            embedding_model=row.embedding_model,
            chunk_size=row.chunk_size,
            similarity_threshold=row.similarity_threshold,
            created_at=row.created_at,
            document_count=row.document_count,
        )

    def import_document(
        self,
        kb_id: str,
        file_path: Path,
    ) -> Document:
        """导入文档到知识库"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        processor = get_processor(file_path)
        text = processor.extract_text(file_path)
        chunks = processor.chunk_text(text, chunk_size=kb.chunk_size)

        embeddings = []
        for chunk in chunks:
            emb = self.ollama.embed(chunk, model=kb.embedding_model)
            embeddings.append(emb)

        doc_id = str(uuid4())
        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            points.append({
                "id": f"{doc_id}_{i}",
                "vector": emb,
                "payload": {
                    "doc_id": doc_id,
                    "kb_id": kb_id,
                    "chunk_index": i,
                    "content": chunk,
                    "filename": file_path.name,
                }
            })

        self.vector_store.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        from services.database import get_session, DocumentRow, KnowledgeBaseRow
        session = get_session()
        try:
            doc_row = DocumentRow(
                doc_id=doc_id,
                kb_id=kb_id,
                filename=file_path.name,
                file_path=str(file_path),
                chunks_count=len(chunks),
            )
            session.add(doc_row)

            kb_row = session.query(KnowledgeBaseRow).filter_by(kb_id=kb_id).first()
            if kb_row:
                kb_row.document_count += 1

            session.commit()
        finally:
            session.close()

        return Document(
            doc_id=doc_id,
            kb_id=kb_id,
            filename=file_path.name,
            file_path=str(file_path),
            chunks_count=len(chunks),
            imported_at=datetime.now(),
        )

    def search_knowledge(
        self,
        kb_id: str,
        query: str,
        limit: int = 5,
        similarity_threshold: float = None,
    ) -> list[dict]:
        """检索知识库"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        threshold = similarity_threshold or kb.similarity_threshold
        query_emb = self.ollama.embed(query, model=kb.embedding_model)

        results = self.vector_store.client.search(
            collection_name=self.collection_name,
            query_vector=query_emb,
            limit=limit,
            query_filter={"must": [{"key": "kb_id", "match": {"value": kb_id}}]},
        )

        return [
            {
                "content": r.payload["content"],
                "filename": r.payload["filename"],
                "chunk_index": r.payload["chunk_index"],
                "score": r.score,
            }
            for r in results if r.score >= threshold
        ]

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库（同时删除所有关联文档）"""
        from services.database import get_session, KnowledgeBaseRow, DocumentRow

        session = get_session()
        try:
            docs = session.query(DocumentRow).filter_by(kb_id=kb_id).all()
            doc_ids = [d.doc_id for d in docs]

            if doc_ids:
                for doc_id in doc_ids:
                    self.vector_store.client.delete(
                        collection_name=self.collection_name,
                        points=[f"{doc_id}_*"],
                    )

            session.query(DocumentRow).filter_by(kb_id=kb_id).delete()
            session.query(KnowledgeBaseRow).filter_by(kb_id=kb_id).delete()
            session.commit()
            return True
        finally:
            session.close()

    def list_documents(self, kb_id: str) -> list[Document]:
        """列出知识库中的文档"""
        from services.database import get_session, DocumentRow
        session = get_session()
        try:
            rows = session.query(DocumentRow).filter_by(kb_id=kb_id).all()
            return [
                Document(
                    doc_id=row.doc_id,
                    kb_id=row.kb_id,
                    filename=row.filename,
                    file_path=row.file_path,
                    chunks_count=row.chunks_count,
                    imported_at=row.imported_at,
                )
                for row in rows
            ]
        finally:
            session.close()