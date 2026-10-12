# Build from the repo root: the gateway needs the workspace lockfile and the core package.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY enzo/pyproject.toml enzo/pyproject.toml
COPY core core
COPY services/gateway services/gateway
RUN uv sync --package gateway --frozen --no-dev

CMD ["uv", "run", "--no-sync", "gateway"]
