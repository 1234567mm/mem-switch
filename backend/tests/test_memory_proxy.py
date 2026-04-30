import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.memory_proxy import MemoryProxy


class TestMemoryProxyInit:
    """Test __init__"""

    def test_init_sets_attributes(self):
        mock_channel_manager = MagicMock()
        mock_memory_injector = MagicMock()
        mock_ollama_service = MagicMock()
        mock_config = MagicMock()
        mock_config.get.return_value = "http://127.0.0.1:11434"

        proxy = MemoryProxy(mock_channel_manager, mock_memory_injector, mock_ollama_service, mock_config)

        assert proxy.channel_manager == mock_channel_manager
        assert proxy.memory_injector == mock_memory_injector
        assert proxy.ollama == mock_ollama_service
        assert proxy.config == mock_config
        assert proxy.ollama_host == "http://127.0.0.1:11434"


class TestMergeUserMessages:
    """Test _merge_user_messages"""

    def test_merge_user_messages(self):
        proxy = MemoryProxy(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "how are you"},
        ]
        result = proxy._merge_user_messages(messages)
        assert result == "hello how are you"

    def test_merge_user_messages_with_dict_content(self):
        proxy = MemoryProxy(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        messages = [
            {"role": "user", "content": {"text": "hello"}},
            {"role": "user", "content": "world"},
        ]
        result = proxy._merge_user_messages(messages)
        assert result == "world"

    def test_merge_user_messages_empty(self):
        proxy = MemoryProxy(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        messages = [
            {"role": "assistant", "content": "hi"},
        ]
        result = proxy._merge_user_messages(messages)
        assert result == ""


class TestForwardToOllama:
    """Test _forward_to_ollama"""

    @pytest.mark.asyncio
    async def test_forward_success(self):
        proxy = MemoryProxy(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        proxy.ollama_host = "http://127.0.0.1:11434"

        with patch('services.memory_proxy.httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await proxy._forward_to_ollama({"model": "test"})

            assert result == {"response": "test response"}
