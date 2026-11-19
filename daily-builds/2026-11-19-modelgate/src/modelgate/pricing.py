"""Cost calculation utilities."""

from modelgate.catalog import Model


def calculate_cost(model: Model, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a completion."""
    return model.blended_cost(input_tokens, output_tokens)
