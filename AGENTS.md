# Enzo: how we build it

Rules for anyone writing code here, human or AI. They apply to **every service** in the repo.
Background and scope live in `data/resources/specs/` (local only, gitignored; start with `implementation-plan.md`).

## 1. How we work (AI assistants included)

- **Ask before deciding.** Never choose a tool, library, technology, folder structure or name alone. Propose options,
  recommend one, wait for a yes.
- **Design first.** Every feature starts with a design discussion. No code until the design is agreed.
- **Big picture, small steps.** Keep the whole system in mind, but implement **one file at a time, one piece of code
  at a time**, unless explicitly asked otherwise. Stop after each step for review.
- **Mocks are honest.** Mocked or stubbed code is marked `# MOCK:` (temporary) or `# STUB:` (deliberate, see the plan).
- **No tests by default.** Write pytest tests only when needed to be sure something works, and say so first.

## 2. Code

- **Single responsibility.** A module, class or function does one thing. Files stay short and readable.
- **Simple and elegant** beats clever and generic. No speculative abstractions.
- **Max line length 120.**
- **Fully typed** (mypy strict).
- **Docstrings everywhere, Google style:**
  - Functions and methods: a short description, `Args:` and `Returns:` (and `Raises:` when relevant).
  - Classes: one short description only, no `Args`/`Attributes` sections.

```python
def call_skill(skill: str, identity: Identity) -> ToolCall:
    """Call an MCP skill on behalf of a user and an agent.

    Args:
        skill: Name of the MCP skill to call.
        identity: User and agent identities carried on the call.

    Returns:
        The recorded tool call, with its allow/deny decision.
    """
```

## 3. Architecture

- **Layers are loosely coupled.** Each layer (presentation, application, domain, infrastructure) depends on
  **interfaces** (e.g. `typing.Protocol` ports), never on another layer's concrete implementation.
- **Adapters at the edges.** External systems (model providers, MCP, A2A, MLflow) sit behind adapters, so each one
  can be swapped, tested alone, or mocked.
- **Each layer is testable in isolation**, with everything else mocked.
- **General parts live in `core/`** (`core.models`, `core.ports`, `core.adapters`). Anything more than one service
  can use goes there; a service keeps only what is specific to it.
- **The folder tree tells the design**, without deep nesting (e.g. `context/builder.py` + `context/steps/*.py`).
- **One service, one folder.** Every service (local agent, MCP servers, A2A agents, gateway…) has its own folder and
  is a member of the uv workspace (root `pyproject.toml`).

## 4. Setup and distribution

Cloning and running needs only **git, uv, Python and Docker Compose**. Nothing else may become a requirement.

```bash
git clone <repo> && cd enzo
cp .env.template .env
docker compose up -d --build   # Ollama (+ model pull), MLflow, services
uv sync
uv run enzo
```

Configuration comes from `.env` (gitignored). Every new setting is also added to `.env.template`.

After changing a service's code, rebuild it: `docker compose up -d --build <service>`. A plain restart keeps the old
image and silently runs the old code.

## 5. Checks

Config lives in the root `pyproject.toml` and applies to every service. Both must pass before a step is done.

```bash
uv run pylint enzo/src core/src services/*/src
uv run mypy enzo/src core/src services/*/src
```

pylint also owns import order: standard library, then third-party (including `core`), then the package's own
imports. New services under `services/` are picked up by the glob.

## 6. Commits

Work in **small, committable steps**. After each one that passes the checks, remind the user to commit and propose
the message.

```text
TYPE(scope?): Subject in the imperative, no final period

Optional body: what and why.

Optional footer, e.g. BREAKING CHANGE: ...
```

Types (uppercase): `FEAT` · `FIX` · `DOCS` · `STYLE` · `REFACTOR` · `PERF` · `TEST` · `BUILD` · `CI` · `CHORE` · `REVERT`.
Examples: `FEAT(gateway): Add MCP tool routing` · `FIX(parts): Publish the task before status updates`.
