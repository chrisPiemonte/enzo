"""The act step: run the tool calls the model asked for, through the gateway."""

from dataclasses import dataclass, field

from core.models.agents import AgentTask, TaskReply
from core.models.chat import Message, SkillCall
from core.ports.gateway import Gateway

from enzo.application.recorder import Recorder


@dataclass
class Outcome:
    """What the tool calls produced: results for the model, or a remote agent waiting for the user."""

    messages: list[Message]
    pending: AgentTask | None = None
    waiting_call: SkillCall | None = None  # the call whose result is the pending task's outcome
    rest: list[SkillCall] = field(default_factory=list)  # calls not run yet, to run once the task ends


@dataclass
class Actions:
    """Runs tool calls through the gateway, recording each one."""

    gateway: Gateway

    async def run(self, calls: list[SkillCall], recorder: Recorder, model: str) -> Outcome:
        """Run the model's tool calls in order, stopping at the first one that needs the user.

        Args:
            calls: Tool calls requested by the model.
            recorder: Records each call as a step and an audit event.
            model: Model that requested the calls.

        Returns:
            One tool message per call run, and the pending task if a remote agent needs the user's input.
        """
        messages: list[Message] = []
        for index, call in enumerate(calls):
            result = await self.gateway.call_tool(call, recorder.identity)
            await recorder.record(result.source or "tool", call.name, result.decision, model)
            if result.task and result.task.state == "input-required":
                return Outcome(messages, pending=result.task, waiting_call=call, rest=calls[index + 1 :])
            messages.append(Message(role="tool", call_id=call.id, content=result.content))
        return Outcome(messages)

    async def reply(self, task: AgentTask, answer: str, recorder: Recorder) -> AgentTask:
        """Pass the user's answer to the remote agent waiting for it.

        Args:
            task: The task waiting for input.
            answer: The user's answer, e.g. "approve".
            recorder: Records the reply as a step and an audit event.

        Returns:
            The task's state after the remote agent's reply.
        """
        reply = TaskReply(agent=task.agent, task_id=task.task_id, answer=answer)
        updated = await self.gateway.reply(reply, recorder.identity)
        await recorder.record(f"a2a:{task.agent}", f"reply:{answer}", "ALLOW")
        return updated
