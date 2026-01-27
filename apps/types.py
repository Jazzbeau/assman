from dataclasses import dataclass


@dataclass
class ProcessConfig:
    """ManagedApp struct for supplying data to new application instances"""

    process_name: str
    process_params: list[str]
    wm_class_target: str
    wm_name_target: str


@dataclass
class ProcessProperties:
    """ManagedApp struct for organising handles for active applications"""

    pg_id: int
    process_id: int
    window_id: int


@dataclass
class XWindowProperties:
    wm_class: str
    wm_pid: int
    wm_name: str
