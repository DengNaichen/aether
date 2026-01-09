from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ==================== Graph Enrollment Schemas ====================
class GraphEnrollmentResponse(BaseModel):
    """Response schema for graph enrollment."""

    id: UUID
    user_id: UUID
    graph_id: UUID
    enrolled_at: datetime
    last_activity: datetime | None = None
    completed_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
