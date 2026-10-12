"""The gateway's HTTP API: one door to models, tools and agents."""

from fastapi import FastAPI

from gateway.llm.routes import router as llm_router
from gateway.tools.routes import router as tools_router

app = FastAPI(title="Enzo gateway")
app.include_router(llm_router)
app.include_router(tools_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the gateway is up.

    Returns:
        A fixed status payload.
    """
    return {"status": "ok"}
