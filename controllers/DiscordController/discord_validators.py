from typing import Any

from controllers.controller_types import ValidatorCallable
from controllers.DiscordController.discord_types import DiscordAppTaskType


def validate_learn_servers(params: dict[str, Any]) -> bool:
    """
    Returns:
        bool
    """
    return not params


def get_discord_validators() -> dict[DiscordAppTaskType, ValidatorCallable]:
    return {
        DiscordAppTaskType.LEARN_SERVERS: validate_learn_servers,
    }
