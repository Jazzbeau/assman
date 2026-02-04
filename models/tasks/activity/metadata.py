from datetime import datetime

from pydantic import BaseModel


class ActivityMetadataModel(BaseModel):
    """
    Base subclass for pydantic representation of an AppActivity's relevant metadata. Primarily designed
    for communication of state to client however also contains information  relevant to activity.

    Should rarely be used directly and instead extended via subclass to provide relevant domain information.

    Example:
    `DiscordScreenshareMetadataModel` may extend by providing `server_id`, `channel_id`, and `share_target` information.
    """

    initialiser: str
    terminator: str | None = None
    start_time: datetime
    end_time: datetime | None = None
