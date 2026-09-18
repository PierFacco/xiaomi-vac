"""Carpet and travelled-path overlays for Xiaomi JSON maps."""
from __future__ import annotations

import json
import logging
import math
from collections.abc import Callable

from PIL import Image, ImageDraw

_LOGGER = logging.getLogger(__name__)


def parse_carpets(unpacked: str | bytes) -> list[list[float]]:
    """Extract carpet quadrilaterals from a Xiaomi JSON map."""
    try:
        carpets = json.loads(unpacked).get("carpets") or []
    except (AttributeError, TypeError, UnicodeDecodeError, ValueError):
        return []
    return [
        carpet["p"]
        for carpet in carpets
        if isinstance(carpet, dict)
        and isinstance(carpet.get("p"), list)
        and len(carpet["p"]) == 8
        and all(
            isinstance(value, (int, float)) and math.isfinite(value)
            for value in carpet["p"]
        )
    ]


def parse_path(unpacked: str | bytes) -> list[list[tuple[float, float]]]:
    """Extract independent travelled-path segments from a Xiaomi JSON map."""
    try:
        payload = json.loads(unpacked)
        encoded = payload.get("paths", {}).get("points") or "[]"
        points = json.loads(encoded) if isinstance(encoded, str) else encoded
    except (AttributeError, TypeError, UnicodeDecodeError, ValueError):
        return []
    if not isinstance(points, list):
        return []

    runs: list[list[dict]] = []
    current: list[dict] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        x, y = point.get("x"), point.get("y")
        if (
            not isinstance(x, (int, float))
            or not isinstance(y, (int, float))
            or not math.isfinite(x)
            or not math.isfinite(y)
        ):
            continue
        if x == 0 and y == 0:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(point)
    if current:
        runs.append(current)
    if not runs:
        return []

    segments: list[list[tuple[float, float]]] = []
    segment: list[tuple[float, float]] = []
    for point in max(runs, key=len):
        if point.get("type") == 0 and segment:
            if len(segment) >= 2:
                segments.append(segment)
            segment = []
        segment.append((point["x"], point["y"]))
    if len(segment) >= 2:
        segments.append(segment)
    return segments


def calibration_transform(
    calibration: list[dict],
) -> Callable[[float, float], tuple[float, float]] | None:
    """Return a vacuum-coordinate to image-pixel transform."""
    if len(calibration) < 3:
        return None
    p0, p1, p2 = calibration[:3]
    try:
        dx = p1["vacuum"]["x"] - p0["vacuum"]["x"]
        dy = p2["vacuum"]["y"] - p0["vacuum"]["y"]
        if not dx or not dy:
            return None
        scale_x = (p1["map"]["x"] - p0["map"]["x"]) / dx
        scale_y = (p2["map"]["y"] - p0["map"]["y"]) / dy
        offset_x = p0["map"]["x"] - p0["vacuum"]["x"] * scale_x
        offset_y = p0["map"]["y"] - p0["vacuum"]["y"] * scale_y
    except (KeyError, TypeError):
        return None
    return lambda x, y: (offset_x + x * scale_x, offset_y + y * scale_y)


def draw_overlays(
    image: Image.Image,
    carpets: list[list[float]],
    path_segments: list[list[tuple[float, float]]],
    calibration: list[dict],
    offset_x: int,
    offset_y: int,
) -> Image.Image:
    """Draw Xiaomi-only overlays without changing the base renderer."""
    transform = calibration_transform(calibration)
    if transform is None or (not carpets and not path_segments):
        return image
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    for carpet in carpets:
        try:
            points = [transform(carpet[i], carpet[i + 1]) for i in range(0, 8, 2)]
            points = [(x - offset_x, y - offset_y) for x, y in points]
            draw.polygon(
                points,
                fill=(210, 170, 90, 70),
                outline=(180, 138, 60, 225),
                width=2,
            )
        except (IndexError, OverflowError, TypeError, ValueError):
            _LOGGER.debug("Could not draw Xiaomi carpet", exc_info=True)
    for segment in path_segments:
        try:
            points = [transform(x, y) for x, y in segment]
            points = [(x - offset_x, y - offset_y) for x, y in points]
            draw.line(points, fill=(64, 200, 255, 210), width=2, joint="curve")
        except (OverflowError, TypeError, ValueError):
            _LOGGER.debug("Could not draw Xiaomi path segment", exc_info=True)
    return image
