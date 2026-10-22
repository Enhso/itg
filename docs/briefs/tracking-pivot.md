# Brief: possession spells and synthetic tracking

Written 2026-10-22 for GitHub Copilot Agent Mode. Read `docs/PLAN.md` and `docs/data-generation.md` first. This brief adds to them and does not replace them.

## Why this work matters

The project now renders synthetic match footage and reports the speed metrics the hackathon rules list (player speed and distance, ball and shot speed, pass difficulty). Both need football-realistic movement. The current generator cannot produce it, because `generate_match` picks the team for every event with a coin flip. In `data/examples/example-01.jsonl`, the 1,966 on-ball events (pass, carry, shot, possession) form 931 same-team runs, a mean of 2.11 events per run. The ball changes hands about 10 times a minute. No renderer or calibration makes that look like football.

The fix has two parts. The generator builds the match out of possession spells. Then a new module synthesises player and ball positions at 10 Hz around those events. Events stay the source of truth. Tracking, footage, and the new metrics are all derived from the events.

Video footage is a strong extra, not a requirement. Keep the planted-truth story intact above everything else. Every planted shift must stay detectable and scored against `ground_truth.json`.

## Work rules

- Work on one branch per unit: `pivot-1a`, `pivot-1b`, `pivot-2`, `pivot-3`, and `pivot-4`. Merge a unit into `main` only after its checks pass, so `main` always works.
- Do the units in order. Each unit ends with its checks passing, a commit, and one line added to the log in `docs/PLAN.md`.
- Unit 2 does not depend on Unit 1. If Unit 1b still fails its checks halfway through Thursday's session, leave it on its branch and do Unit 2. Unit 3 needs both 1b and 2.
- **Hard stop.** These units get Thursday's and Friday's sessions only. At the end of Friday's session, stop where you are. An unfinished unit stays on the branch, and the agent work on Saturday goes ahead regardless.
- Run Python only through uv: `uv run ...`. The plan explains why the system Python is unsafe here.
- Raw StatsBomb or IDSSE files never enter the repository or the product. Commit only aggregate parameters, the same boundary that `docs/data-generation.md` sets for StatsBomb.
- Keep the existing style. The repo uses frozen dataclasses, standard-library code, and short modules. Add `numpy` as a runtime dependency only if a measured runtime makes it necessary, and say so in the log.
- When a check fails and the fix is unclear, stop and write down what you saw. Do not loosen a check to make it pass.

## Unit 1a: event contract

This unit changes the data shape and keeps the current generation logic, so it merges on its own before the generator rewrite starts.

In `src/itg/models.py`, change `MatchEvent` as follows:

- Add `t: float`, the seconds since kickoff, with `0 <= t < 5400`. Make `minute` (1-based, `int(t // 60) + 1`) and `second` (`int(t % 60)`) read-only properties derived from `t`. `dataclasses.asdict` skips properties, so `to_dict()` must add `minute` and `second` itself. The JSONL keys then stay the same, and `interpret.py` keeps working.
- Add `end_x: float | None` and `end_y: float | None` for pass, carry, and shot events.
- Add `duration: float | None`, the seconds a pass, carry, or shot takes.
- Add `spell_id: int`, the possession spell the event belongs to. A defending team's pressure or tackle carries the `spell_id` of the opponent's spell in which it happens.

Document the coordinate convention in the module docstring. Event `x`, `y`, `end_x`, and `end_y` are in the acting team's attacking frame, so the acting team always attacks toward `x = 120`. This is the StatsBomb convention that `interpret.py` already assumes. A location seen by the other team is `(120 - x, 80 - y)`.

Add these helpers to `src/itg/pitch.py`: `PITCH_LENGTH_M = 105.0`, `PITCH_WIDTH_M = 68.0`, and `to_metres(x, y)`. One x unit is 0.875 m and one y unit is 0.85 m, so the 120 by 80 grid is not square in metres. Compute every distance and speed in metres from here on.

In `src/itg/generator.py`, change `_players` from 9 players to 11 per team, one per role in a 4-3-3: `GK`, `LB`, `LCB`, `RCB`, `RB`, `LCM`, `CM`, `RCM`, `LW`, `ST`, `RW`. Keep the current id pattern (team prefix plus role code, for example `TST`). Display names are out of scope.

