from enum import Enum


class HealthState(Enum):
    """
    Represents possible AppController Health States
    """

    HEALTHY = "healthy"
    UNINITIALISED = "uninitialised"
    ERROR = "error"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPED = "stopped"
