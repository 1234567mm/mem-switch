from pydantic import BaseModel


class OllamaStatusResponse(BaseModel):
    connected: bool
    models_count: int


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None


class PullModelRequest(BaseModel):
    model: str


class PullModelResponse(BaseModel):
    status: str
    model: str
    error: str | None = None
