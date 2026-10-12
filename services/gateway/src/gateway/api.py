"""The gateway's HTTP API: one door to models, tools and agents."""

from collections.abc import Awaitable, Callable
from contextlib import nullcontext

import mlflow
from core.tracing import setup as setup_tracing
from fastapi import FastAPI, Request, Response
from mlflow.entities import SpanType
from mlflow.tracing import set_tracing_context_from_http_request_headers

from gateway.llm.routes import router as llm_router
from gateway.settings import settings
from gateway.tools.routes import router as tools_router

setup_tracing(settings.mlflow_url, settings.experiment, async_logging=False)  # see core.tracing.setup
app = FastAPI(title="Enzo gateway")


@app.middleware("http")
async def continue_trace(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Wrap the request in one span, joined to the caller's trace when the caller sent one (else a new trace).

    Args:
        request: The incoming request, possibly carrying trace context headers.
        call_next: The rest of the request handling.

    Returns:
        The response.
    """
    headers = dict(request.headers)
    traced_call = "traceparent" in headers
    with set_tracing_context_from_http_request_headers(headers) if traced_call else nullcontext():
        with mlflow.start_span(f"gateway {request.method} {request.url.path}", span_type=SpanType.CHAIN):
            return await call_next(request)
app.include_router(llm_router)
app.include_router(tools_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the gateway is up.

    Returns:
        A fixed status payload.
    """
    return {"status": "ok"}
