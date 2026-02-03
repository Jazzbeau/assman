import asyncio
import time
from abc import ABC, abstractmethod
from asyncio.queues import Queue
from typing import Any, Dict, Generic
from uuid import UUID

from assman_types import JSONType
from controllers.apptask import AppTask, TaskStatus
from controllers.controller_types import (
    ActivityHealthCheck,
    AppActivity,
    AppActivityType,
    AppBroadcastType,
    AppHealthCheckType,
    BaseHealthCheckType,
    CoreHealthCheck,
    ExecutorCallable,
    Failure,
    HealthCheckT,
    HealthState,
    ManagedAppTaskType,
    ManagedAppType,
    ValidatorCallable,
)


class AppController(
    ABC,
    Generic[ManagedAppType, ManagedAppTaskType, AppActivityType, AppHealthCheckType],
):
    """Base implementation of common AppController descendant components"""

    def __init__(self, broadcaster):
        self.broadcaster = broadcaster
        self.task_queue: Queue[UUID] = asyncio.Queue()
        self.active_tasks: Dict[UUID, AppTask] = {}
        self.health_status: HealthState = HealthState.UNINITIALISED
        self.activity: AppActivity | None = None
        self.base_health_checks: list[CoreHealthCheck] = [
            CoreHealthCheck(
                check_type=BaseHealthCheckType.RUNNING, executor=self.app.is_running
            ),
            CoreHealthCheck(
                check_type=BaseHealthCheckType.INTERACTABLE,
                executor=self.app.is_interactable,
            ),
            CoreHealthCheck(
                check_type=BaseHealthCheckType.VISIBLE, executor=self.app.is_locatable
            ),
        ]
        self._task_supervisor: asyncio.Task | None = None
        self._task_failures: asyncio.Queue[Failure] = asyncio.Queue()
        self._event_tasks: set[asyncio.Task] = set()
        self._running: bool = False

    @property
    def app_name(self) -> str:
        """Define ManagedApp subclass name for controller"""
        return self.app.name

    async def broadcast(
        self, broadcast_type: AppBroadcastType, payload: dict[str, JSONType]
    ):
        """Broadcast standardiser for websocket response"""
        msg = {
            "app": self.app_name,
            "message_type": broadcast_type.value,
            "payload": payload,
        }
        await self.broadcaster.broadcast(msg)

    # Heartbeat / Health supervisor
    async def _supervise(self):
        while True:
            failure_type = await self._task_failures.get()
            if failure_type is Failure.CRITICAL:
                await self.rectify_state()

    # Heartbeat + Healthchecks
    async def broadcast_health(self, is_error: bool = False):
        health_broadcast_type = (
            AppBroadcastType.HEALTH_ERROR
            if is_error
            else AppBroadcastType.HEALTH_UPDATE
        )
        await self.broadcast(
            broadcast_type=health_broadcast_type,
            payload={
                "activity": self.activity.to_dict() if self.activity else None,
                "health_status": self.health_status.value,
            },
        )

    async def start(self):
        print(f"Starting {self.app_name} controller")
        if self._task_supervisor is None:
            # Start once, allow start() calls after init
            asyncio.create_task(self._supervise())
        self.health_status = HealthState.STARTING
        self._running = True
        await self.app.launch()
        self._event_tasks.add(asyncio.create_task(self.heartbeat(), name="heartbeat"))
        self._event_tasks.add(
            asyncio.create_task(self.process_tasks(), name="process_tasks")
        )

    def is_running(self):
        return self._running

    async def stop(self):
        if not self._running:
            raise RuntimeError("Cannot stop non-running controller")

        self._running = False
        self.health_status = HealthState.STOPPED

        for task in self._event_tasks:
            task.cancel()

        # Wait until all loops finish
        await asyncio.gather(*self._event_tasks, return_exceptions=True)

        self._event_tasks.clear()
        await self.app.terminate()

    async def handle_check_failures(self, failed_checks: list[HealthCheckT]) -> None:
        print(f"Handling failures for {self.app_name} controller")
        generic_core_failed_checks = [
            check
            for check in failed_checks
            if isinstance(check, CoreHealthCheck)
            and isinstance(check.check_type, BaseHealthCheckType)
        ]
        app_core_failed_checks = [
            check
            for check in failed_checks
            if isinstance(check, CoreHealthCheck)
            and not isinstance(check.check_type, BaseHealthCheckType)
        ]
        app_activity_failed_checks = [
            check for check in failed_checks if isinstance(check, ActivityHealthCheck)
        ]

        if generic_core_failed_checks:
            self.health_status = HealthState.ERROR
            await self.broadcast_health(is_error=True)
            self.report_failure(Failure.CRITICAL)
        elif app_core_failed_checks:
            self.health_status = HealthState.ERROR
            await self.broadcast_health(is_error=True)
            await self.handle_app_health_failures(app_core_failed_checks)

        if app_activity_failed_checks:
            self.health_status = HealthState.DEGRADED
            await self.broadcast_health(is_error=True)
            await self.handle_activity_health_failures(app_activity_failed_checks)

    def report_failure(self, failure_type: Failure):
        if failure_type is Failure.CRITICAL:
            # Don't wait to report.
            self._task_failures.put_nowait(Failure.CRITICAL)

    async def rectify_state(self) -> None:
        print(f"Rectifying state (restarting) for {self.app_name} controller")
        # NOT final implementation; but functional restarting
        await self.stop()
        await self.start()

    def get_health_checks(self) -> list[HealthCheckT]:
        print(f"Fetching health checks for {self.app_name} controller")
        checks: list[HealthCheckT] = [*self.base_health_checks, *self.app_health_checks]
        if self.activity:
            print(
                f"Found activity: {self.activity.activity_type.value} getting health checks for {self.app_name} controller"
            )
            current_activity_checks = self.activity_health_checks.get(
                self.activity.activity_type
            )
            if current_activity_checks is None:
                raise ValueError(
                    f"Activity: {self.activity.activity_type} did not have a corresponding checks list; even if none required, check list must be initialised"
                )
            checks.extend(current_activity_checks)
        return checks

    async def heartbeat(self):
        """Basic logic for maintaining heartbeat - requires sub controller to implement do_heartbeat()"""
        try:
            while self._running:
                await asyncio.sleep(5)
                print(f"Doing heartbeat for {self.app_name} controller")
                checks_to_run = self.get_health_checks()
                failed_checks = []
                for check in checks_to_run:
                    print(f"Running health check: {check.check_type.value}")
                    if not await check.execute():
                        failed_checks.append(check)
                if failed_checks:
                    print(f"Health Checks failed: {failed_checks}")
                    await self.handle_check_failures(failed_checks)
                else:
                    print(f"All checks passed for {self.app_name} controller heartbeat")
                    # All checks passed: Single truth for healthy state in application
                    self.health_status = HealthState.HEALTHY
                await self.broadcast_health()
        except asyncio.CancelledError:
            print(f"Heartbeat routine cancelled for {self.app_name} controller")
            self.health_status = HealthState.STOPPED
            raise

    # Task runner
    async def submit_task(
        self, task_type: ManagedAppTaskType, params: Dict[str, Any]
    ) -> UUID:
        """Create and enque a task for processing.
        Contructs new AppTask, broadcast event, adds to task queue and task pool for processing via process_tasks.

        Args:
            task_type: The type of the task to execute (Must be obtained via subclass ManagedAppTaskType generic implementation (i.e. 'MpvAppTaskType.PLAY')
            params: Dictionary of task-specific arugments to pass to the executor, see ManagedApp executors dict entry for task_type enum key.

        Returns:
            The UUID of the newly created task, allowing the submitter (i.e. FastAPI route handler -> Frontend) to track status of task.
        """
        print(f"Submitting task {task_type.value} for {self.app_name} controller")
        param_validator = self.validators.get(task_type)
        if not param_validator:
            raise ValueError(
                f"Task validation failed - no validator found for task of type {task_type.value}"
            )
        try:
            param_validator(params)
        except ValueError as e:
            raise ValueError(f"Task: {task_type} failed with message: {str(e)}")
        task = AppTask(
            task_type=task_type,
            params=params,
        )
        await self.broadcast(
            broadcast_type=AppBroadcastType.TASK_CREATE, payload=task.to_dict()
        )
        self.active_tasks[task.id] = task
        print(
            f"Enqueing task {task.id} {task.task_type.value} for {self.app_name} controller"
        )
        await self.task_queue.put(task.id)
        return task.id

    async def process_tasks(self):
        """Process tasks from the queue sequentially.

        Continuously pulls tasks from the task queue, executes them, and broadcasts
        their lifecycle events. Tasks are executed one at a time in FIFO order.

        For each task:
        1. Updates status to RUNNING and broadcasts task start
        2. Executes the task via its registered executor
        3. On success: marks COMPLETED and broadcasts finish
        4. On failure: marks FAILED, captures error, and broadcasts error

        Broadcasts:
            TASK_RUNNING: When task execution begins
            TASK_FINISH: When task completes successfully
            TASK_ERROR: When task fails with exception
            APP_RESPONSE: When executor produces data (via execute_task)

        This method runs indefinitely and should be started as a background task.
        """
        try:
            while self._running:
                task_id = await self.task_queue.get()
                task = self.active_tasks[task_id]  # Access new entry
                print(f"Found task: {task_id} in controller for {self.app_name}")

                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

                await self.broadcast(
                    broadcast_type=AppBroadcastType.TASK_RUNNING, payload=task.to_dict()
                )

                try:
                    await self.execute_task(task)
                    task.status = TaskStatus.COMPLETED
                    task.finished_at = time.time()
                    await self.broadcast(
                        broadcast_type=AppBroadcastType.TASK_FINISH,
                        payload=task.to_dict(),
                    )
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.finished_at = time.time()
                    task.error = str(e)
                    await self.broadcast(
                        broadcast_type=AppBroadcastType.TASK_ERROR,
                        payload=task.to_dict(),
                    )
                finally:
                    self.task_queue.task_done()
        except asyncio.CancelledError:
            print(f"Cancelling task runner routine for {self.app_name}")
            raise

    async def execute_task(self, task: AppTask) -> Any:
        """Route task to its corresponding executor, and broadcast responses.

        Retrieves executor via dictionary dispatcher mapping - executes it using app instance with
        AppTask provided parameters. Broadcasts result as an APP_RESPONSE if the executor returns a
        ExecutorResponse.

        Raises:
            ValueError if no executor mapping is found for AppTaskType
        """
        print(f"Attempting to execute task: {task.task_type.value}")
        executor = self.executors.get(task.task_type)
        if not executor:
            raise ValueError(
                f"Execution failed - no executor found for task of type {task.task_type.value}"
            )
        res = await executor(self.app, task.params)
        if res:
            await self.broadcast(
                broadcast_type=AppBroadcastType.APP_RESPONSE, payload=res.to_dict()
            )

    @property
    @abstractmethod
    def app(self) -> ManagedAppType:
        """Subclass to return ManagedAppType app instance"""
        raise NotImplementedError

    @abstractmethod
    async def handle_app_health_failures(
        self, failed_checks: list[CoreHealthCheck]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def handle_activity_health_failures(
        self, failed_checks: list[ActivityHealthCheck]
    ) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def validators(self) -> dict[ManagedAppTaskType, ValidatorCallable]:
        """Define dictionary of synchronous Generic[AppTask] parameter validation functions indexed using
        Generic[ManagedAppTaskType] enum.

        Stored functions must be synchronous and must be passed a parameter dictionary; even if empty.

        Should maintain alignment with keys in self.executors sourced via Generic[ManagedAppTaskType] values

        Args:
            None / self
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def executors(
        self,
    ) -> dict[ManagedAppTaskType, ExecutorCallable]:
        """Define dictionary of asynchronous Generic[AppTask] executor functions indexed using Generic[ManagedAppTaskType] enum.
        Stored functions must be asynchronous and accept Generic[ManagedAppType] + Params dictionary; and may only return
        ExecutorResponse, or nothing.

        Should maintain alignment with keys in self.validators sourced via Generic[ManagedAppTaskType] values

        Args:
            None / self
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def activity_health_checks(
        self,
    ) -> dict[AppActivityType, list[ActivityHealthCheck]]:
        """Define dictionary of Generic[AppActivityType] Enum indexed mappings to HealthCheck lists.
        HealthCheck lists may be supersets of associated, lesser activities.

        Example:
        Discord's 'ScreenSharing' is a subactivity of 'InVoiceChannel', therefore concatenates the
        HealthCheck of the 'InVoiceChannel' check with an additional check for 'ScreenSharing' state.

        Args:
            None / self

        Returns:
            List of relevant HealthChecks for a given AppActivityType, which may itself be a concatenation of another AppActivities
            assocaited HealthCheck, for instance - Discord's ScreenSharing HealthChecks might include InVoiceChannels checks
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def app_health_checks(self) -> list[CoreHealthCheck]:
        raise NotImplementedError
