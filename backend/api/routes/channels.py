# backend/api/routes/channels.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4

from services.channel_manager import ChannelManager
from api.schemas.channel import (
    ChannelResponse, ChannelUpdate, ChannelSwitchRequest,
    ChannelListResponse, ChannelConfig,
)
from config import AppConfig

router = APIRouter(prefix="/api/channels", tags=["channels"])
channel_mgr = ChannelManager(AppConfig())


def _row_to_response(row, config_row, config: AppConfig) -> ChannelResponse:
    return ChannelResponse(
        id=row.id,
        platform=row.platform,
        channel_type=row.channel_type,
        enabled=bool(row.enabled),
        auto_record=bool(row.auto_record),
        config=ChannelConfig(
            recall_count=config_row.recall_count if config_row else 5,
            similarity_threshold=config_row.similarity_threshold if config_row else 0.7,
            injection_position=config_row.injection_position if config_row else "system",
            max_tokens=config_row.max_tokens if config_row else None,
        ),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=ChannelListResponse)
async def list_channels():
    channels = channel_mgr.list_channels()
    return ChannelListResponse(channels=channels)


@router.get("/status")
async def channels_status():
    """获取所有通道状态"""
    channels = channel_mgr.list_channels()
    return {
        "channels": [
            {
                "platform": ch.platform,
                "channel_type": ch.channel_type,
                "enabled": ch.enabled,
                "connected": ch.enabled,
            }
            for ch in channels
        ]
    }


@router.get("/{platform}", response_model=ChannelResponse)
async def get_channel(platform: str):
    channel = channel_mgr.get_channel(platform)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return channel


@router.put("/{platform}", response_model=ChannelResponse)
async def update_channel(platform: str, data: ChannelUpdate):
    channel = channel_mgr.update_channel(platform, data.model_dump(exclude_none=True))
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return channel


@router.post("/{platform}/switch", response_model=ChannelResponse)
async def switch_channel(platform: str, data: ChannelSwitchRequest):
    result = channel_mgr.switch_channel(platform, data.channel_type)
    if not result:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return result


@router.post("/{platform}/enable")
async def toggle_channel(platform: str, enabled: bool):
    success = channel_mgr.set_enabled(platform, enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return {"status": "ok", "platform": platform, "enabled": enabled}