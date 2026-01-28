import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Generic, Type, TypeVar
from uuid import uuid4

from apps.managed_app import ManagedApp
from controllers.task import AppTask, TaskStatus


class HealthState(Enum):
    INITIALISING = "initialising"
    HEALTHY = "healthy"
    STOPPED = "stopped"
    MISSING = "missing"
    ERROR = "error"
    DEGRADED = "degraded"


class GenericTasks(Enum):
    HEALTHUPDATE = "health_update"
    TASKUPDATE = "task_update"


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


# Define
T = TypeVar("T", bound="ManagedApp")


class AppController(ABC, Generic[T]):
    """Base implementation of common AppController descendant components"""

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Subclass must implement"""
        pass

    def __init__(self, broadcaster):
        self.broadcaster = broadcaster
        self.task_queue = asyncio.Queue()
        self.app: T = self.get_app()
        self.active_tasks: Dict[str, AppTask] = {}
        self.health_status: HealthState = HealthState.STOPPED

    async def broadcast(self, broadcast_type: str, payload: dict):
        """Broadcast standardiser for websocket response"""
        msg = {
            "broadcast_type": broadcast_type,
            "app": self.app_name,
            "payload": payload,
        }
        await self.broadcaster.broadcast(msg)

    async def start(self):
        """Start background tasks - not related to underlying ManagedApp"""
        asyncio.create_task(self.heartbeat())
        asyncio.create_task(self.process_tasks())

    @abstractmethod
    def get_app(self) -> T:
        """Sub controller must return app"""
        pass

    # Task execution
    @abstractmethod
    async def execute_task(self, task: AppTask) -> Any:
        """Subclass to implement execution workflow - accepts task object with type and parameters"""
        pass

    # Heartbeat + Healthchecks
    async def broadcast_health(self):
        raise NotImplementedError

    async def handle_check_failures(self, failed_checks: list[HealthCheck]) -> None:
        # Filter to base / app health checks
        base_health_failures = list(
            filter(lambda check: check.is_base_check(), failed_checks)
        )
        app_health_failures = list(
            filter(lambda check: not check.is_base_check(), failed_checks)
        )

        if base_health_failures:
            # These are critical and require immediate hard resolution
            self.health_status = HealthState.ERROR
            raise NotImplementedError
            # return

        # Call the subclass handler for domain specific health failures, they may or may not be critical
        await self.handle_app_check_failures(app_health_failures)

    @abstractmethod
    async def handle_app_check_failures(self, failed_checks: list[HealthCheck]) -> None:
        raise NotImplementedError

    def get_health_checks(self) -> list[HealthCheck]:
        """
        Return concatenation of generic heartbeat HealthChecks with domain specific activity based HealthChecks
        """
        # Build base health checks for core functionality
        base_checks = [
            HealthCheck(BaseHealthCheckType.IS_RUNNING, self.app.is_running),
            HealthCheck(BaseHealthCheckType.IS_INTERACTABLE, self.app.is_interactable),
            HealthCheck(BaseHealthCheckType.IS_VISIBLE, self.app.is_locatable),
        ]
        # Get result of app domain health check builder
        app_checks: list[HealthCheck] = self.get_app_health_checks()
        return base_checks + app_checks

    @abstractmethod
    def get_app_health_checks(self) -> list[HealthCheck]:
        """Return HealthChecks related to app and its activity dependant health checks"""
        raise NotImplementedError

    async def heartbeat(self):
        """Basic logic for maintaining heartbeat - requires sub controller to implement do_heartbeat()"""
        while True:
            await asyncio.sleep(5)
            try:
                # Get list of HealthChecks (with callbacks attached)
                checks_to_run = self.get_health_checks()
                failed_checks = []
                for check in checks_to_run:
                    # Execute callbacks
                    if not await check.execute():
                        failed_checks.append(check)

                if failed_checks:
                    await self.handle_check_failures(failed_checks)
                else:
                    self.health_status = HealthState.HEALTHY

                await self.broadcast_health()
            except Exception as e:
                self.health_status = HealthState.ERROR
                pass

    async def process_tasks(self):
        """Generic task queue manager"""
        while True:
            # Yield here if no jobs, task_queue contents are submitted via submit_task
            task_id = await self.task_queue.get()
            task = self.active_tasks[task_id]  # Access new entry

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            await self.broadcast(
                broadcast_type=GenericTasks.TASKUPDATE.value,
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
                    broadcast_type=GenericTasks.TASKUPDATE.value,
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
                    broadcast_type=GenericTasks.TASKUPDATE.value,
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
            broadcast_type=GenericTasks.TASKUPDATE.value,
            payload={
                "task_id": task.id,
                "status": task.status.value,
            },
        )
        self.active_tasks[task_id] = task
        await self.task_queue.put(task_id)
        return task_id
