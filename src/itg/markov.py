"""Compact, seedable Markov model for football event motion and types."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .pitch import PITCH_LENGTH, PITCH_WIDTH

DEFAULT_MODEL_PATH = Path("data/models/statsbomb_markov.json")
EVENT_TYPES = ("pass", "pressure", "tackle", "shot", "carry", "possession")
X_BINS = 6
Y_BINS = 4


def state_for(event_type: str, x: float, y: float) -> str:
    x_bin = min(X_BINS - 1, max(0, int(x / PITCH_LENGTH * X_BINS)))
    y_bin = min(Y_BINS - 1, max(0, int(y / PITCH_WIDTH * Y_BINS)))
    return f"{event_type}:{x_bin}:{y_bin}"


def _parse_state(state: str) -> tuple[str, int, int]:
    event_type, x_bin, y_bin = state.split(":")
    return event_type, int(x_bin), int(y_bin)


class EventMarkovModel:
    """Sample correlated event types and locations from fitted parameters."""

    def __init__(self, parameters: dict[str, Any]) -> None:
        self.parameters = parameters
        self.transitions = parameters["transitions"]
        self.initial = parameters["initial"]
        self.displacements = parameters["displacements"]

    @classmethod
    def load(cls, path: Path = DEFAULT_MODEL_PATH) -> "EventMarkovModel":
        return cls(json.loads(path.read_text()))

    def _choose(self, rng: random.Random, weights: dict[str, float]) -> str:
        choices = tuple(weights)
        return rng.choices(choices, weights=tuple(weights[item] for item in choices), k=1)[0]

    def initial_event(self, rng: random.Random) -> tuple[str, float, float]:
        state = self._choose(rng, self.initial)
        event_type, x_bin, y_bin = _parse_state(state)
        return event_type, rng.uniform(x_bin * PITCH_LENGTH / X_BINS, (x_bin + 1) * PITCH_LENGTH / X_BINS), rng.uniform(
            y_bin * PITCH_WIDTH / Y_BINS, (y_bin + 1) * PITCH_WIDTH / Y_BINS
        )

    def next_event(
        self, rng: random.Random, previous_type: str, previous_x: float, previous_y: float
    ) -> tuple[str, float, float]:
        previous_state = state_for(previous_type, previous_x, previous_y)
        next_state = self._choose(rng, self.transitions.get(previous_state, self.initial))
        event_type, _, _ = _parse_state(next_state)
        displacement = self.displacements.get(f"{previous_state}>{next_state}", {"dx_mean": 0, "dx_std": 12, "dy_mean": 0, "dy_std": 12})
        x = previous_x + rng.gauss(displacement["dx_mean"], max(2.0, displacement["dx_std"]))
        y = previous_y + rng.gauss(displacement["dy_mean"], max(2.0, displacement["dy_std"]))
        return event_type, max(0.0, min(PITCH_LENGTH, x)), max(0.0, min(PITCH_WIDTH, y))


def load_optional_model(path: Path = DEFAULT_MODEL_PATH) -> EventMarkovModel | None:
    if not path.exists():
        return None
    return EventMarkovModel.load(path)
