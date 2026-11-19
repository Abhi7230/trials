"""Request routing with policy and filtering."""

from dataclasses import dataclass

from modelgate.catalog import Catalog, Model
from modelgate.policies import Policy, get_policy
from modelgate.tokens import Tokenizer


class NoRouteError(Exception):
    """No models satisfy the request requirements."""


@dataclass
class RoutingRequest:
    """Routing request parameters."""

    model: str  # "auto", "auto:policy", or explicit model ID
    messages: list[dict[str, str]]
    temperature: float = 0.7
    required_capabilities: frozenset[str] = frozenset()
    policy_override: str | None = None  # From x-modelgate-policy header


class Router:
    """Model router with policy and filtering."""

    def __init__(self, catalog: Catalog, tokenizer: Tokenizer, default_policy: str = "balanced"):
        self.catalog = catalog
        self.tokenizer = tokenizer
        self.default_policy = default_policy

    def route(self, request: RoutingRequest) -> list[Model]:
        """Route request to ordered list of candidate models."""
        # Handle explicit model
        if not request.model.startswith("auto"):
            explicit = self.catalog.get(request.model)
            if explicit is None:
                raise NoRouteError(f"Model not found: {request.model}")
            return [explicit]

        # Parse auto:policy or use default
        if request.model.startswith("auto:"):
            policy_name = request.model.split(":", 1)[1]
        elif request.policy_override:
            policy_name = request.policy_override
        else:
            policy_name = self.default_policy

        policy = get_policy(policy_name)

        # Estimate context size
        prompt_text = " ".join(msg.get("content", "") for msg in request.messages)
        input_tokens = self.tokenizer.estimate(prompt_text)
        output_tokens = 500  # Conservative estimate

        # Filter by context window and capabilities
        min_context = input_tokens + output_tokens
        candidates = self.catalog.filter(
            min_context=min_context,
            required_capabilities=request.required_capabilities,
        )

        if not candidates:
            raise NoRouteError(
                f"No models found for context={min_context}, "
                f"capabilities={request.required_capabilities}"
            )

        # Rank by policy
        ranked = policy.rank(candidates, input_tokens, output_tokens)
        return [model for model, _score in ranked]
