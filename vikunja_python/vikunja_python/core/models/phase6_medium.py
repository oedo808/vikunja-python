"""Phase 6: Medium Priority Models (Bucket, Reaction, Subscription)"""
from pydantic import BaseModel, Field, ConfigDict
from enum import IntEnum
from datetime import datetime
from typing import Optional
from vikunja_python.core.models.base import User

class ReactionKind(IntEnum):
    """Reaction kinds as defined by Vikunja API."""
    HEART = 1
    THUMBS_UP = 2
    FACE_WITH_TEARS_OF_JOY = 3

class Reaction(BaseModel):
    """Reaction on a task or comment."""
    model_config = ConfigDict(extra='ignore')
    value: str = Field(..., description="The emoji reaction value (e.g., Unicode emoji)")
    user: Optional[User] = Field(None, description="The user who reacted")
    created: datetime = Field(..., description="Timestamp of the reaction")

class ReactionCreateRequest(BaseModel):
    """Request to create a new reaction."""
    model_config = ConfigDict(extra='ignore')
    value: str = Field(..., description="The emoji reaction value")

class ReactionMapEntry(BaseModel):
    """A single entry in a reaction map."""
    value: str
    count: int

class SubscriptionType(IntEnum):
    """Types of subscriptions available."""
    TASK = 1
    PROJECT = 2

class Subscription(BaseModel):
    """A subscription to a task or project."""
    model_config = ConfigDict(extra='ignore')
    id: int
    type: SubscriptionType = Field(..., description="The type of the subscription")
    entity_id: int = Field(..., description="The ID of the subscribed task or project")
    created: datetime = Field(..., description="Timestamp of creation")

class SubscriptionCreateRequest(BaseModel):
    """Request to create a new subscription."""
    model_config = ConfigDict(extra='ignore')
    type: SubscriptionType = Field(..., description="The type of the subscription")
    entity_id: int = Field(..., description="The ID of the subscribed task or project")

class Bucket(BaseModel):
    """A bucket (column) in a Kanban board."""
    model_config = ConfigDict(extra='ignore')
    id: int
    title: str = Field(..., description="The title of the bucket")
    color: str | None = Field(None, description="Hex color of the bucket")
    position: int = Field(..., description="Position in the board")

class BucketCreateRequest(BaseModel):
    """Request to create a new bucket."""
    model_config = ConfigDict(extra='ignore')
    title: str = Field(..., description="The title of the bucket")
    color: str | None = Field(None, description="Hex color of the bucket")

class BucketUpdateRequest(BaseModel):
    """Request to update an existing bucket."""
    model_config = ConfigDict(extra='ignore')
    title: str | None = Field(None, description="The updated title")
    color: str | None = Field(None, description="The updated color")
    position: int | None = Field(None, description="The updated position")

class BucketMoveRequest(BaseModel):
    """Request to move a bucket."""
    model_config = ConfigDict(extra='ignore')
    new_position: int = Field(..., description="The new position of the bucket")
