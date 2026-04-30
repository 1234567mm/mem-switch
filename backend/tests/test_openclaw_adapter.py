import pytest
import json
from pathlib import Path
from datetime import datetime
from adapters.openclaw_adapter import OpenClawAdapter


@pytest.fixture
def adapter():
    return OpenClawAdapter()


class TestDetect:
    def test_detect_existing_path(self, adapter, tmp_path):
        sessions_dir = tmp_path / ".openclaw" / "sessions"
        sessions_dir.mkdir(parents=True)
        assert adapter.detect(str(sessions_dir)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_none_path(self):
        # Result depends on whether ~/.openclaw/sessions exists in test environment
        adapter = OpenClawAdapter()
        result = adapter.detect(None)
        assert isinstance(result, bool)


class TestParse:
    def test_parse_nonexistent_base_path(self, adapter):
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

        session_file = sessions_dir / "test_session.json"
        session_data = {
            "session_id": "openclaw-123",
            "conversation": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ],
            "timestamp": "2024-01-01T00:00:00"
        }
        session_file.write_text(json.dumps(session_data))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "openclaw-123"
        assert len(conversations[0].messages) == 2

    def test_parse_multiple_sessions(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        for i in range(2):
            session_file = sessions_dir / f"session_{i}.json"
            session_file.write_text(json.dumps({
                "session_id": f"openclaw-{i}",
                "conversation": [{"role": "user", "content": f"Msg {i}"}],
                "timestamp": "2024-01-01T00:00:00"
            }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 2

    def test_parse_nested_sessions(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions" / "nested"
        sessions_dir.mkdir(parents=True)

        session_file = sessions_dir / "nested.json"
        session_file.write_text(json.dumps({
            "session_id": "nested-openclaw",
            "conversation": [{"role": "user", "content": "Nested"}],
            "timestamp": "2024-01-01T00:00:00"
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

    def test_parse_missing_session_id(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_id.json"
        session_file.write_text(json.dumps({
            "conversation": [{"role": "user", "content": "Hello"}],
            "timestamp": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "no_id"

    def test_parse_missing_timestamp(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_timestamp.json"
        session_file.write_text(json.dumps({
            "session_id": "test",
            "conversation": [{"role": "user", "content": "Hello"}]
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
        assert conversations[0].timestamp is not None

    def test_parse_missing_conversation(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "no_conv.json"
        session_file.write_text(json.dumps({
            "session_id": "test",
            "timestamp": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 0


class TestValidateConversation:
    def test_validate_empty_conversation(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "empty.json"
        session_file.write_text(json.dumps({
            "session_id": "empty-test",
            "conversation": [],
            "timestamp": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "valid.json"
        session_file.write_text(json.dumps({
            "session_id": "valid-openclaw",
            "conversation": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ],
            "timestamp": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(sessions_dir))
        assert len(conversations) == 1
