"""Render a deterministic synthetic football clip from a committed example."""

from pathlib import Path

from itg.footage import render_clip
from itg.generator import MatchConfig, generate_match


def main() -> None:
    match = generate_match(MatchConfig(seed=1, match_id="example-01", shift_minute=61, shift_team="away", shift_kind="high_press"))
    render_clip(match, Path("data/examples/example-01.mp4"))


if __name__ == "__main__":
    main()
