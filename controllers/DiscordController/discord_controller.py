from enum import Enum
from typing import Awaitable, Callable, Any

from apps.discord_app import DiscordApp
from controllers.AppController.app_controller import AppController
from controllers.DiscordController.health_checks.discord_activity_health_checks import get_discord_activity_health_checks
from controllers.DiscordController.health_checks.discord_app_health_checks import get_discord_app_health_checks
from controllers.controller_types import (
    ActivityHealthCheck,
    CoreHealthCheck,
    ExecutorResponse
)
from utils.broadcaster import Broadcaster

class DiscordAppTaskType(Enum):
    """Define enumeration of tasks assignable to AppTask instances
    These are the tasks which will run within the asynchronous task queue
    and represent high-level chains of action / workflows within the VM interface
    """ 
    JOIN_SERVER = "join_server"
    SEND_MESSAGE = "send_message"
    START_SCREENSHARE = "start_screen_share"
    END_SCREENSHARE = "end_screen_share"
    LAUNCH = "launch"
    FETCH_MESSAGES = "fetch_messages"
    GET_SERVERS = "get_servers"

class DiscordAppActivityType(Enum):
    """Define enumeration of activities assignable to AppController state
    Represents activity states for the Discord client in the virtual machine;
    certain tasks such as 'join_voice_channel' should leave the app with 
    'in_voice_channel' activity being set, with 'leave_voice_channel' unsetting
    the activity.

    Not used to directly execute activites on the virutal machine, but used for 
    conditional HealthCheck injection within the Heartbeat routine, and also for 
    reporting application state to clients.
    """
    IN_VOICE_CHANNEL = "in_voice_channel"
    SCREEN_SHARING = "screen_sharing"

class DiscordHealthCheckType(Enum):
    IS_LOGGED_IN = "is_logged_in"


class DiscordAppController(AppController[DiscordApp, DiscordAppTaskType, DiscordAppActivityType, DiscordHealthCheckType]):
    def __init__(self, broadcaster):
        super().__init__(broadcaster)
        self._app = DiscordApp()

    @property
    def app(self) -> DiscordApp:
        return self._app

    @property
    def app_health_checks(self) -> list[CoreHealthCheck]:
        """TODO: Elaborate
        List of HealthChecks that are imperative to state management, but are not activity based.
        To be checked in heartbeat whenver app is alive
        """
        return get_discord_app_health_checks(self)

    @property
    def activity_health_checks(self) -> dict[DiscordAppActivityType, list[ActivityHealthCheck]]:
        """TODO: Elaborate
        Dictionary of activity indexed HealthCheck lists that are assocaited with specific activity states
        lists may be superset of another health check, i.e. SCREEN_SHARING includes the checks for IN_VOICE_CHANNEL + additional
        """
        return get_discord_activity_health_checks(self)

    async def handle_app_health_failures(self, failed_checks: list[CoreHealthCheck]):
        raise NotImplementedError

    async def handle_activity_health_failures(self, failed_checks: list[ActivityHealthCheck]) -> None:
        raise NotImplementedError


    @property
    def executors(self) -> dict[DiscordAppTaskType, Callable[[DiscordApp, dict[str, Any]], Awaitable[ExecutorResponse | None]]]:
        # return get_discord_executors()
        return {DiscordAppTaskType.JOIN_SERVER: test_executor}

    @property
    def validators(self) -> dict[DiscordAppTaskType, Callable[[dict[str, Any]], bool]]:
        # return get_discord_validators()
        return {DiscordAppTaskType.JOIN_SERVER: test_validator}


async def test_executor(arg1: DiscordApp, params: dict[str, Any]) -> ExecutorResponse | None:
    return ExecutorResponse("MESSAGES",
                            {"message-id:ujg932j2":{
                                "time":952195.21,
                                "sender_id":"231ujg03",
                                "content":"Hello stinky"
                                }
                            })
def test_validator(params: dict[str, Any]) -> bool:
    return True
