# Build from the repo root: the server needs the workspace lockfile.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY enzo/pyproject.toml enzo/pyproject.toml
COPY core core
COPY services/mcp-history services/mcp-history
RUN uv sync --package mcp-history --frozen --no-dev

CMD ["uv", "run", "--no-sync", "mcp-history"]
