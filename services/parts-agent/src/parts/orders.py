"""The ordering logic, deterministic: check the part fits, find when it is in hand, pick a visit slot."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal

APPROVE = {"approve", "approved", "yes", "y", "ok", "confirm"}
REJECT = {"reject", "rejected", "no", "n", "cancel"}


@dataclass
class Proposal:
    """An order and a visit window, waiting for approval."""

    serial: str
    account: str
    part: str
    part_name: str
    visit: str

    def question(self) -> str:
        """Phrase the proposal as a question for the user.

        Returns:
            The approval question.
        """
        return f"Order {self.part_name} {self.part} for {self.serial}, technician visit {self.visit}. Approve?"


def propose(request: str, data: dict[str, Any], check_access: Callable[[str], None]) -> Proposal | str:
    """Turn a free-text request into an order proposal, or explain why it cannot be placed.

    Access is checked as soon as the instrument's account is known, before anything about the instrument is
    revealed.

    Args:
        request: What the caller asked for, e.g. "Order P-123 for SN-1001".
        data: The agent's data product (instruments, parts, calendar).
        check_access: Called with the instrument's account; raises PermissionError to deny.

    Returns:
        A proposal, or the reason the order is rejected.
    """
    serial, part = _find(r"SN-\d+", request), _find(r"P-\d+", request)
    if serial is None or part is None:
        return "I need an instrument serial (SN-…) and a part number (P-…)."
    instrument, item = data["instruments"].get(serial), data["parts"].get(part)
    if instrument is not None:
        check_access(instrument["account"])
    if instrument is None or item is None:
        return f"Unknown {'instrument ' + serial if instrument is None else 'part ' + part}."
    if instrument["model"] not in item["fits"]:
        return f"{part} ({item['name']}) fits {', '.join(item['fits'])}, not {instrument['model']} ({serial})."
    in_hand = date.fromisoformat(data["as_of"]) + timedelta(days=0 if item["stock"] > 0 else item["lead_days"])
    slot = next((s for s in data["calendar"] if date.fromisoformat(s["date"]) >= in_hand), None)
    if slot is None:
        return f"No technician slot after {in_hand} (when {part} is in hand)."
    visit = f"{date.fromisoformat(slot['date']):%a %d %b} {slot['window']} ({slot['technician']})"
    return Proposal(serial=serial, account=instrument["account"], part=part, part_name=item["name"], visit=visit)


def decide(answer: str) -> Literal["approve", "reject"] | None:
    """Read the user's answer to a proposal.

    Args:
        answer: What the user replied.

    Returns:
        approve, reject, or None if the answer is neither.
    """
    word = answer.strip().lower()
    return "approve" if word in APPROVE else "reject" if word in REJECT else None


def _find(pattern: str, text: str) -> str | None:
    """Return the first match of a pattern in a text.

    Args:
        pattern: Regular expression.
        text: Text to search.

    Returns:
        The match, upper-cased, or None.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).upper() if match else None
