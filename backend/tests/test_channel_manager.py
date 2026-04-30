import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from services.channel_manager import ChannelManager


@pytest.fixture
def mock_config():
    return Mock()


@pytest.fixture
def manager(mock_config):
    return ChannelManager(mock_config)


class TestListChannels:
    @patch("services.channel_manager.get_session")
    def test_list_channels_empty(self, mock_get_session, manager):
        mock_session = Mock()
        mock_session.query.return_value.all.return_value = []
        mock_get_session.return_value = mock_session

        result = manager.list_channels()
        assert result == []

    @patch("services.channel_manager.get_session")
    def test_list_channels_with_data(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 1
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config_row
        mock_session.query.return_value.all.return_value = [mock_row]
        mock_get_session.return_value = mock_session

        result = manager.list_channels()
        assert len(result) == 1
        assert result[0].platform == "claude_code"


class TestGetChannel:
    @patch("services.channel_manager.get_session")
    def test_get_channel_found(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 1
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_row, mock_config_row]
        mock_get_session.return_value = mock_session

        result = manager.get_channel("claude_code")
        assert result is not None
        assert result.platform == "claude_code"

    @patch("services.channel_manager.get_session")
    def test_get_channel_not_found(self, mock_get_session, manager):
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session

        result = manager.get_channel("nonexistent")
        assert result is None


class TestUpdateChannel:
    @patch("services.channel_manager.get_session")
    def test_update_channel_not_found(self, mock_get_session, manager):
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session

        result = manager.update_channel("nonexistent", {"channel_type": "api"})
        assert result is None

    @patch("services.channel_manager.get_session")
    def test_update_channel_type(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 1
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_row, mock_config_row]
        mock_get_session.return_value = mock_session

        result = manager.update_channel("claude_code", {"channel_type": "api"})
        assert result is not None

    @patch("services.channel_manager.get_session")
    def test_update_enabled(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 0
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_row, mock_config_row]
        mock_get_session.return_value = mock_session

        result = manager.update_channel("claude_code", {"enabled": True})
        assert result is not None
        assert result.enabled is True


class TestSwitchChannel:
    @patch("services.channel_manager.get_session")
    def test_switch_channel(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 1
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_row, mock_config_row]
        mock_get_session.return_value = mock_session

        result = manager.switch_channel("claude_code", "api")
        assert result is not None
        assert result.channel_type == "api"


class TestSetEnabled:
    @patch("services.channel_manager.get_session")
    def test_set_enabled_true(self, mock_get_session, manager):
        mock_row = Mock()
        mock_row.id = "ch-1"
        mock_row.platform = "claude_code"
        mock_row.channel_type = "local"
        mock_row.enabled = 0
        mock_row.auto_record = 0
        mock_row.created_at = "2024-01-01T00:00:00"
        mock_row.updated_at = "2024-01-02T00:00:00"

        mock_config_row = Mock()
        mock_config_row.recall_count = 5
        mock_config_row.similarity_threshold = 0.7
        mock_config_row.injection_position = "system"
        mock_config_row.max_tokens = None

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_row, mock_config_row]
        mock_get_session.return_value = mock_session

        result = manager.set_enabled("claude_code", True)
        assert result is True

    @patch("services.channel_manager.get_session")
    def test_set_enabled_not_found(self, mock_get_session, manager):
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session

        result = manager.set_enabled("nonexistent", True)
        assert result is False
