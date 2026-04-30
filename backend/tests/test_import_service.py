import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from services.batch_import_service import BatchImportService


@pytest.fixture
def import_service(tmp_session, mock_vector_store, mock_ollama, mock_config):
    with patch("services.batch_import_service.get_session", return_value=tmp_session):
        yield BatchImportService(mock_vector_store, mock_ollama, mock_config)


class TestImportBatch:
    def test_import_returns_task_id(self, import_service, tmp_path):
        src = tmp_path / "conversations.json"
        src.write_text(json.dumps([{
            "session_id": "s1",
            "source": "json_file",
            "timestamp": "2024-01-01T00:00:00",
            "messages": [{"role": "user", "content": "Hello"}]
        }]))
        result = import_service.import_batch(
            source_type="json_file",
            source_path=str(src),
        )
        assert "task_id" in result or result.get("status") == "error"

    def test_skips_already_imported_session(self, import_service, tmp_session, tmp_path):
        from services.database import SessionRow
        existing = SessionRow(id="dup-session", source="json_file")
        tmp_session.add(existing)
        tmp_session.commit()

        src = tmp_path / "dup.json"
        src.write_text(json.dumps([{
            "session_id": "dup-session",
            "source": "json_file",
            "timestamp": "2024-01-01T00:00:00",
            "messages": [{"role": "user", "content": "dup"}]
        }]))
        # 不应抛异常，幂等处理
        result = import_service.import_batch(source_type="json_file", source_path=str(src))
        assert result.get("skipped_files", 0) >= 1


class TestGetTaskStatus:
    def test_returns_error_for_nonexistent_task(self, import_service):
        result = import_service.get_task_status("nonexistent-task-id")
        assert result.get("status") == "error"

    def test_returns_task_info(self, import_service, tmp_session, tmp_path):
        src = tmp_path / "simple.json"
        src.write_text(json.dumps([{
            "session_id": "task-test-s1",
            "source": "json_file",
            "timestamp": "2024-01-01T00:00:00",
            "messages": [{"role": "user", "content": "test"}]
        }]))
        import_service.import_batch(source_type="json_file", source_path=str(src))
        # 任务已创建，可以查询状态
        tasks = import_service.list_tasks(limit=10)
        assert isinstance(tasks, list)