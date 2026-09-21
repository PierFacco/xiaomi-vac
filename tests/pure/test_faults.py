"""Pure tests for the fault-code translation table (issue #2).

The device reports named faults but the integration only carried the raw
integer (siid 2/piid 2). These tests pin the authoritative code -> text
mapping from the vendor app, the generic label for unknown codes, and the
"no fault" sentinel (0/None) that must not render as a fault label.
"""
from __future__ import annotations

import pytest

# Imported standalone (not via the HA-importing package __init__) — see conftest.
import faults


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (2108, "Repositioning…"),
        (589, "Couldn't reposition — please resume the clean"),
        (611, "Couldn't reposition — please resume the clean"),
        (502, "Low battery"),
        (2114, "Dust box full"),
    ],
)
def test_known_fault_codes_translate_to_exact_text(code: int, expected: str) -> None:
    """Each authoritative vendor fault code maps to its exact app text."""
    assert faults.fault_text(code) == expected


def test_unknown_fault_code_gets_generic_label() -> None:
    """Codes outside the table still surface a readable label with the code."""
    assert faults.fault_text(1234) == "Unknown fault (1234)"


@pytest.mark.parametrize("value", [0, None])
def test_no_fault_translates_to_none(value: int | None) -> None:
    """0 is the no-fault sentinel and None an unread prop: both stay None."""
    assert faults.fault_text(value) is None


def test_relocating_fault_constant_is_2108() -> None:
    assert faults.RELOCATING_FAULT == 2108


def test_is_relocating_true_only_while_repositioning_active() -> None:
    assert faults.is_relocating(2108) is True


@pytest.mark.parametrize("code", [589, 611, 502, 2114])
def test_is_relocating_false_for_other_known_faults(code: int) -> None:
    assert faults.is_relocating(code) is False


def test_is_relocating_false_without_a_fault() -> None:
    assert faults.is_relocating(None) is False
