"""FastAPI application."""

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from modelgate.breaker import CircuitBreaker
from modelgate.cache import ResponseCache
from modelgate.catalog import Catalog, Model
from modelgate.config import load_config
from modelgate.executor import ExecutionError, Executor
from modelgate.limits import LimitExceededError, LimitsManager
from modelgate.pricing import calculate_cost
from modelgate.providers import MockProvider
from modelgate.router import NoRouteError, Router, RoutingRequest
from modelgate.tokens import SimpleTokenizer

# Global config path (set by CLI)
CONFIG_PATH = Path("models.yaml")

# Lazy-loaded components
_catalog: Catalog | None = None
_cache: ResponseCache | None = None
_limits: LimitsManager | None = None
_breaker: CircuitBreaker | None = None
_router: Router | None = None
_executor: Executor | None = None
_provider: MockProvider | None = None


def get_components() -> tuple[Catalog, ResponseCache, LimitsManager, Router, Executor]:
    """Lazy-load and return components."""
    global _catalog, _cache, _limits, _breaker, _router, _executor, _provider

    if _catalog is None:
        cfg = load_config(CONFIG_PATH)
        _catalog = Catalog([Model.from_config(m) for m in cfg.models])
        _cache = ResponseCache(
            max_size=cfg.cache.max_size,
            ttl_seconds=cfg.cache.ttl_seconds,
        )
        _limits = LimitsManager(
            default_daily_usd=cfg.limits.default_daily_usd,
            default_rpm=cfg.limits.default_rpm,
            default_tpm=cfg.limits.default_tpm,
        )
        _breaker = CircuitBreaker(
            failure_threshold=cfg.circuit_breaker.failure_threshold,
            cooldown_seconds=cfg.circuit_breaker.cooldown_seconds,
        )
        _router = Router(_catalog, SimpleTokenizer())
        _provider = MockProvider(latency_ms=10)
        _executor = Executor(
            provider=_provider,
            breaker=_breaker,
            max_attempts=cfg.fallback.max_attempts,
            timeout=cfg.fallback.timeout_seconds,
        )

    return _catalog, _cache, _limits, _router, _executor  # type: ignore


app = FastAPI(title="Modelgate", version="0.1.0")


# Request/Response models
class Message(BaseModel):
    """Chat message."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


class Usage(BaseModel):
    """Token usage."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    """Completion choice."""

    index: int
    message: Message
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response."""

    error: dict[str, Any]


class ModelInfo(BaseModel):
    """Model metadata."""

    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "modelgate"


class ModelsResponse(BaseModel):
    """List of models."""

    object: str = "list"
    data: list[ModelInfo]


# Auth helper
def check_auth(authorization: str | None) -> str:
    """Check authorization and return API key."""
    # Load config to check if keys are configured
    cfg = load_config(CONFIG_PATH)

    if not cfg.keys:
        # Open mode
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    api_key = authorization[7:]
    if api_key not in cfg.keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.get("/v1/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    """List available models."""
    catalog, _, _, _, _ = get_components()
    models = [ModelInfo(id=m.id) for m in catalog.all()]
    return ModelsResponse(data=models)


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """Get metrics."""
    _, cache, _, _, executor = get_components()
    provider = executor.provider

    return {
        "cache_size": len(cache._cache),
        "provider_calls": getattr(provider, "call_count", 0),
    }


@app.get("/v1/usage")
def usage(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Get usage for API key."""
    api_key = check_auth(authorization)
    _, _, limits, _, _ = get_components()

    remaining = limits.get_remaining_budget(api_key)
    return {
        "api_key": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        "remaining_budget_usd": remaining,
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(
    request: ChatCompletionRequest,
    req: Request,
    authorization: str | None = Header(None),
    x_modelgate_policy: str | None = Header(None),
) -> ChatCompletionResponse:
    """OpenAI-compatible chat completions endpoint."""
    api_key = check_auth(authorization)
    catalog, cache, limits, router, executor = get_components()

    # Parse capabilities from request
    capabilities = set()
    if request.model.endswith("-vision"):
        capabilities.add("vision")

    # Normalize request for caching
    cache_request = {
        "model": request.model,
        "messages": [m.model_dump() for m in request.messages],
        "temperature": request.temperature,
    }

    # Check cache
    cached = cache.get(cache_request)
    if cached:
        req.state.cache_hit = True
        return ChatCompletionResponse.model_validate(cached)

    req.state.cache_hit = False

    try:
        # Route
        routing_request = RoutingRequest(
            model=request.model,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            required_capabilities=frozenset(capabilities),
            policy_override=x_modelgate_policy,
        )

        candidates = router.route(routing_request)

        # Estimate tokens for limits check
        prompt = " ".join(m.content for m in request.messages)
        est_tokens = len(prompt) // 4
        est_cost = candidates[0].blended_cost(est_tokens, 500)

        # Check limits
        try:
            limits.check_and_consume(api_key, est_tokens, est_cost)
        except LimitExceededError as e:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "message": str(e),
                        "type": "insufficient_quota",
                        "code": "rate_limit_exceeded",
                    }
                },
            ) from e

        # Execute
        result = executor.execute(candidates, cache_request)

        # Calculate actual cost
        cost = calculate_cost(result.model, result.response.input_tokens, result.response.output_tokens)

        # Build response
        response_data = {
            "id": f"chatcmpl-{int(time.time())}",
            "created": int(time.time()),
            "model": result.model.id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result.response.content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": result.response.input_tokens,
                "completion_tokens": result.response.output_tokens,
                "total_tokens": result.response.input_tokens + result.response.output_tokens,
            },
        }

        # Cache response
        cache.put(cache_request, response_data)

        # Add custom headers
        req.state.model = result.model.id
        req.state.cost = cost
        req.state.attempts = result.attempts

        return ChatCompletionResponse.model_validate(response_data)

    except NoRouteError as e:
        raise HTTPException(status_code=400, detail={"error": {"message": str(e)}}) from e
    except ExecutionError as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": f"All {e.attempts} attempts failed",
                    "attempts": e.attempts,
                    "errors": e.errors,
                }
            },
        ) from e


@app.middleware("http")
async def add_custom_headers(request: Request, call_next):  # type: ignore
    """Add custom headers to responses."""
    response = await call_next(request)

    # Add cache header
    if hasattr(request.state, "cache_hit"):
        response.headers["x-modelgate-cache"] = "hit" if request.state.cache_hit else "miss"

    # Add model/cost/attempts headers
    if hasattr(request.state, "model"):
        response.headers["x-modelgate-model"] = request.state.model
    if hasattr(request.state, "cost"):
        response.headers["x-modelgate-cost-usd"] = f"{request.state.cost:.8f}"
    if hasattr(request.state, "attempts"):
        response.headers["x-modelgate-attempts"] = str(request.state.attempts)

    return response
