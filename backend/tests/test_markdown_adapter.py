import pytest
from pathlib import Path
from adapters.markdown_adapter import MarkdownAdapter


@pytest.fixture
def adapter():
    return MarkdownAdapter()


class TestDetect:
    def test_detect_md_file(self, adapter, tmp_path):
        md_file = tmp_path / "conversation.md"
        md_file.write_text("# Test")
        assert adapter.detect(str(md_file)) is True

    def test_detect_markdown_file(self, adapter, tmp_path):
        md_file = tmp_path / "conversation.markdown"
        md_file.write_text("# Test")
        assert adapter.detect(str(md_file)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/file.md") is False

    def test_detect_non_markdown_file(self, adapter, tmp_path):
        txt_file = tmp_path / "conversation.txt"
        txt_file.write_text("plain text")
        assert adapter.detect(str(txt_file)) is False

    def test_detect_none_path(self, adapter):
        assert adapter.detect(None) is False


class TestParse:
    def test_parse_simple_conversation(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# User
Hello, how are you?

# Assistant
I'm doing great!
""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1
        assert conversations[0].session_id == "test"
        assert len(conversations[0].messages) == 2

    def test_parse_conversation_with_code_blocks(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""## User
Write a function

## Assistant
```python
def hello():
    return "world"
```
""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 2

    def test_parse_empty_file(self, adapter, tmp_path):
        md_file = tmp_path / "empty.md"
        md_file.write_text("")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 0

    def test_parse_nonexistent_file(self, adapter):
        conversations = adapter.parse("/nonexistent/file.md")
        assert len(conversations) == 0

    def test_parse_user_format(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""User: Hello
Assistant: Hi there!""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1

    def test_parse_ai_format(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""AI: Response
Human: Question""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1

    def test_parse_ai_format_capital(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""Assistant: Response
Human: Question""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1

    def test_parse_multiline_content(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""User: Line 1
Line 2
Line 3

Assistant: Answer 1
Answer 2""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1
        user_msg = conversations[0].messages[0]
        assert "Line 1" in user_msg["content"]
        assert "Line 2" in user_msg["content"]


class TestValidateConversation:
    def test_validate_single_message_is_valid(self, adapter, tmp_path):
        # Single message is still valid (base_adapter only requires messages exist)
        md_file = tmp_path / "test.md"
        md_file.write_text("User: Hello")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1

    def test_validate_valid_conversation(self, adapter, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""User: Hello
Assistant: Hi""")
        conversations = adapter.parse(str(md_file))
        assert len(conversations) == 1