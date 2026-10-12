# Build from the repo root: the server needs the workspace lockfile.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY enzo/pyproject.toml enzo/pyproject.toml
COPY core core
COPY services/mcp-manuals services/mcp-manuals
RUN uv sync --package mcp-manuals --frozen --no-dev

CMD ["uv", "run", "--no-sync", "mcp-manuals"]
