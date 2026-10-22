"""Fit aggregate spatial scene templates from a bounded StatsBomb 360 sample."""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

BASE_URL = "https://raw.githubusercontent.com/hudl/open-data/master/data"
API_URL = "https://api.github.com/repos/hudl/open-data/contents/data/three-sixty?per_page=100"


def _get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "itg-iima-calibration/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _download(match_id: str) -> tuple[str, list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
    try:
        events = _get_json(f"{BASE_URL}/events/{match_id}.json")
        scenes = _get_json(f"{BASE_URL}/three-sixty/{match_id}.json")
        return match_id, events, scenes
    except (OSError, ValueError):
        return match_id, None, None


def fit(sample_limit: int, workers: int) -> dict[str, Any]:
    files = [item for item in _get_json(API_URL) if item.get("name", "").endswith(".json")]
    match_ids = [Path(item["name"]).stem for item in files[:sample_limit]]
    templates: defaultdict[str, list[tuple[float, float, bool]]] = defaultdict(list)
    matches = snapshots = players = 0
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="statsbomb-360") as executor:
        for match_id, events, scenes in executor.map(_download, match_ids):
            if not events or not scenes:
                continue
            event_types = {
                event.get("id"): event.get("type", {}).get("name", "unknown").lower()
                for event in events
                if event.get("id")
            }
            accepted = 0
            for scene in scenes:
                event_type = event_types.get(scene.get("event_uuid"))
                frame = scene.get("freeze_frame") or []
                actor = next((item.get("location") for item in frame if item.get("actor")), None)
                if not event_type or not actor:
                    continue
                accepted += 1
                snapshots += 1
                for item in frame:
                    location = item.get("location")
                    if not location:
                        continue
                    players += 1
                    templates[event_type].append(
                        (float(location[0]) - float(actor[0]), float(location[1]) - float(actor[1]), bool(item.get("teammate")))
                    )
            if accepted:
                matches += 1

    output: dict[str, Any] = {
        "version": 1,
        "source": "StatsBomb Open Data 360 (temporary calibration only)",
        "matches": matches,
        "snapshots": snapshots,
        "players": players,
        "templates": {},
    }
    for event_type, values in sorted(templates.items()):
        teammates = [item for item in values if item[2]]
        opponents = [item for item in values if not item[2]]

        def summary(items: list[tuple[float, float, bool]]) -> dict[str, float | int]:
            if not items:
                return {"count": 0, "dx_mean": 0.0, "dy_mean": 0.0, "dx_std": 1.0, "dy_std": 1.0}
            dx = [item[0] for item in items]
            dy = [item[1] for item in items]
            dx_mean = sum(dx) / len(dx)
            dy_mean = sum(dy) / len(dy)
            return {
                "count": len(items),
                "dx_mean": round(dx_mean, 4),
                "dy_mean": round(dy_mean, 4),
                "dx_std": round(max(1.0, (sum((value - dx_mean) ** 2 for value in dx) / len(dx)) ** 0.5), 4),
                "dy_std": round(max(1.0, (sum((value - dy_mean) ** 2 for value in dy) / len(dy)) ** 0.5), 4),
            }

        output["templates"][event_type] = {"teammate": summary(teammates), "opponent": summary(opponents)}
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matches", type=int, default=32)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=Path("data/models/statsbomb_360_templates.json"))
    args = parser.parse_args()
    if args.matches < 1 or args.workers < 1:
        raise ValueError("matches and workers must be at least 1")
    model = fit(args.matches, args.workers)
    if model["matches"] < 5:
        raise RuntimeError(f"only fitted {model['matches']} matches; refusing to write a small 360 sample")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    print(f"fitted {model['matches']} matches, {model['snapshots']} snapshots, {model['players']} players -> {args.output}")


if __name__ == "__main__":
    main()
