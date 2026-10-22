"""Deterministic rolling features, evidence extraction, and shift scoring."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .models import Match, MatchEvent, Team
from .pitch import PITCH_LENGTH


@dataclass(frozen=True)
class WindowStats:
    start_minute: int
    end_minute: int
    pressure: dict[Team, int]
    field_tilt: dict[Team, float]
    possession: dict[Team, float]
    pass_accuracy: dict[Team, float]
    shots: dict[Team, int]
    carries: dict[Team, int]
    tackles: dict[Team, int]

    def evidence(self) -> dict[str, object]:
        return {
            "window": f"{self.start_minute}-{self.end_minute}",
            "pressure": self.pressure,
            "field_tilt": self.field_tilt,
            "possession": self.possession,
            "pass_accuracy": self.pass_accuracy,
            "shots": self.shots,
            "carries": self.carries,
            "tackles": self.tackles,
        }


@dataclass(frozen=True)
class DetectionResult:
    minute: int
    team: Team
    kind: str
    before: WindowStats
    after: WindowStats
    score: float


def _window(events: Iterable[MatchEvent], start: int, end: int) -> tuple[MatchEvent, ...]:
    return tuple(event for event in events if start <= event.minute <= end)


def rolling_stats(match: Match, window_minutes: int = 5) -> tuple[WindowStats, ...]:
    """Return non-overlapping evidence windows, including before/after candidates."""
    windows: list[WindowStats] = []
    for start in range(1, 91, window_minutes):
        events = _window(match.events, start, min(90, start + window_minutes - 1))
        pressure = {team: sum(event.team == team and event.type == "pressure" for event in events) for team in ("home", "away")}
        territorial = {
            team: sum(event.team == team and event.x >= PITCH_LENGTH * 0.55 for event in events)
            for team in ("home", "away")
        }
        territory_total = max(1, sum(territorial.values()))
        possession_counts = {
            team: sum(event.team == team and event.type in {"possession", "pass", "carry"} for event in events)
            for team in ("home", "away")
        }
        possession_total = max(1, sum(possession_counts.values()))
        pass_accuracy = {}
        shots = {team: sum(event.team == team and event.type == "shot" for event in events) for team in ("home", "away")}
        carries = {team: sum(event.team == team and event.type == "carry" for event in events) for team in ("home", "away")}
        tackles = {team: sum(event.team == team and event.type == "tackle" for event in events) for team in ("home", "away")}
        for team in ("home", "away"):
            passes = [event for event in events if event.team == team and event.type == "pass"]
            pass_accuracy[team] = round(
                100 * mean(event.outcome == "complete" for event in passes), 1
            ) if passes else 0.0
        windows.append(
            WindowStats(
                start_minute=start,
                end_minute=min(90, start + window_minutes - 1),
                pressure=pressure,
                field_tilt={team: round(100 * territorial[team] / territory_total, 1) for team in ("home", "away")},
                possession={team: round(100 * possession_counts[team] / possession_total, 1) for team in ("home", "away")},
                pass_accuracy=pass_accuracy,
                shots=shots,
                carries=carries,
                tackles=tackles,
            )
        )
    return tuple(windows)


def detect_moments(match: Match, window_minutes: int = 5, threshold: float = 12.0) -> tuple[DetectionResult, ...]:
    windows = rolling_stats(match, window_minutes)
    detections: list[DetectionResult] = []
    for before, after in zip(windows, windows[1:]):
        for team in ("home", "away"):
            pressure_delta = after.pressure[team] - before.pressure[team]
            tilt_delta = after.field_tilt[team] - before.field_tilt[team]
            possession_delta = after.possession[team] - before.possession[team]
            shot_delta = after.shots[team] - before.shots[team]
            carry_delta = after.carries[team] - before.carries[team]
            tackle_delta = after.tackles[team] - before.tackles[team]
            candidates = (
                ("high_press", pressure_delta >= 2 and tilt_delta >= 4, abs(pressure_delta) * 2 + abs(tilt_delta)),
                ("possession_surge", possession_delta >= 8 and carry_delta >= 2, possession_delta + carry_delta * 2),
                ("direct_attack", shot_delta >= 4 and carry_delta >= 2 and tilt_delta >= 4, shot_delta * 8 + carry_delta * 2 + tilt_delta),
                ("low_block", tackle_delta >= 2 and tilt_delta <= -4, tackle_delta * 2 + abs(tilt_delta)),
            )
            qualifying = [candidate for candidate in candidates if candidate[1]]
            if qualifying:
                kind, _, score = max(qualifying, key=lambda candidate: candidate[2])
            else:
                kind, score = "", 0.0
            if qualifying and score >= threshold:
                detections.append(
                    DetectionResult(
                        minute=after.start_minute,
                        team=team,
                        kind=kind,
                        before=before,
                        after=after,
                        score=round(score, 1),
                    )
                )
    return tuple(detections)


def score_detections(match: Match, detections: Iterable[DetectionResult], tolerance: int = 5) -> dict[str, object]:
    detections = tuple(detections)
    matched = []
    for shift in match.planted_shifts:
        candidates = [
            detection for detection in detections
            if detection.team == shift.team
            and detection.kind == shift.kind
            and abs(detection.minute - shift.minute) <= tolerance
        ]
        matched.append({"shift_id": shift.shift_id, "found": bool(candidates), "minutes": [d.minute for d in candidates]})
    return {
        "match_id": match.match_id,
        "tolerance_minutes": tolerance,
        "found": sum(item["found"] for item in matched),
        "total": len(matched),
        "shifts": matched,
    }
