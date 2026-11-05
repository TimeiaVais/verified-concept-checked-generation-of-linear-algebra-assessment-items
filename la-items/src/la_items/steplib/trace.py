"""Shared trace recorder for instrumented solution steps.

Every library step is declared with @step(concept_id). Calling it appends the
concept to the active trace. A step called outside `recording()` raises, so a
solution cannot run its steps without them being recorded.
"""

import collections.abc
import contextlib
import contextvars
import functools
import typing

from la_items.graph import loader

__all__ = ["CONCEPTS", "recording", "step"]

P = typing.ParamSpec("P")
R = typing.TypeVar("R")

CONCEPTS: typing.Final = loader.load_graph()
_active: contextvars.ContextVar[list[str] | None] = contextvars.ContextVar(
    "active_trace", default=None
)


@contextlib.contextmanager
def recording() -> collections.abc.Iterator[list[str]]:
    """Collect the concepts of all steps called inside the block, in call order.

    Yields
    ------
    list[str]
        The trace. It fills while the block runs.
    """
    trace: list[str] = []
    token = _active.set(trace)

    try:
        yield trace

    finally:
        _active.reset(token)


def step(
    concept_id: str,
) -> collections.abc.Callable[[collections.abc.Callable[P, R]], collections.abc.Callable[P, R]]:
    """Bind a library step to one graph concept.

    Parameters
    ----------
    concept_id : str
        An exact id from the concept graph.

    Returns
    -------
    Callable
        The decorator. The wrapped step records `concept_id` on each call.

    Raises
    ------
    ValueError
        It raises when `concept_id` is not in the graph.
    """
    if concept_id not in CONCEPTS:
        raise ValueError(f"step bound to unknown concept {concept_id!r}")

    def decorate(fn: collections.abc.Callable[P, R]) -> collections.abc.Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            trace = _active.get()
            if trace is None:
                raise RuntimeError(f"step {fn.__name__} called outside recording()")
            trace.append(concept_id)
            step_output = fn(*args, **kwargs)

            return step_output

        wrapper.concept = concept_id  # type: ignore[attr-defined]

        return wrapper

    return decorate
