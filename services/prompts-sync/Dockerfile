# Build from the repo root: the job needs the workspace lockfile and the core package.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY enzo/pyproject.toml enzo/pyproject.toml
COPY core core
COPY services/prompts-sync services/prompts-sync
RUN uv sync --package prompts-sync --frozen --no-dev

CMD ["uv", "run", "--no-sync", "prompts-sync"]
