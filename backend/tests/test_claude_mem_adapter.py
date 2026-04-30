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