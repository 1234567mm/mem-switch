"""Batch import service with concurrency control and deduplication."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from config import IMPORTS_DIR, AppConfig
from services.database import get_session, ImportTaskRow, ImportTaskFileRow, SessionRow
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from services.memory_service import MemoryService
from services.memory_extractor import MemoryExtractor
from services.profile_manager import ProfileManager
from adapters import get_adapter, Conversation


class BatchImportService:
    """批量导入服务，支持并发控制和去重检测"""

    def __init__(
        self,
        vector_store: VectorStore,
        ollama_service: OllamaService,
        config: AppConfig,
        max_concurrent_files: int = 5,
    ):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.max_concurrent_files = max_concurrent_files
        self.semaphore = asyncio.Semaphore(max_concurrent_files)
        self.collection_name = "conversations"
        self.profile_manager = ProfileManager()

    def import_batch(
        self,
        source_type: str,
        source_path: str,
        extract_memories: bool = True,
        extract_dimensions: list[str] = None,
        delete_after_import: bool = False,
    ) -> dict:
        """创建批量导入任务"""
        db = get_session()
        try:
            adapter = get_adapter(source_type)
            if not adapter.detect(source_path):
                return {"status": "error", "message": f"Source not found: {source_path}"}

            conversations = adapter.parse(source_path)
            total_files = len(conversations)

            task_id = str(uuid4())
            now = datetime.now()

            task_row = ImportTaskRow(
                id=task_id,
                source_type=source_type,
                total_files=total_files,
                completed_files=0,
                failed_files=0,
                skipped_files=0,
                status="processing",
                progress=0.0,
                created_at=now,
                updated_at=now,
            )
            db.add(task_row)
            db.commit()

            for conv in conversations:
                file_row = ImportTaskFileRow(
                    task_id=task_id,
                    file_name=conv.source,
                    file_path=source_path,
                    status="pending",
                    session_id=conv.session_id,
                    skipped=False,
                )
                db.add(file_row)
            db.commit()

            asyncio.run(
                self._process_batch(
                    task_id=task_id,
                    conversations=conversations,
                    extract_memories=extract_memories,
                    extract_dimensions=extract_dimensions,
                    delete_after_import=delete_after_import,
                )
            )

            task_row = db.query(ImportTaskRow).filter_by(id=task_id).first()
            return {
                "status": task_row.status,
                "task_id": task_id,
                "total_files": task_row.total_files,
                "completed_files": task_row.completed_files,
                "failed_files": task_row.failed_files,
                "skipped_files": task_row.skipped_files,
                "progress": task_row.progress,
            }
        finally:
            db.close()

    async def _process_batch(
        self,
        task_id: str,
        conversations: list[Conversation],
        extract_memories: bool,
        extract_dimensions: Optional[list[str]],
        delete_after_import: bool,
    ):
        """处理批量导入任务"""
        tasks = [
            self._process_file(
                task_id=task_id,
                conv=conv,
                extract_memories=extract_memories,
                extract_dimensions=extract_dimensions,
            )
            for conv in conversations
        ]
        await asyncio.gather(*tasks)

        db = get_session()
        try:
            task_row = db.query(ImportTaskRow).filter_by(id=task_id).first()
            task_row.status = "completed" if task_row.failed_files == 0 else "partial"
            task_row.updated_at = datetime.now()
            db.commit()
        finally:
            db.close()

    async def _process_file(
        self,
        task_id: str,
        conv: Conversation,
        extract_memories: bool,
        extract_dimensions: Optional[list[str]],
    ):
        """处理单个文件（带信号量限流）"""
        async with self.semaphore:
            db = get_session()
            try:
                file_row = (
                    db.query(ImportTaskFileRow)
                    .filter_by(task_id=task_id, session_id=conv.session_id)
                    .first()
                )

                if not file_row:
                    return

                if self._check_duplicate(db, conv.session_id):
                    file_row.status = "skipped"
                    file_row.skipped = True
                    file_row.processed_at = datetime.now()
                    db.commit()

                    task_row = db.query(ImportTaskRow).filter_by(id=task_id).first()
                    task_row.skipped_files += 1
                    task_row.updated_at = datetime.now()
                    db.commit()
                    return

                result = await self._import_single(
                    conv=conv,
                    extract_memories=extract_memories,
                    extract_dimensions=extract_dimensions,
                )

                file_row.status = result.get("status", "failed")
                file_row.memories_created = result.get("memories_created", 0)
                file_row.error = result.get("error")
                file_row.processed_at = datetime.now()

                task_row = db.query(ImportTaskRow).filter_by(id=task_id).first()
                if result.get("status") == "success":
                    task_row.completed_files += 1
                else:
                    task_row.failed_files += 1
                task_row.updated_at = datetime.now()

                self._update_task_progress(db, task_row)
                db.commit()

            finally:
                db.close()

    def _check_duplicate(self, db: Session, session_id: str) -> bool:
        """检查会话是否已导入"""
        existing = db.query(SessionRow).filter_by(id=session_id).first()
        if existing and not existing.deleted:
            return True

        qdrant_exists = self.vector_store.client.retrieve(
            collection_name=self.collection_name,
            ids=[session_id],
        )
        return len(qdrant_exists) > 0

    async def _import_single(
        self,
        conv: Conversation,
        extract_memories: bool,
        extract_dimensions: Optional[list[str]],
    ) -> dict:
        """导入单个对话"""
        session_id = conv.session_id

        try:
            text_content = self._format_conversation_for_embedding(conv)
            emb = await asyncio.to_thread(self.ollama.embed, text_content)

            await asyncio.to_thread(
                self.vector_store.client.upsert,
                collection_name=self.collection_name,
                points=[{
                    "id": session_id,
                    "vector": emb,
                    "payload": {
                        "session_id": session_id,
                        "source": conv.source,
                        "timestamp": conv.timestamp.isoformat(),
                        "messages": conv.messages,
                        "message_count": len(conv.messages),
                    }
                }]
            )

            self._save_session_metadata(session_id, conv)

            memories_created = 0
            if extract_memories:
                extractor = MemoryExtractor(self.ollama, self.config)
                extracted = extractor.extract_memories(
                    text_content,
                    dimensions=extract_dimensions or ["preference", "expertise", "project_context"],
                )

                memory_service = MemoryService(self.vector_store, self.ollama, self.config)
                for dim, data in extracted.items():
                    if 'error' not in data and 'data' in data:
                        memory_service.create_memory(
                            content=str(data['data']),
                            memory_type=dim,
                            dimensions={
                                "label": data.get('label', dim),
                                "confidence": data.get('confidence', 0.8),
                            },
                            source_session_id=session_id,
                        )
                        memories_created += 1

            return {
                "status": "success",
                "session_id": session_id,
                "source": conv.source,
                "messages_count": len(conv.messages),
                "memories_created": memories_created,
            }

        except Exception as e:
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    def _save_session_metadata(self, session_id: str, conv: Conversation):
        """保存会话元数据到 SQLite"""
        db = get_session()
        try:
            row = SessionRow(
                id=session_id,
                source=conv.source,
                import_time=datetime.now(),
                deleted=False,
            )
            db.add(row)
            db.commit()
        finally:
            db.close()

    def _format_conversation_for_embedding(self, conv: Conversation) -> str:
        """将对话格式化为 embedding 文本"""
        lines = []
        for msg in conv.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _update_task_progress(self, db: Session, task_row: ImportTaskRow):
        """更新任务进度"""
        if task_row.total_files > 0:
            task_row.progress = (
                (task_row.completed_files + task_row.failed_files + task_row.skipped_files)
                / task_row.total_files
            ) * 100.0
        else:
            task_row.progress = 100.0
        task_row.updated_at = datetime.now()

    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        db = get_session()
        try:
            task_row = db.query(ImportTaskRow).filter_by(id=task_id).first()
            if not task_row:
                return {"status": "error", "message": "Task not found"}

            file_rows = (
                db.query(ImportTaskFileRow)
                .filter_by(task_id=task_id)
                .all()
            )

            return {
                "task_id": task_row.id,
                "source_type": task_row.source_type,
                "total_files": task_row.total_files,
                "completed_files": task_row.completed_files,
                "failed_files": task_row.failed_files,
                "skipped_files": task_row.skipped_files,
                "status": task_row.status,
                "progress": task_row.progress,
                "created_at": task_row.created_at.isoformat(),
                "updated_at": task_row.updated_at.isoformat(),
                "files": [
                    {
                        "file_name": f.file_name,
                        "status": f.status,
                        "error": f.error,
                        "session_id": f.session_id,
                        "memories_created": f.memories_created,
                    }
                    for f in file_rows
                ]
            }
        finally:
            db.close()

    def list_tasks(self, limit: int = 20) -> list[dict]:
        """获取任务列表"""
        db = get_session()
        try:
            tasks = (
                db.query(ImportTaskRow)
                .order_by(ImportTaskRow.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "task_id": t.id,
                    "source_type": t.source_type,
                    "total_files": t.total_files,
                    "completed_files": t.completed_files,
                    "failed_files": t.failed_files,
                    "skipped_files": t.skipped_files,
                    "status": t.status,
                    "progress": t.progress,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ]
        finally:
            db.close()
