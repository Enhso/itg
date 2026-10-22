# Brief: correct the possession spells and fit both calibrations from real data

Written 2026-10-22 by Claude for GitHub Copilot Agent Mode, for the second session on Thursday 22 October. It replaces `docs/briefs/tracking-pivot.md` for today's work. Where the two disagree, follow this brief. Read `docs/PLAN.md` and `docs/data-generation.md` first.

## Why this session exists

Claude reviewed the first attempt at the tracking pivot. Part of it holds up: the event contract in `src/itg/models.py` and `src/itg/pitch.py`, and the pass-to-receipt chain inside a possession spell. The rest needs rework before Saturday, when the agents start reading the event stream:

- Both calibration files, `data/models/statsbomb_spells.json` and `data/models/idsse_tracking.json`, hold hand-written numbers. Neither fit script downloads anything.
- Pressures and tackles sit in the attacking team's coordinates instead of the defender's.
- The ball jumps a median of 33 m at every change of possession, and about a quarter of the spells end with no turnover event.
- A pressure follows 70% of actions. Seed 61 has 988 pressures, 996 passes, and 69 shots.
- The detector's `high_press` and `low_block` conditions were loosened until they no longer test the direction of field tilt.
- The tracking code keeps every player at a fixed point. Friday's brief handles tracking.

This session fixes the event stream and replaces both calibration files with real fits.

## Rules for this session

- Every number in a file under `data/models/` comes from a script that downloads and reads the source data in the same run. When the download fails, the script exits with a non-zero code and writes nothing. Stop that unit and put the error output in the log.
- When a check fails and the fix is unclear, stop that unit. Put the command and its output in the log, then start the next unit.
- Checks keep the thresholds this brief gives them. Tests read their targets from the calibration files.
- Run Python only through `uv run`.
- Keep raw StatsBomb and IDSSE files outside the repository. Read StatsBomb over HTTPS into memory. kloppy caches IDSSE downloads in `~/kloppy_cache`.
- The runtime package `src/itg` stays standard-library only. Fit scripts may use packages from the `calibration` dependency group.
- Keep the existing style: frozen dataclasses, short modules, and named constants for tuned numbers.
- Commit at the end of each unit, on its branch. Merge a unit into `main` only after its checks pass.
- Do the units in order. Unit 2 needs Unit 1. Unit 3 needs neither, so if Unit 1 or Unit 2 is stuck, leave it on its branch and do Unit 3.
- **Hard stop.** Stop at the end of today's session. An unfinished unit stays on its branch, with a log entry that says where it stopped.

## Facts verified on 2026-10-22

Claude checked these facts on this machine before writing the brief.

