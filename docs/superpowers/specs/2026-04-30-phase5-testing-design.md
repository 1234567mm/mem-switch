# Phase 5: Testing and Stabilization — Design Spec

## Overview

**Goal**: Achieve >60% backend test coverage, establishing a reliable testing foundation for Mem-Switch.

**Scope**:
- Phase 5.1: Testing infrastructure and core route tests
- Phase 5.2: claude-mem import adapter development

**Timeline**: Sequential — Phase 5.1 completes before Phase 5.2 begins.

---

## 1. Test Infrastructure

### 1.1 Dependencies

Add to `backend/requirements.txt`:
```
pytest-cov>=4.1.0
```

### 1.2 Database Strategy

**Approach**: Independent temporary SQLite databases per test.

| Property | Value |
|----------|-------|
| Mode | WAL (Write-Ahead Logging) |
| Location | `tmp_path` fixture (pytest built-in) |
| Cleanup | Automatic via fixture teardown |
| Naming | `test_{uuid}.db` |

**Why**: WAL mode mirrors production behavior while maintaining test isolation. Independent databases per test enable parallel execution.

### 1.3 Fixtures (conftest.py)

```python
# tmp_db: Creates isolated temporary database
@pytest.fixture
def tmp_db(tmp_path):
    """Creates independent temporary SQLite with WAL mode."""
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}")
    # Initialize tables...
    yield engine
    # Cleanup via tmp_path automatic cleanup

# db_with_memories: Pre-populated test data
@pytest.fixture
def db_with_memories(tmp_db):
    """Creates database with 5 test Memory records."""
    # Returns (session, memory_ids)

# mock_ollama: Ollama embedding mock
@pytest.fixture
def mock_ollama():
    """Returns mock embedding vector [0.1] * 768."""

# mock_vector_store: Qdrant client mock
@pytest.fixture
def mock_vector_store():
    """Returns mocked VectorStore with upsert/delete/search."""
```

### 1.4 External Dependencies

| Dependency | Strategy |
|------------|----------|
| Qdrant | Mock (real Qdrant requires Docker) |
| Ollama | Mock (real Ollama may not be running) |
| SQLite | Real (using tmp databases) |

**Rationale**: Qdrant and Ollama are integration points. Unit tests should run without external services. Integration tests (optional Phase 6) can use real services.

---

## 2. Test File Structure

### 2.1 Existing Tests (minimal changes)

| File | Status |
|------|--------|
| `test_health_api.py` | Keep as-is |
| `test_settings_api.py` | Keep as-is |
| `test_hardware_detector.py` | Keep as-is |

### 2.2 New Test Files

```
backend/tests/
├── conftest.py                 # Shared fixtures (NEW: fixtures)
├── test_memory_api.py          # NEW: ~15% coverage
├── test_knowledge_api.py       # NEW: ~15% coverage
├── test_search_api.py          # NEW: ~10% coverage
├── test_import_api.py          # NEW: ~10% coverage
├── test_health_api.py          # Existing
├── test_settings_api.py        # Existing
└── test_hardware_detector.py    # Existing
```

### 2.3 Coverage Targets by Module

| Module | Target | Tests |
|--------|--------|-------|
| `memory_service.py` | 80% | CRUD, expire, stats |
| `knowledge_service.py` | 80% | KB CRUD, documents |
| `search_service.py` | 70% | query, history, hot |
| `batch_import_service.py` | 70% | import flow, task status |
| Routes (memory, knowledge, search) | 80% | HTTP status, response shape |

**Aggregate target**: >60% overall backend coverage.

---

## 3. Test Specifications

### 3.1 test_memory_api.py

```python
# Tests for MemoryService and /api/memory routes

class TestMemoryService:
    def test_create_memory(self, tmp_db, mock_ollama, mock_vector_store):
        """Create memory with valid content."""
        # Arrange
        service = MemoryService(vector_store, ollama, config)
        # Act
        result = service.create_memory(content="Test memory", memory_type="feature")
        # Assert
        assert result.memory_id is not None
        assert result.content == "Test memory"

    def test_list_memories(self, db_with_memories):
        """List returns all non-deleted memories."""
        # Assert length matches fixture

    def test_update_memory(self, db_with_memories):
        """Update modifies content and updates call_count."""
        # Assert updated fields

    def test_delete_memory(self, db_with_memories):
        """Delete marks as deleted (soft delete)."""
        # Assert not in list results

    def test_expire_memory(self, db_with_memories):
        """Expire sets expired_at timestamp."""
        # Assert expired_at is not None

    def test_get_statistics(self, db_with_memories):
        """Statistics returns counts by type."""
        # Assert type counts
```

