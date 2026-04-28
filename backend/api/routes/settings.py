from fastapi import APIRouter
from config import AppConfig
from api.schemas.settings import AppConfigResponse, AppConfigUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])
_config = AppConfig()


@router.get("", response_model=AppConfigResponse)
async def get_settings():
    return AppConfigResponse(**_config.as_dict())


@router.put("", response_model=AppConfigResponse)
async def update_settings(data: AppConfigUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    _config.update(updates)
    return AppConfigResponse(**_config.as_dict())
