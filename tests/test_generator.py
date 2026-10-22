import json
from pathlib import Path
from statistics import mean

from itg.generator import MatchConfig, generate_match
from itg.examples import generate_examples
from itg.footage import render_clip
from itg.pitch import PITCH_LENGTH, PITCH_WIDTH
from itg.scene import SceneModel


def test_generation_is_seeded_and_jsonl_serializable():
    first = generate_match(MatchConfig(seed=7))
    second = generate_match(MatchConfig(seed=7))

    assert first.events == second.events
    rows = [json.loads(line) for line in first.jsonl().splitlines()]
    assert len(rows) == len(first.events)
    assert {"minute", "second", "team", "player", "type"} <= rows[0].keys()


def test_generator_preserves_match_invariants_and_plants_shift():
    match = generate_match(MatchConfig(seed=61, shift_minute=61))

    assert len(match.events) >= 90 * 8
    assert all(1 <= event.minute <= 90 for event in match.events)
    assert all(0 <= event.x <= PITCH_LENGTH and 0 <= event.y <= PITCH_WIDTH for event in match.events)
    assert match.planted_shifts[0].minute == 61
    assert match.planted_shifts[0].kind == "high_press"


def test_example_batch_writes_ten_matches(tmp_path: Path):
    generate_examples(tmp_path)

    event_files = sorted(tmp_path.glob("example-*.jsonl"))
    truth_files = sorted(tmp_path.glob("example-*.ground_truth.json"))
    assert len(event_files) == len(truth_files) == 10
    assert sum(1 for _ in event_files[0].open()) > 2_000
    kinds = {json.loads(path.read_text())["shifts"][0]["kind"] for path in truth_files}
    assert kinds == {"high_press", "possession_surge", "direct_attack", "low_block"}


def test_synthetic_clip_has_manifest(tmp_path: Path):
    clip = render_clip(generate_match(MatchConfig(seed=1)), tmp_path / "match.mp4", seconds=1, fps=2)

    assert clip.exists()
    assert clip.stat().st_size > 1_000
    assert len(json.loads(clip.with_suffix(".frames.json").read_text())) == 2


def test_fitted_markov_model_keeps_same_team_motion_continuous():
    def jumps(match):
        previous = {}
        values = []
        for event in match.events:
            if event.team in previous:
                x, y = previous[event.team]
                values.append(((event.x - x) ** 2 + (event.y - y) ** 2) ** 0.5)
            previous[event.team] = (event.x, event.y)
        return values

    learned = jumps(generate_match(MatchConfig(seed=61)))
    independent = jumps(generate_match(MatchConfig(seed=61, model_path=Path("/tmp/missing-markov.json"))))

    assert mean(learned) < mean(independent) * 0.8


def test_360_scene_model_produces_two_role_aware_teams():
    scene = SceneModel.load()
    positions = scene.positions(3, "pass", 60, 40, "away", 10)

    assert len(positions) == 22
    assert sum(player_id.startswith("home-") for player_id, _, _ in positions) == 11
    assert sum(player_id.startswith("away-") for player_id, _, _ in positions) == 11
    assert all(0 <= x <= PITCH_LENGTH and 0 <= y <= PITCH_WIDTH for _, x, y in positions)

    next_positions = scene.positions(3, "pass", 60, 40, "away", 10.1)
    movement = [
        ((x - next_x) ** 2 + (y - next_y) ** 2) ** 0.5
        for (_, x, y), (_, next_x, next_y) in zip(positions, next_positions)
    ]
    assert max(movement) < 1.0
