"""Role-aware synthetic match scenes calibrated by aggregate 360 templates."""

from __future__ import annotations

import json
import math
from pathlib import Path

from .pitch import PITCH_LENGTH, PITCH_WIDTH, clamp_location

DEFAULT_SCENE_MODEL = Path("data/models/statsbomb_360_templates.json")

FORMATION = (
    (8, 40), (22, 15), (22, 32), (22, 48), (22, 65),
    (48, 25), (48, 40), (48, 56),
    (78, 18), (78, 40), (78, 62),
)


class SceneModel:
    def __init__(self, parameters: dict[str, object]) -> None:
        self.templates = parameters.get("templates", {})

    @classmethod
    def load(cls, path: Path = DEFAULT_SCENE_MODEL) -> "SceneModel":
        return cls(json.loads(path.read_text()))

    def positions(
        self, seed: int, event_type: str, event_x: float, event_y: float, attacking_team: str, elapsed_seconds: float = 0.0
    ) -> tuple[tuple[str, float, float], ...]:
        template = self.templates.get(event_type, {})
        teammate = template.get("teammate", {}) if isinstance(template, dict) else {}
        opponent = template.get("opponent", {}) if isinstance(template, dict) else {}
        teammate_spread = float(teammate.get("dx_std", 12.0)) if isinstance(teammate, dict) else 12.0
        opponent_spread = float(opponent.get("dx_std", 15.0)) if isinstance(opponent, dict) else 15.0
        result: list[tuple[str, float, float]] = []
        for side in ("home", "away"):
            is_attacking = side == attacking_team
            direction = 1 if attacking_team == "away" else -1
            for index, (base_x, base_y) in enumerate(FORMATION):
                if is_attacking:
                    target_x = event_x + direction * (base_x - 48) * 0.35
                else:
                    target_x = PITCH_LENGTH - event_x + (base_x - 48) * 0.2
                target_y = event_y + (base_y - 40) * 0.35
                spread = teammate_spread if is_attacking else opponent_spread
                phase = seed * 0.017 + index * 0.73 + (0.4 if side == "away" else 0.0)
                jitter_x = min(8, spread * 0.35) * math.sin(elapsed_seconds * 0.18 + phase)
                jitter_y = 5 * math.cos(elapsed_seconds * 0.14 + phase * 1.7)
                x, y = clamp_location(target_x + jitter_x, target_y + jitter_y)
                result.append((f"{side}-{index + 1}", x, y))
        return tuple(result)
