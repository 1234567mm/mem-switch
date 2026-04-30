import pytest
import json
from pathlib import Path
from adapters.codex_adapter import CodexAdapter


@pytest.fixture
def adapter():
    return CodexAdapter()


class TestDetect:
    def test_detect_existing_path(self, adapter, tmp_path):
        sessions_dir = tmp_path / ".codex" / "sessions"
        sessions_dir.mkdir(parents=True)
        assert adapter.detect(str(sessions_dir)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_none_path(self, adapter):
        # Result depends on whether default path exists in test environment
        result = adapter.detect(None)
        assert isinstance(result, bool)


class TestParse:
    def test_parse_nonexistent_path(self, adapter):
        conversations = adapter.parse("/nonexistent/path")
        assert len(conversations) == 0

    def test_parse_empty_directory(self, adapter, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        conversations = adapter.parse(str(empty_dir))
        assert len(conversations) == 0

    def test_parse_single_session(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "test.json"
        session_data = {
            "id": "codex-session-123",
            "created_at": "2024-01-01T00:00:00",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]
        }
        session_file.write_text(json.dumps(session_data))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "codex-session-123"
        assert len(conversations[0].messages) == 2

    def test_parse_multiple_sessions(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        for i in range(2):
            session_file = sessions_dir / f"session_{i}.json"
            session_file.write_text(json.dumps({
                "id": f"codex-{i}",
                "messages": [{"role": "user", "content": f"Msg {i}"}],
                "created_at": "2024-01-01T00:00:00"
            }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 2

    def test_parse_nested_sessions(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions" / "nested"
        sessions_dir.mkdir(parents=True)

        session_file = sessions_dir / "nested.json"
        session_file.write_text(json.dumps({
            "id": "nested-codex",
            "messages": [{"role": "user", "content": "Nested"}],
            "created_at": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(tmp_path / "sessions"))
        assert len(conversations) >= 1

    def test_parse_invalid_json(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        invalid_file = sessions_dir / "invalid.json"
        invalid_file.write_text("{ invalid }")

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 0

    def test_parse_missing_id(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_id.json"
        session_file.write_text(json.dumps({
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        # Falls back to filename stem
        assert conversations[0].session_id == "no_id"

    def test_parse_missing_created_at(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_timestamp.json"
        session_file.write_text(json.dumps({
            "id": "test",
            "messages": [{"role": "user", "content": "Hello"}]
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        assert conversations[0].timestamp is not None

    def test_parse_missing_messages(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_messages.json"
        session_file.write_text(json.dumps({
            "id": "test",
            "created_at": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 0


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "empty.json"
        session_file.write_text(json.dumps({
            "id": "empty-test",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 0

    def test_validate_valid(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "valid.json"
        session_file.write_text(json.dumps({
            "id": "valid-codex",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1