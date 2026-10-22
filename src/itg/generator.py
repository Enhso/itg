"""Seedable synthetic match event generation with observable planted shifts."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from .markov import load_optional_model
from .models import Match, MatchEvent, PlantedShift, Team
from .pitch import PITCH_LENGTH, PITCH_WIDTH


@dataclass(frozen=True)
class MatchConfig:
    seed: int = 61
    match_id: str = "demo-001"
    duration_minutes: int = 90
    home_team: str = "Corvane FC"
    away_team: str = "Tessaly Athletic"
    shift_minute: int = 61
    shift_team: Team = "away"
    shift_kind: str = "high_press"
    shift_duration: int = 12
    # Calibrated against the core action-event volume (passes, carries,
    # pressures, and shots) in the external development sample.
    base_events_per_minute: int = 27
    model_path: Path = Path("data/models/statsbomb_markov.json")


def _players(team: Team) -> tuple[str, ...]:
    prefix = "C" if team == "home" else "T"
    return tuple(f"{prefix}{position}" for position in ("GK", "CB1", "CB2", "FB", "CM1", "CM2", "W", "AM", "ST"))


def _event_type(rng: random.Random) -> str:
    return rng.choices(
        ["pass", "pressure", "tackle", "shot", "carry", "possession"],
        weights=[55, 16, 8, 3, 10, 8],
        k=1,
    )[0]


def generate_match(config: MatchConfig = MatchConfig()) -> Match:
    """Generate one fictional match whose planted shift changes event behavior."""
    rng = random.Random(config.seed)
    players = {"home": _players("home"), "away": _players("away")}
    events: list[MatchEvent] = []
    shift_end = config.shift_minute + config.shift_duration
    model = load_optional_model(config.model_path)
    previous: dict[Team, tuple[str, float, float]] = {}

    for minute in range(1, config.duration_minutes + 1):
        in_shift = config.shift_minute <= minute < shift_end
        for _ in range(config.base_events_per_minute + (3 if in_shift else 0)):
            team: Team
            if in_shift:
                shift_probability = 0.75 if config.shift_kind in {"possession_surge", "direct_attack"} else 0.68
                team = config.shift_team if rng.random() < shift_probability else ("home" if config.shift_team == "away" else "away")
            else:
                team = "home" if rng.random() < 0.5 else "away"
            if model is None:
                kind = _event_type(rng)
                x = rng.uniform(0, PITCH_LENGTH)
                y = rng.uniform(0, PITCH_WIDTH)
            elif team not in previous:
                kind, x, y = model.initial_event(rng)
            else:
                kind, x, y = model.next_event(rng, *previous[team])
            if in_shift and team == config.shift_team:
                weights = {
                    "high_press": [35, 34, 10, 4, 10, 7],
                    "possession_surge": [25, 3, 2, 1, 50, 19],
                    "direct_attack": [15, 3, 2, 35, 40, 5],
                    "low_block": [28, 12, 28, 2, 10, 20],
                }.get(config.shift_kind)
                if weights is None:
                    raise ValueError(f"Unsupported shift kind: {config.shift_kind}")
                kind = rng.choices(
                    ["pass", "pressure", "tackle", "shot", "carry", "possession"],
                    weights=weights,
                    k=1,
                )[0]
            if in_shift and team == config.shift_team:
                if config.shift_kind == "low_block":
                    x = min(x, PITCH_LENGTH * 0.375)
                else:
                    x = max(x, PITCH_LENGTH * 0.55)
            previous[team] = (kind, x, y)
            outcome = "complete" if kind == "pass" and rng.random() < (0.78 if in_shift else 0.84) else "success"
            if kind in {"tackle", "pressure"} and rng.random() < 0.14:
                outcome = "foul"
            events.append(
                MatchEvent(
                    minute=minute,
                    second=rng.randrange(60),
                    team=team,
                    player=rng.choice(players[team]),
                    type=kind,
                    x=round(x, 2),
                    y=round(y, 2),
                    outcome=outcome,
                    receiver=rng.choice(players[team]) if kind == "pass" else None,
                    value=round(rng.uniform(0.01, 0.18), 3) if kind == "shot" else None,
                )
            )

    events.sort(key=lambda event: (event.minute, event.second, event.team, event.type))
    shift = PlantedShift(
        shift_id="shift-001",
        minute=config.shift_minute,
        team=config.shift_team,
        kind=config.shift_kind,
        duration_minutes=config.shift_duration,
    )
    return Match(
        match_id=config.match_id,
        seed=config.seed,
        home_team=config.home_team,
        away_team=config.away_team,
        players=players,
        events=tuple(events),
        planted_shifts=(shift,),
    )
