"""Utilities for writing reproducible synthetic example batches."""

from __future__ import annotations

import json
from pathlib import Path

from .generator import MatchConfig, generate_match

SHIFT_KINDS = ("high_press", "possession_surge", "direct_attack", "low_block")


def generate_examples(output_dir: Path, count: int = 10, first_seed: int = 1) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        match_number = index + 1
        match_id = f"example-{match_number:02d}"
        match = generate_match(
            MatchConfig(
                seed=first_seed + index,
                match_id=match_id,
                # Keep shifts on rolling-window boundaries so their evidence
                # appears within the detector's five-minute scoring tolerance.
                shift_minute=61 + (index % 2),
                shift_team="away" if index % 2 == 0 else "home",
                shift_kind=SHIFT_KINDS[index % len(SHIFT_KINDS)],
            )
        )
        (output_dir / f"{match_id}.jsonl").write_text(match.jsonl() + "\n")
        (output_dir / f"{match_id}.ground_truth.json").write_text(
            json.dumps(match.ground_truth(), indent=2, sort_keys=True) + "\n"
        )
