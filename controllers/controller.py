import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, Type, TypeVar
from uuid import uuid4

from controllers.task import AppTask, TaskStatus


class ManagedApp:
    pass


# Define
T = TypeVar("T", bound="ManagedApp")


class AppController(ABC, Generic[T]):
    """Base implementation of common AppController descendant components"""

    class HealthStatus(Enum):
        INITIALISING = "initialising"
        RUNNING = "running"
        STOPPED = "stopped"
        MISSING = "missing"
        ERROR = "error"
        DEGRADED = "degraded"

    class GenericTasks(Enum):
        HEALTHUPDATE = "health_update"
        TASKUPDATE = "task_update"

    @property
    @abstractmethod
    def AppTasks(self) -> Type[Enum]:
        """Subclasses need to define their task list via this Enum"""
        pass

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Subclass must implement"""
        pass

    @property
    def valid_task_types(self) -> dict:
        """Return dictionary of base + subclass tasks"""
        generic_tasks = AppController.GenericTasks.__members__
        app_tasks = self.AppTasks.__members__
        return {**generic_tasks, **app_tasks}

    def __init__(self, broadcaster, app: T):
        self.broadcaster = broadcaster
        self.task_queue = asyncio.Queue()
        self.app: T = app
        self.active_tasks: Dict[str, AppTask] = {}
        self.health_status: AppController.HealthStatus = (
            AppController.HealthStatus.INITIALISING
        )

    @abstractmethod
    async def create_app(self):
        """Sub controller must implement per-app startup logic"""
        pass

    @abstractmethod
    async def update_health(self) -> None:
        """Subclass must implement per-app logic on what constitutes health"""
        pass

    @abstractmethod
    async def execute_task(self, task: AppTask) -> Any:
        """Subclass to implement execution workflow - accepts task object with type and parameters"""
        pass

    async def broadcast(self, task_type: str, payload: dict):
        """Broadcast standardiser for websocket response"""
        msg = {"task_type": task_type, "app": self.app_name, "payload": payload}
        await self.broadcaster.broadcast(msg)

    async def start(self):
        """Start background tasks - not related to underlying ManagedApp"""
        # TODO: Implement ownership and ability to end these
        asyncio.create_task(self.heartbeat())
        asyncio.create_task(self.process_tasks())

    async def heartbeat(self):
        """Basic logic for maintaining heartbeat - requires sub controller to implement check_health()"""
        while True:
            # TODO: Environment variable for polling rate
            await asyncio.sleep(5)

            try:
                # Use per-app defined 'health' check
                await self.update_health()

                await self.broadcast(
                    task_type=AppController.GenericTasks.HEALTHUPDATE.value,
                    payload={
                        "app": self.app_name,
                        "health": self.health_status,
                    },
                )
            except Exception as e:  # Catchall
                await self.broadcast(
                    task_type=AppController.GenericTasks.HEALTHUPDATE.value,
                    payload={
                        "app": self.app_name,
                        "health": self.health_status,
                        "error": str(e),
                    },
                )

    async def process_tasks(self):
        """Generic task queue manager"""
        while True:
            # Yield here if no jobs, task_queue contents are submitted via submit_task
            task_id = await self.task_queue.get()
            task = self.active_tasks[task_id]  # Access corresponding entry

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            await self.broadcast(
                task_type=AppController.GenericTasks.TASKUPDATE.value,
                payload={
                    "task_id": task_id,
                    "status": task.status.value,
                    "app": self.app_name,
                },
            )

            try:
                # Execute task and wait until it returns
                task.result = await self.execute_task(task)
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                await self.broadcast(
                    task_type=AppController.GenericTasks.TASKUPDATE.value,
                    payload={
                        "task_id": task_id,
                        "status": task.status.value,
                        "app": self.app_name,
                    },
                )
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                await self.broadcast(
                    task_type=AppController.GenericTasks.TASKUPDATE.value,
                    payload={
                        "task_id": task_id,
                        "status": task.status.value,
                        "error": task.error,
                    },
                )
            finally:
                self.task_queue.task_done()

    async def submit_task(self, task_type: str, params: Dict) -> str:
        """Main entrypoint for task submission"""
        # Create ID -> create task dict object -> add to active tasks -> add key (ID) to queue for task executor
        # Generate ID
        task_id = str(uuid4())
        task = AppTask(
            id=task_id,
            # TODO: Implement per-app enum of valid task types
            type=task_type,
            status=TaskStatus.PENDING,
            params=params,
            created_at=time.time(),
        )

        await self.broadcast(
            task_type=AppController.GenericTasks.TASKUPDATE.value,
            payload={
                "task_id": task.id,
                "status": task.status.value,
            },
        )
        self.active_tasks[task_id] = task
        await self.task_queue.put(task_id)
        return task_id
