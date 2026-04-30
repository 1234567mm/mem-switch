import pytest
import json
from pathlib import Path
from adapters.claude_code_adapter import ClaudeCodeAdapter


@pytest.fixture
def adapter():
    return ClaudeCodeAdapter()


class TestDetect:
    def test_detect_existing_path(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)
        assert adapter.detect(str(projects_dir)) is True

    def test_detect_nonexistent_path(self, adapter):
        assert adapter.detect("/nonexistent/path") is False

    def test_detect_none_path(self):
        adapter = ClaudeCodeAdapter()
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

    def test_parse_single_project_with_session(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "session.jsonl"
        conv_file.write_text(json.dumps({
            "id": "claude-code-123",
            "created_at": "2024-01-01T00:00:00",
            "project": "test_project",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "claude-code-123"
        assert len(conversations[0].messages) == 2

    def test_parse_multiple_projects(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        for i in range(2):
            project_dir = projects_dir / f"project_{i}"
            project_dir.mkdir()
            conv_dir = project_dir / "conversations"
            conv_dir.mkdir()
            conv_file = conv_dir / "conv.jsonl"
            conv_file.write_text(json.dumps({
                "id": f"conv-{i}",
                "messages": [{"role": "user", "content": f"Msg {i}"}],
                "created_at": "2024-01-01T00:00:00"
            }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 2

    def test_parse_multiple_sessions_in_project(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "my_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        for i in range(2):
            conv_file = conv_dir / f"session_{i}.jsonl"
            conv_file.write_text(json.dumps({
                "id": f"session-{i}",
                "messages": [{"role": "user", "content": f"Msg {i}"}],
                "created_at": "2024-01-01T00:00:00"
            }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 2

    def test_parse_invalid_jsonl_line(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "invalid.jsonl"
        conv_file.write_text("{ invalid json }\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 0

    def test_parse_missing_id(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "no_id.jsonl"
        conv_file.write_text(json.dumps({
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T00:00:00"
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 1
        assert conversations[0].session_id == "no_id"

    def test_parse_missing_created_at(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "no_time.jsonl"
        conv_file.write_text(json.dumps({
            "id": "test",
            "messages": [{"role": "user", "content": "Hello"}]
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 1
        assert conversations[0].timestamp is not None

    def test_parse_missing_messages(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "no_msgs.jsonl"
        conv_file.write_text(json.dumps({
            "id": "test",
            "created_at": "2024-01-01T00:00:00"
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 0

    def test_parse_no_conversations_dir(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 0

    def test_parse_non_project_file(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        conv_file = projects_dir / "not_a_project.jsonl"
        conv_file.write_text(json.dumps({
            "id": "should-be-ignored",
            "messages": [{"role": "user", "content": "Hello"}]
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 0


class TestParseJsonlFile:
    def test_parse_jsonl_single_line(self, adapter, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(json.dumps({
            "id": "jsonl-test",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T00:00:00"
        }) + "\n")

        convs = adapter._parse_jsonl_file(jsonl_file)
        assert len(convs) == 1

    def test_parse_jsonl_multiple_lines(self, adapter, tmp_path):
        jsonl_file = tmp_path / "multi.jsonl"
        content = "\n".join([
            json.dumps({"id": f"conv-{i}", "messages": [{"role": "user", "content": f"Msg {i}"}], "created_at": "2024-01-01T00:00:00"})
            for i in range(3)
        ])
        jsonl_file.write_text(content + "\n")

        convs = adapter._parse_jsonl_file(jsonl_file)
        assert len(convs) == 3

    def test_parse_jsonl_with_empty_lines(self, adapter, tmp_path):
        jsonl_file = tmp_path / "empty_lines.jsonl"
        content = json.dumps({"id": "test", "messages": [{"role": "user", "content": "Hello"}], "created_at": "2024-01-01T00:00:00"}) + "\n\n\n"
        jsonl_file.write_text(content)

        convs = adapter._parse_jsonl_file(jsonl_file)
        assert len(convs) == 1

    def test_parse_jsonl_with_invalid_line(self, adapter, tmp_path):
        jsonl_file = tmp_path / "mixed.jsonl"
        content = "\n".join([
            json.dumps({"id": "valid-1", "messages": [{"role": "user", "content": "Valid"}], "created_at": "2024-01-01T00:00:00"}),
            "{ invalid }",
            json.dumps({"id": "valid-2", "messages": [{"role": "user", "content": "Also valid"}], "created_at": "2024-01-01T00:00:00"})
        ])
        jsonl_file.write_text(content + "\n")

        convs = adapter._parse_jsonl_file(jsonl_file)
        assert len(convs) == 2


class TestValidateConversation:
    def test_validate_empty_messages(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "empty.jsonl"
        conv_file.write_text(json.dumps({
            "id": "empty-test",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 0

    def test_validate_valid_conversation(self, adapter, tmp_path):
        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir()

        conv_file = conv_dir / "valid.jsonl"
        conv_file.write_text(json.dumps({
            "id": "valid-claude",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ],
            "created_at": "2024-01-01T00:00:00"
        }) + "\n")

        conversations = adapter.parse(str(projects_dir))
        assert len(conversations) == 1