- On `main`, `uv run pytest` gives 9 passed.
- `main` plus the draft's `src/itg/models.py`, `src/itg/pitch.py`, and `src/itg/generator.py` gives 8 passed and 1 failed. The failure is `tests/test_interpret.py::test_detector_finds_each_supported_shift_kind` on `direct_attack`.
- StatsBomb event files carry `possession`, `possession_team`, `team`, `period`, `timestamp` (period-relative, `HH:MM:SS.mmm`), `minute` (cumulative across periods), `location`, and `duration`. Pass events have `pass.end_location`, `pass.recipient`, and `pass.outcome`. A missing `pass.outcome` means the pass was complete. Carry events have `carry.end_location`. Tackles are `Duel` events whose `duel.type.name` is `Tackle`. Receipts are `Ball Receipt*` events. Every location is in the acting team's attacking frame.
- One Bundesliga match, `3895292`, has 166 possessions in about 97 minutes, with 1,080 passes, 905 carries, 278 pressures, and 29 shots. Use it only as a sanity reference.
- `competitions.json` lists 80 competition seasons, 67 of them men's. The first is the men's 1. Bundesliga 2023/2024 (`competition_id` 9, `season_id` 281), whose matches file lists only 34 matches.
- StatsBomb `duration` covers the action only. In match `3895292`, on-ball events average about 1.9 s of match time each, so stoppages and gaps hold much of a match's time.
- The draft's `uv.lock` resolved kloppy 3.19.1, and every kloppy fact below is checked against that version. Its signatures are `kloppy.sportec.load_open_tracking_data(match_id, sample_rate=None, limit=None, coordinates=None, only_alive=False)` and `kloppy.sportec.load_open_event_data(match_id, event_types=None, coordinates=None, event_factory=None)`.
- `sample_rate` is a fraction of frames. `sample_rate=0.2` keeps every fifth frame.
- The valid IDSSE match ids are `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, and `J03WR9`. The ids `J03WPF` and `J03WQF` in the old brief are wrong.
- kloppy downloads IDSSE from the Hugging Face dataset `pysport/idsse-data`. Each tracking XML is 349 to 419 MB. The event XML for `J03WPY` is 0.7 MB.
- kloppy parses the tracking XML with `iterparse`, but it keeps every frame in memory. The machine has 14 GB of RAM, and about 7 GB were free while Claude worked.
- `coordinates="kloppy"` gives values from 0 to 1, with the origin at the top left and y pointing down. That is the orientation of the project's 120 by 80 grid.
- The `J03WPY` metadata gives a pitch of 105.00 m by 68.00 m. Its starters carry DFL positions such as `TW`, `LV`, `IVL`, `IVR`, `RV`, `DMZ`, `ZO`, `OLM`, `ORM`, and `STZ`. Its teams play 4-2-3-1 and 4-1-3-2.
- kloppy's `Player` has `starting` and `starting_position`. Its frames have `ball_owning_team` and `ball_state`.
- `/usr/bin/time -v` exists and reports `Maximum resident set size`.

## Unit 0: park the first attempt

Claude committed `CLAUDE.md` and this brief on `main` before your session. Everything else that is modified or untracked in the working tree is the first attempt.

1. Run `git status --short`. Confirm that it lists only the draft's files.
2. Run these commands:

	```bash
	git switch -c pivot-draft
	git add -A
	git commit -m "Park the first tracking-pivot attempt for review"
	git switch main
	```

### Unit 0 checks

1. `git status --short` on `main` prints nothing.
2. `git log --oneline -1 pivot-draft` shows the parking commit.
3. `uv run pytest` on `main` gives 9 passed.

## Unit 1: fit the possession spells from StatsBomb

Branch: `rework-events`, created from `main`.

1. Run `git switch -c rework-events main`.
2. Create `scripts/fit_statsbomb_spells.py` as a new file. The draft's version on `pivot-draft` is hard-coded, so nothing in it carries over.
3. Give the script the options `--matches` (default 60), `--workers` (default 12), and `--output` (default `data/models/statsbomb_spells.json`).
4. Import `_get_json` and `BASE_URL` from `scripts/fit_statsbomb_model.py`. Run the script as a module, `uv run python -m scripts.fit_statsbomb_spells`, so that the import works.
5. Select the same matches on every run. Walk `competitions.json` in file order and keep the rows whose `competition_gender` is `male`. Take at most 10 matches from each competition season, in its matches file order, until you have `--matches` of them. The cap keeps one team's season from dominating the sample.
6. Download the event files in parallel and keep them in memory. If any download fails, exit with a non-zero code and write nothing.
7. Use periods 1 and 2 only. A match's length in minutes is the sum of the last `timestamp` in each period, divided by 60.
8. Compute the aggregates below. Write them to `--output` with `json.dumps(..., indent=2, sort_keys=True)`.
9. Print every value in the output as a readable summary.
10. In `docs/data-generation.md`, add a paragraph on the spell calibration: what it reads, its provenance fields, and the command that reproduces it.

Use these definitions:

- A **spell** is one `possession` value in one match. Its owner is `possession_team.id`.
- A spell's **on-ball events** are its `Pass`, `Carry`, `Shot`, and `Ball Receipt*` events whose `team.id` is the owner. Skip spells with no on-ball events, and count them in the provenance.
- A spell's **duration** is its last event's timestamp minus its first, in seconds.
- A spell's **end** is `shot` when the owner's last on-ball event is a `Shot`. It is `incomplete_pass` when that event is a `Pass` with a `pass.outcome`. It is `other` in every other case.
- An event **ends** at its timestamp plus its `duration`, or at its timestamp when it has no `duration`.
- `gap_within_spell_s` is the time from the end of one owner on-ball event to the start of the next owner on-ball event in the same spell, floored at 0.
- `gap_between_spells_s` is the time from the end of a spell's last event to the start of the next spell's first event, within the same period.
- **Core actions** are `Pass`, `Carry`, `Pressure`, and `Shot` events by either team.
- Convert lengths to metres with `itg.pitch.to_metres` on the x and y differences, then take the distance.
- **Field tilt** for a 5-minute window is the home team's share, in percent, of the window's events with `location[0] >= 66`. The windows are minutes 0 to 4, 5 to 9, and so on up to 89, by the `minute` field. Count `Pass`, `Carry`, `Shot`, `Pressure`, `Ball Receipt*`, and `Duel` tackle events. This mirrors `rolling_stats` in `src/itg/interpret.py`. The home team is `home_team` in the matches file.

Write this shape. The quantiles are `p10`, `p50`, and `p90` unless the shape says otherwise.

```json
{
	"provenance": {
		"source": "StatsBomb Open Data",
		"selection": "at most 10 matches per male competition season, in competitions.json order",
		"matches_requested": 60,
		"matches_read": 60,
		"match_ids": [],
		"events_read": 0,
		"possessions_read": 0,
		"possessions_without_on_ball_events": 0
	},
	"match_minutes_mean": 0.0,
	"core_actions_per_minute": 0.0,
	"per_team_per_90": {"pass": 0.0, "carry": 0.0, "pressure": 0.0, "shot": 0.0, "tackle": 0.0, "interception": 0.0},
	"pass_completion": 0.0,
	"spell_changes_per_minute": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"on_ball_events_per_spell": {"p10": 0, "p50": 0, "p90": 0, "histogram": {"1": 0.0, "2": 0.0, "40+": 0.0}},
	"spell_duration_s": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"gap_within_spell_s": {"p1": 0.0, "p5": 0.0, "p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0},
	"gap_between_spells_s": {"p1": 0.0, "p5": 0.0, "p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0},
	"spell_end_shares": {"shot": 0.0, "incomplete_pass": 0.0, "other": 0.0},
	"pressures_per_defending_second": 0.0,
	"pass_length_m": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"pass_duration_s_by_length": {"under_15m": {}, "15m_to_30m": {}, "over_30m": {}},
	"carry_length_m": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"carry_duration_s": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"field_tilt_5min": {"p1": 0.0, "p5": 0.0, "p95": 0.0, "p99": 0.0}
}
```

- `per_team_per_90` counts each team's events, scales them to 90 minutes by the match length, and averages over teams and matches.
- `spell_changes_per_minute` is each match's spell count divided by its length, with quantiles across matches.
- The histogram gives the share of spells for each on-ball event count from 1 to 39, and `40+` for the rest.
- The two gap distributions store more quantiles and a mean, because stoppages give them a long tail.
- `pressures_per_defending_second` is the number of `Pressure` events by the team without the ball, summed over spells, divided by the summed spell durations.

The script exits non-zero and writes nothing when a guard below fails. The guards catch unit and coordinate mistakes. They are wide estimates, not targets.

- `matches_read` equals `matches_requested`.
- The p50 of `spell_changes_per_minute` is between 1.0 and 3.5.
- The p50 of `pass_length_m` is between 8 and 30.
- `per_team_per_90.shot` is between 5 and 25.
- `per_team_per_90.pressure` is between 60 and 250.

If real data falls outside a guard after you rule out a bug, widen that guard and give the reason in the log.

### Unit 1 checks

1. `uv run python -m scripts.fit_statsbomb_spells` exits with code 0 and prints the summary. Record the elapsed time.
2. Run it a second time. `sha256sum data/models/statsbomb_spells.json` prints the same hash after both runs.
3. A new test, `tests/test_calibration_provenance.py::test_statsbomb_spells_provenance`, reads the file offline. It asserts that `matches_read` equals `matches_requested`, that both equal `len(match_ids)`, and that the count is at least 40. It asserts that `events_read` and `possessions_read` are greater than 0.
4. `uv run pytest` passes.
5. Before the commit, `git status --short` lists only the script, the JSON file, the test, and `docs/data-generation.md`.
6. Commit, then merge into `main`:

	```bash
	git add scripts/fit_statsbomb_spells.py data/models/statsbomb_spells.json tests/test_calibration_provenance.py docs/data-generation.md
	git commit -m "Fit possession-spell aggregates from StatsBomb Open Data"
	git switch main
	git merge --ff-only rework-events
	git switch rework-events
	```

## Unit 2: correct the spell generator

Branch: `rework-events`, continued.

### Start from the draft

1. Run `git checkout pivot-draft -- src/itg/models.py src/itg/pitch.py src/itg/generator.py`.
2. Run `uv run pytest`. Every test passes except `test_detector_finds_each_supported_shift_kind`, which fails on `direct_attack`.

Keep `models.py` and `pitch.py` as they are. `generator.py` is the code you correct. Keep `src/itg/interpret.py` as it is on `main`. The line numbers below refer to `src/itg/generator.py` on `pivot-draft`.

### Corrections

1. **Defender frame.** Lines 170 and 185 write pressure and tackle locations in the possessing team's frame. Write them in the defender's frame, at `(120 - ball_x, 80 - ball_y)`, where `(ball_x, ball_y)` is the ball in the possessing team's frame.
2. **Spell start.** Lines 111 to 113 give every spell's first action a fresh location from `model.initial_event`. Start each spell where the previous spell left the ball, mirrored into the new team's frame. Start the match at the centre spot, `(60, 40)`.
3. **Spell end.** End every spell with exactly one turnover. Draw its kind from `spell_end_shares`:
	- For `shot`, the owner shoots. The shot ends at `x = 120`, with `y` between 36 and 44. The next spell starts at the mirrored point, where the goalkeeper has the ball.
	- For `incomplete_pass`, the owner's last action is a pass with outcome `incomplete`. The next spell starts at the pass's end location, mirrored.
	- For `other`, a defender makes a `tackle` at the ball after the owner's last action. The next spell starts at the tackle's location.
4. **Spell length.** Line 99 draws `uniform(13, 24)` seconds. Draw the spell's number of on-ball events from the `on_ball_events_per_spell` histogram instead. Time then follows from the action durations and the gaps in correction 5.
5. **Durations, lengths, and gaps.** Draw pass durations from `pass_duration_s_by_length` for the pass's length group, and carry durations from `carry_duration_s`. Draw pass and carry lengths from `pass_length_m` and `carry_length_m`. After each on-ball action, advance time by a draw from `gap_within_spell_s`. Between spells, advance time by a draw from `gap_between_spells_s`. Point passes and carries forward on average, and keep the spread in a named constant.
	- To draw from a distribution, draw a quantile uniformly between its lowest and highest stored percentile, then interpolate linearly between the stored values. That range is 0.1 to 0.9 for p10, p50, and p90, and 0.01 to 0.99 for the gaps.
6. **Pressure rate.** Line 161 sets `max(pressure_rate, 0.7)`. Instead, after each action, add a pressure with probability `1 - exp(-rate * elapsed)`. Here `rate` is `pressures_per_defending_second`, and `elapsed` is the action's duration plus the gap that follows it.
7. **Planted shifts.** Lines 115 to 135 move an action's start location during a shift, which makes the ball jump. Delete them. Express each shift through spell parameters only: the pressure rate, the spell length, the end shares, how far forward passes and carries go, and the mix of passes, carries, and shots. Put the multipliers in named constants at the top of the module. Start from these values:
	- `high_press`: while the shift team defends, its pressure rate doubles, the opponent's spells are 40% shorter, and the opponent's `other` share doubles.
	- `low_block`: while the shift team defends, its pressure rate halves, the opponent passes and carries further forward, and the opponent's `other` share doubles.
	- `possession_surge`: the shift team's spells are 60% longer, with more carries.
	- `direct_attack`: the shift team's spells are 40% shorter, its passes and carries go further forward, and its `shot` share doubles.
8. **The Markov model.** If `EventMarkovModel.next_event` fits the spell loop, use it to choose each action's type. Otherwise remove the model from the generator, and list `data/models/statsbomb_markov.json` and `scripts/fit_statsbomb_model.py` as unused in the log, for Hatim to decide.
9. **Dead code.** Delete the empty `if` block at lines 195 to 200, the branches at lines 55 to 58 that cannot run, and the `3.5 if model is not None else 9.0` spread at line 114.
10. Run `uv run python scripts/generate_examples.py` to regenerate `data/examples/`.

### Detector

These are the detector conditions on `main`:

| Kind               | Condition                                                  |
| ------------------ | ---------------------------------------------------------- |
| `high_press`       | `pressure_delta >= 2 and tilt_delta >= 4`                  |
| `possession_surge` | `possession_delta >= 8 and carry_delta >= 2`               |
| `direct_attack`    | `shot_delta >= 4 and carry_delta >= 2 and tilt_delta >= 4` |
| `low_block`        | `tackle_delta >= 2 and tilt_delta <= -4`                   |

If the detector misses a kind, strengthen that kind's multipliers first. Retune a detector condition only when stronger multipliers fail. For each retune, log the old value, the new value, and the reason. Each condition keeps its direction. For example, `high_press` always requires field tilt to rise.

### Unit 2 checks

Put the new tests in `tests/test_spells.py`. Each test reads its targets from `data/models/statsbomb_spells.json`.

1. `uv run pytest` passes. In the log, list every test you changed or removed, and why. Replace `test_fitted_markov_model_keeps_same_team_motion_continuous` with check 4, because that test measured the old coin-flip generator.
2. Generate seeds 1 to 10 with the default `MatchConfig` and average over them. Each of these is within 25% of the calibration:
	- spell changes per minute, against the p50;
	- the median number of on-ball events per spell, against the p50;
	- the median spell duration, against `spell_duration_s.p50`;
	- passes, carries, pressures, and shots per team per 90 minutes;
	- core actions per minute.
3. For seed 61, every spell ends with exactly one turnover. The owner's last on-ball action is a shot or an incomplete pass, or the spell's last event is a tackle by the other team. No shot or incomplete pass comes before a spell's last action.
4. For seed 61, the ball never jumps. Each on-ball event (`pass`, `carry`, `shot`, or `possession`) starts within 0.5 units of where the previous on-ball event left the ball, across spell boundaries too. A pass, carry, or shot leaves the ball at `(end_x, end_y)`. A `possession` event leaves it at `(x, y)`. Compare in absolute coordinates by mirroring away events with `(120 - x, 80 - y)`.
5. For seed 61, every pressure and tackle sits within 0.5 units of the ball, in absolute coordinates.
6. For seed 61, each completed pass is followed by a `possession` event by the named receiver. That event lies within 0.5 units of `(end_x, end_y)`, at `t >= pass.t + pass.duration`. `t` never decreases, and `minute` and `second` agree with `t`.
7. For each of the four shift kinds at seed 61, `score_detections` finds the shift. The after window minus the before window, for the shift team, moves in the planted direction:
	- `high_press`: pressures and field tilt both rise;
	- `possession_surge`: possession rises;
	- `direct_attack`: shots and field tilt both rise;
	- `low_block`: tackles rise and field tilt falls.
8. After you regenerate the examples, the detector finds all 10 planted shifts in the committed batch. Paste the scores.
9. Report only: run `generate_examples(tmp_dir, count=20)`, score every match, and give the number found out of 20 and the misses.
10. Report only: for seeds 1 to 10, give the lowest and highest home field tilt across the 5-minute windows outside the shift windows, and each shift window's value. Put them beside `field_tilt_5min.p1` and `field_tilt_5min.p99`.
11. Commit, then merge into `main`:

	```bash
	git add src tests data/examples
	git commit -m "Build spells with real turnovers and defender-frame events"
	git switch main
	git merge --ff-only rework-events
	```

## Unit 3: fit the tracking calibration from IDSSE

Branch: `rework-idsse`, created from `main`.

### Set up

1. Run `git switch -c rework-idsse main`.
2. Run `uv add --group calibration "kloppy==3.19.1"`. The facts in this brief are checked against that version. If you use `numpy`, add it to the same group.
3. Add the IDSSE paragraph to `docs/data-generation.md`. Copy it from `git show pivot-draft:docs/data-generation.md`, and leave the rest of the file as it is on `main`.
4. Create `scripts/fit_idsse_tracking.py` as a new file. The draft's version reads its own output, so nothing in it carries over.
5. Give the script the options `--matches` (default 2), `--limit` (default none), and `--sample-rate` (default 1.0). Take match ids in this order: `J03WPY`, `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WQQ`, `J03WR9`.
6. Load each match with `coordinates="kloppy"` and `only_alive=True`. Process one match at a time, and release it before you load the next.
7. When `--limit` is set, pass it to kloppy, print the summary, and write nothing.

### Run a smoke test first

Run one match with a frame limit before the full fit:

```bash
/usr/bin/time -v uv run --group calibration python scripts/fit_idsse_tracking.py --matches 1 --limit 5000
```

The first run downloads about 370 MB. Record the elapsed time and the `Maximum resident set size`. To estimate the peak memory of a full match, scale the resident size to 90,000 frames. If the estimate is above 5 GB, run the full fit with `--sample-rate 0.2`.

### Method

- Convert to metres. Multiply x by the pitch length and y by the pitch width from each match's metadata.
- Find each team's attacking direction in each period from its goalkeeper's mean x in that period. In a team's attacking frame, the team attacks toward +x. Mirror the other direction with `(length - x, width - y)`.
- Smooth positions with a centred moving average over 0.2 s, then take differences for speed and acceleration.
- A team is **in possession** on frames where `frame.ball_owning_team` is that team.
- The **ball third** comes from the ball's x in the team's attacking frame. It is `defensive` below one third of the pitch length, `attacking` above two thirds, and `middle` between.
- **Roles.** For each team and match, take the 10 outfield starters (`Player.starting`). Compute their mean positions in the attacking frame, on frames before the team's first substitution. The 4 deepest form the back four, the next 3 the midfield, and the top 3 the attack. Within each line, sort by mean y, low y first, because low y is the left side. Assign `LB`, `LCB`, `RCB`, `RB`, then `LCM`, `CM`, `RCM`, then `LW`, `ST`, `RW`. The goalkeeper is `GK`. Print each starter's `starting_position`, mean position, and assigned role.
- **Role groups** for the speed figures are `GK`, `FB` (`LB` and `RB`), `CB` (`LCB` and `RCB`), `CM` (`LCM`, `CM`, and `RCM`), `W` (`LW` and `RW`), and `ST`.
- **Team length** runs from the deepest to the most advanced outfield player in x. **Team width** runs from the lowest to the highest outfield player in y. **Line height** is the mean distance of the 4 deepest outfield players from their own goal line. **Centroid offset** is the outfield centroid's x minus the ball's x.
- **Role offsets** are each role's position minus the outfield centroid. Use only frames where all 10 outfield starters of that team are on the pitch.
- **Pass and shot speed.** Take passes and shots from the event data. Find the tracking frame at the event's period and timestamp, and take the peak ball speed in the next 1 s. Group passes by length. Use the event's end location if kloppy gives one. Otherwise use the ball's position when its speed next drops below 3 m/s.
- **Nearest defender.** On frames where the ball moves slower than 3 m/s, take the distance from the ball to the nearest player of the team without the ball. Group by the ball third in the owning team's attacking frame.

Write this shape to `data/models/idsse_tracking.json` with `json.dumps(..., indent=2, sort_keys=True)`. The quantiles are `p10`, `p50`, and `p90` unless the shape says otherwise. Take `frame_rate_hz` from the dataset metadata.

```json
{
	"provenance": {
		"source": "IDSSE",
		"license": "CC-BY 4.0",
		"citation": "Bassek, Rein, Weber, and Memmert, An integrated dataset of spatiotemporal and event data in elite soccer, Scientific Data 12:195 (2025), doi:10.1038/s41597-025-04505-y",
		"kloppy_version": "",
		"match_ids": [],
		"frame_rate_hz": 0.0,
		"sample_rate": 1.0,
		"in_play_frames": {},
		"pitch_m": {}
	},
	"speed_ms": {"GK": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "p99.9": 0.0}},
	"acceleration_ms2_p99": {"GK": 0.0},
	"distance_m_per_min": {"GK": {"p10": 0.0, "p50": 0.0, "p90": 0.0}},
	"team_shape": {
		"in_possession": {
			"defensive": {"length_m": {}, "width_m": {}, "line_height_m": {}, "centroid_ball_dx_m": {}},
			"middle": {},
			"attacking": {}
		},
		"out_of_possession": {}
	},
	"role_offsets_m": {
		"in_possession": {
			"defensive": {"LB": {"dx_mean": 0.0, "dx_std": 0.0, "dy_mean": 0.0, "dy_std": 0.0}},
			"middle": {},
			"attacking": {}
		},
		"out_of_possession": {}
	},
	"pass_ball_speed_ms": {"under_15m": {}, "15m_to_30m": {}, "over_30m": {}},
	"shot_ball_speed_ms": {"p10": 0.0, "p50": 0.0, "p90": 0.0},
	"nearest_defender_slow_ball_m": {"defensive": {}, "middle": {}, "attacking": {}}
}
```

Fill every role group in `speed_ms`, `acceleration_ms2_p99`, and `distance_m_per_min`. Fill all 11 roles in every `role_offsets_m` cell. `distance_m_per_min` uses each player's distance in each 5-minute block of in-play time.

### Guards

The script exits non-zero and writes nothing when a guard fails. The ranges are wide estimates that catch unit and coordinate mistakes. They are not targets.

- Every role group's `p99.9` speed is between 6 and 11.5 m/s.
- The `p50` shot speed is between 12 and 40 m/s.
- The `p50` out-of-possession team length in the middle third is between 20 and 60 m.
- In-play frames per match are between 50,000 and 130,000 at 25 fps. Scale the range by the sample rate.
- `ball_owning_team` is set on at least 80% of in-play frames.
- At least 99.9% of player positions lie within 2 m of the pitch.

If real data falls outside a guard after you rule out a bug, widen that guard and give the reason in the log.

### Unit 3 checks

1. The log has the smoke run's elapsed time and peak memory.
2. `uv run --group calibration python scripts/fit_idsse_tracking.py` exits with code 0. It prints every output value and the role assignments.
3. Run it a second time, which reads from the kloppy cache. `sha256sum data/models/idsse_tracking.json` prints the same hash after both runs.
4. A new test, `tests/test_calibration_provenance.py::test_idsse_tracking_provenance`, reads the file offline. It asserts that `match_ids` is not empty, that every match has more than 0 in-play frames, and that `kloppy_version` is set. Add the test to the file from Unit 1, or create the file if Unit 1 did not merge.
5. `uv run pytest` passes without the `calibration` group.
6. Before the commit, `git status --short` lists only the script, the JSON file, the test, `pyproject.toml`, `uv.lock`, and `docs/data-generation.md`.
7. Commit, then merge into `main`:

	```bash
	git add scripts/fit_idsse_tracking.py data/models/idsse_tracking.json tests/test_calibration_provenance.py pyproject.toml uv.lock docs/data-generation.md
	git commit -m "Fit tracking aggregates from two IDSSE matches"
	git switch main
	git merge --ff-only rework-idsse
	```

## Out of scope

Leave these for later briefs, even if you finish early:

- `src/itg/tracking.py`, `src/itg/tracking_stats.py`, and the footage renderer, which wait for Friday's brief;
- `src/itg/scene.py` and its test, which stay on `main` until tracking replaces them;
- everything in the out-of-scope list of `docs/briefs/tracking-pivot.md`.

## How to report

Write the report in `docs/briefs/tracking-rework-log.md`. For each unit, give:

1. what changed, by file;
2. each check with its exact command and raw output, or the last 20 lines of a longer output;
3. each deviation from this brief, with its reason.

End the report with three headings. **Snags** covers friction, such as a tool that misbehaved or instructions that conflicted. **Wants** covers a tool or capability that would have helped. **Distress** covers a task shape that felt contradictory or ambiguous, if there was one.

Add one line per finished unit to the log in `docs/PLAN.md`. Keep the report and the `docs/PLAN.md` change uncommitted while you work. No unit branch touches those files, so they stay in place when you switch branches. At the end of the session, commit them on `main`:

```bash
git switch main
git add docs/briefs/tracking-rework-log.md docs/PLAN.md
git commit -m "Log the tracking rework session"
```
