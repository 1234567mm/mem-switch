import pytest
import json
from pathlib import Path
from adapters.generic_adapter import GenericAdapter


@pytest.fixture
def adapter():
    return GenericAdapter()


class TestDetect:
    def test_detect_existing_file(self, adapter, tmp_path):
        file = tmp_path / "data.json"
        file.write_text("{}")
        assert adapter.detect(str(file)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/file") is False

    def test_detect_none_path(self, adapter):
        assert adapter.detect(None) is False

    def test_detect_directory(self, adapter, tmp_path):
        # GenericAdapter detects any existing path, including directories
        assert adapter.detect(str(tmp_path)) is True


class TestParse:
    def test_parse_json_array(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Hello"}]))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1

    def test_parse_json_dict_with_messages(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps({"messages": [{"role": "user", "content": "Hi"}]}))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1

    def test_parse_json_single_object(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps({"role": "user", "content": "Single"}))
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 1

    def test_parse_json_empty_array(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("[]")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_json_invalid(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("{ invalid }")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_json_non_array_or_object(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('"just a string"')
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0

    def test_parse_markdown(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""User: Hello
Assistant: Hi""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1

    def test_parse_text_role_format(self, adapter, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("""User: Hello
Assistant: Hi""")
        conversations = adapter.parse(str(txt_file))
        assert len(conversations) == 1

    def test_parse_text_human_format(self, adapter, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("""Human: Question
AI: Answer""")
        conversations = adapter.parse(str(txt_file))
        assert len(conversations) == 1

    def test_parse_nonexistent_file(self, adapter):
        conversations = adapter.parse("/nonexistent/file.json")
        assert len(conversations) == 0

    def test_parse_invalid_json_non_list(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text("123")
        conversations = adapter.parse(str(json_file))
        assert len(conversations) == 0


class TestPrivateMethods:
    def test_parse_json_method(self, adapter, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"role": "user", "content": "Test"}]))
        result = adapter._parse_json(json_file)
        assert len(result) == 1

    def test_parse_text_method(self, adapter, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("User: Hello")
        result = adapter._parse_text(txt_file)
        assert len(result) == 1


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("invalid format line")
        conversations = adapter.parse(str(txt_file))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("""User: Hello
Assistant: Hi""")
        conversations = adapter.parse(str(txt_file))
        assert len(conversations) == 1