from apps.discord_app import DiscordApp
from controllers.controller_types import CoreHealthCheck
from controllers.DiscordController.discord_types import DiscordHealthCheckType


def get_discord_app_health_checks(
    app: DiscordApp,
) -> list[CoreHealthCheck[DiscordHealthCheckType]]:
    return [
        CoreHealthCheck(
            check_type=DiscordHealthCheckType.IS_LOGGED_IN,
            executor=app.is_locatable,  # Placeholder
        ),
        CoreHealthCheck(
            check_type=DiscordHealthCheckType.IS_LOGGED_IN, executor=app.is_locatable
        ),
    ]
