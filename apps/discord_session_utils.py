from typing import Literal

from models.discord_server import DiscordChannel, DiscordServer


def get_channel_by_id(pool: dict[str, DiscordChannel], id: str) -> DiscordChannel:
    try:
        return pool[id]
    except KeyError:
        raise FileNotFoundError(f"Unknown or invalid channel_id: {id}")


def get_server_by_id(pool: dict[str, DiscordServer], id: str) -> DiscordServer:
    try:
        return pool[id]
    except KeyError:
        raise FileNotFoundError(f"Unknown or invalid server_id {id}")


def get_channels_by_name(
    pool: dict[str, DiscordChannel],
    name: str,
    strict_match=True,
    case_sensitive=True,
    channel_type: Literal["all", "voice", "text"] = "all",
) -> list[DiscordChannel]:
    if not pool:
        return []
    if channel_type == "all":
        pool_values = list(pool.values())
    else:
        pool_values = list(filter(lambda ch: ch.type == channel_type, pool.values()))

    if strict_match:
        return list(
            filter(
                lambda ch: (name if case_sensitive else name.lower())
                == (ch.name if case_sensitive else ch.name.lower()),
                pool_values,
            )
        )
    else:
        return list(
            filter(
                lambda ch: (name if case_sensitive else name.lower())
                in (ch.name if case_sensitive else ch.name.lower()),
                pool_values,
            )
        )


def get_servers_by_name(
    pool: dict[str, DiscordServer],
    name: str,
    strict_match=True,
    case_sensitive=True,
) -> list[DiscordServer]:
    if not pool:
        return []
    pool_values = list(pool.values())

    if strict_match:
        return list(
            filter(
                lambda ch: (name if case_sensitive else name.lower())
                == (ch.name if case_sensitive else ch.name.lower()),
                pool_values,
            )
        )
    else:
        return list(
            filter(
                lambda ch: (name if case_sensitive else name.lower())
                in (ch.name if case_sensitive else ch.name.lower()),
                pool_values,
            )
        )


def get_channels(
    pool: dict[str, DiscordChannel],
    channel_type: Literal["any", "voice", "text"] = "any",
) -> list[DiscordChannel]:
    if not pool:
        return []
    if channel_type == "any":
        return list(pool.values())
    return list(filter(lambda ch: ch.type == channel_type, pool.values()))
