"""An audit log kept in memory, standing in for the JSONL file."""

from core.models.audit import AuditEvent


class MockAuditLog:
    """Keeps events in a list for the lifetime of the process."""

    def __init__(self) -> None:
        """Start with an empty log."""
        self.events: list[AuditEvent] = []

    async def record(self, event: AuditEvent) -> None:
        """Append an event in memory.

        Args:
            event: The action, who performed it and its outcome.
        """
        self.events.append(event)
