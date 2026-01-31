from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Any, TypeVar
from apps.managed_app import ManagedApp


class HealthState(Enum):
    INITIALISING = "initialising"
    HEALTHY = "healthy"
    STOPPED = "stopped"
    MISSING = "missing"
    ERROR = "error"
    DEGRADED = "degraded"


class GenericTaskType(Enum):
    HEALTH_UPDATE = "health_update"
    TASK_UPDATE = "task_update"


class BaseHealthCheckType(Enum):
    IS_RUNNING = "is_running"
    IS_INTERACTABLE = "is_interactable"
    IS_VISIBLE = "is_visible"


@dataclass
class HealthCheck:
    """Callback wrapper with additional utility functions attached"""

    check_type: Enum  # Validate later, any enum now

    # Must be passed an argumentless callback async function that returns bool
    executor: Callable[[], Awaitable[bool]]

    async def execute(self) -> bool:
        return await self.executor()

    def is_base_check(self) -> bool:
        return isinstance(self.check_type, BaseHealthCheckType)


@dataclass
class AppActivity:
    end_time: float
    activity_name: str
    initialiser: str | None = None
    start_time: float | None = None
    terminator: str | None = None
    metadata: dict = {}

# Used for abstract base controller to define itself as a base for a ManagedApp subclass
ManagedAppType = TypeVar("ManagedAppType", bound="ManagedApp")
ManagedAppTaskType = TypeVar("ManagedAppTaskType", bound="Enum")
