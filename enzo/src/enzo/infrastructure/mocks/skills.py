"""Canned MCP tools with the scenario's data, for working without the gateway."""

import json

from core.models.chat import SkillCall, SkillResult, SkillSpec

SERIAL = {"serial": {"type": "string", "description": "Instrument serial number, e.g. SN-1001"}}

SKILLS = [
    SkillSpec(
        name="get_recent_telemetry",
        description="Recent readings and error codes reported by an instrument.",
        input_schema={"type": "object", "properties": SERIAL, "required": ["serial"]},
    ),
    SkillSpec(
        name="get_service_history",
        description="Past faults, actions taken and parts used on an instrument.",
        input_schema={"type": "object", "properties": SERIAL, "required": ["serial"]},
    ),
    SkillSpec(
        name="search_manual",
        description="Search the service manual of an instrument model, e.g. for a fault code.",
        input_schema={
            "type": "object",
            "properties": {"model": {"type": "string"}, "query": {"type": "string"}},
            "required": ["model", "query"],
        },
    ),
]

DATA = {
    "get_recent_telemetry": {
        "serial": "SN-1001", "model": "GC-X100", "oven_setpoint_c": 250, "oven_readings_c": [244, 256],
        "errors_24h": {"E42": 3}, "record_ids": ["tel-1001-0412"], "dataset_version": "mock",
    },
    "get_service_history": {
        "serial": "SN-1001",
        "events": [{"when": "8 months ago", "fault": "E42", "action": "replaced heater assembly", "part": "P-123"}],
        "record_ids": ["svc-1001-007"], "dataset_version": "mock",
    },
    "search_manual": {
        "model": "GC-X100",
        "snippets": [{"section": "7.3", "text": "E42: oven temperature unstable. Replace heater assembly P-123."}],
        "record_ids": ["man-gcx100-7.3"], "dataset_version": "mock",
    },
}


def call_skill(call: SkillCall) -> SkillResult:
    """Return the canned data for a tool, always allowed.

    Args:
        call: The tool call; its arguments are ignored.

    Returns:
        The canned data as JSON, or a denial for an unknown tool.
    """
    if call.name not in DATA:
        return SkillResult(call_id=call.id, name=call.name, decision="DENY", content="unknown tool", source="mock")
    content = json.dumps(DATA[call.name])
    return SkillResult(call_id=call.id, name=call.name, decision="ALLOW", content=content, source="mcp:mock")
