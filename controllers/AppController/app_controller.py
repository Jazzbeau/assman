import asyncio
import time
from abc import ABC, abstractmethod
from asyncio.queues import Queue
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Generic, Type
from uuid import uuid4

from controllers.types import (
    AppActivity,
    BaseHealthCheckType,
    GenericTaskType,
    HealthCheck,
    HealthState,
    ManagedAppType,
)

from controllers.task import AppTask, TaskStatus


class AppController(ABC, Generic[ManagedAppType]):
    """Base implementation of common AppController descendant components"""

    def __init__(self, broadcaster):
        self.broadcaster = broadcaster

        # Tasks queuing 
        self.task_queue: Queue[str] = asyncio.Queue()
        self.active_tasks: Dict[str, AppTask] = {}

        self.app: ManagedAppType = self.get_app()
        self.health_status: HealthState = HealthState.STOPPED
        self.activity: AppActivity | None = None

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
            # Do something drastic, like restart the entire managed app (call a function to do that)

        # Call the subclass handler for domain specific health failures, they may or may not be critical
        await self.handle_app_check_failures(app_health_failures)

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
            except Exception:
                self.health_status = HealthState.ERROR
                raise NotImplementedError

    async def process_tasks(self):
        """Generic task queue manager"""
        while True:
            # Yield here if no jobs, task_queue contents are submitted via submit_task
            task_id = await self.task_queue.get()
            task = self.active_tasks[task_id]  # Access new entry

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            await self.broadcast(
                broadcast_type=GenericTaskType.TASK_UPDATE.value,
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
                    broadcast_type=GenericTaskType.TASK_UPDATE.value,
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
                    broadcast_type=GenericTaskType.TASK_UPDATE.value,
                    payload={
                        "task_id": task_id,
                        "status": task.status.value,
                        "error": task.error,
                    },
                )
            finally:
                self.task_queue.task_done()

    async def submit_task(self, task_type: str, params: Dict) -> str:
        ############### TODO ################
        #
        #   Implement 'validator = self.validators.get(task_type)                  
        #   or whatever that syntax is.
        #                                  
        #   ALSO!!! Need to change entire AppTask structure and function
        #   arguments to change task_type -> Enum for type safety!
        #
        #####################################
        task_id = str(uuid4())
        task = AppTask(
            id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            params=params,
            created_at=time.time(),
        )

        await self.broadcast(
            broadcast_type=GenericTaskType.TASK_UPDATE.value,
            payload={
                "task_id": task.id,
                "status": task.status.value,
            },
        )
        self.active_tasks[task_id] = task
        await self.task_queue.put(task_id)
        return task_id

    @property
    @abstractmethod
    def app_name(self) -> str:
        '''Return ManagedApp subclass name for controller'''
        # TODO: Should this be fetched from the subclass directly? I think yes.
        raise NotImplementedError

    # ToDo: Determine if this is needed; really work on the actual app launch / getting functionality - should we just define this as a @property and return the app?
    @abstractmethod
    def get_app(self) -> ManagedAppType:
        """Sub controller must return app"""
        raise NotImplementedError

    #TODO: Determine if this lives in the AppController scope or subclass; with executor implementation this might able to be elevated directly to subclass level; with appropriate broadcast setup for result of executor 
    @abstractmethod
    async def execute_task(self, task: AppTask) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def handle_app_check_failures(self, failed_checks: list[HealthCheck]) -> None:
        '''Intercept failed HealthChecks from heartbeat and take appropriate action to rectify ManagedApp state or fail gracefully'''
        raise NotImplementedError

    ####### Unsure on this one
    @abstractmethod
    def get_app_task_types(self) -> Type[Enum]:
        pass

    @abstractmethod
    def get_app_health_checks(self) -> list[HealthCheck]:
        '''Return HealthChecks related to ManagedApp subclass instance, these may be conditionally selected based
           on current activity state of app controller to ensure minimum required checks are undertaken for state management'''
        raise NotImplementedError

    @property
    @abstractmethod
    def validators(self) -> dict[Enum, Callable[[dict[str, Any]], bool]]:
        '''Defines a dictionary indexed via TaskType enums containing synchronous boolean functions for task-specific
           param shape validation, including raising errors for parameter inclusion on parameter-free functions'''
        raise NotImplementedError

    @property
    @abstractmethod
    def executors(self) -> dict[Enum, Callable[[ManagedAppType, dict[str, Any]], Awaitable[Any]]]:
        '''Defines a dictionary indexed via TaskType enums containing asynchronous functions for task-specific
           execution. These functions require a ManagedApp subclass as a parameter, and an optional (populated or empty)
           dictionary of parameters. The shape of this dictionary is task specific and should be validated via a corresponding
           entry in validators dictionary. These functions may optionally return a value which is to be broadcast via websocket'''
        raise NotImplementedError

