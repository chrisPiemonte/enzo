"""One accountability record per action."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from core.models.identity import Decision


class AuditEvent(BaseModel):
    """An append-only record of who did what, with which outcome."""

    trace_id: str
    user: str
    agent: str
    action: str
    target: str
    decision: Decision
    model: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
