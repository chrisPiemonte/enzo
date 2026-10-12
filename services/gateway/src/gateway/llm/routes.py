"""HTTP routes for model completions."""

from core.models.chat import Completion, CompletionRequest
from fastapi import APIRouter, Depends, HTTPException

from gateway.auth import caller_tokens
from gateway.llm.config import AliasConfig, load_config
from gateway.llm.providers.factory import build_provider
from gateway.llm.providers.provider import ProviderError
from gateway.llm.router import RouteError, resolve
from gateway.settings import settings

router = APIRouter(prefix="/v1")
config = load_config(settings.config, settings.model_dump(mode="json"))


@router.get("/models")
def models() -> dict[str, AliasConfig]:
    """List the model aliases callers can use.

    Returns:
        Each alias with the provider and model behind it.
    """
    return config.aliases


@router.post("/complete", dependencies=[Depends(caller_tokens)])
async def complete(request: CompletionRequest) -> Completion:
    """Complete a conversation with the model behind the requested alias.

    Args:
        request: Alias, messages and tools to send to the model.

    Returns:
        The model's completion.

    Raises:
        HTTPException: 404 if the alias or provider is unknown, 502 if the provider fails.
    """
    try:
        route = resolve(request, config)
        provider = build_provider(route)
        return await provider.complete(route.model, request.messages, request.tools)
    except RouteError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
