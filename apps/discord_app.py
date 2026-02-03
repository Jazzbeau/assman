from typing import Literal

from apps.discord_session import DiscordSession
from apps.managed_app import ManagedApp
from apps.types import ProcessConfig, ProcessProperties
from assman_types import JSONType
from config import config
from models.discord_server import DiscordChannel, DiscordServer


class DiscordApp(ManagedApp):
    process_config = ProcessConfig(
        process_name="discord",
        process_params=[f"--remote-debugging-port={config.DISCORD_RPC_PORT}"],
        wm_class_target="discord",
        wm_name_target="discord",
    )

    @property
    def name(self):
        return "discord"

    def __init__(self):
        self.process_properties: ProcessProperties | None = None
        self.session: DiscordSession | None = None

    async def focus(self):
        raise NotImplementedError()

    # Heartbeat implementations

    async def is_interactable(self) -> bool:
        # DEBUG REMOVE ME DEBUG REMOVE ME
        return True
        # raise NotImplementedError()

    async def is_locatable(self) -> bool:
        # DEBUG REMOVE ME DEBUG REMOVE ME
        return True
        raise NotImplementedError()

    # is_running is actually implemented in base class

    # Playwright Setup
    async def start_playwright(self):
        self.session = DiscordSession(self)
        if not await self.is_running():
            raise RuntimeError(
                "Cannot start playwright on uninitilaised application instance"
            )
        await self.session.start()

    async def learn_servers(self):
        if not self.session:
            raise RuntimeError("Cannot learn servers without playwright initialisation")
        await self.session.learn_servers()

    async def learn_channels(self, server: DiscordServer):
        if not self.session:
            raise RuntimeError(
                "Cannot learn channels from server without playwright initialisation"
            )
        await self.session.learn_channels(server)

    # Getters

    def get_servers(self) -> list[dict[str, JSONType]]:
        if not self.session:
            raise RuntimeError("Cannot fetch servers without playwright initialisation")
        server_list = [
            server.to_dict() for server in self.session.get_servers_as_list()
        ]
        return server_list

    def get_channels(
        self, channel_type: Literal["any", "voice", "text"] = "any"
    ) -> list[dict[str, JSONType]]:
        if not self.session:
            raise RuntimeError("Cannot fetch server without playwright initialisation")
        channels = [
            channel.to_dict() for channel in self.session.get_channels(channel_type)
        ]
        return channels

    def get_server_by_id(self, id) -> DiscordServer:
        if not self.session:
            raise RuntimeError("Cannot fetch server without playwright initialisation")
        return self.session.get_server_by_id(id)

    def get_channel_by_id(self, id) -> DiscordChannel:
        if not self.session:
            raise RuntimeError("Cannot fetch channel without playwright initialisation")
        return self.session.get_channel_by_id(id)

    def get_channels_by_name(
        self,
        name: str,
        strict_match: bool = True,
        case_sensitive=True,
        channel_type: Literal["all", "voice", "text"] = "all",
    ) -> list[DiscordChannel]:
        if not self.session:
            raise RuntimeError(
                "Cannot fetch channel by name without playwright initialisation"
            )
        return self.session.get_channels_by_name(
            name, strict_match, case_sensitive, channel_type
        )

    def get_servers_by_name(
        self,
        name: str,
        strict_match=True,
        case_sensitive=True,
    ) -> list[DiscordServer]:
        if not self.session:
            raise RuntimeError(
                "Cannot fetch channel by name without playwright initialisation"
            )
        return self.session.get_servers_by_name(name, strict_match, case_sensitive)
