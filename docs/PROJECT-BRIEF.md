# ITG-IIMA project brief

## Executive defense

ITG-IIMA is an explainable synthetic-football intelligence system. It does not
stop at narrating an event or displaying a scoreline: it generates a
football-realistic synthetic match, plants known tactical changes, detects
those changes with deterministic code, and preserves the evidence needed for
agents to explain and personalize the result later.

The central product claim is:

> Scorelines tell you what happened. ITG-IIMA tells you when the game turned,
> why it turned, and which evidence supports the explanation.

The project is deliberately built around a separation of responsibilities:

- deterministic code owns event generation, statistics, detection, evidence,
  and ground truth;
- models and agents will own language, verification workflows, and
  personalization;
- the UI will show verified output rather than an unverified model draft.

That separation is the project’s trust argument. An agent cannot silently
invent the statistic behind a card because the statistic is computed outside
the model and can be re-queried by a fact-checker.

## Why the scope fits the hackathon

The hackathon asks for synthetic football events to be transformed into
meaningful intelligence, explanations, personalized experiences, and
machine-readable or broadcast-oriented outputs. ITG-IIMA maps directly onto
those requirements:

| Requirement | ITG-IIMA response |
| --- | --- |
| Ingest synthetic events | Seedable fictional match generator with JSONL output |
| Aggregate meaningful states | Five-minute rolling pressure, field tilt, possession, passing, and event features |
| Identify key moments | Detector compares adjacent windows and reports evidence |
| Explain why moments matter | Planned Analyst → Fact-checker → Persona pipeline |
| Personalize | Planned analyst/fan views, English/French output, and player focus |
| Broadcast/streaming use | Planned timed overlay JSON and web second-screen |
| Data innovation | Planted truth makes detector quality measurable rather than subjective |
| Microsoft stack | Foundry model deployment, Agent Framework plan, Azure Container Apps plan, Copilot Agent Mode workflow |

The project uses fictional clubs and players and labels its data and footage
as synthetic. It does not use real match footage, real clubs, or real player
records in the product.

## Current architecture

```text
                  ┌─────────────────────────────┐
                  │ Synthetic match generator   │
                  │ seed + team styles + shifts  │
                  └──────────────┬──────────────┘
                                 │
             ┌───────────────────┴───────────────────┐
             │                                       │
             ▼                                       ▼
   JSONL event stream                         ground_truth.json
             │                                       │
             └───────────────────┬───────────────────┘
                                 ▼
                  ┌─────────────────────────────┐
                  │ Deterministic interpretation │
                  │ rolling stats + detector     │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  typed MatchState + evidence
                                 │
                 ┌───────────────┴────────────────┐
                 ▼                                ▼
       planned agent explanation          synthetic footage surface
       Analyst → Fact-checker → Persona   renderer now; model video optional
```

The event stream is authoritative. The footage path is a separate visual
surface that can later be analyzed and reconciled against the event timeline.
It must not replace deterministic ground truth.

## What is implemented

### Synthetic event contract

`src/itg/models.py` defines typed contracts for:

- `MatchEvent`: minute, second, team, fictional player, event type,
  coordinates, outcome, optional receiver, and optional shot value;
- `PlantedShift`: shift identifier, minute, team, tactical kind, and duration;
- `Match`: match metadata, players, events, planted shifts, JSONL serialization,
  and ground-truth serialization.

Supported event types are `pass`, `pressure`, `tackle`, `shot`, `carry`, and
`possession`.

### Seedable generator

`src/itg/generator.py` creates reproducible fictional matches. The generator
uses a seed, fictional team/player names, configurable shift timing and team,
and a calibrated baseline of 27 events per minute. That baseline is a broad
volume target, not a replay of any real match.

Supported planted tactical profiles are:

- `high_press`: more pressure actions and advanced territorial positions;
- `possession_surge`: more possession, carrying, and controlled progression;
- `direct_attack`: more carries and shots toward the attacking end;
- `low_block`: deeper territorial positions and more defensive tackles.

The shifts alter generated events, not just metadata. This makes them
observable by the interpretation layer.

### Deterministic interpretation

`src/itg/interpret.py` computes five-minute windows containing:

- pressure counts;
- complementary field tilt;
- complementary possession;
- pass accuracy;
- shots, carries, and tackles.

The detector compares adjacent windows and emits a `DetectionResult` containing
the detected minute, team, tactical kind, before/after windows, and a score.
`score_detections()` compares those results against planted truth with a
configurable minute tolerance.

### Committed example dataset

`data/examples/` contains ten reproducible fictional matches:

- one JSONL stream per match;
- one ground-truth JSON file per match;
- a README explaining regeneration;
- varied tactical truth across both teams.

Current distribution:

| Shift kind | Count |
| --- | ---: |
| `high_press` | 3 |
| `possession_surge` | 3 |
| `direct_attack` | 2 |
| `low_block` | 2 |

The examples are generated with:

```bash
uv run python scripts/generate_examples.py
```

### Synthetic footage

