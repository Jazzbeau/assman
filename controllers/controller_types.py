from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable, Dict, Generic, List, TypeAlias, TypeVar, Union

from apps.managed_app import ManagedApp

# Generics for AppController subclass definitions
ManagedAppType = TypeVar("ManagedAppType", bound="ManagedApp")
ManagedAppTaskType = TypeVar("ManagedAppTaskType", bound="Enum")
AppActivityType = TypeVar("AppActivityType", bound="Enum")

JSONType = Union[str, int, float, bool, None, Dict[str, "JSONType"], List["JSONType"]]


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


@dataclass
class ExecutorResponse:
    response_name: str
    payload: dict[str, JSONType]

    def to_dict(self) -> dict[str, JSONType]:
        return {"response_name": self.response_name, **self.payload}


@dataclass
class AppActivity(Generic[AppActivityType]):
    activity_type: AppActivityType
    initialiser: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    terminator: str | None = None
    # Need to specify to make a new dict for EVERY instance; otherwise `{}` will share
    metadata: dict[str, JSONType] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONType]:
        response = {}
        response["activity_type"] = self.activity_type.value
        response["initialiser"] = self.initialiser
        if self.start_time:
            response["start_time"] = datetime.fromtimestamp(
                self.start_time, tz=timezone.utc
            ).isoformat()
        else:
            response["start_time"] = None
        if self.end_time:
            response["end_time"] = datetime.fromtimestamp(
                self.end_time, tz=timezone.utc
            ).isoformat()
        else:
            response["end_time"] = None
        response["terminator"] = self.terminator
        response["metadata"] = self.metadata
        return response


# Health Management Types


class HealthState(Enum):
    HEALTHY = "healthy"
    UNINITIALISED = "uninitialised"
    ERROR = "error"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPED = "stopped"


class BaseHealthCheckType(Enum):
    RUNNING = "running"
    INTERACTABLE = "interactable"
    VISIBLE = "visible"


AppHealthCheckType = TypeVar("AppHealthCheckType", bound="Enum")


@dataclass
class CoreHealthCheck(Generic[AppHealthCheckType]):
    check_type: Union[AppHealthCheckType, BaseHealthCheckType]
    executor: Callable[[], Awaitable[bool]]

    async def execute(self) -> bool:
        return await self.executor()


@dataclass
class ActivityHealthCheck(Generic[AppActivityType]):
    check_type: AppActivityType
    executor: Callable[[], Awaitable[bool]]

    async def execute(self) -> bool:
        return await self.executor()


HealthCheckT: TypeAlias = Union[
    CoreHealthCheck[AppHealthCheckType], ActivityHealthCheck[AppActivityType]
]
