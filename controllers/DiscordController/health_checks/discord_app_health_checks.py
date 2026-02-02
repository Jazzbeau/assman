from controllers.DiscordController.discord_controller import DiscordAppController, DiscordHealthCheckType
from controllers.controller_types import CoreHealthCheck

def get_discord_app_health_checks(controller: DiscordAppController) -> list[CoreHealthCheck[DiscordHealthCheckType]]:
    return [
        CoreHealthCheck(
            check_type=DiscordHealthCheckType.IS_LOGGED_IN,
            executor=controller.app.is_locatable #Placeholder
        ),
        CoreHealthCheck(
            check_type=DiscordHealthCheckType.IS_LOGGED_IN,
            executor=controller.app.is_locatable
        )
    ]
