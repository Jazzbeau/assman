from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Generic, Union

from models.types.activity import AppActivityType
from models.types.health import AppHealthCheckType


class BaseHealthCheckType(Enum):
    """
    Enumeration containing core health checks to maintain representation of an AppController's ManagedApp state.
    These are inherent to all heartbeat cycles.
    """

    RUNNING = "running"
    INTERACTABLE = "interactable"
    VISIBLE = "visible"


@dataclass
class CoreHealthCheck(Generic[AppHealthCheckType]):
    """
    General-purpose container for heartbeat HealthCheck callback functions.
        `check_type`:
            An Enum value representing the identifier for the specific healthcheck.
            Accepts `BaseHealthCheckType` from AppController base class, or subclass
            implemented `AppHealthCheckType` generic. The latter should represent
            HealthCheck objects which must run at all times during a running state.
        `executor`:
            An asynchronous boolean callback function which executes on a `ManagedApp` instance,
            should execute the minimum possible actions to determine a singular boolean truth.

            Example: `is_running` (base) executes a corresponding function on `ManagedApp` to determine if its PID is running.

        Methods:
            execute() -> bool:
                Executes and waits for callback function
    """

    check_type: Union[AppHealthCheckType, BaseHealthCheckType]

    # TODO: Have this accept the app for modularisation
    executor: Callable[[], Awaitable[bool]]

    async def execute(self) -> bool:
        return await self.executor()


@dataclass
class ActivityHealthCheck(Generic[AppActivityType]):
    """
    Container for heartbeat HealthCheck callback function designed to valdiate the state of a given active AppActivity.
        `check_type`:
            An Enum value representing the identifier for the specific healthcheck.
            Accepts subclass implemented `AppActivityType` generic (The same type as the activity itself).
        `executor`:
            An asynchronous boolean callback function which executes on a `ManagedApp` instance,
            should execute the minimum possible actions to determine a singular boolean truth regarding activity.

            Example: `is_in_voice_channel` (discord) executes a corresponding function on `DiscordApp` instance to determine
            via Playwright if Discord client account is presently connected to a voice channel.

        Methods:
            execute() -> bool:
                Executes and waits for callback function
    """

    check_type: AppActivityType
    # TODO: Have this accept the app for modularisation
    executor: Callable[[], Awaitable[bool]]

    async def execute(self) -> bool:
        return await self.executor()
