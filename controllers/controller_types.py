from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, TypeAlias, TypeVar, Union

from apps.discord_app import DiscordApp
from apps.managed_app import ManagedApp
from assman_types import JSONType

# Generics for AppController subclass definitions


ValidatorCallable: TypeAlias = Callable[[dict[str, Any]], bool]


class HealthFailure(Enum):
    CRITICAL = "critical"


class AppBroadcastType(Enum):
    TASK_RUNNING = "task_running"
    TASK_UPDATE = "task_update"
    TASK_FINISH = "task_finish"
    TASK_ERROR = "task_error"
    TASK_CREATE = "task_create"
    HEALTH_UPDATE = "health_update"
    HEALTH_ERROR = "health_error"
    ACTIVITY_START = "activity_start"
    ACTIVITY_END = "activity_end"
    APP_LAUNCH = "app_launch"
    APP_TERMINATE = "app_terminate"
    APP_UPDATE = "app_udate"
    APP_RESPONSE = "app_response"


# Health Management Types
