# Build from the repo root: the agent needs the workspace lockfile.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY enzo/pyproject.toml enzo/pyproject.toml
COPY core core
COPY services/parts-agent services/parts-agent
RUN uv sync --package parts-agent --frozen --no-dev

CMD ["uv", "run", "--no-sync", "parts-agent"]
