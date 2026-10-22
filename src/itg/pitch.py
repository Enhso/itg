"""Canonical football pitch geometry and presentation conversions."""

from __future__ import annotations

PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0


def clamp_location(x: float, y: float) -> tuple[float, float]:
    return max(0.0, min(PITCH_LENGTH, x)), max(0.0, min(PITCH_WIDTH, y))


def to_pixels(x: float, y: float, width: int, height: int, margin_x: int = 80, margin_y: int = 50) -> tuple[int, int]:
    pitch_width = width - 2 * margin_x
    pitch_height = height - 2 * margin_y
    return (
        margin_x + round(x / PITCH_LENGTH * pitch_width),
        margin_y + round(y / PITCH_WIDTH * pitch_height),
    )
