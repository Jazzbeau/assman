from __future__ import annotations

from apps.discord_app import DiscordApp
from controllers.controller_types import ActivityHealthCheck
from controllers.DiscordController.discord_types import DiscordAppActivityType


def get_discord_activity_health_checks(
    app: DiscordApp,
) -> dict[DiscordAppActivityType, list[ActivityHealthCheck[DiscordAppActivityType]]]:
    return {
        DiscordAppActivityType.IN_VOICE_CHANNEL: [
            ActivityHealthCheck(
                check_type=DiscordAppActivityType.IN_VOICE_CHANNEL,
                executor=app.is_locatable,
            )
        ],
        DiscordAppActivityType.SCREEN_SHARING: [
            ActivityHealthCheck(
                check_type=DiscordAppActivityType.IN_VOICE_CHANNEL,
                executor=app.is_locatable,
            )
        ],
    }
