import pytest
import json
from pathlib import Path
from adapters.gemini_cli_adapter import GeminiCLIAdapter


@pytest.fixture
def adapter():
    return GeminiCLIAdapter()


class TestDetect:
    def test_detect_existing_path(self, adapter, tmp_path):
        history_dir = tmp_path / ".gemini" / "history"
        history_dir.mkdir(parents=True)
        assert adapter.detect(str(history_dir)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_none_path(self):
        adapter = GeminiCLIAdapter()
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
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "gemini_session.json"
        session_data = {
            "id": "gemini-123",
            "create_time": "2024-01-01T00:00:00",
            "turns": [
                {
                    "role": "user",
                    "parts": [{"text": "Hello"}]
                },
                {
                    "role": "model",
                    "parts": [{"text": "Hi there"}]
                }
            ]
        }
        session_file.write_text(json.dumps(session_data))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "gemini-123"
        assert len(conversations[0].messages) == 2

    def test_parse_multiple_sessions(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        for i in range(2):
            session_file = history_dir / f"session_{i}.json"
            session_file.write_text(json.dumps({
                "id": f"gemini-{i}",
                "create_time": "2024-01-01T00:00:00",
                "turns": [
                    {"role": "user", "parts": [{"text": f"Msg {i}"}]}
                ]
            }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 2

    def test_parse_nested_sessions(self, adapter, tmp_path):
        history_dir = tmp_path / "history" / "nested"
        history_dir.mkdir(parents=True)

        session_file = history_dir / "nested.json"
        session_file.write_text(json.dumps({
            "id": "nested-gemini",
            "create_time": "2024-01-01T00:00:00",
            "turns": [
                {"role": "user", "parts": [{"text": "Nested"}]}
            ]
        }))

        conversations = adapter.parse(str(tmp_path / "history"))
        assert len(conversations) >= 1

    def test_parse_invalid_json(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        invalid_file = history_dir / "invalid.json"
        invalid_file.write_text("{ invalid }")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 0

    def test_parse_missing_id(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "no_id.json"
        session_file.write_text(json.dumps({
            "create_time": "2024-01-01T00:00:00",
            "turns": [
                {"role": "user", "parts": [{"text": "Hello"}]}
            ]
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "no_id"

    def test_parse_missing_create_time(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "no_time.json"
        session_file.write_text(json.dumps({
            "id": "test",
            "turns": [
                {"role": "user", "parts": [{"text": "Hello"}]}
            ]
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert conversations[0].timestamp is not None

    def test_parse_missing_turns(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "no_turns.json"
        session_file.write_text(json.dumps({
            "id": "test",
            "create_time": "2024-01-01T00:00:00"
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 0

    def test_parse_multiple_parts(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "multi_parts.json"
        session_file.write_text(json.dumps({
            "id": "multi-parts",
            "create_time": "2024-01-01T00:00:00",
            "turns": [
                {
                    "role": "user",
                    "parts": [{"text": "Part 1"}, {"text": "Part 2"}]
                }
            ]
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 2


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "empty.json"
        session_file.write_text(json.dumps({
            "id": "empty-test",
            "create_time": "2024-01-01T00:00:00",
            "turns": []
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "valid.json"
        session_file.write_text(json.dumps({
            "id": "valid-gemini",
            "create_time": "2024-01-01T00:00:00",
            "turns": [
                {"role": "user", "parts": [{"text": "Hello"}]},
                {"role": "model", "parts": [{"text": "Hi"}]}
            ]
        }))

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
