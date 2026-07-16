from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import ApprovalDecisionValue


@dataclass
class ApprovalDecision:
    id: UUID
    entity_type: str
    entity_id: UUID
    decided_by: UUID
    decision: ApprovalDecisionValue
    comment: str | None
    decided_at: datetime
