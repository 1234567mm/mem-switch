import pytest
from adapters.clipboard_adapter import ClipboardAdapter


@pytest.fixture
def adapter():
    return ClipboardAdapter()


class TestSetContent:
    def test_set_content(self, adapter):
        adapter.set_content("User: Hello\nAssistant: Hi")
        assert adapter._clipboard_content == "User: Hello\nAssistant: Hi"


class TestDetect:
    def test_detect_with_content(self, adapter):
        adapter.set_content("some content")
        assert adapter.detect() is True

    def test_detect_empty_content(self, adapter):
        adapter.set_content("")
        assert adapter.detect() is False

    def test_detect_whitespace_only(self, adapter):
        adapter.set_content("   ")
        assert adapter.detect() is False

    def test_detect_none_content(self, adapter):
        adapter.set_content("")
        assert adapter.detect() is False


class TestParse:
    def test_parse_simple_user_assistant(self, adapter):
        adapter.set_content("""User: Hello
Assistant: Hi there!""")
        conversations = adapter.parse()
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 2

    def test_parse_human_role(self, adapter):
        adapter.set_content("""Human: Question
AI: Answer""")
        conversations = adapter.parse()
        assert len(conversations) == 1
        assert conversations[0].messages[0]["role"] == "user"

    def test_parse_ai_role(self, adapter):
        adapter.set_content("""User: Question
Assistant: Answer""")
        conversations = adapter.parse()
        assert len(conversations) == 1
        assert conversations[0].messages[1]["role"] == "assistant"

    def test_parse_empty_content(self, adapter):
        adapter.set_content("")
        conversations = adapter.parse()
        assert len(conversations) == 0

    def test_parse_whitespace_content(self, adapter):
        adapter.set_content("   \n   \n   ")
        conversations = adapter.parse()
        assert len(conversations) == 0

    def test_parse_invalid_format(self, adapter):
        adapter.set_content("This is not in role: format")
        conversations = adapter.parse()
        assert len(conversations) == 0

    def test_parse_multiple_lines(self, adapter):
        adapter.set_content("""User: Line 1
User: Line 2
Assistant: Response""")
        conversations = adapter.parse()
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 3

    def test_parse_session_id(self, adapter):
        adapter.set_content("User: Hello")
        conversations = adapter.parse()
        assert conversations[0].session_id == "clipboard"

    def test_parse_source(self, adapter):
        adapter.set_content("User: Hello")
        conversations = adapter.parse()
        assert conversations[0].source == "clipboard"


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter):
        adapter.set_content("invalid format")
        conversations = adapter.parse()
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter):
        adapter.set_content("""User: Hello
Assistant: Hi""")
        conversations = adapter.parse()
        assert len(conversations) == 1