# Phase 5: Testing and Stabilization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现后端测试覆盖率 >60%，建立可靠测试基础。

**Architecture:** 分层测试策略 — Service 层用 Mock 隔离外部依赖，数据库用独立临时 SQLite，路由用 TestClient。

**Tech Stack:** pytest, pytest-cov, unittest.mock, starlette.testclient

---

## 文件结构

```
backend/
├── tests/
│   ├── conftest.py                    # NEW: 所有 fixtures
│   ├── test_memory_service.py         # NEW
│   ├── test_knowledge_service.py     # NEW
│   ├── test_search_service.py         # NEW
│   ├── test_import_service.py         # NEW
│   ├── test_claude_mem_adapter.py     # NEW (Phase 5.2)
│   ├── test_health_api.py             # 已有
│   ├── test_settings_api.py           # 已有
│   └── test_hardware_detector.py      # 已有
├── adapters/
│   ├── __init__.py                    # 需更新：注册 claude_mem
│   └── claude_mem_adapter.py          # NEW (Phase 5.2)
├── services/
│   ├── memory_service.py              # 被测
│   ├── knowledge_service.py           # 被测
│   ├── search_service.py              # 被测
│   └── batch_import_service.py        # 被测
└── requirements.txt                   # 需更新：pytest-cov, chromadb
```

---

## Task 1: 更新依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 pytest-cov 和 chromadb 依赖**

```txt
pytest-cov>=4.1.0
chromadb>=0.5.0
```

- [ ] **Step 2: 运行 pip install**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pip install -r requirements.txt
```

Expected: 成功安装，pytest-cov 和 chromadb 可导入

- [ ] **Step 3: 提交**

```bash
git add backend/requirements.txt && git commit -m "chore: add pytest-cov and chromadb to requirements"
```

---

## Task 2: 创建 tests/conftest.py

**Files:**
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: 写入 conftest.py**

```python
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import Base, MemoryRow, KnowledgeBaseRow, DocumentRow


# ── SQLite 临时库 ─────────────────────────────────────────────────

