import time
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable


class HealthState(Enum):
    INITIALISING = "initialising"
    HEALTHY = "healthy"
    STOPPED = "stopped"
    MISSING = "missing"
    ERROR = "error"
    DEGRADED = "degraded"


class GenericTaskTypes(Enum):
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
    # Must be passed argumentless callback async function that returns bool
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
