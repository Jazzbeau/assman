from dataclasses import dataclass
from typing import Literal

import apps.discord_session_utils as utils
from assman_types import JSONType


@dataclass
class DiscordChannel:
    id: str
    server_id: str
    name: str
    type: Literal["voice", "text"]

    def to_dict(self) -> dict[str, JSONType]:
        return {
            "id": self.id,
            "server_id": self.server_id,
            "name": self.name,
            "type": self.type,
        }


@dataclass
class DiscordServer:
    id: str
    name: str
    image_url: str
    channels: dict[str, DiscordChannel]

    def get_channels(
        self, type: Literal["any", "text", "voice"]
    ) -> list[DiscordChannel]:
        return utils.get_channels(self.channels, type)

    def to_dict(self) -> dict[str, JSONType]:
        return {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
            "channels": {
                channel_id: channel.to_dict()
                for channel_id, channel in self.channels.items()
            },
        }
