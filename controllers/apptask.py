from dataclasses import dataclass, field
import time
from enum import Enum
from typing import Any, Dict, Generic, Optional
from uuid import UUID, uuid4
from controllers.controller_types import JSONType, ManagedAppTaskType


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AppTask(Generic[ManagedAppTaskType]):
    '''Represents a state management interface for an AppController's operation requests.
    
    Args:
        task_type: The specific action of the task to process. Must be a member of the controller's ManagedAppTaskType enum, which fills the generic.
        params: A dictionary of arbitrary, per-task_type properties to serve as arguments for the function executed via task typing.

        status: Current status of the task; a member of the TaskStatus enum.
        id: Auto-generated UUID4 identifier. Used in the job queue and to identify job status over websocket to frontend services.
        created_at: Auto-generated timestamp of task creation via time.time().
        error: Error message set on task failure, broadcast to websocket receivers.
        started_at: Timestamp when task execution began via time.time().
        finished_at: Timestamp when task finished (error or completion) via time.time().
    '''
    task_type: ManagedAppTaskType
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[float] = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, JSONType]:
        return {
            "task_type": self.task_type.value,
            "status": self.status.value,
            "id": str(self.id),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finish_at": self.finished_at,
            "duration": self._calculate_duration(self.started_at, self.finished_at),
            "error": self.error,
        }

    def _calculate_duration(self, start: float | None, finish:float | None) -> float | None:
        if start and finish:
            return finish - start
        return None

