import pytest

from la_items.steplib import trace


@trace.step("det_2x2")
def det2(a: int, b: int, c: int, d: int) -> int:
    return a * d - b * c


@trace.step("cofactor_expansion")
def outer() -> int:
    return det2(1, 2, 3, 4)


def test_nested_steps_recorded_in_order() -> None:
    with trace.recording() as recorded:
        assert outer() == -2
    assert recorded == ["cofactor_expansion", "det_2x2"]


def test_step_outside_recording_raises() -> None:
    with pytest.raises(RuntimeError, match="outside recording"):
        det2(1, 2, 3, 4)


def test_recordings_are_isolated() -> None:
    with trace.recording() as first:
        det2(1, 0, 0, 1)
        with trace.recording() as inner:
            det2(1, 0, 0, 1)
        det2(1, 0, 0, 1)
    assert first == ["det_2x2", "det_2x2"]
    assert inner == ["det_2x2"]


def test_unknown_concept_rejected() -> None:
    with pytest.raises(ValueError, match="unknown concept"):
        trace.step("eigenvalues_2x2")


def test_step_exposes_concept() -> None:
    assert det2.concept == "det_2x2"  # type: ignore[attr-defined]
