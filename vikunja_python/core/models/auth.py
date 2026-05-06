from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class APIPermissions(BaseModel):
    model_config = ConfigDict(extra='ignore')

    # Using a dict of lists to represent the structure discovered in the PUT request
    # e.g., {"projects": ["create", "delete"], "tasks": ["read_all"]}
    # We'll use a generic Dict for the actual implementation to handle the vast array of keys.
    pass


class APIToken(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    title: str
    token: str
    permissions: Dict[str, List[str]]
    expires_at: Optional[datetime] = None
    created: datetime
    updated: Optional[datetime] = None


class APITokenCreateRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    title: str
    permissions: Dict[str, List[str]]
    expires_at: Optional[datetime] = None
