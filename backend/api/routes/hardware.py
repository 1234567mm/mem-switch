from fastapi import APIRouter
from services.hardware_detector import detect_hardware, recommend_models
from api.schemas.hardware import ModelRecommendationResponse

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/detect", response_model=ModelRecommendationResponse)
async def detect():
    hw = detect_hardware()
    rec = recommend_models(hw)
    return ModelRecommendationResponse(
        tier=rec["tier"],
        recommended_llm=rec["recommended_llm"],
        recommended_embedding=rec["recommended_embedding"],
        label=rec["label"],
    )
