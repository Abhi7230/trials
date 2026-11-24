"""Exceptions for GGUF operations."""


class GGUFError(Exception):
    """Base exception for GGUF operations."""

    def __init__(self, message: str, offset: int | None = None):
        self.offset = offset
        if offset is not None:
            message = f"{message} (at byte offset {offset})"
        super().__init__(message)
