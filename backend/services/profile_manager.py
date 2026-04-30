from typing import Optional
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field


@dataclass
class Profile:
    profile_id: str
    dimensions: dict = field(default_factory=dict)
    summary: str = ""
    updated_at: datetime = field(default_factory=datetime.now)


class ProfileManager:
    """用户画像管理器"""

    def __init__(self):
        self._profiles = {}

    def create_profile(self) -> Profile:
        """创建新画像"""
        profile_id = str(uuid4())
        profile = Profile(
            profile_id=profile_id,
            dimensions={},
            summary="",
            updated_at=datetime.now(),
        )
        self._profiles[profile_id] = profile
        return profile

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        return self._profiles.get(profile_id)

    def update_profile(
        self,
        profile_id: str,
        dimension: str,
        data: dict,
    ) -> Profile:
        """更新画像中的特定维度"""
        profile = self._profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")

        if dimension not in profile.dimensions:
            profile.dimensions[dimension] = []

        profile.dimensions[dimension].append({
            "data": data,
            "updated_at": datetime.now().isoformat(),
        })
        profile.updated_at = datetime.now()

        return profile

    def merge_memories(
        self,
        profile_id: str,
        memories: dict[str, dict],
    ) -> Profile:
        """合并提取的记忆到画像"""
        profile = self._profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")

        for dim, memory_data in memories.items():
            if 'data' in memory_data and 'error' not in memory_data['data']:
                self.update_profile(profile_id, dim, memory_data['data'])

        return profile

    def get_profile_summary(self, profile_id: str) -> str:
        """获取画像摘要"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return ""
        return profile.summary