from itg.generator import MatchConfig, generate_match
from itg.interpret import detect_moments, rolling_stats, score_detections


def test_rolling_stats_have_complementary_field_tilt_and_possession():
    match = generate_match(MatchConfig(seed=61))
    windows = rolling_stats(match)

    assert len(windows) == 18
    for window in windows:
        assert round(window.field_tilt["home"] + window.field_tilt["away"], 1) == 100.0
        assert round(window.possession["home"] + window.possession["away"], 1) == 100.0


def test_detector_finds_demo_shift_within_tolerance():
    match = generate_match(MatchConfig(seed=61, shift_minute=61))
    detections = detect_moments(match)
    score = score_detections(match, detections)

    assert score["found"] == 1
    assert score["total"] == 1
    assert score["shifts"][0]["found"] is True


def test_detector_finds_each_supported_shift_kind():
    from itg.examples import SHIFT_KINDS
    from itg.generator import MatchConfig, generate_match

    for kind in SHIFT_KINDS:
        match = generate_match(MatchConfig(seed=61, shift_kind=kind))
        score = score_detections(match, detect_moments(match))
        assert score["found"] == 1, (kind, score)
        assert score["shifts"][0]["found"] is True
