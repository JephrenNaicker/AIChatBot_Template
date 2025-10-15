# models/bot.py
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class Bot:
    def __init__(
            self,
            name: str,
            emoji: str = "🤖",
            desc: str = "",
            tags: List[str] = None,
            status: str = "draft",
            scenario: str = "",
            personality: Dict[str, Any] = None,
            system_rules: str = "",
            appearance: Dict[str, Any] = None,
            voice: Dict[str, Any] = None,
            custom: bool = True,
            creator: str = "anonymous",
            bot_id: str = None,
            created_at: str = None
    ):
        self.bot_id = bot_id or str(uuid.uuid4())
        self.name = name
        self.emoji = emoji
        self.desc = desc
        self.tags = tags or []
        self.status = status  # "draft" or "published"
        self.scenario = scenario
        self.personality = personality or {
            "tone": "Friendly",
            "traits": [],
            "greeting": ""
        }
        self.system_rules = system_rules
        self.appearance = appearance or {
            "description": "",
            "avatar_type": "emoji",  # "emoji", "uploaded", "generated"
            "avatar_data": None  # base64 string or file path
        }
        self.voice = voice or {
            "enabled": False,
            "emotion": "neutral"
        }
        self.custom = custom
        self.creator = creator
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert bot instance to dictionary for serialization"""
        return {
            "bot_id": self.bot_id,
            "name": self.name,
            "emoji": self.emoji,
            "desc": self.desc,
            "tags": self.tags,
            "status": self.status,
            "scenario": self.scenario,
            "personality": self.personality,
            "system_rules": self.system_rules,
            "appearance": self.appearance,
            "voice": self.voice,
            "custom": self.custom,
            "creator": self.creator,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bot':
        """Create Bot instance from dictionary"""
        return cls(
            bot_id=data.get("bot_id"),
            name=data["name"],
            emoji=data.get("emoji", "🤖"),
            desc=data.get("desc", ""),
            tags=data.get("tags", []),
            status=data.get("status", "draft"),
            scenario=data.get("scenario", ""),
            personality=data.get("personality", {}),
            system_rules=data.get("system_rules", ""),
            appearance=data.get("appearance", {}),
            voice=data.get("voice", {}),
            custom=data.get("custom", True),
            creator=data.get("creator", "anonymous"),
            created_at=data.get("created_at")
        )

    def update_from_form_data(self, form_data: Dict[str, Any]):
        """Update bot from form data (used in create/edit)"""
        self.name = form_data["basic"]["name"]
        self.emoji = form_data["basic"]["emoji"]
        self.desc = form_data["basic"]["desc"]
        self.tags = form_data["tags"]
        self.status = form_data["status"]
        self.scenario = form_data.get("scenario", "")

        # Update personality
        self.personality = {
            "tone": form_data["personality"].get("tone", "Friendly"),
            "traits": form_data["personality"]["traits"],
            "greeting": form_data["personality"]["greeting"]
        }

        # Update system rules
        self.system_rules = form_data.get("system_rules", "")

        # Update appearance
        self.appearance = {
            "description": form_data["appearance"]["description"],
            "avatar_type": form_data["appearance"].get("avatar_type", "emoji"),
            "avatar_data": form_data["appearance"].get("avatar_data")
        }

        # Update voice
        self.voice = form_data.get("voice", {"enabled": False})

    def is_published(self) -> bool:
        return self.status == "published"

    def has_voice(self) -> bool:
        return self.voice.get("enabled", False)

    def get_avatar_display(self) -> str:
        """Get what to display for avatar (emoji or indication of image)"""
        if self.appearance.get("avatar_type") == "emoji":
            return self.emoji
        elif self.appearance.get("avatar_type") in ["uploaded", "generated"]:
            return "🖼️"  # Indicate image avatar
        return self.emoji