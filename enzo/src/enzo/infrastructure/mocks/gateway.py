"""The whole gateway, mocked: a scripted model, canned tools and a canned parts agent."""

from core.models.agents import AgentTask, TaskReply
from core.models.chat import Completion, Message, SkillCall, SkillResult, SkillSpec
from core.models.identity import Identity

from enzo.infrastructure.mocks import agents, skills

ANSWER = (
    "Oven temperature is unstable (E42, readings 244–256 °C around a 250 °C setpoint). The same fault was fixed "
    "8 months ago by replacing heater assembly P-123, and the GC-X100 manual points to P-123. Replace P-123."
)
EVIDENCE = [
    SkillCall(id="mock-1", name="get_recent_telemetry", args={"serial": "SN-1001"}),
    SkillCall(id="mock-2", name="get_service_history", args={"serial": "SN-1001"}),
    SkillCall(id="mock-3", name="search_manual", args={"model": "GC-X100", "query": "E42"}),
]


class MockGateway:
    """Gather evidence, then answer and order the part, then report how the order ended."""

    async def complete(self, messages: list[Message], tools: list[SkillSpec], identity: Identity) -> Completion:
        """Return the next scripted turn.

        Args:
            messages: The conversation so far; only checked for tool results.
            tools: Checked for the ordering skill.
            identity: Ignored.

        Returns:
            Skill calls on the first turn, then the canned answer with the order if it can be placed.
        """
        if not any(message.role == "tool" for message in messages):
            return Completion(model="mock", provider="mock", text=None, skill_calls=EVIDENCE)
        order = next((m for m in messages if m.role == "tool" and m.call_id == "mock-order"), None)
        if order is not None:  # the parts agent's task is over: report how it ended
            return Completion(model="mock", provider="mock", text=f"Order outcome: {order.content}")
        request = {"request": "Order heater assembly P-123 for SN-1001 and schedule a technician visit."}
        calls = [SkillCall(id="mock-order", name=agents.ORDER_TOOL.name, args=request)]
        offered = agents.ORDER_TOOL in tools
        return Completion(model="mock", provider="mock", text=ANSWER, skill_calls=calls if offered else [])

    async def list_tools(self, identity: Identity) -> list[SkillSpec]:
        """List the canned tools.

        Args:
            identity: Ignored.

        Returns:
            The three skills and the parts agent's ordering skill.
        """
        return [*skills.SKILLS, agents.ORDER_TOOL]

    async def call_tool(self, call: SkillCall, identity: Identity) -> SkillResult:
        """Answer a tool call from the canned skills or the canned parts agent.

        Args:
            call: The tool call.
            identity: Ignored, no entitlement check is mocked.

        Returns:
            The canned result.
        """
        return agents.order(call) if call.name == agents.ORDER_TOOL.name else skills.call_skill(call)

    async def reply(self, reply: TaskReply, identity: Identity) -> AgentTask:
        """Pass the answer to the canned parts agent.

        Args:
            reply: Agent, task and answer.
            identity: Ignored.

        Returns:
            The completed or rejected task.
        """
        return agents.reply(reply)
