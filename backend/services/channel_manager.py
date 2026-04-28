# backend/services/channel_manager.py

from typing import Optional
from datetime import datetime
from uuid import uuid4

from services.database import get_session, ChannelRow, ChannelConfigRow, PlatformSettingsRow
from api.schemas.channel import ChannelResponse, ChannelConfig


class ChannelManager:
    PLATFORMS = ["claude_code", "codex", "openclaw", "opencode", "gemini_cli", "hermes"]

    def __init__(self, config):
        self.config = config

    def list_channels(self) -> list[ChannelResponse]:
        session = get_session()
        try:
            rows = session.query(ChannelRow).all()
            channels = []
            for row in rows:
                config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
                channels.append(self._row_to_response(row, config_row))
            return channels
        finally:
            session.close()

    def get_channel(self, platform: str) -> Optional[ChannelResponse]:
        session = get_session()
        try:
            row = session.query(ChannelRow).filter_by(platform=platform).first()
            if not row:
                return None
            config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
            return self._row_to_response(row, config_row)
        finally:
            session.close()

    def update_channel(self, platform: str, data: dict) -> Optional[ChannelResponse]:
        session = get_session()
        try:
            row = session.query(ChannelRow).filter_by(platform=platform).first()
            if not row:
                return None

            # 更新 channel 字段
            if "channel_type" in data and data["channel_type"]:
                row.channel_type = data["channel_type"]
            if "enabled" in data and data["enabled"] is not None:
                row.enabled = 1 if data["enabled"] else 0
            if "auto_record" in data and data["auto_record"] is not None:
                row.auto_record = 1 if data["auto_record"] else 0
            row.updated_at = datetime.now().isoformat()

            # 更新 config 字段
            config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
            if config_row:
                if "recall_count" in data and data["recall_count"] is not None:
                    config_row.recall_count = data["recall_count"]
                if "similarity_threshold" in data and data["similarity_threshold"] is not None:
                    config_row.similarity_threshold = data["similarity_threshold"]
                if "injection_position" in data and data["injection_position"]:
                    config_row.injection_position = data["injection_position"]
                if "max_tokens" in data:
                    config_row.max_tokens = data["max_tokens"]

            session.commit()
            return self._row_to_response(row, config_row)
        finally:
            session.close()

    def switch_channel(self, platform: str, channel_type: str) -> Optional[ChannelResponse]:
        return self.update_channel(platform, {"channel_type": channel_type})

    def set_enabled(self, platform: str, enabled: bool) -> bool:
        result = self.update_channel(platform, {"enabled": enabled})
        return result is not None

    def _row_to_response(self, row: ChannelRow, config_row: ChannelConfigRow) -> ChannelResponse:
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