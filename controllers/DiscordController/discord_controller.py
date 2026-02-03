from apps.discord_app import DiscordApp
from controllers.AppController.app_controller import AppController
from controllers.controller_types import (
    ActivityHealthCheck,
    CoreHealthCheck,
    ExecutorCallable,
    ValidatorCallable,
)
from controllers.DiscordController.discord_executors import get_discord_executors
from controllers.DiscordController.discord_types import (
    DiscordAppActivityType,
    DiscordAppTaskType,
    DiscordHealthCheckType,
)
from controllers.DiscordController.discord_validators import get_discord_validators
from controllers.DiscordController.health_checks.discord_activity_health_checks import (
    get_discord_activity_health_checks,
)
from controllers.DiscordController.health_checks.discord_app_health_checks import (
    get_discord_app_health_checks,
)


class DiscordAppController(
    AppController[
        DiscordApp, DiscordAppTaskType, DiscordAppActivityType, DiscordHealthCheckType
    ]
):
    def __init__(self, broadcaster):
        self._app = DiscordApp()
        super().__init__(broadcaster)

    @property
    def app(self) -> DiscordApp:
        return self._app

    @property
    def app_health_checks(self) -> list[CoreHealthCheck]:
        """TODO: Elaborate
        List of HealthChecks that are imperative to state management, but are not activity based.
        To be checked in heartbeat whenver app is alive
        """
        return get_discord_app_health_checks(self.app)

    @property
    def activity_health_checks(
        self,
    ) -> dict[DiscordAppActivityType, list[ActivityHealthCheck]]:
        """TODO: Elaborate
        Dictionary of activity indexed HealthCheck lists that are assocaited with specific activity states
        lists may be superset of another health check, i.e. SCREEN_SHARING includes the checks for IN_VOICE_CHANNEL + additional
        """
        return get_discord_activity_health_checks(self.app)

    @property
    def executors(
        self,
    ) -> dict[DiscordAppTaskType, ExecutorCallable]:
        return get_discord_executors()

    @property
    def validators(self) -> dict[DiscordAppTaskType, ValidatorCallable]:
        return get_discord_validators()

    async def handle_app_health_failures(self, failed_checks: list[CoreHealthCheck]):
        raise NotImplementedError

    async def handle_activity_health_failures(
        self, failed_checks: list[ActivityHealthCheck]
    ) -> None:
        raise NotImplementedError

    async def start_playwright(self) -> None:
        await self.app.start_playwright()
