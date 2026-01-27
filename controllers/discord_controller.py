from enum import Enum
from typing import Type

from controllers.controller import AppController
from controllers.task import AppTask
from utils.broadcaster import Broadcaster


class ManagedApp:
    pass


class DiscordApp(ManagedApp):
    pass


class DiscordAppController(AppController):
    class DiscordTasks(Enum):
        JOINSERVER = "join_server"
        SENDMESSAGE = "send_message"
        STARTSCREENSHARE = "start_screen_share"
        ENDSCREENSHARE = "end_screen_share"
        LAUNCH = "launch"
        FETCHMESSAGES = "fetch_messages"
        GETSERVERS = "get_servers"

    @property
    def AppTasks(self) -> Type[Enum]:
        return DiscordAppController.DiscordTasks

    @property
    def app_name(self) -> str:
        return "discord"

    async def create_app(self):
        pass

    async def update_health(self):
        health_checks = [
            # If is_running fails -> status = stopped
            (self.HealthStatus.STOPPED, self.app.is_running),
            # If can_locate_window fails -> status = missing
            (self.HealthStatus.MISSING, self.app.can_locate_window),
            # If can_interact fails > status = degraded
            (self.HealthStatus.DEGRADED, self.app.can_interact),
        ]

        # Assume best case
        status = self.HealthStatus.RUNNING
        for fail_status, check in health_checks:
            if not await check():
                status = fail_status
                # Ordered from most -> least severe; break at most severe
                break

        self.health_status = status

    async def execute_task(self, task: AppTask):
        if task.type not in self.valid_task_types:
            # Task is not in union of generic AppTasks or app specific AppTasks
            raise AttributeError(
                f"Task: [{task.type}] was not found in valid task types"
            )

        if task.type == "get_servers":
            server_data = await self.app.get_servers()
            return server_data

        if task.type == "join_server":
            # TODO: Validate task parmam shape
            await self.app.join_server(task.params["server_id"])


discord_app = DiscordApp()
broadcaster = Broadcaster()
dac = DiscordAppController(discord_app, broadcaster)