`src/itg/footage.py` renders a deterministic, broadcast-style MP4 from the
synthetic match events. It creates a simple pitch, team-colored event markers,
and a scoreboard-like overlay. A sidecar frame manifest maps rendered frames
back to event indices and match minutes.

The current generated clip is:

```text
data/examples/example-01.mp4
data/examples/example-01.frames.json
```

Generate it with:

```bash
uv run python scripts/generate_footage.py
```

This is intentionally a controllable fallback for the demo. It is more
reliable than generative video for matching exact planted truth.

## StatsBomb calibration decision

StatsBomb Open Data was used only as temporary external calibration material.
Ten official event files were inspected outside the repository to learn:

- event vocabulary;
- broad event volume;
- relationships among passes, carries, pressures, and shots.

The first aggregate target was approximately 2,275 core action events per
90-minute match, or about 27 per minute. Only aggregate targets were retained.
No raw source files, real teams, real players, source coordinates, or source
event rows were committed or placed in the product.

The policy is important for both compliance and product quality:

1. the runtime remains synthetic-only;
2. the generator remains controllable and seedable;
3. planted truth remains measurable;
4. the demo is not a disguised replay of historical data;
5. any public attribution can be added without redistributing source data.

The external source and license are kept in session scratch, not this
repository. The repository documentation records the boundary in
`docs/data-generation.md`.

## Foundry and model strategy

The current Foundry resource has a deployed `gpt-5-mini` model. A successful
Agent Framework smoke test was completed before implementation began. The
planned explanation path is:

1. Analyst reads typed match state and drafts an explanation.
2. Fact-checker independently re-queries evidence and rejects incorrect
   figures.
3. Analyst revises rejected claims.
4. Persona re-expresses the verified result for an analyst or casual fan and
   in English or French.

Models never calculate core match statistics. They consume deterministic
evidence tools.

### Optional Foundry video generation

The repository includes `scripts/foundry_video.py`, an optional no-secret
client for Foundry’s asynchronous video-generation API. It uses an Azure CLI
access token and requires a separately deployed video model:

```bash
export FOUNDRY_OPENAI_ENDPOINT="https://<resource>.openai.azure.com"
export FOUNDRY_VIDEO_MODEL="<video-deployment>"
uv run python scripts/foundry_video.py
```

The current resource exposes only `gpt-5-mini`, not a video-generation
deployment, so this path is not a current dependency. If enabled later,
generated footage must be labeled synthetic and treated as corroborating
visual input, not as the source of truth. Generative video can contain
inconsistent positions, timing, or actions.

## Validation evidence

The current test suite contains seven focused tests:

```bash
uv run pytest
```

The latest run passed all seven tests. Validation also established:

- same seed produces identical events;
- JSONL output is parseable;
- event minutes and coordinates stay within bounds;
- field tilt and possession remain complementary;
- all four shift kinds are detectable;
- all ten committed examples have their planted shift found within the
  five-minute tolerance;
- the deterministic footage renderer creates a valid ten-second MP4;
- the footage manifest has one entry per rendered frame.

The current Foundry deployment was checked with Azure CLI and contains only:

```text
gpt-5-mini, version 2025-08-07
```

No secret or API key is stored in source control.

## Honest limitations

The current implementation is a strong deterministic foundation, not the
finished product. It does not yet include:

- the Analyst, Fact-checker, and Persona agents;
- Agent Framework orchestration and trace events;
- fact-check rejection/revision UI;
- timed overlay JSON endpoint;
- web second-screen;
- player-focus mode;
- frame/video analysis and event reconciliation;
- Azure Container Apps deployment;
- a real video-generation deployment.

The deterministic footage renderer is also intentionally schematic. It is
useful for a reproducible demo and analysis seam, but it is not computer
vision, broadcast footage, or proof that a model can understand football
video.

These limitations are explicit rather than hidden. The next work should
extend the existing typed evidence seam instead of letting models recompute or
invent match state.

## Immediate next work

1. Add `MatchState` and evidence tools around the existing `WindowStats` and
   `DetectionResult` contracts.
2. Implement the Analyst → Fact-checker reject-and-revise loop with structured
   trace events and a deterministic fault-injection switch.
3. Add Persona output for analyst/fan views and English/French.
4. Emit timed overlay JSON from verified cards.
5. Build the web second-screen with replay, timeline, momentum strip, cards,
   evidence chips, and trace drawer.
6. Add a frame-sampling/video-analysis adapter that reports observations with
   timestamps and confidence, then reconciles them against `MatchState`.
7. Deploy the cached replay path to Azure Container Apps.
8. Capture the two-minute demo around the planted shift, visible rejection,
   verified evidence, synthetic footage, and deployed second screen.

## Restart commands

From the repository root:

```bash
uv python pin --managed-python 3.12
uv run pytest
uv run python scripts/generate_examples.py
uv run python scripts/generate_footage.py
```

Source-of-truth documents:

- `docs/PLAN.md` — product direction, schedule, architecture, and constraints;
- `docs/demo-script.md` — required demo shots and judging coverage;
- `docs/data-generation.md` — synthetic-data and calibration boundary;
- `docs/PROJECT-BRIEF.md` — this defense, current evidence, limitations, and
  restart point.
