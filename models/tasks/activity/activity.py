from dataclasses import dataclass
from typing import Generic

from models.broadcast.activity import ActivityBroadcastModel
from models.tasks.activity.metadata import ActivityMetadataModel
from models.types.activity import AppActivityType


@dataclass
class AppActivity(Generic[AppActivityType]):
    """
    Represents a current running activity for an AppController

    Attributes:
        activity_type: Generic(AppActivityType)
            A representation of the current activity via subclass implemented $APPActivityType enumeration
        metadata: ActivityMetadataModel
            A pydantic representation of metadata, at a minimum containing information regarding runtime and initialising / terminating task UUID's

    Methods:
        to_broadcast_model():
            Returns a pydantic model for broadcasting via AppController's Broadcaster websocket interface
    """

    activity_type: AppActivityType
    metadata: ActivityMetadataModel

    def to_broadcast_model(self) -> ActivityBroadcastModel:
        return ActivityBroadcastModel(
            activity_type=self.activity_type, metadata=self.metadata
        )
