# models/profile.py
from typing import Dict, Any
from datetime import datetime


class Profile:
    def __init__(
            self,
            username: str,
            display_name: str = "",
            bio: str = "",
            avatar: str = "👤",
            theme: str = "system",
            created_at: str = None
    ):
        self.username = username
        self.display_name = display_name or username
        self.bio = bio
        self.avatar = avatar
        self.theme = theme
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar": self.avatar,
            "theme": self.theme,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        return cls(
            username=data["username"],
            display_name=data.get("display_name", data["username"]),
            bio=data.get("bio", ""),
            avatar=data.get("avatar", "👤"),
            theme=data.get("theme", "system"),
            created_at=data.get("created_at")
        )

    def update(self, updates: Dict[str, Any]):
        """Update profile with new data"""
        for key, value in updates.items():
            if hasattr(self, key) and key != "username":  # username shouldn't be changed
                setattr(self, key, value)