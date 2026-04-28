# backend/api/schemas/channel.py

from pydantic import BaseModel
from typing import Optional


class ChannelConfig(BaseModel):
    recall_count: int = 5
    similarity_threshold: float = 0.7
    injection_position: str = "system"
    max_tokens: Optional[int] = None


class ChannelResponse(BaseModel):
    id: str
    platform: str
    channel_type: str  # 'default' | 'mem_switch'
    enabled: bool
    auto_record: bool
    config: ChannelConfig
    created_at: str
    updated_at: str


class ChannelUpdate(BaseModel):
    channel_type: Optional[str] = None
    enabled: Optional[bool] = None
    auto_record: Optional[bool] = None
    recall_count: Optional[int] = None
    similarity_threshold: Optional[float] = None
    injection_position: Optional[str] = None
    max_tokens: Optional[int] = None


class ChannelSwitchRequest(BaseModel):
    channel_type: str  # 'default' | 'mem_switch'


class ChannelListResponse(BaseModel):
    channels: list[ChannelResponse]
    global_enabled: bool = True