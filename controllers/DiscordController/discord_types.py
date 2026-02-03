from enum import Enum
from typing import Protocol

from apps.discord_app import DiscordApp


class DiscordAppControllerProtocol(Protocol):
    app: DiscordApp


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
    LEARN_SERVERS = "learn_servers"


class DiscordHealthCheckType(Enum):
    IS_LOGGED_IN = "is_logged_in"
