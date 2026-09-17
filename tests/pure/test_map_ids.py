"""Behavior of active-map-id resolution.

A poll's data must be attributed to a physical map the device still lists. The
ijai interim/realtime upload (written while the robot localizes or moves)
carries mapHeadId=0, which is not a catalogue id — such an orphan render still
belongs to the currently active map and must not blank the camera.
"""
from __future__ import annotations

import map_ids


def test_orphan_blob_id_is_attributed_to_the_catalogue_active_map() -> None:
    """A mapHeadId=0 interim render resolves to the active catalogue map."""
    assert map_ids.resolve_active_map_id(
        blob_id=0,
        active_meta_id=1788943059,
        mqtt_id=None,
        previous_id=None,
        known_ids={1788943059, 111, 222, 333, 444},
        has_map_list=True,
    ) == 1788943059


def test_blob_id_is_trusted_when_there_is_no_catalogue() -> None:
    """Brands without a map-list catalogue keep their blob's own map id."""
    assert map_ids.resolve_active_map_id(
        blob_id=7,
        active_meta_id=None,
        mqtt_id=None,
        previous_id=None,
        known_ids=set(),
        has_map_list=False,
    ) == 7


def test_orphan_blob_id_falls_back_to_the_mqtt_signalled_id() -> None:
    """With no catalogue-active entry, the MQTT curMapId attributes the render."""
    assert map_ids.resolve_active_map_id(
        blob_id=0,
        active_meta_id=None,
        mqtt_id=4242,
        previous_id=None,
        known_ids={1788943059, 111},
        has_map_list=True,
    ) == 4242


def test_orphan_blob_id_falls_back_to_the_previously_served_id() -> None:
    """With no catalogue-active entry or MQTT signal, keep the last served map."""
    assert map_ids.resolve_active_map_id(
        blob_id=0,
        active_meta_id=None,
        mqtt_id=None,
        previous_id=555,
        known_ids={1788943059, 111},
        has_map_list=True,
    ) == 555


def test_missing_id_without_a_catalogue_resolves_to_the_single_map_key() -> None:
    """A catalogue-less device with no blob id has exactly one physical map."""
    assert map_ids.resolve_active_map_id(
        blob_id=None,
        active_meta_id=None,
        mqtt_id=None,
        previous_id=None,
        known_ids=set(),
        has_map_list=False,
    ) == map_ids.SINGLE_MAP_ID


def test_missing_id_with_a_catalogue_does_not_invent_a_single_map() -> None:
    """A transient empty catalogue on a multi-map device must not fake a map."""
    assert map_ids.resolve_active_map_id(
        blob_id=None,
        active_meta_id=None,
        mqtt_id=None,
        previous_id=None,
        known_ids={1788943059, 111},
        has_map_list=True,
    ) is None


def test_known_map_ids_collects_numeric_catalogue_ids() -> None:
    """Catalogue ids are read as ints; entries without a usable id are ignored."""
    assert map_ids.known_map_ids(
        [{"id": 42}, {"id": "7"}, {"name": "no id"}, {"id": None}, {"id": "x"}]
    ) == {42, 7}


def test_blob_id_absent_from_a_nonempty_catalogue_is_orphan() -> None:
    """A blob that names a map the device does not list is an interim frame."""
    assert map_ids.is_orphan_blob_id(0, {42, 7}) is True


def test_blob_id_in_the_catalogue_is_not_orphan() -> None:
    assert map_ids.is_orphan_blob_id(42, {42, 7}) is False


def test_blob_id_is_not_orphan_without_a_catalogue() -> None:
    """No catalogue to compare against: the blob id is taken at face value."""
    assert map_ids.is_orphan_blob_id(7, set()) is False


def test_missing_blob_id_is_not_orphan() -> None:
    assert map_ids.is_orphan_blob_id(None, {42}) is False


def test_in_catalogue_blob_id_beats_the_catalogue_active_entry() -> None:
    """A blob that names a real map is ground truth for that map."""
    assert map_ids.resolve_active_map_id(
        blob_id=111,
        active_meta_id=1788943059,
        mqtt_id=None,
        previous_id=None,
        known_ids={1788943059, 111},
        has_map_list=True,
    ) == 111
