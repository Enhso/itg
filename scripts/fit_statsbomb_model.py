"""Fit a compact Markov event model from a temporary StatsBomb Open Data sample."""

from __future__ import annotations

import argparse
import json
import math
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from itg.markov import EVENT_TYPES, state_for

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
SUPPORTED = set(EVENT_TYPES)


def _get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "itg-iima-calibration/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _event_type(event: dict[str, Any]) -> str | None:
    name = event.get("type", {}).get("name", "").lower()
    mapping = {
        "pass": "pass",
        "pressure": "pressure",
        "tackle": "tackle",
        "shot": "shot",
        "carry": "carry",
        "ball receipt": "possession",
        "dribble": "carry",
        "clearance": "tackle",
    }
    return mapping.get(name) if mapping.get(name) in SUPPORTED else None


def _download_match_events(match_ref: tuple[int, int]) -> tuple[int, list[dict[str, Any]] | None]:
    _, match_id = match_ref
    try:
        return match_id, _get_json(f"{BASE_URL}/events/{match_id}.json")
    except (OSError, ValueError):
        return match_id, None


def fit(sample_limit: int, workers: int = 12) -> tuple[dict[str, Any], int, int]:
    if workers < 1:
        raise ValueError("workers must be at least 1")
    competitions = _get_json(f"{BASE_URL}/competitions.json")
    match_refs: list[tuple[int, int]] = []
    for competition in competitions:
        if len(match_refs) >= sample_limit:
            break
        url = f"{BASE_URL}/matches/{competition['competition_id']}/{competition['season_id']}.json"
        try:
            matches = _get_json(url)
        except (OSError, ValueError):
            continue
        for match in matches:
            match_refs.append((competition["competition_id"], match["match_id"]))
            if len(match_refs) >= sample_limit:
                break

    initial: Counter[str] = Counter()
    transitions: defaultdict[str, Counter[str]] = defaultdict(Counter)
    displacement_values: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    match_count = event_count = 0
    # Fetch independently hosted event files concurrently. executor.map
    # preserves match_refs order, so the aggregate remains reproducible.
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="statsbomb") as executor:
        downloaded_events = executor.map(_download_match_events, match_refs)
        for (_, match_id), (downloaded_match_id, events) in zip(match_refs, downloaded_events):
            if match_id != downloaded_match_id or events is None:
                continue
            by_team: defaultdict[str, list[tuple[str, float, float]]] = defaultdict(list)
            for event in events:
                kind = _event_type(event)
                location = event.get("location")
                team = event.get("team", {}).get("name")
                if kind is None or not location or not team:
                    continue
                x, y = float(location[0]), float(location[1])
                by_team[team].append((kind, x, y))
                event_count += 1
            if not by_team:
                continue
            match_count += 1
            for sequence in by_team.values():
                first_kind, first_x, first_y = sequence[0]
                initial[state_for(first_kind, first_x, first_y)] += 1
                for (kind_a, x_a, y_a), (kind_b, x_b, y_b) in zip(sequence, sequence[1:]):
                    state_a = state_for(kind_a, x_a, y_a)
                    state_b = state_for(kind_b, x_b, y_b)
                    transitions[state_a][state_b] += 1
                    displacement_values[f"{state_a}>{state_b}"].append((x_b - x_a, y_b - y_a))

    def probabilities(counter: Counter[str]) -> dict[str, float]:
        total = sum(counter.values())
        return {key: round(value / total, 8) for key, value in sorted(counter.items())} if total else {}

    displacements: dict[str, dict[str, float]] = {}
    for key, values in displacement_values.items():
        dx = [item[0] for item in values]
        dy = [item[1] for item in values]
        dx_mean = sum(dx) / len(dx)
        dy_mean = sum(dy) / len(dy)
        displacements[key] = {
            "dx_mean": round(dx_mean, 4),
            "dx_std": round(math.sqrt(sum((value - dx_mean) ** 2 for value in dx) / max(1, len(dx) - 1)), 4),
            "dy_mean": round(dy_mean, 4),
            "dy_std": round(math.sqrt(sum((value - dy_mean) ** 2 for value in dy) / max(1, len(dy) - 1)), 4),
        }
    model = {
        "version": 1,
        "source": "StatsBomb Open Data (temporary calibration only)",
        "matches": match_count,
        "events": event_count,
        "state_definition": "event_type plus 6 x-position bins and 4 y-position bins",
        "initial": probabilities(initial),
        "transitions": {key: probabilities(value) for key, value in sorted(transitions.items())},
        "displacements": displacements,
    }
    return model, match_count, event_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matches", type=int, default=120)
    parser.add_argument("--workers", type=int, default=12, help="parallel event downloads")
    parser.add_argument("--output", type=Path, default=Path("data/models/statsbomb_markov.json"))
    args = parser.parse_args()
    model, match_count, event_count = fit(args.matches, workers=args.workers)
    if match_count < 50:
        raise RuntimeError(f"only fitted {match_count} matches; refusing to write a small calibration sample")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    print(f"fitted {match_count} matches and {event_count} events -> {args.output}")


if __name__ == "__main__":
    main()
