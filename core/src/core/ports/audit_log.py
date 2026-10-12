"""Port to the append-only audit log."""

from typing import Protocol

from core.models.audit import AuditEvent


class AuditLog(Protocol):
    """Records one accountability event per action."""

    async def record(self, event: AuditEvent) -> None:
        """Append an event to the log.

        Args:
            event: The action, who performed it and its outcome.
        """
