from enum import Enum

from apps.discord_app import DiscordApp
from controllers.controller import AppController
from controllers.controller_types import (
    HealthCheck,
)
from controllers.task import AppTask


class DiscordTasks(Enum):
    JOIN_SERVER = "join_server"
    SEND_MESSAGE = "send_message"
    START_SCREENSHARE = "start_screen_share"
    END_SCREENSHARE = "end_screen_share"
    LAUNCH = "launch"
    FETCH_MESSAGES = "fetch_messages"
    GET_SERVERS = "get_servers"

class DiscordHealthCheckType(Enum):
    IS_LOGGED_IN = "is_logged_in"
    IS_IN_VOICE_CHANNEL = "is_in_voice_channel"
    IS_STREAMING = "is_streaming"

class DiscordAppController(AppController):
    def __init__(self, broadcaster):
        super().__init__(broadcaster)

    @property
    def app_name(self) -> str:
        return "discord"

    async def get_app(self):
        return DiscordApp()

    async def execute_task(self, task: AppTask):
        if task.type == "get_servers":
            server_data = self.app.get_servers()
            return server_data

        if task.type == "join_server":
            # TODO: Validate task parmam shape
            await self.app.join_server(task.params["server_id"])

    async def handle_app_check_failures(self, failed_checks: list[HealthCheck]) -> None:
        for check in failed_checks:
            match check.check_type:
                case '':

        raise NotImplementedError

    def get_app_health_checks(self) -> list[HealthCheck]:
        raise NotImplementedError
