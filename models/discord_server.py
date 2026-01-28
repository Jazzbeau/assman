from dataclasses import dataclass
from typing import Literal

from requests import utils

import apps.discord_session_utils as utils


@dataclass
class DiscordChannel:
    id: str
    server_id: str
    name: str
    type: Literal["voice", "text"]


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
