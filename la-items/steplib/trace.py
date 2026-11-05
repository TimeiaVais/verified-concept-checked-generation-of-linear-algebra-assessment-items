"""Shared trace recorder for instrumented solution steps.

Every library step is declared with @step(concept_id). Calling it appends the
concept to the active trace. A step called outside `recording()` raises, so a
solution cannot run its steps without them being recorded.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import ParamSpec, TypeVar

from graph.loader import load_graph

P = ParamSpec("P")
R = TypeVar("R")

CONCEPTS = load_graph()
_active: ContextVar[list[str] | None] = ContextVar("active_trace", default=None)


@contextmanager
def recording() -> Iterator[list[str]]:
    """Collect the concepts of all steps called inside the block, in call order."""
    trace: list[str] = []
    token = _active.set(trace)
    try:
        yield trace
    finally:
        _active.reset(token)


def step(concept_id: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if concept_id not in CONCEPTS:
        raise ValueError(f"step bound to unknown concept {concept_id!r}")

    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            trace = _active.get()
            if trace is None:
                raise RuntimeError(f"step {fn.__name__} called outside recording()")
            trace.append(concept_id)
            return fn(*args, **kwargs)

        wrapper.concept = concept_id  # type: ignore[attr-defined]
        return wrapper

    return decorate