### 3.2 test_knowledge_api.py

```python
class TestKnowledgeService:
    def test_create_knowledge_base(self, tmp_db):
        """Create KB with name and description."""

    def test_list_knowledge_bases(self, tmp_db):
        """List returns all KBs."""

    def test_add_document(self, tmp_db):
        """Add document to KB updates document_count."""

    def test_delete_knowledge_base(self, tmp_db):
        """Delete removes KB and associated documents."""
```

### 3.3 test_search_api.py

```python
class TestSearchService:
    def test_search_query(self, tmp_db, mock_vector_store):
        """Search returns relevant results."""

    def test_search_history(self, tmp_db):
        """History returns recent queries."""

    def test_hot_searches(self, tmp_db):
        """Hot returns most frequent queries."""

    def test_cache_behavior(self, tmp_db, mock_vector_store):
        """Second search hits cache (faster)."""
```

### 3.4 test_import_api.py

```python
class TestBatchImportService:
    def test_import_json_file(self, tmp_path, mock_ollama, mock_vector_store):
        """Import JSON file creates memories."""

    def test_import_skips_duplicates(self, tmp_path, db_with_memories):
        """Already imported session is skipped."""

    def test_import_task_status(self, tmp_db):
        """Task status reflects progress."""

    def test_preview_import(self, tmp_path):
        """Preview returns session info without importing."""
```

---

## 4. CI Integration

### 4.1 GitHub Actions (ci.yml)

```yaml
- name: Run backend tests
  run: |
    cd backend
    pytest tests/ -v --cov=./services --cov-report=xml --cov-report=term

- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: backend/coverage.xml
```

### 4.2 Coverage Reporting

| Report Type | Purpose |
|------------|---------|
| `coverage.xml` | GitHub Actions artifact / Codecov upload |
| `coverage/term` | CI console output |

---

## 5. Phase 5.2: claude-mem Import Adapter

### 5.1 Compatibility

| claude-mem Field | Mem-Switch Mapping |
|-----------------|-------------------|
| `observations.session_id` | `MemoryRow.source_session_id` |
| `observations.type` | `MemoryRow.type` (direct map) |
| `observations.title` | `MemoryRow.content` (first 200 chars) |
| `observations.narrative` | `MemoryRow.content` (full) |
| `observations.facts` | metadata JSON |
| `observations.concepts` | metadata JSON |
| `sessions` | `SessionRow` (reused) |
| `user_prompts` | messages array in session |

### 5.2 New Adapter

```
backend/adapters/claude_mem_adapter.py  # NEW
```

Supports:
- JSON import with observations/sessions/user_prompts
- Type mapping: decision/bugfix/feature/refactor/discovery/change
- Batch memory extraction from imported observations

---

## 6. Acceptance Criteria

### Phase 5.1

| Criterion | Verification |
|-----------|--------------|
| pytest-cov installed | `pip install pytest-cov` succeeds |
| All tests pass | `pytest tests/ -v` passes |
| Coverage >60% | `pytest --cov=./services --cov-report=term` shows >60% |
| CI passes | GitHub Actions CI job succeeds |
| No external dependencies | Tests run without Docker/Qdrant/Ollama |

### Phase 5.2

| Criterion | Verification |
|-----------|--------------|
| claude-mem JSON imports | `import_conversations(source_type="claude_mem", ...)` works |
| Type mapping correct | observation.type → MemoryRow.type |
| Session linkage | memories linked to source_session_id |

---

## 7. Out of Scope

- Frontend tests (P2, deferred)
- Integration tests with real Qdrant/Ollama (P3, optional Phase 6)
- Performance testing
- Load testing

---

## 8. Notes

- Tests use `TestClient` from `starlette.testclient` for API route testing (no server startup needed)
- Mock Ollama returns fixed vector `[0.1] * 768` (matches embedding dimension)
- Database fixture creates fresh schema each time (no migration testing in P5)
