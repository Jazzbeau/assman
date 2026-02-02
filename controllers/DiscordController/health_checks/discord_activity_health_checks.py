from controllers.DiscordController.discord_controller import DiscordAppActivityType, DiscordAppController
from controllers.controller_types import ActivityHealthCheck

def get_discord_activity_health_checks(controller: DiscordAppController) -> dict[DiscordAppActivityType, list[ActivityHealthCheck[DiscordAppActivityType]]]:
    return {
        DiscordAppActivityType.IN_VOICE_CHANNEL : [
            ActivityHealthCheck(check_type=DiscordAppActivityType.IN_VOICE_CHANNEL, executor=controller.app.is_locatable) # Placeholder executor
        ],
        DiscordAppActivityType.SCREEN_SHARING : [
            ActivityHealthCheck(check_type=DiscordAppActivityType.IN_VOICE_CHANNEL, executor=controller.app.is_locatable)
        ],
    }
