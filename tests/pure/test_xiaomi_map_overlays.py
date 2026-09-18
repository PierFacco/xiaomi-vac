"""Pure-tier tests for Xiaomi JSON carpet and travelled-path overlays."""
from __future__ import annotations

import importlib
import json
import sys
from types import ModuleType, SimpleNamespace

from PIL import Image

from xiaomi_map_overlays import (
    calibration_transform,
    draw_overlays,
    parse_carpets,
    parse_path,
)


def _point(x, y, type_=1):
    return {"x": x, "y": y, "type": type_}


def _path_payload(points):
    return json.dumps({"paths": {"points": json.dumps(points)}})


def _map_data():
    return SimpleNamespace(
        path=None,
        charger=None,
        vacuum_position=None,
        goto=None,
        rooms={},
        walls=[],
        no_go_areas=[],
        no_mopping_areas=[],
        zones=[],
        vacuum_room=None,
        vacuum_room_name=None,
    )


def test_parse_carpets_keeps_only_numeric_quadrilaterals():
    payload = json.dumps({"carpets": [
        {"p": [0, 0, 1000, 0, 1000, 1000, 0, 1000]},
        {"p": [1, 2]},
        {"p": [0, 0, "bad", 0, 1, 1, 0, 1]},
        {"p": [0, 0, float("nan"), 0, 1, 1, 0, 1]},
    ]})

    assert parse_carpets(payload) == [
        [0, 0, 1000, 0, 1000, 1000, 0, 1000]
    ]
    assert parse_carpets("not json") == []


def test_parse_path_removes_sentinels_and_splits_new_legs():
    points = [
        _point(0, 0, 0),
        _point(1, 1),
        _point(10, 1),
        _point(500, 500, 0),
        _point(510, 500),
        _point(0, 0, 0),
    ]

    assert parse_path(_path_payload(points)) == [
        [(1, 1), (10, 1)],
        [(500, 500), (510, 500)],
    ]


def test_parse_path_drops_single_point_legs_and_malformed_payloads():
    points = [_point(1, 1), _point(2, 2), _point(99, 99, 0)]

    assert parse_path(_path_payload(points)) == [[(1, 1), (2, 2)]]
    assert parse_path("not json") == []
    assert parse_path(json.dumps({"paths": {"points": {}}})) == []


def test_vector_overlays_are_scaled_without_changing_legacy_path(monkeypatch):
    parser_package = ModuleType("vacuum_map_parser_ijai")
    parser_package.__path__ = []
    protobuf_module = ModuleType("vacuum_map_parser_ijai.RobotMap_pb2")
    monkeypatch.setitem(sys.modules, "vacuum_map_parser_ijai", parser_package)
    monkeypatch.setitem(
        sys.modules, "vacuum_map_parser_ijai.RobotMap_pb2", protobuf_module
    )
    sys.modules.pop("map_vector", None)
    map_vector = importlib.import_module("map_vector")

    md = _map_data()
    md.path = SimpleNamespace(path=[[
        SimpleNamespace(x=100, y=200),
        SimpleNamespace(x=300, y=400),
    ]])

    out = map_vector.vector_map(
        md,
        b"",
        ijai_grid=False,
        units_per_metre=1000,
        carpets=[[0, 0, 1000, 0, 1000, 1000, 0, 1000]],
        path_segments=[[(0, 0), (1000, 0)], [(2000, 2000), (2500, 2000)]],
    )

    assert out["path"] == [[0.1, 0.2], [0.3, 0.4]]
    assert out["path_segments"] == [
        [[0.0, 0.0], [1.0, 0.0]],
        [[2.0, 2.0], [2.5, 2.0]],
    ]
    assert out["carpets"] == [[0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]]


def test_calibration_transform_maps_vacuum_coordinates_to_pixels():
    calibration = [
        {"vacuum": {"x": 0, "y": 0}, "map": {"x": 100, "y": 200}},
        {"vacuum": {"x": 10, "y": 0}, "map": {"x": 110, "y": 200}},
        {"vacuum": {"x": 0, "y": 10}, "map": {"x": 100, "y": 190}},
    ]
    transform = calibration_transform(calibration)

    assert transform is not None
    assert transform(5, 5) == (105, 195)


def test_draw_overlays_uses_calibration_and_crop_offset():
    image = Image.new("RGBA", (20, 20), (255, 255, 255, 255))
    calibration = [
        {"vacuum": {"x": 0, "y": 0}, "map": {"x": 5, "y": 15}},
        {"vacuum": {"x": 10, "y": 0}, "map": {"x": 15, "y": 15}},
        {"vacuum": {"x": 0, "y": 10}, "map": {"x": 5, "y": 5}},
    ]

    result = draw_overlays(
        image,
        [[0, 0, 10, 0, 10, 10, 0, 10]],
        [[(0, 5), (10, 5)]],
        calibration,
        offset_x=2,
        offset_y=2,
    )

    assert result.getpixel((8, 8)) == (64, 200, 255, 210)
