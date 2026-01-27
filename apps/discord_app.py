from apps.discord_session import DiscordSession
from apps.managed_app import ManagedApp
from apps.types import ProcessConfig, ProcessProperties
from config import config


class DiscordApp(ManagedApp):
    process_config = ProcessConfig(
        process_name="discord",
        process_params=[f"--remote-debugging-port={config.DISCORD_RPC_PORT}"],
        wm_class_target="discord",
        wm_name_target="discord",
    )

    def __init__(self):
        self.process_properties: ProcessProperties | None = None
        self.session: DiscordSession | None = None

    def can_interact(self) -> bool:
        raise NotImplementedError()
        return True

    def can_locate_window(self) -> bool:
        raise NotImplementedError()
        return True

    async def focus(self):
        raise NotImplementedError()
        pass

    async def start_playwright(self):
        self.session = DiscordSession(self)
        if not self.is_running():
            raise ValueError(
                "Cannot start playwright on uninitilaised application instance"
            )
        await self.session.start()
