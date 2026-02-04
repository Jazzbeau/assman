from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, TypeAlias

from apps.discord_app import DiscordApp
from models.types.task import ManagedAppTaskType


@dataclass
class ExecutorResponse(Generic[ManagedAppTaskType]):
    response_name: ManagedAppTaskType
    payload: dict[str, JSONType]

    def to_dict(self) -> dict[str, JSONType]:
        return {"response_name": self.response_name.value, **self.payload}