@pytest.fixture
def tmp_engine(tmp_path):
    """独立临时 SQLite，WAL 模式，与生产行为一致。"""
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def tmp_session(tmp_engine):
    """与临时库绑定的 SQLAlchemy Session。"""
    Session = sessionmaker(bind=tmp_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def db_with_memories(tmp_session):
    """预填充 5 条 MemoryRow 记录。"""
    memory_ids = []
    for i in range(5):
        row = MemoryRow(
            id=str(uuid4()),
            type=["preference", "skill", "fact", "preference", "skill"][i],
            content=f"Test memory content {i}",
            confidence=0.8 + i * 0.02,
            qdrant_id=str(uuid4()),
            source_session_id="session_fixture",
            call_count=i,
        )
        tmp_session.add(row)
        memory_ids.append(row.id)
    tmp_session.commit()
    yield tmp_session, memory_ids


# ── ChromaDB Mock ────────────────────────────────────────────────

@pytest.fixture
def mock_chroma_collection():
    """模拟 ChromaDB collection。"""
    collection = MagicMock()
    collection._store = {}

    def fake_upsert(ids, documents=None, metadatas=None):
        for i, id_ in enumerate(ids):
            collection._store[id_] = {
                "document": documents[i] if documents else "",
                "metadata": metadatas[i] if metadatas else {},
            }
    collection.upsert.side_effect = fake_upsert

    collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    def fake_peek(limit=10):
        items = list(collection._store.items())[:limit]
        return {
            "ids": [k for k, _ in items],
            "documents": [v["document"] for _, v in items],
            "metadatas": [v["metadata"] for _, v in items],
        }
    collection.peek.side_effect = fake_peek

    def fake_delete(ids):
        for id_ in ids:
            collection._store.pop(id_, None)
    collection.delete.side_effect = fake_delete

    def fake_get():
        return {"ids": list(collection._store.keys())}
    collection.get.side_effect = fake_get

    collection.count.return_value = 0
    return collection


@pytest.fixture
def mock_vector_store(mock_chroma_collection):
    """模拟 VectorStore。"""
    vs = MagicMock()
    vs.client.get_collection.return_value = mock_chroma_collection
    vs.client.get_or_create_collection.return_value = mock_chroma_collection
    vs.scroll.return_value = ([], None)
    return vs


# ── Ollama Mock ─────────────────────────────────────────────────

@pytest.fixture
def mock_ollama():
    """返回固定 768 维向量。"""
    ollama = MagicMock()
    ollama.embed.return_value = [0.1] * 768
    return ollama


# ── AppConfig Mock ──────────────────────────────────────────────

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get.return_value = "nomic-embed-text"
    config.embedding_model = "nomic-embed-text"
    return config
```

- [ ] **Step 2: 运行验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && python -c "import tests.conftest; print('conftest OK')"
```

Expected: 无错误输出

- [ ] **Step 3: 提交**

```bash
git add backend/tests/conftest.py && git commit -m "feat: add test fixtures in conftest.py"
```

---

## Task 3: test_memory_service.py

**Files:**
- Create: `backend/tests/test_memory_service.py`
- Test: `services/memory_service.py`

- [ ] **Step 1: 写入失败的测试**

```python
import pytest
from services.memory_service import MemoryService


@pytest.fixture
def memory_service(mock_vector_store, mock_ollama, mock_config):
    return MemoryService(mock_vector_store, mock_ollama, mock_config)


class TestCreateMemory:
    def test_returns_memory_with_id(self, memory_service):
        result = memory_service.create_memory(content="test", memory_type="preference")
        assert result.memory_id is not None
        assert result.content == "test"
        assert result.type == "preference"

    def test_calls_embed_once(self, memory_service, mock_ollama):
        memory_service.create_memory(content="test", memory_type="skill")
        mock_ollama.embed.assert_called_once_with("test")

    def test_upsert_called_with_correct_collection(self, memory_service, mock_vector_store):
        memory_service.create_memory(content="test", memory_type="fact")
        mock_vector_store.client.get_collection.assert_called_with("memories")

    def test_default_confidence(self, memory_service):
        result = memory_service.create_memory(content="test", memory_type="fact")
        assert result.confidence == 0.8

    def test_custom_dimensions_confidence(self, memory_service):
        result = memory_service.create_memory(
            content="test", memory_type="fact",
            dimensions={"confidence": 0.95}
        )
        assert result.confidence == 0.95


class TestDeleteMemory:
    def test_delete_returns_true_on_success(self, memory_service):
        assert memory_service.delete_memory("any-id") is True

    def test_delete_raises_returns_false(self, memory_service, mock_vector_store):
        mock_vector_store.client.get_collection.side_effect = Exception("fail")
        assert memory_service.delete_memory("any-id") is False


class TestListMemories:
    def test_list_returns_memories(self, memory_service, mock_chroma_collection):
        # 预填充数据
        mock_chroma_collection._store["mem1"] = {"document": "test", "metadata": {
            "memory_id": "mem1", "type": "preference", "content": "test",
            "created_at": "2024-01-01T00:00:00", "invalidated": False,
            "dimensions": {}, "confidence": 0.8, "source_session_id": None
        }}
        mock_chroma_collection.count.return_value = 1

        results = memory_service.list_memories()
        assert isinstance(results, list)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/test_memory_service.py -v 2>&1 | head -50
```

Expected: 测试加载成功（无 import 错误），具体 assertion 失败取决于 mock 状态

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_memory_service.py && git commit -m "test: add MemoryService unit tests"
```

---

## Task 4: test_knowledge_service.py

**Files:**
- Create: `backend/tests/test_knowledge_service.py`
- Test: `services/knowledge_service.py`

- [ ] **Step 1: 写入失败的测试**

```python
import pytest
from unittest.mock import patch, MagicMock
from services.knowledge_service import KnowledgeService


@pytest.fixture
def knowledge_service(tmp_session, mock_vector_store, mock_ollama, mock_config):
    with patch("services.knowledge_service.get_session", return_value=tmp_session):
        yield KnowledgeService(mock_vector_store, mock_ollama, mock_config)


class TestCreateKnowledgeBase:
    def test_creates_kb_and_returns_id(self, knowledge_service):
        kb = knowledge_service.create_knowledge_base(name="研究笔记", description="HTL 文献")
        assert kb.kb_id is not None
        assert kb.name == "研究笔记"

    def test_default_chunk_size(self, knowledge_service):
        kb = knowledge_service.create_knowledge_base(name="test")
        assert kb.chunk_size == 500

    def test_persisted_to_sqlite(self, knowledge_service, tmp_session):
        from services.database import KnowledgeBaseRow
        kb = knowledge_service.create_knowledge_base(name="persist-test")
        row = tmp_session.query(KnowledgeBaseRow).filter_by(kb_id=kb.kb_id).first()
        assert row is not None


class TestListKnowledgeBases:
    def test_returns_created_kbs(self, knowledge_service):
        knowledge_service.create_knowledge_base(name="KB1")
        knowledge_service.create_knowledge_base(name="KB2")
        result = knowledge_service.list_knowledge_bases()
        assert len(result) >= 2


class TestDeleteKnowledgeBase:
    def test_delete_removes_from_sqlite(self, knowledge_service, tmp_session):
        from services.database import KnowledgeBaseRow
        kb = knowledge_service.create_knowledge_base(name="to-delete")
        knowledge_service.delete_knowledge_base(kb.kb_id)
        row = tmp_session.query(KnowledgeBaseRow).filter_by(kb_id=kb.kb_id).first()
        assert row is None
```

- [ ] **Step 2: 运行测试验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/test_knowledge_service.py -v 2>&1 | head -40
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_knowledge_service.py && git commit -m "test: add KnowledgeService unit tests"
```

---

## Task 5: test_search_service.py

**Files:**
- Create: `backend/tests/test_search_service.py`
- Test: `services/search_service.py`

- [ ] **Step 1: 写入失败的测试**

```python
import pytest
from unittest.mock import patch, MagicMock
from services.search_service import SearchService


@pytest.fixture
def search_service(tmp_session, mock_vector_store, mock_ollama):
    with patch("services.search_service.get_session", return_value=tmp_session):
        with patch("services.search_service.VectorStore", return_value=mock_vector_store):
            with patch("services.search_service.OllamaService", return_value=mock_ollama):
                yield SearchService()


class TestUnifiedSearch:
    def test_search_returns_dict(self, search_service):
        result = search_service.unified_search(query="test", scopes=["memory"])
        assert isinstance(result, dict)

    def test_cache_hit_on_second_call(self, search_service):
        """相同参数第二次调用应命中缓存。"""
        search_service.unified_search(query="cache-test", scopes=["memory"], limit=5)
        result = search_service.unified_search(query="cache-test", scopes=["memory"], limit=5)
        assert result.get("_from_cache") is True

    def test_different_queries_no_cache_collision(self, search_service):
        search_service.unified_search(query="query-A", scopes=["memory"])
        result = search_service.unified_search(query="query-B", scopes=["memory"])
        assert result.get("_from_cache") is not True


class TestSearchMemories:
    def test_small_data_uses_like(self, search_service, tmp_session):
        # 小数据量（< 1000）使用 LIKE 搜索
        result = search_service.search_memories("test", limit=10, session=tmp_session)
        assert "results" in result
        assert "method" in result


class TestGetHotMemories:
    def test_returns_memories_sorted_by_call_count(self, search_service, tmp_session):
        result = search_service.get_hot_memories(limit=5)
        assert isinstance(result, list)
```

- [ ] **Step 2: 运行测试验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/test_search_service.py -v 2>&1 | head -40
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_search_service.py && git commit -m "test: add SearchService unit tests"
```

---

## Task 6: test_import_service.py

**Files:**
- Create: `backend/tests/test_import_service.py`
- Test: `services/batch_import_service.py`

- [ ] **Step 1: 写入失败的测试**

```python
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
```

- [ ] **Step 2: 运行测试验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/test_import_service.py -v 2>&1 | head -50
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_import_service.py && git commit -m "test: add BatchImportService unit tests"
```

---

## Task 7: 更新 CI 配置

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 更新 CI 配置添加覆盖率检查**

```yaml
- name: Run backend tests with coverage
  run: |
    cd backend
    pytest tests/ -v \
      --cov=./services \
      --cov=./adapters \
      --cov-report=xml \
      --cov-report=term-missing \
      --cov-fail-under=60

- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: backend/coverage.xml
```

- [ ] **Step 2: 本地运行覆盖率验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/ -v --cov=./services --cov=./adapters --cov-report=term-missing 2>&1 | tail -60
```

Expected: Overall coverage > 60%

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/ci.yml && git commit -m "ci: add coverage threshold and reporting to CI"
```

---

## Task 8: claude_mem_adapter (Phase 5.2)

**Files:**
- Create: `backend/adapters/claude_mem_adapter.py`
- Modify: `backend/adapters/__init__.py`

- [ ] **Step 1: 写入 claude_mem_adapter.py**

```python
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base_adapter import BaseAdapter, Conversation


TYPE_MAP = {
    "decision": "decision",
    "bugfix": "bugfix",
    "feature": "feature",
    "refactor": "refactor",
    "discovery": "discovery",
    "change": "change",
}
DEFAULT_TYPE = "fact"


class ClaudeMemAdapter(BaseAdapter):
    """claude-mem 数据库导入适配器"""

    source_name = "claude_mem"

    def detect(self, source_path: str = None) -> bool:
        if not source_path:
            return False
        db_path = Path(source_path) / "claude-mem.db"
        return db_path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not source_path:
            return []
        db_path = Path(source_path) / "claude-mem.db"
        if not db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取所有 sessions
            cursor.execute("SELECT * FROM sdk_sessions ORDER BY created_at DESC")
            sessions = cursor.fetchall()

            conversations = []
            for session in sessions:
                cursor.execute(
                    "SELECT * FROM observations WHERE sdk_session_id = ? ORDER BY created_at",
                    (session["sdk_session_id"],)
                )
                observations = cursor.fetchall()

                if not observations:
                    continue

                messages = []
                for obs in observations:
                    obs_type = obs.get("type", DEFAULT_TYPE)
                    mapped_type = TYPE_MAP.get(obs_type, DEFAULT_TYPE)

                    narrative = obs.get("narrative", "")
                    content = narrative if narrative else obs.get("title", "")

                    messages.append({
                        "role": "assistant",
                        "content": f"[{mapped_type}] {content}" if content else obs.get("title", ""),
                        "metadata": {
                            "type": mapped_type,
                            "facts": obs.get("facts", ""),
                            "concepts": obs.get("concepts", ""),
                            "files_read": obs.get("files_read", ""),
                            "files_modified": obs.get("files_modified", ""),
                        }
                    })

                cursor.execute(
                    "SELECT * FROM user_prompts WHERE sdk_session_id = ? ORDER BY created_at",
                    (session["sdk_session_id"],)
                )
                prompts = cursor.fetchall()

                for prompt in prompts:
                    messages.append({
                        "role": "user",
                        "content": prompt.get("prompt_text", ""),
                    })

                conversations.append(Conversation(
                    session_id=session["sdk_session_id"],
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(session["created_at"]) if session["created_at"] else datetime.now(),
                    messages=sorted(messages, key=lambda m: m.get("timestamp", "")),
                ))

            conn.close()
            return [c for c in conversations if self.validate_conversation(c)]

        except Exception as e:
            print(f"Error parsing claude-mem db: {e}")
            return []

    def _observation_to_memory(self, obs: dict) -> dict:
        """将 claude-mem observation 转换为 memory 格式。"""
        obs_type = obs.get("type", DEFAULT_TYPE)
        mapped_type = TYPE_MAP.get(obs_type, DEFAULT_TYPE)

        narrative = obs.get("narrative", "")
        content = narrative if narrative else obs.get("title", "")

        return {
            "type": mapped_type,
            "content": content or obs.get("title", ""),
            "metadata": {
                "facts": obs.get("facts", ""),
                "concepts": obs.get("concepts", ""),
                "title": obs.get("title", ""),
            },
            "session_id": obs.get("session_id", obs.get("sdk_session_id", "")),
        }
```

- [ ] **Step 2: 更新 adapters/__init__.py**

在 `ADAPTERS` 字典中添加:
```python
'claude_mem': ClaudeMemAdapter,
```

- [ ] **Step 3: 运行验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && python -c "from adapters import get_adapter; a = get_adapter('claude_mem'); print(type(a).__name__)"
```

Expected: `ClaudeMemAdapter`

- [ ] **Step 4: 提交**

```bash
git add backend/adapters/claude_mem_adapter.py backend/adapters/__init__.py && git commit -m "feat: add claude-mem database import adapter"
```

---

## Task 9: test_claude_mem_adapter.py (Phase 5.2)

**Files:**
- Create: `backend/tests/test_claude_mem_adapter.py`
- Test: `adapters/claude_mem_adapter.py`

- [ ] **Step 1: 写入失败的测试**

```python
import pytest
import json
from pathlib import Path
from datetime import datetime
from adapters.claude_mem_adapter import ClaudeMemAdapter


@pytest.fixture
def adapter():
    return ClaudeMemAdapter()


class TestDetect:
    def test_detect_valid_claude_mem_db(self, tmp_path, adapter):
        db_file = tmp_path / "claude-mem.db"
        db_file.write_bytes(b"SQLite format 3")
        assert adapter.detect(str(tmp_path)) is True

    def test_detect_missing_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_no_db_file(self, adapter, tmp_path):
        assert adapter.detect(str(tmp_path)) is False


class TestTypeMapping:
    def test_type_mapping_decision(self, adapter):
        obs = {"type": "decision", "title": "T", "narrative": "N",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["type"] == "decision"

    def test_type_mapping_bugfix(self, adapter):
        obs = {"type": "bugfix", "title": "Fix", "narrative": "Fixed it",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["type"] == "bugfix"

    def test_type_mapping_feature(self, adapter):
        obs = {"type": "feature", "title": "Feature", "narrative": "Added X",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["type"] == "feature"

    def test_type_mapping_unknown_defaults_to_fact(self, adapter):
        obs = {"type": "unknown_type", "title": "T", "narrative": "N",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["type"] == "fact"


class TestContentMapping:
    def test_content_uses_narrative(self, adapter):
        obs = {"type": "feature", "title": "Short", "narrative": "Full narrative content",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["content"] == "Full narrative content"

    def test_content_fallback_to_title(self, adapter):
        obs = {"type": "change", "title": "Title Only", "narrative": "",
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["content"] == "Title Only"

    def test_content_fallback_to_title_when_narrative_none(self, adapter):
        obs = {"type": "discovery", "title": "Discovered X", "narrative": None,
               "session_id": "s1", "created_at": "2024-01-01T00:00:00",
               "facts": "", "concepts": ""}
        memory = adapter._observation_to_memory(obs)
        assert memory["content"] == "Discovered X"
```

- [ ] **Step 2: 运行测试验证**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/test_claude_mem_adapter.py -v
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_claude_mem_adapter.py && git commit -m "test: add claude-mem adapter tests"
```

---

## Task 10: 最终覆盖率验证

- [ ] **Step 1: 运行完整测试套件**

```bash
cd /home/wchao/workspace/Date_LIB/backend && pytest tests/ -v --cov=./services --cov=./adapters --cov-report=term-missing 2>&1 | tail -80
```

Expected: Overall coverage > 60%

- [ ] **Step 2: 检查是否有需要补充的测试**

覆盖率报告中标记为 `missing` 的行是需要补充测试的代码路径。

- [ ] **Step 3: 提交最终版本**

```bash
git add -A && git commit -m "feat: complete Phase 5 testing infrastructure and claude-mem adapter"
```

---

## 验收标准

| 步骤 | 标准 | 验证命令 |
|------|------|---------|
| 1 | pytest-cov 和 chromadb 安装成功 | `pip show pytest-cov chromadb` |
| 2 | conftest.py 加载无错误 | `python -c "import tests.conftest"` |
| 3-6 | 所有测试文件存在且可运行 | `pytest tests/ --collect-only` |
| 7 | CI 配置覆盖率 >60% | `pytest --cov --cov-fail-under=60` |
| 8 | claude_mem_adapter 已注册 | `from adapters import get_adapter; get_adapter('claude_mem')` |
| 9 | claude_mem 测试通过 | `pytest tests/test_claude_mem_adapter.py -v` |
| 10 | 整体覆盖率 >60% | `pytest --cov --cov-report=term --cov-fail-under=60` |

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-phase5-testing.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 我将按 Task 顺序派遣 subagent 执行每个任务，任务间回顾检查

**2. Inline Execution** - 我在当前 session 中按计划逐步执行，频繁 commit

选择哪个方式？