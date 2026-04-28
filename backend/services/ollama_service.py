import ollama


class OllamaService:
    def __init__(self, host: str):
        self.host = host

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