In 1a, the coin-flip generator stays. Fill `t` from the current minute and second. Set `spell_id` from a counter that increases whenever the event team changes. Leave `end_x`, `end_y`, and `duration` as `None`.

### Unit 1a checks

1. `uv run pytest` passes. Change existing tests only where the contract changed, and say which.
2. `uv run python scripts/generate_examples.py` regenerates `data/examples/`, and the detector still finds all 10 planted shifts within the tolerance.

## Unit 1b: possession spells

### Calibrate spells from StatsBomb

Write `scripts/fit_statsbomb_spells.py`. Reuse the download pattern in `scripts/fit_statsbomb_model.py`, which reads events over HTTPS and writes no raw files. StatsBomb events carry `possession` and `possession_team`. A spell is one `possession` value, owned by `possession_team`. Write `data/models/statsbomb_spells.json` with these aggregates:

- the distribution of on-ball events per spell, counting pass, carry, shot, and ball receipt by the possession team;
- the distribution of spell duration in seconds;
- the distribution of pass length, and pass `duration` grouped by length (under 15 m, 15 m to 30 m, over 30 m);
- carry length and carry duration;
- the defending team's pressures per second of spell time;
- how spells end, as shares of incomplete pass, tackle or interception, shot, and other.

StatsBomb coordinates use the 120 by 80 pitch, so convert lengths with `to_metres` before you group them.

### Generate the match as spells

Rewrite `generate_match` as a loop over spells. The home team kicks off. A spell has these parts:

1. Draw the spell's length from the calibrated distribution.
2. Build a chain of on-ball actions for the possessing team. The existing `EventMarkovModel` can still choose each action's type and location, restricted to `pass`, `carry`, and `shot`. A completed pass ends where the next action starts. Follow it with a `possession` event by the receiver at `(end_x, end_y)`. Completed passes are the only source of `possession` events, so receipts never double up. Time advances by each action's `duration` plus a short gap between actions.
3. Insert the defending team's pressure and tackle events at the calibrated rate, located at the ball in the defender's frame.
4. End the spell with a turnover: an incomplete pass, a tackle, or a shot. The next spell starts with the other team at the mirrored location.

Keep the volume of core actions near the current calibration of 27 per minute. That figure counts `pass`, `carry`, `pressure`, and `shot` only, as `docs/data-generation.md` explains. It excludes `possession` receipts and tackles. Then express each planted shift through spells, not through the per-event team flip:

- `high_press`: when the shift team defends, it presses more and wins the ball sooner, so its own spells start further up the pitch.
- `possession_surge`: the shift team's spells get longer, with more passes and carries.
- `direct_attack`: the shift team's spells get shorter, with more forward carries and shots.
- `low_block`: when the shift team defends, it sits deeper and tackles more.

The window statistics will move, so the detector thresholds in `detect_moments` may need retuning. If you retune them, list the old and new values in the log line.

### Unit 1b checks

1. `uv run pytest` passes. Change existing tests only where the generator's behavior changed, and say which.
2. A new test generates seed 61 and asserts two things. The median number of on-ball events per spell and the number of spell changes per minute are each within 25% of the values in `statsbomb_spells.json`. Read the targets from that file, not from literals.
3. A new test asserts chain continuity. After each completed pass comes a `possession` event by the named receiver, within 0.5 units of `(end_x, end_y)`, at `t >= pass.t + pass.duration`.
4. A new test asserts that `t` never decreases across the stream, and that `minute` and `second` agree with `t`.
5. Seed 61 has a mean of 24 to 30 core actions (`pass`, `carry`, `pressure`, and `shot`) per minute.
6. `uv run python scripts/generate_examples.py` regenerates `data/examples/`, and the detector finds all 10 planted shifts within the tolerance.
7. A stress run calls `generate_examples(tmp_dir, count=20)`. That gives seeds 1 to 20 with the same shift kinds, teams, and minutes as the committed batch. Score every match and report how many of the 20 shifts the detector finds.

## Unit 2: IDSSE tracking calibration

IDSSE has 7 Bundesliga matches with 25 fps optical tracking of all players and the ball, plus synced events. Its license is CC-BY 4.0. Cite it as Bassek, Rein, Weber, and Memmert, "An integrated dataset of spatiotemporal and event data in elite soccer", *Scientific Data* 12:195 (2025), doi:10.1038/s41597-025-04505-y.

