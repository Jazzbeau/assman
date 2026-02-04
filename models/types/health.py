from enum import Enum
from typing import TypeAlias, TypeVar, Union

AppHealthCheckType = TypeVar("AppHealthCheckType", bound="Enum")

HealthCheckT: TypeAlias = Union[
    CoreHealthCheck[AppHealthCheckType], ActivityHealthCheck[AppActivityType]
]
