"""Tracing helpers: MLflow setup, and a typed wrapper around mlflow.trace."""

import atexit
import logging
import os
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


def setup(url: str, experiment: str, async_logging: bool = True) -> None:
    """Send traces to MLflow; if MLflow is unreachable, keep working without tracing.

    Args:
        url: MLflow tracking server URL.
        experiment: Experiment that traces starting in this service belong to.
        async_logging: Export in the background. Services that continue a caller's trace must pass False: the
            remote trace context ends with the request, before a background export would run, and its spans
            would be dropped.
    """
    logging.getLogger("mlflow").setLevel(logging.WARNING)  # keep MLflow's INFO chatter out of the logs
    if not async_logging:  # trace logging has its own async switch, on by default; enable_async_logging misses it
        os.environ["MLFLOW_ENABLE_ASYNC_TRACE_LOGGING"] = "false"
    try:
        mlflow.set_tracking_uri(url)
        mlflow.set_experiment(experiment)
        mlflow.config.enable_async_logging(async_logging)  # type: ignore[no-untyped-call]  # mlflow ships it untyped
        atexit.register(mlflow.flush_trace_async_logging)
    except Exception as error:  # pylint: disable=broad-exception-caught  # tracing must never stop the service
        logging.getLogger(__name__).warning("tracing disabled: %r", error)
        mlflow.tracing.disable()
