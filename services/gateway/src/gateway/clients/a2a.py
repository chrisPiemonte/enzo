"""Talk to an A2A agent: read its card, start and continue tasks."""

import uuid

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.types import AgentCard, Message, Part, Role, SendMessageRequest, Task, TaskState
from core.models.agents import AgentTask
from core.models.agents import TaskState as Status

STATES: dict[int, Status] = {
    TaskState.TASK_STATE_INPUT_REQUIRED: "input-required",
    TaskState.TASK_STATE_COMPLETED: "completed",
    TaskState.TASK_STATE_REJECTED: "rejected",
    TaskState.TASK_STATE_CANCELED: "rejected",
}


async def fetch_card(url: str) -> AgentCard:
    """Read an agent's card.

    Args:
        url: Base URL of the agent.

    Returns:
        The agent card, with its skills.
    """
    async with httpx.AsyncClient() as http:
        return await A2ACardResolver(http, url).get_agent_card()


async def send(url: str, agent: str, text: str, task_id: str | None = None) -> AgentTask:
    """Send a message to an agent, starting a task or continuing one.

    Args:
        url: Base URL of the agent.
        agent: Agent name, reported in the task.
        text: The request, or the answer to an input-required task.
        task_id: The task to continue; None starts a new one.

    Returns:
        The task's state after the agent's reply.
    """
    message = Message(message_id=uuid.uuid4().hex, role=Role.ROLE_USER, parts=[Part(text=text)], task_id=task_id or "")
    task = Task()
    async with await create_client(url, ClientConfig(streaming=False)) as client:
        async for response in client.send_message(SendMessageRequest(message=message)):
            if response.HasField("task"):
                task = response.task
    return _to_agent_task(agent, task)


def _to_agent_task(agent: str, task: Task) -> AgentTask:
    """Translate an A2A task into the shared task model.

    Args:
        agent: Agent name.
        task: The A2A task.

    Returns:
        The shared task; any state other than input-required, completed or rejected counts as failed.
    """
    text = " ".join(part.text for part in task.status.message.parts if part.text)
    state: Status = STATES.get(task.status.state, "failed")
    return AgentTask(agent=agent, task_id=task.id, state=state, message=text)
