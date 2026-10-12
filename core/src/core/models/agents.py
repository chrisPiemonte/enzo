"""Tasks handed to remote agents, and the user's answers to them."""

from typing import Literal

from pydantic import BaseModel

TaskState = Literal["input-required", "completed", "rejected", "failed"]


class AgentTask(BaseModel):
    """Where a task handed to a remote agent stands."""

    agent: str
    task_id: str
    state: TaskState
    message: str


class TaskReply(BaseModel):
    """The user's answer to a task that is waiting for input."""

    agent: str
    task_id: str
    answer: str
