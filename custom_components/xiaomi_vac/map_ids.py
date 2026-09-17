"""Which physical map a poll's data belongs to. Pure — no HA imports.

The cloud blob's own ``mapHeadId`` is ground truth *only* when it names a map
the device still lists. ijai's interim/realtime upload (the frame the robot
writes while it is localizing, moving, or mid-clean) carries ``mapHeadId=0``,
which is not a catalogue id. Treating it as a map of its own invents a phantom
entry, which the map-list prune then evicts, blanking the camera for a cycle
even though the real active map is cached. An orphan render belongs to the
currently active map, so it is attributed there instead.
"""
from __future__ import annotations

# Cache key for devices whose map capability has no map-list catalogue at all
# (single physical map, e.g. viomi/dreame/roidmi profiles without get_map_list).
SINGLE_MAP_ID = 0


def resolve_active_map_id(
    *,
    blob_id: int | None,
    active_meta_id: int | None,
    mqtt_id: int | None,
    previous_id: int | None,
    known_ids: set[int],
    has_map_list: bool,
) -> int | None:
    """Resolve which physical map this cycle's data belongs to.

    Order of trust:

    1. The blob's own embedded id, but ONLY when it names a known physical map.
       An id outside the catalogue is an interim/realtime render of the *active*
       map, not a map of its own. When there is no catalogue to check against,
       the blob id is taken as-is (brands without a map list never carry one).
    2. The catalogue's "cur" entry.
    3. The MQTT-signaled curMapId.
    4. The id served on the previous cycle.
    5. A fixed single-map key, but ONLY for profiles with no map-list
       capability — an empty catalogue from a transient read failure on a
       multi-map device must not be mistaken for that.
    """
    if blob_id is not None and (not known_ids or blob_id in known_ids):
        return blob_id
    if active_meta_id is not None:
        return active_meta_id
    if mqtt_id is not None:
        return mqtt_id
    if previous_id is not None:
        return previous_id
    if not has_map_list and not known_ids:
        return SINGLE_MAP_ID
    return None