Add `kloppy` to a dependency group named `calibration`, not to the runtime dependencies: `uv add --group calibration kloppy`. Load matches with `kloppy.sportec.load_open_tracking_data(match_id=...)` and `load_open_event_data(match_id=...)`. The match ids are `J03WPY`, `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPF`, and `J03WQF`. Check the current kloppy signatures before you depend on any optional argument.

Write `scripts/fit_idsse_tracking.py` with a `--matches` option that defaults to 2. Run it with `uv run --group calibration python scripts/fit_idsse_tracking.py`. It writes `data/models/idsse_tracking.json`.

Work in metres and seconds. Take the pitch size from each dataset's metadata rather than assuming 105 m by 68 m. Smooth positions before you differentiate them, for example with a centred 5-frame moving average, because raw 25 fps differences are noisy. Use in-play frames only. Map the DFL positions in the metadata to six role groups: `GK`, `FB`, `CB`, `CM`, `W`, and `ST`.

The output holds these aggregates:

- speed in m/s per role group at p50, p90, p99, and p99.9, and acceleration in m/s² per role group at p99;
- team shape by phase (`in_possession`, `out_of_possession`) and by ball third in that team's attacking frame (`defensive`, `middle`, `attacking`), as team length, team width, defensive line height, and the team centroid's x offset from the ball. Team length runs from the deepest to the most advanced outfield player. Defensive line height is the mean distance of the four deepest outfield players from their own goal line;
- role offsets from the team centroid (mean and standard deviation of dx and dy) per role group, phase, and ball third;
- the peak ball speed in the 1 s after each pass, grouped by pass length (under 15 m, 15 m to 30 m, over 30 m), at p10, p50, and p90. If kloppy gives no pass end location, use the ball's tracked position when its speed next drops below 3 m/s;
- the peak ball speed in the 1 s after each shot, at p10, p50, and p90;
- the distance from the nearest defender to the ball while the ball moves slower than 3 m/s, per ball third, at p10, p50, and p90;
- metadata: the source name, the license, the citation, the match ids used, the frame rate, and the frame count.

Add guards that catch unit and coordinate mistakes. These are not targets. The ranges are deliberately wide estimates. If a guard fails, the script exits non-zero and writes nothing:

- every role group's p99.9 speed is between 6 and 11.5 m/s;
- the p50 peak shot speed is between 12 and 40 m/s;
- the median out-of-possession team length is between 20 and 60 m.

If real data falls outside a guard after you have ruled out a bug, widen that guard and explain why in the log line.

Add IDSSE to the calibration policy in `docs/data-generation.md`, with its license, the citation, and the same raw-data boundary as StatsBomb.

### Unit 2 checks

1. The script runs on 2 matches and prints a summary table of every output value for review.
2. After the run, `git status --short` lists only the new script, `data/models/idsse_tracking.json`, and the changed `pyproject.toml`, `uv.lock`, and docs. If kloppy caches downloads inside the working tree, point its cache outside the repository.
3. `uv run pytest` still passes without the `calibration` group installed.

## Unit 3: synthesise tracking at 10 Hz

### Data shape

Create `src/itg/tracking.py`:

```python
@dataclass(frozen=True)
class PlayerPosition:
	player: str  # roster id, the same value as MatchEvent.player
	team: Team
	x: float
	y: float


@dataclass(frozen=True)
class TrackingFrame:
	t: float
	ball_x: float
	ball_y: float
	possession: Team | None
	players: tuple[PlayerPosition, ...]  # 22 players, home first


def synthesize_tracking(match: Match, fps: int = 10) -> Iterator[TrackingFrame]: ...
```

Tracking frames use one absolute frame. The home team attacks toward `x = 120` for the whole match, with no half-time switch this week. An away event at `(x, y)` sits at `(120 - x, 80 - y)`. `synthesize_tracking` is deterministic for a given match, seeded from `match.seed`. It yields frames one at a time, so a full match of 54,000 frames never sits in memory.

### Movement

- The ball follows the events. During a pass, carry, or shot, it moves from `(x, y)` to `(end_x, end_y)` over `duration`. Between actions, it stays with the player on the ball. The ball has no height this week.
- Each player moves toward a target. The target is the team centroid plus the player's role offset from `idsse_tracking.json`, for the current phase and ball third. The centroid follows the ball by the calibrated offset and holds the team's defensive line height.
- The defending team sends its nearest player toward the ball carrier. The receiver of a pass runs to the pass's end location.
- Cap each player's speed at their role group's p99.9 and their acceleration at the group's p99.

