"""The orchestration loop: build context → think → act → repeat, pausing while a remote agent asks the user."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from core.models.agents import AgentTask
from core.models.chat import Message, SkillCall
from core.models.identity import Identity
from core.models.reply import AgentReply, ToolCall
from core.ports.audit_log import AuditLog
from core.ports.gateway import Gateway
from core.ports.memory_store import MemoryStore

from enzo.application.actions import Actions, Outcome
from enzo.application.context.builder import ContextBuilder
from enzo.application.context.context import Context
from enzo.application.recorder import Recorder

MAX_TURNS = 5


@dataclass
class Paused:
    """A question on hold while a remote agent waits for the user; resumed once its task ends."""

    context: Context
    recorder: Recorder
    task: AgentTask
    call: SkillCall
    rest: list[SkillCall]
    model: str


@dataclass
class TriageAgent:
    """Answers a question by alternating model turns and tool calls until the model is done."""

    builder: ContextBuilder
    gateway: Gateway
    actions: Actions
    memory: MemoryStore
    audit: AuditLog
    paused: dict[str, Paused] = field(default_factory=dict)  # trace id -> question on hold
    on_step: Callable[[ToolCall], None] | None = None  # called with each step as it happens

    async def ask(self, question: str, identity: Identity) -> AgentReply:
        """Start answering a question.

        Args:
            question: The user's question.
            identity: User and agent on whose behalf every call is made.

        Returns:
            The answer, or, if a remote agent needs the user, its question in pending.
        """
        recorder = Recorder(self.audit, identity, uuid.uuid4().hex[:8], self.on_step)
        return await self._run(await self.builder.build(question, identity), recorder)

    async def answer(self, trace_id: str, text: str) -> AgentReply:
        """Pass the user's answer to the remote agent; once its task ends, hand the outcome back to the model.

        Args:
            trace_id: The question on hold.
            text: The user's answer, e.g. "approve".

        Returns:
            The agent's next question, or the model's answer now that the task is over.
        """
        paused = self.paused.pop(trace_id)
        task = await self.actions.reply(paused.task, text, paused.recorder)
        if task.state == "input-required":
            paused.task = task
            self.paused[trace_id] = paused
            return self._reply(paused.recorder, paused.model, "", task)
        result = Message(role="tool", call_id=paused.call.id, content=f"{task.agent} task {task.state}: {task.message}")
        paused.context.history.append(result)
        outcome = await self.actions.run(paused.rest, paused.recorder, paused.model)
        return await self._continue(paused.context, paused.recorder, paused.model, "", outcome)

    async def _run(self, context: Context, recorder: Recorder) -> AgentReply:
        """Alternate model turns and tool calls until the model answers or a remote agent needs the user.

        Args:
            context: Everything the model sees.
            recorder: Records steps and audit events for this question.

        Returns:
            The answer, or a reply pending on a remote agent.
        """
        for _ in range(MAX_TURNS):
            completion = await self.gateway.complete(context.messages(), context.tools, recorder.identity)
            text = completion.text or ""
            if not completion.skill_calls:
                question = context.history[0]
                await self.memory.remember(recorder.identity, [question, Message(role="assistant", content=text)])
                return self._reply(recorder, completion.model, text)
            context.history.append(Message(role="assistant", content=text, skill_calls=completion.skill_calls))
            outcome = await self.actions.run(completion.skill_calls, recorder, completion.model)
            if outcome.pending:
                return await self._continue(context, recorder, completion.model, text, outcome)
            context.history += outcome.messages
        return self._reply(recorder, "", "No answer within the turn limit.")

    async def _continue(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, context: Context, recorder: Recorder, model: str, text: str, outcome: Outcome
    ) -> AgentReply:
        """Record the tool results, then pause on a pending task or carry on with the model.

        Args:
            context: Everything the model sees.
            recorder: Records steps and audit events for this question.
            model: Model that requested the calls.
            text: What the model said alongside the calls.
            outcome: Results of the calls run so far.

        Returns:
            A reply pending on a remote agent, or the result of carrying on.
        """
        context.history += outcome.messages
        if outcome.pending and outcome.waiting_call:
            paused = Paused(context, recorder, outcome.pending, outcome.waiting_call, outcome.rest, model)
            self.paused[recorder.trace_id] = paused
            return self._reply(recorder, model, text, outcome.pending)
        return await self._run(context, recorder)

    @staticmethod
    def _reply(recorder: Recorder, model: str, text: str, pending: AgentTask | None = None) -> AgentReply:
        """Build a reply carrying only the steps taken since the previous reply.

        Args:
            recorder: Records of this question.
            model: Model that produced the text.
            text: What the model said.
            pending: The remote agent's task, if it is waiting for the user.

        Returns:
            The reply.
        """
        steps = recorder.new_steps()
        return AgentReply(trace_id=recorder.trace_id, model=model, steps=steps, answer=text, pending=pending)
