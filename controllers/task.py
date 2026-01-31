from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, Optional
from uuid import UUID
from controllers.types import ManagedAppTaskType


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AppTask(Generic[ManagedAppTaskType]):
    '''Represents a state management interface for an AppController's operation requests. Contains execution types

    Args:
        id: A UUID4 representing an intenral identifier to be given to the specific job. Utilised as identifier in job queue, and to identify job status meaningfully over websocket to frontend services
        task_type: The specific action of the task to process. Utilised in task execution alongside `params` to signify action to take by task executor. The type of this argument must be an Enum - which will fill the role of the generic ManagedAppTaskType for the class.  
        params: A dictionary of arbitrary, per-task_type properties to serve as arguments for function executed via task typing.
        status: Utilised to identify the current status of the class; a member of the TaskStatus Enum.
        result: An optional string to signify outcome to websocket recievers, should not be critical to operation
        error: An optional string to signify error outcomes to websocket recievers, should not be critical to operaetion
        created_at: A float containing the time of creation via time.time()
        started_at: A float containing the time of execution via time.time()
        finished_at: A float containing the time of finish (error or completion) via time.time()
    '''
    id: UUID
    task_type: ManagedAppTaskType
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str| None = None
    created_at: Optional[float] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "task_type": self.task_type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finish_at": self.finished_at,
            "duration": self._calculate_duration(self.started_at, self.finished_at),
        }

    def _calculate_duration(self, start: float | None, finish:float | None) -> float | None:
        if start and finish:
            return finish - start
        return None

