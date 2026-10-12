"""Tracing helper: a typed wrapper around mlflow.trace."""

from collections.abc import Callable
from typing import Any, TypeVar, cast

import mlflow

F = TypeVar("F", bound=Callable[..., Any])


def traced(name: str, span_type: str) -> Callable[[F], F]:
    """Record each call of the decorated function as an MLflow span, with its inputs and output.

    A thin wrapper so type checkers and linters see the original signature, which mlflow.trace hides from them.

    Args:
        name: Span name.
        span_type: MLflow span type, e.g. SpanType.LLM.

    Returns:
        The decorator.
    """

    def decorate(func: F) -> F:
        """Wrap one function.

        Args:
            func: The function to trace.

        Returns:
            The traced function, with the same signature.
        """
        return cast(F, mlflow.trace(func, name=name, span_type=span_type))

    return decorate
