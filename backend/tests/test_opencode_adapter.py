import pytest
from pathlib import Path
from adapters.opencode_adapter import OpenCodeAdapter


@pytest.fixture
def adapter():
    return OpenCodeAdapter()


class TestDetect:
    def test_detect_existing_path(self, adapter, tmp_path):
        history_dir = tmp_path / ".opencode" / "history"
        history_dir.mkdir(parents=True)
        assert adapter.detect(str(history_dir)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_none_path(self):
        adapter = OpenCodeAdapter()
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

    def test_parse_single_markdown_session(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "test_session.md"
        session_file.write_text("""## User
Hello
## Assistant
Hi there""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "test_session"
        assert len(conversations[0].messages) == 2

    def test_parse_multiple_markdown_sessions(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        for i in range(2):
            session_file = history_dir / f"session_{i}.md"
            session_file.write_text(f"""## User
Message {i}
## Assistant
Response {i}""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 2

    def test_parse_nested_sessions(self, adapter, tmp_path):
        history_dir = tmp_path / "history" / "nested"
        history_dir.mkdir(parents=True)

        session_file = history_dir / "nested.md"
        session_file.write_text("""## User
Nested
## Assistant
Session""")

        conversations = adapter.parse(str(tmp_path / "history"))
        assert len(conversations) >= 1

    def test_parse_bold_user_assistant(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "bold_format.md"
        session_file.write_text("""**User**
Bold User
**Assistant**
Bold Assistant""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 2

    def test_parse_multiline_content(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "multiline.md"
        session_file.write_text("""## User
Line 1
Line 2
Line 3
## Assistant
Response""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert "Line 1" in conversations[0].messages[0]["content"]
        assert "Line 2" in conversations[0].messages[0]["content"]

    def test_parse_only_user(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "user_only.md"
        session_file.write_text("""## User
Only user message""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1

    def test_parse_non_md_files_ignored(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        md_file = history_dir / "valid.md"
        md_file.write_text("""## User
Hello""")

        txt_file = history_dir / "ignore.txt"
        txt_file.write_text("This should be ignored")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1


class TestParseMarkdownSession:
    def test_parse_markdown_session_user_assistant(self, adapter):
        content = """## User
Hello
## Assistant
Hi"""
        conv = adapter._parse_markdown_session(content, "test")
        assert len(conv.messages) == 2
        assert conv.session_id == "test"
        assert conv.messages[0]["role"] == "user"
        assert conv.messages[1]["role"] == "assistant"

    def test_parse_markdown_session_bold_format(self, adapter):
        content = """**User**
Bold user
**Assistant**
Bold assistant"""
        conv = adapter._parse_markdown_session(content, "bold")
        assert len(conv.messages) == 2

    def test_parse_markdown_session_multiline(self, adapter):
        content = """## User
Line 1
Line 2
Line 3
## Assistant
Response"""
        conv = adapter._parse_markdown_session(content, "multi")
        assert len(conv.messages) == 2
        assert "Line 1" in conv.messages[0]["content"]

    def test_parse_markdown_session_no_assistant(self, adapter):
        content = """## User
Only user"""
        conv = adapter._parse_markdown_session(content, "user_only")
        assert len(conv.messages) == 1

    def test_parse_markdown_session_empty(self, adapter):
        content = ""
        conv = adapter._parse_markdown_session(content, "empty")
        assert len(conv.messages) == 0


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "empty.md"
        session_file.write_text("No headers here")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        session_file = history_dir / "valid.md"
        session_file.write_text("""## User
Hello
## Assistant
Hi""")

        conversations = adapter.parse(str(history_dir))
        assert len(conversations) == 1
