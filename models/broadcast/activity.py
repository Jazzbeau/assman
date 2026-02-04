from typing import Generic

from pydantic import BaseModel

from models.tasks.activity.metadata import ActivityMetadataModel
from models.types.activity import AppActivityType


class ActivityBroadcastModel(BaseModel, Generic[AppActivityType]):
    activity_type: AppActivityType
    metadata: ActivityMetadataModel
