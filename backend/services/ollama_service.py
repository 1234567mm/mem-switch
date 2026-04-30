import ollama


class OllamaService:
    def __init__(self, config=None, host: str = None):
        if host:
            self.host = host
        elif isinstance(config, str):
            self.host = config
        elif config:
            self.host = config.get("ollama_host", "http://127.0.0.1:11434")
        else:
            self.host = "http://127.0.0.1:11434"

    def _client(self):
        return ollama.Client(host=self.host)

    def is_connected(self) -> bool:
        try:
            self._client().list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[dict]:
        try:
            resp = self._client().list()
            models = resp.get("models", [])
            return [
                {
                    "name": m.get("name", ""),
                    "size": m.get("size", 0),
                    "modified_at": m.get("modified_at", ""),
                }
                for m in models
            ]
        except Exception:
            return []

    def pull_model(self, model_name: str) -> dict:
        try:
            self._client().pull(model_name)
            return {"status": "success", "model": model_name}
        except Exception as e:
            return {"status": "error", "model": model_name, "error": str(e)}

    def embed(self, text: str, model: str = "nomic-embed-text") -> list[float]:
        """Generate embeddings for text."""
        try:
            resp = self._client().embeddings(model=model, prompt=text)
            return resp.get("embedding", [])
        except Exception as e:
            return []

    def generate(self, prompt: str, model: str = "qwen2.5:7b") -> str:
        """Generate text response."""
        try:
            resp = self._client().generate(model=model, prompt=prompt)
            return resp.get("response", "")
        except Exception as e:
            return f"Error: {e}"
