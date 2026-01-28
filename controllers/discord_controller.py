from enum import Enum

from apps.discord_app import DiscordApp
from controllers.controller import AppController
from controllers.task import AppTask


class DiscordTasks(Enum):
    JOINSERVER = "join_server"
    SENDMESSAGE = "send_message"
    STARTSCREENSHARE = "start_screen_share"
    ENDSCREENSHARE = "end_screen_share"
    LAUNCH = "launch"
    FETCHMESSAGES = "fetch_messages"
    GETSERVERS = "get_servers"


class DiscordAppController(AppController):

    def __init__(self, broadcaster):
        super().__init__(broadcaster)
        self.app = DiscordApp()

    @property
    def app_name(self) -> str:
        return "discord"

    async def get_app(self):
        return DiscordApp()

    async def execute_task(self, task: AppTask):
        if task.type == "get_servers":
            server_data = await self.app.get_servers()
            return server_data

        if task.type == "join_server":
            # TODO: Validate task parmam shape
            await self.app.join_server(task.params["server_id"])
