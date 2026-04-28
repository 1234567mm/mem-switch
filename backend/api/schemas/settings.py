from pydantic import BaseModel


class AppConfigResponse(BaseModel):
    ollama_host: str
    llm_model: str
    embedding_model: str
    qdrant_host: str
    qdrant_port: int
    memory_expiry_days: int
    extract_dimensions: list[str]


class AppConfigUpdate(BaseModel):
    ollama_host: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None
    memory_expiry_days: int | None = None
