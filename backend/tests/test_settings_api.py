from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_settings():
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_host" in data
    assert "embedding_model" in data


def test_update_settings():
    resp = client.put("/api/settings", json={"llm_model": "qwen2.5:7b"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm_model"] == "qwen2.5:7b"
