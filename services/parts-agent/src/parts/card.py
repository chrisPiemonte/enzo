"""The agent card: who this agent is and what it can do, published at /.well-known/agent-card.json."""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

PORT = 9100
URL = os.environ.get("PARTS_AGENT_URL", f"http://parts-agent:{PORT}/")  # the address callers use; set in compose

ORDER_SKILL = AgentSkill(
    id="order_part_and_schedule_visit",
    name="Order part and schedule visit",
    description=(
        "Propose a spare parts order for an instrument and a technician visit window. "
        "Checks the part fits the instrument's model. The engineer must approve before the order is placed."
    ),
    tags=["parts", "orders", "scheduling"],
    examples=["Order heater assembly P-123 for SN-1001 and schedule a technician visit."],
)

CARD = AgentCard(
    name="parts-agent",
    description="Orders spare parts and schedules field technician visits.",
    supported_interfaces=[AgentInterface(url=URL, protocol_binding="JSONRPC")],
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(),
    skills=[ORDER_SKILL],
)
