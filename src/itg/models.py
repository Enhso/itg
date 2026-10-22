"""Typed contracts shared by the ingest and interpret stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

EventType = Literal["pass", "pressure", "tackle", "shot", "carry", "possession"]
Team = Literal["home", "away"]


@dataclass(frozen=True)
class MatchEvent:
    minute: int
    second: int
    team: Team
    player: str
    type: EventType
    x: float
    y: float
    outcome: str
    receiver: str | None = None
    value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlantedShift:
    shift_id: str
    minute: int
    team: Team
    kind: str
    duration_minutes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Match:
    match_id: str
    seed: int
    home_team: str
    away_team: str
    players: dict[Team, tuple[str, ...]]
    events: tuple[MatchEvent, ...]
    planted_shifts: tuple[PlantedShift, ...]

    def ground_truth(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "shifts": [shift.to_dict() for shift in self.planted_shifts],
        }

    def jsonl(self) -> str:
        import json

        return "\n".join(json.dumps(event.to_dict(), sort_keys=True) for event in self.events)
