"""Create deterministic synthetic broadcast-style footage from match events."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .models import Match
from .pitch import PITCH_LENGTH, PITCH_WIDTH, to_pixels
from .scene import SceneModel


def _ppm_frame(
    match: Match, frame: int, frame_count: int, scene_model: SceneModel, width: int = 960, height: int = 540
) -> bytes:
    pixels = bytearray([22, 92, 54] * (width * height))

    def pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset : offset + 3] = bytes(color)

    def rect(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
        for y in range(max(0, y0), min(height, y1)):
            for x in range(max(0, x0), min(width, x1)):
                pixel(x, y, color)

    # White pitch markings and a compact scoreboard make the clip readable
    # without claiming to be real broadcast footage.
    for x in (80, width - 80, width // 2):
        for y in range(50, height - 50):
            pixel(x, y, (235, 245, 235))
    for x in range(80, width - 79):
        pixel(x, 50, (235, 245, 235))
        pixel(x, height - 51, (235, 245, 235))
    replay_second = frame / max(1, frame_count - 1) * 90 * 60
    event_index = min(len(match.events) - 1, max(0, min(range(len(match.events)), key=lambda i: abs((match.events[i].minute * 60 + match.events[i].second) - replay_second))))
    event = match.events[event_index]
    for player_id, player_x, player_y in scene_model.positions(
        match.seed, event.type, event.x, event.y, event.team, replay_second
    ):
        x, y = to_pixels(player_x, player_y, width, height)
        color = (245, 220, 70) if player_id.startswith("home") else (80, 180, 255)
        rect(x - 5, y - 5, x + 6, y + 6, color)
    window_start = replay_second - 5
    window_end = replay_second + 2
    for item in match.events:
        timestamp = item.minute * 60 + item.second
        if window_start <= timestamp <= window_end:
            x, y = to_pixels(item.x, item.y, width, height)
            color = (255, 255, 255) if item is event else (180, 180, 180)
            rect(x - 2, y - 2, x + 3, y + 3, color)
    rect(18, 14, 410, 39, (12, 24, 35))
    minute = event.minute
    label = f"{match.home_team} 0 - 0 {match.away_team}   {minute:02d}'"
    # Encode a simple ASCII scoreboard as blocks; detailed text is supplied
    # by the JSON manifest and analysis pipeline.
    for index, char in enumerate(label[:48]):
        if char != " ":
            rect(28 + index * 7, 20, 33 + index * 7, 32, (240, 240, 240))
    return f"P6\n{width} {height}\n255\n".encode() + bytes(pixels)


def render_clip(match: Match, output_path: Path, seconds: int = 10, fps: int = 10) -> Path:
    """Render a small MP4 clip and sidecar frame manifest with ffmpeg."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to render synthetic footage")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = output_path.parent / f".{output_path.stem}-frames"
    frames_dir.mkdir(exist_ok=True)
    frame_count = seconds * fps
    manifest = []
    try:
        scene_model = SceneModel.load()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        scene_model = SceneModel({})
    for frame in range(frame_count):
        frame_path = frames_dir / f"frame-{frame:04d}.ppm"
        frame_path.write_bytes(_ppm_frame(match, frame, frame_count, scene_model))
        replay_second = frame / max(1, frame_count - 1) * 90 * 60
        event_index = min(len(match.events) - 1, max(0, min(range(len(match.events)), key=lambda i: abs((match.events[i].minute * 60 + match.events[i].second) - replay_second))))
        event = match.events[event_index]
        manifest.append({"frame": frame, "minute": event.minute, "event_index": event_index})
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
            "-i", str(frames_dir / "frame-%04d.ppm"), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", str(output_path),
        ],
        check=True,
    )
    (output_path.with_suffix(".frames.json")).write_text(json.dumps(manifest, indent=2) + "\n")
    shutil.rmtree(frames_dir)
    return output_path
