"""Deterministic synthetic match intelligence primitives."""

from .generator import MatchConfig, generate_match
from .interpret import DetectionResult, detect_moments, rolling_stats, score_detections
from .markov import EventMarkovModel

__all__ = [
    "DetectionResult",
    "EventMarkovModel",
    "MatchConfig",
    "detect_moments",
    "generate_match",
    "rolling_stats",
    "score_detections",
]
