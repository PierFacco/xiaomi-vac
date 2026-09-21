"""Fault-code translation for ijai-family vacuums (issue #2).

The device reports named faults, but MIoT only carries the raw integer
(siid 2/piid 2); the vendor app translates the codes. This module is the
pure (no Home Assistant) translation table so the device layer and any
future UI share one authoritative mapping. Codes are vendor-app
authoritative: 2108 repositioning, 589/611 relocation failed, 502 low
battery, 2114 dust box full.
"""
from __future__ import annotations

FAULT_TEXT: dict[int, str] = {
    2108: "Repositioning…",
    589: "Couldn't reposition — please resume the clean",
    611: "Couldn't reposition — please resume the clean",
    502: "Low battery",
    2114: "Dust box full",
}

RELOCATING_FAULT = 2108


def fault_text(fault: int | None) -> str | None:
    """Translate a raw fault code to its vendor-app text.

    ``None`` (unread prop) and ``0`` (no fault) both stay ``None``; codes
    outside the table get a generic label so the raw value still surfaces
    readably.
    """
    if fault is None or fault == 0:
        return None
    return FAULT_TEXT.get(fault, f"Unknown fault ({fault})")


def is_relocating(fault: int | None) -> bool:
    """True only while the repositioning fault (2108) is active."""
    return fault == RELOCATING_FAULT
