from typing import Any

from apps.discord_app import DiscordApp
from controllers.controller_types import ExecutorCallable, ExecutorResponse
from controllers.DiscordController.discord_types import DiscordAppTaskType


async def execute_learn_servers(
    app: DiscordApp, params: dict[str, Any]
) -> ExecutorResponse:
    """
    Returns:
        Payload: {"servers": [DiscordServer.to_dict()]}
    """
    await app.learn_servers()
    servers = app.get_servers()
    return ExecutorResponse(
        response_name=DiscordAppTaskType.LEARN_SERVERS, payload={"servers": servers}
    )


def get_discord_executors() -> dict[DiscordAppTaskType, ExecutorCallable]:
    return {
        DiscordAppTaskType.LEARN_SERVERS: execute_learn_servers,
    }