### Tactics and planted shifts

Give each team a `Tactics` value over time, with `line_height_m`, `compactness`, and `press`. Defaults come from the calibration. A planted shift changes the shift team's tactics for its duration. `high_press` raises line height and press. `low_block` lowers line height and raises compactness. `possession_surge` and `direct_attack` can leave tactics unchanged this week.

`tracking.py` may read `match.planted_shifts`, because it is part of the simulator. In `interpret.py`, only `score_detections` may read planted shifts. The detector must never see them.

### Footage

Change `src/itg/footage.py` to draw the players and the ball from the tracking frame at each replay time, instead of from `SceneModel`. After that change nothing uses `src/itg/scene.py` or `test_360_scene_model_produces_two_role_aware_teams`, so delete both. Leave `data/models/statsbomb_360_templates.json` and `scripts/fit_statsbomb_360.py` in place, and list them in the log line as now unused, for Hatim to decide. Regenerate the clip with `uv run python scripts/generate_footage.py`.

### Unit 3 checks

1. Two runs on the same match give identical first 600 frames.
2. Every frame has 22 players, 11 per team, all inside `0..120` by `0..80`.
3. Over the full seed-61 match, no player's speed between consecutive frames exceeds their role group's p99.9 by more than 5%.
4. For completed passes, the median ball speed in each length group falls inside the IDSSE p10 to p90 band for that group. This compares the StatsBomb pass durations from Unit 1b against an independent source. If it fails, take pass durations from the IDSSE ball speeds instead, and say so in the log line.
5. For seed 61 with `high_press` at 61', the away team's mean defensive line height in minutes 61 to 65 exceeds its mean in minutes 56 to 60 by at least half of the configured change. Run the same check for `low_block` with the sign reversed.
6. Print the time to synthesise a full match, and record it in the log line.
7. Hatim watches `data/examples/example-01.mp4` and confirms that players move continuously and the ball travels between players.

## Unit 4: tracking metrics in Interpret

Create `src/itg/tracking_stats.py`. It reads the tracking frames and the match events. `interpret.py` stays events-only. Compute the following:

- per player per window, the distance covered in metres and the top speed in m/s;
- `SpeedAlert(t, player, team, speed_ms)` each time a player rises above the calibrated p99 speed, with one alert per crossing rather than one per frame;
- per pass, the distance in metres, the ball speed in m/s, and a difficulty from 0 to 100; per shot, the shot speed in m/s;
- per window per team, the mean defensive line height in metres and the team length in metres.

The difficulty is a hand-set formula this week, and its evidence says so with `"difficulty_model": "hand-set v0"`. Its inputs are the pass distance, the distance from the receiver to the nearest opponent at reception, and the number of opponents within 2 m of the straight pass line. Combine them in a logistic of a weighted sum, with the weights as named constants.

Add `TrackingWindowStats.evidence()`, keyed by the same `window` string as `WindowStats.evidence()`, so agents can join the two. Do not change the detector in this unit.

### Unit 4 checks

1. Behavior tests on hand-built frames assert literal expected values:
	- A player who moves 0.8 x units per frame at 10 fps has a speed of `0.8 * 0.875 * 10 = 7.0` m/s.
	- A speed alert fires once when the speed crosses the threshold. It does not fire again while the speed stays above the threshold.
	- A shot from `(100, 40)` to `(120, 40)` with `duration = 0.5` has a shot speed of `17.5 / 0.5 = 35.0` m/s.
2. The detector still finds all 10 planted shifts in the committed examples.
3. For seed 61, the evidence for window 61 to 65 shows the away team's line height above window 56 to 60.

## Out of scope

Leave these out even if a unit finishes early:

- the second-screen overlays on the footage, which belong to Sunday's session;
- auto-eventing over the rendered video, which is the last stretch item in `docs/PLAN.md`;
- player display names;
- ball height;
- a broadcast-perspective camera;
- SkillCorner body pose;
- Google Research Football, Metrica, and SoccerNet-GAR;
- agents, Foundry calls, and `scripts/foundry_video.py`.

## How to report each unit

End each unit with a short summary that covers four things:

- what changed;
- each check with its measured result;
- any deviation from this brief and the reason for it;
- two closing headings, **Snags** for friction such as a tool that misbehaved or instructions that conflicted, and **Wants** for a tool or capability that would have helped.
