from pydantic import BaseModel


class ModelRecommendationResponse(BaseModel):
    tier: str
    recommended_llm: list[str]
    recommended_embedding: str
    label: str
