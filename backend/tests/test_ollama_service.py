from unittest.mock import patch, MagicMock
import pytest

from services.ollama_service import OllamaService


class TestOllamaServiceInit:
    """Test __init__ method"""

    def test_init_with_config_string(self):
        """Test init with config as host string"""
        service = OllamaService(config="http://custom:11434")
        assert service.host == "http://custom:11434"

    def test_init_with_config_dict(self):
        """Test init with config as dict"""
        service = OllamaService(config={"ollama_host": "http://custom:11434"})
        assert service.host == "http://custom:11434"

    def test_init_with_config_dict_no_host(self):
        """Test init with config dict without host"""
        service = OllamaService(config={})
        assert service.host == "http://127.0.0.1:11434"

    def test_init_with_host_param(self):
        """Test init with host parameter"""
        service = OllamaService(host="http://hostparam:11434")
        assert service.host == "http://hostparam:11434"

    def test_init_with_no_params(self):
        """Test init with no parameters defaults"""
        service = OllamaService()
        assert service.host == "http://127.0.0.1:11434"

    def test_init_host_overrides_config(self):
        """Test host param overrides config dict"""
        service = OllamaService(config={"ollama_host": "http://config:11434"}, host="http://host:11434")
        assert service.host == "http://host:11434"


class TestOllamaServiceClient:
    """Test _client method"""

    @patch('services.ollama_service.ollama.Client')
    def test_client_returns_ollama_client(self, mock_client_class):
        """Test _client returns ollama.Client with correct host"""
        service = OllamaService(host="http://test:11434")
        client = service._client()
        mock_client_class.assert_called_once_with(host="http://test:11434")


class TestIsConnected:
    """Test is_connected method"""

    @patch('services.ollama_service.ollama.Client')
    def test_is_connected_success(self, mock_client_class):
        """Test is_connected returns True on success"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {}

        service = OllamaService(host="http://test:11434")
        assert service.is_connected() is True

    @patch('services.ollama_service.ollama.Client')
    def test_is_connected_failure(self, mock_client_class):
        """Test is_connected returns False on exception"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.side_effect = Exception("Connection failed")

        service = OllamaService(host="http://test:11434")
        assert service.is_connected() is False


class TestListModels:
    """Test list_models method"""

    @patch('services.ollama_service.ollama.Client')
    def test_list_models_success(self, mock_client_class):
        """Test list_models returns formatted models"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            "models": [
                {"name": "model1", "size": 1000, "modified_at": "2024-01-01"},
                {"name": "model2", "size": 2000, "modified_at": "2024-01-02"},
            ]
        }

        service = OllamaService(host="http://test:11434")
        result = service.list_models()

        assert len(result) == 2
        assert result[0]["name"] == "model1"
        assert result[0]["size"] == 1000
        assert result[1]["name"] == "model2"

    @patch('services.ollama_service.ollama.Client')
    def test_list_models_empty(self, mock_client_class):
        """Test list_models returns empty list when no models"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {"models": []}

        service = OllamaService(host="http://test:11434")
        result = service.list_models()

        assert result == []

    @patch('services.ollama_service.ollama.Client')
    def test_list_models_failure(self, mock_client_class):
        """Test list_models returns empty list on exception"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.side_effect = Exception("Failed")

        service = OllamaService(host="http://test:11434")
        result = service.list_models()

        assert result == []

    @patch('services.ollama_service.ollama.Client')
    def test_list_models_missing_keys(self, mock_client_class):
        """Test list_models handles missing keys gracefully"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            "models": [
                {"name": "model1"},
                {"size": 1000},
                {},
            ]
        }

        service = OllamaService(host="http://test:11434")
        result = service.list_models()

        assert result[0]["name"] == "model1"
        assert result[0]["size"] == 0
        assert result[0]["modified_at"] == ""


class TestPullModel:
    """Test pull_model method"""

    @patch('services.ollama_service.ollama.Client')
    def test_pull_model_success(self, mock_client_class):
        """Test pull_model returns success status"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance

        service = OllamaService(host="http://test:11434")
        result = service.pull_model("test-model")

        assert result["status"] == "success"
        assert result["model"] == "test-model"

    @patch('services.ollama_service.ollama.Client')
    def test_pull_model_failure(self, mock_client_class):
        """Test pull_model returns error status on exception"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.pull.side_effect = Exception("Download failed")

        service = OllamaService(host="http://test:11434")
        result = service.pull_model("test-model")

        assert result["status"] == "error"
        assert result["model"] == "test-model"
        assert "Download failed" in result["error"]


class TestEmbed:
    """Test embed method"""

    @patch('services.ollama_service.ollama.Client')
    def test_embed_success(self, mock_client_class):
        """Test embed returns embeddings"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        service = OllamaService(host="http://test:11434")
        result = service.embed("test text")

        assert result == [0.1, 0.2, 0.3]

    @patch('services.ollama_service.ollama.Client')
    def test_embed_default_model(self, mock_client_class):
        """Test embed uses default model"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.embeddings.return_value = {"embedding": [0.1]}

        service = OllamaService(host="http://test:11434")
        service.embed("test text")

        mock_instance.embeddings.assert_called_once_with(model="nomic-embed-text", prompt="test text")

    @patch('services.ollama_service.ollama.Client')
    def test_embed_failure(self, mock_client_class):
        """Test embed returns empty list on exception"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.embeddings.side_effect = Exception("Failed")

        service = OllamaService(host="http://test:11434")
        result = service.embed("test text")

        assert result == []


class TestGenerate:
    """Test generate method"""

    @patch('services.ollama_service.ollama.Client')
    def test_generate_success(self, mock_client_class):
        """Test generate returns response text"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.generate.return_value = {"response": "Generated text"}

        service = OllamaService(host="http://test:11434")
        result = service.generate("test prompt")

        assert result == "Generated text"

    @patch('services.ollama_service.ollama.Client')
    def test_generate_default_model(self, mock_client_class):
        """Test generate uses default model"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.generate.return_value = {"response": "text"}

        service = OllamaService(host="http://test:11434")
        service.generate("test prompt")

        mock_instance.generate.assert_called_once_with(model="qwen2.5:7b", prompt="test prompt")

    @patch('services.ollama_service.ollama.Client')
    def test_generate_failure(self, mock_client_class):
        """Test generate returns error message on exception"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.generate.side_effect = Exception("Generation failed")

        service = OllamaService(host="http://test:11434")
        result = service.generate("test prompt")

        assert "Error:" in result
        assert "Generation failed" in result
