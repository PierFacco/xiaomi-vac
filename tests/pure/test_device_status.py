"""Pure tests for IjaiVacuumDevice status handling."""
from __future__ import annotations

import pytest

from .helpers import FakeMiotDevice, load_device_module


@pytest.mark.parametrize(
    ("raw_status", "expected_raw", "expected_activity"),
    [
        (5, 5, "cleaning"),
        (2, 2, "paused"),
        (999, 999, "idle"),
    ],
)
def test_status_maps_raw_activity(monkeypatch, raw_status, expected_raw, expected_activity):
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    FakeMiotDevice.property_values = {(status_prop.siid, status_prop.piid): raw_status}

    status = device.status()

    assert status.raw_status == expected_raw
    assert status.activity == expected_activity


# Firmware status enum (siid 2/piid 1, authoritative from the vendor plugin):
# 0 sleep, 1 idle, 2 pause, 3 goCharging, 4 charging, 5 sweepMoping,
# 6 sweepMoping2, 7 moping, 8 upgrading, 9 mopCleaning, 10 mopAirdrying.
_STATUS_LABELS = {
    0: "sleep",
    1: "idle",
    2: "paused",
    3: "returning",
    4: "charging",
    5: "cleaning",
    6: "cleaning",
    7: "mopping",
    8: "upgrading",
    9: "mop_cleaning",
    10: "mop_air_drying",
}


@pytest.mark.parametrize(
    ("raw", "expected_status"),
    [
        *[(raw, label) for raw, label in _STATUS_LABELS.items()],
        # raw outside both tables -> status falls back to the activity ("idle")
        (999, "idle"),
    ],
)
def test_status_exposes_translated_device_state(monkeypatch, raw, expected_status):
    """status.status is the translated device-state label (issue #1); a raw
    value missing from the label table falls back to the collapsed activity."""
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    FakeMiotDevice.property_values = {(status_prop.siid, status_prop.piid): raw}

    status = device.status()

    assert status.raw_status == raw
    assert status.status == expected_status
    if raw in (8, 9, 10):
        # upgrading / mop cleaning / mop air-drying must not collapse to idle
        assert status.activity != "idle"


def test_status_raises_when_required_prop_fails(monkeypatch):
    """A failing status read must raise DeviceCommunicationError, not return idle."""
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    FakeMiotDevice.property_values = {
        (status_prop.siid, status_prop.piid): RuntimeError("network timeout")
    }

    with pytest.raises(device_mod.DeviceCommunicationError):
        device.status()


def test_status_translates_repositioning_fault(monkeypatch):
    """fault stays raw; fault_text/relocating derive from it (issue #2).

    The fault prop is siid 2/piid 2; 2108 is the vendor's repositioning code.
    """
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    fault_prop = device.core.fault
    FakeMiotDevice.property_values = {
        (status_prop.siid, status_prop.piid): 5,
        (fault_prop.siid, fault_prop.piid): 2108,
    }

    status = device.status()

    assert status.fault == 2108
    assert status.fault_text == "Repositioning…"
    assert status.relocating is True


def test_status_relocation_failed_is_not_relocating(monkeypatch):
    """589 (relocation failed) translates but is not an active repositioning."""
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    fault_prop = device.core.fault
    FakeMiotDevice.property_values = {
        (status_prop.siid, status_prop.piid): 5,
        (fault_prop.siid, fault_prop.piid): 589,
    }

    status = device.status()

    assert status.fault == 589
    assert status.fault_text == "Couldn't reposition — please resume the clean"
    assert status.relocating is False


def test_status_tolerates_optional_prop_none(monkeypatch):
    """Optional props returning None must not raise; required status must succeed."""
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    # Only supply the required status prop; everything else defaults to None via FakeMiotDevice.
    FakeMiotDevice.property_values = {(status_prop.siid, status_prop.piid): 5}

    status = device.status()

    assert status.raw_status == 5
    # Optional fields that have no prop on this model or no value stay None.
    assert status.sweep_type_raw is None or isinstance(status.sweep_type_raw, int)


def test_status_skips_absent_core_props(monkeypatch):
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "dreame.vacuum.p2008")
    status_prop = device.core.status
    FakeMiotDevice.property_values = {(status_prop.siid, status_prop.piid): 5}

    assert device.core.sweep_type is None
    assert device.core.alarm is None

    status = device.status()

    assert status.sweep_type_raw is None
    assert status.alarm_raw is None
    assert all(call[1] is not None and call[2] is not None for call in FakeMiotDevice.instances[-1].calls)


def test_lean_core_fields_stay_parked(monkeypatch):
    """clean-area/time remain outside core and parked at None (consumable
    life is polled now — covered by tests/pure/test_consumables.py)."""
    device_mod = load_device_module(monkeypatch)
    device = device_mod.IjaiVacuumDevice("host", "token", "ijai.vacuum.v17")
    status_prop = device.core.status
    FakeMiotDevice.property_values = {(status_prop.siid, status_prop.piid): 5}

    status = device.status()

    assert status.clean_area is None
    assert status.clean_time is None


def test_as_int_coercion(monkeypatch):
    device_mod = load_device_module(monkeypatch)

    assert device_mod._as_int("83") == 83
    assert device_mod._as_int(None) is None
    assert device_mod._as_int("junk") is None


@pytest.mark.parametrize(
    "model",
    [
        "roidmi.vacuum.r1b",
        "roborock.vacuum.a01",
        "dreame.vacuum.r2235a",
    ],
)
def test_device_refuses_non_onboardable_models(monkeypatch, model: str):
    device_mod = load_device_module(monkeypatch)

    with pytest.raises(ValueError):
        device_mod.IjaiVacuumDevice("host", "token", model)
