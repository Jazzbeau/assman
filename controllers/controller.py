import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict


class AppController(ABC):
    """Define basic components and requirements for ManagedApp controller classes"""

    def __init__(self, status_broadcaster):
        self.status_broadcaster = status_broadcaster

        # Enables assman to schedule jobs without waiting
        self.task_queue = asyncio.Queue()

        # Used to track state of jobs for status reporting
        self.active_tasks: Dict[str, Task] = {}

        # Used to track state of job
        self.health_status = HealthStatus()

        # Provided via inheritor
        self.app = self.create_app()

    @abstractmethod
    def create_app(self):
        """Subclass provided ManagedApp instance"""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Subclass defines meaning of health states for app"""
        pass

    @abstractmethod
    async def execute_task(self, task: Task) -> Any:
        """Subclass routes task types to app methods"""
        pass

    async def start(self):
        """Start required components for all app controllers"""
        self.create_task(self.heartbeat())
        self.create_task(self.process_tasks())

    async def heartbeat(self):
        """Generic heartbeat, relies on subclass implementation of check_health"""
        while True:
            await asyncio.sleep(5)

            try:
                health = await self.check_health()  # Subclass must implement

                await self.broadcaster.broadcast(
                    {"type": "app_health", "app": self.app_name, "health": health}
                )

            except Exception as e:
                await self.broadcaster.broadcast(
                    {
                        "type": "app_health",
                        "app": self.app_name,
                        "health": {"running": False, "error": str(e)},
                    }
                )

    async def process_tasks(self):
        """Task processor via async task queue"""
        while True:
            task_id = await self.task_queue.get()
            task = self.active_tasks[task_id]
            await self.broadcaster.broadcast({
                "type": "task_update",
                "task_id": task_id,
                "status": "running",
                "app": self.app_name
            )}

                                             try:

