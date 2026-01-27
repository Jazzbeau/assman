from dataclasses import dataclass
from typing import Literal


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
    channels: list[DiscordChannel]
