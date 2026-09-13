from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    details: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogRead]
    total: int
    limit: int
    offset: int
