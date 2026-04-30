import pytest
import json
from pathlib import Path
from adapters.json_file_adapter import JSONFileAdapter


@pytest.fixture
def adapter():
    return JSONFileAdapter()


class TestDetect:
    def test_detect_json_file(self, adapter, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("{}")
        assert adapter.detect(str(json_file)) is True

    def test_detect_uppercase_extension(self, adapter, tmp_path):
        json_file = tmp_path / "data.JSON"
        json_file.write_text("{}")
        assert adapter.detect(str(json_file)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/file.json") is False

    def test_detect_non_json_file(self, adapter, tmp_path):
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("plain text")
        assert adapter.detect(str(txt_file)) is False

    def test_detect_none_path(self, adapter):
        assert adapter.detect(None) is False

    def test_detect_directory(self, adapter, tmp_path):
        assert adapter.detect(str(tmp_path)) is False


class TestParse:
    def test_parse_array_format(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Hello"}]))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1
        assert conversations[0].session_id == "test"
        assert len(conversations[0].messages) == 1

    def test_parse_dict_with_messages(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps({"messages": [{"role": "user", "content": "Hi"}]}))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1

    def test_parse_dict_single_object(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps({"role": "user", "content": "Single"}))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1

    def test_parse_empty_array(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("[]")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_nonexistent_file(self, adapter):
        conversations = adapter.parse("/nonexistent/file.json")
        assert len(conversations) == 0

    def test_parse_invalid_json(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("{ invalid json }")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_number_json(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("123")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_string_json(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('"just a string"')
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_null_json(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("null")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_timestamp(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Hello"}]))
        conversations = adapter.parse(str(json_file))
        assert conversations[0].timestamp is not None

    def test_parse_source_field(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Hello"}]))
        conversations = adapter.parse(str(json_file))
        assert conversations[0].source == "json_file"


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("[]")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Hello"}]))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1