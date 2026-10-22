# Copilot instructions for ITG-IIMA

This repository is a fresh hackathon project built around the ITG-IIMA concept described in `docs/PLAN.md` and `docs/demo-script.md`. Treat those files as the source of truth for scope, product direction, and implementation constraints until project code exists.

## Command conventions

The repo intentionally requires a managed Python environment instead of the system Python:

- Pin the project interpreter: `uv python pin --managed-python 3.12`
- Run Python commands and tests through uv: `uv run ...`
- Test the full suite: `uv run pytest`
- Run one test file or test selection: `uv run pytest path/to/test_file.py` or `uv run pytest path/to/test_file.py -k test_name`

There is no root-level build or lint configuration in this repo yet. If the project later adds Python tooling, prefer the repo's own commands over inventing new ones; keep using `uv run` for anything that executes Python.

## High-level architecture

The product is organized around five stages that must stay conceptually separated:

1. Ingest: synthetic match engine that streams JSONL events and a planted ground-truth shift file.
2. Interpret: deterministic, code-driven rolling stats and regime/moment detection; this layer turns raw events into explainable signals.
3. Explain: multi-agent pipeline where an Analyst agent drafts insights, a Fact-checker verifies them against match state, and a Persona agent re-expresses the result for different audiences.
4. Render: timed, machine-readable overlay JSON plus a web second-screen that displays timeline, momentum strip, cards, and evidence.
5. Personalize: analyst vs casual-fan views, language switching (English/French), and optional player-focus mode.

The intended architecture is intentionally split between deterministic logic and LLM reasoning:

- Deterministic Python code owns event generation, rolling-stat calculations, regime detection, and evidence extraction.
- LLM agents consume the shared match state and cite data rather than inventing numbers.
- The web app should present the verified output, not the raw model draft.

## Key repo conventions

- New code only: do not copy or port older code into this repo just because it is similar.
- Synthetic data only: no StatsBomb or real football event data should appear in the product.
- Use fictional clubs, players, and match setups; the script and app are expected to be clearly synthetic.
- Keep the evidence loop explicit: every claim should be traceable to match state and ideally pass through a fact-checking/rejection cycle.
- Treat the demo as a live product/storytelling experience, not just a model output: the app needs a replayable second screen, overlay card outputs, and a public deployment path.
- Keep Azure and model access outside source control: use `AzureCliCredential` and do not commit secrets or keys.
- The repo is judged as a Microsoft stack project: expect Foundry, Agent Framework, Azure Container Apps, and GitHub Copilot Agent Mode to appear in the implementation and the final demo narrative.
- Keep the `main` branch in a working state; the project plan explicitly says it should hold a working demo.
- The repo is docs-first and product-spec-first. When scope is uncertain, prefer `docs/PLAN.md` and `docs/demo-script.md` over assumptions about framework or UI structure.

## Working from a brief

Each session works from a brief in `docs/briefs/`. The brief gives the session's units, steps, checks, and hard stop. The rules below apply to every brief, and a brief adds only what is specific to its session.

### Branches and commits

- Work on the branch the brief names for each unit, and commit at the end of each unit on that branch.
- Merge a unit into `main` only after its checks pass.
- An unfinished unit stays on its branch, with a log entry that says where it stopped.
- Stop at the brief's hard stop, even in the middle of a unit.

### Checks

- Run every check the brief lists, and record each result.
- Checks keep the thresholds the brief gives them. Tests read their targets from the data files under `data/models/`.
- When a check fails and the fix is unclear, stop that unit. Record the command and its output in the log, then start the next unit the brief allows.
- When a brief allows a threshold change, log the old value, the new value, and the reason. A changed condition keeps its direction: a condition that requires a value to rise still requires it to rise.

### External data

- Every number in a file under `data/models/` comes from a fit script that downloads and reads the source data in the same run.
- When the download fails, the fit script exits with a non-zero code and writes nothing.
- The output records its provenance: the source, the ids read, and the row or frame counts. An offline test asserts that provenance.
- A second run of the fit script reproduces its output byte for byte.
- Raw source files and download caches stay outside the repository. Only the aggregates that a fit script writes enter it.
- A fit script's guards catch unit and coordinate mistakes. If real data falls outside a guard after you rule out a bug, widen that guard and give the reason in the log.

### Code

- The runtime package `src/itg` uses the standard library only. Fit scripts may use packages from the `calibration` dependency group.
- Keep the existing style: frozen dataclasses, short modules, and named constants for tuned numbers.

### Reporting

Write the report in `docs/briefs/<brief name>-log.md`. For each unit, give:

1. what changed, by file;
2. each check with its exact command and its raw output, or the last 20 lines of a longer output;
3. each deviation from the brief, with its reason.

End the report with three headings. **Snags** covers friction, such as a tool that misbehaved or instructions that conflicted. **Wants** covers a tool or capability that would have helped. **Distress** covers a task shape that felt contradictory or ambiguous, if there was one.

Add one line per finished unit to the log in `docs/PLAN.md`. Keep the report and the `docs/PLAN.md` change uncommitted while you work. Unit branches leave those files alone, so they stay in place when you switch branches. At the end of the session, commit both on `main`.

## Practical expectations for future sessions

- Prefer the simplest file or module split that preserves the five-stage architecture and makes evidence flows easy to inspect.
- When adding tests, keep them focused on deterministic behavior (generator output, rolling-stat windows, detector logic, and fact-check evidence) before adding broad integration tests.
- Make the trace view and fault-injection flow observable; the plan treats these as critical demo features for explaining multi-agent behavior.
- Keep the app budget-friendly: cached replays, rate-limited live generation, and token logging are part of the design intent.

## Source-of-truth files

- `docs/PLAN.md` — product concept, architecture, Azure setup, schedule, and implementation constraints.
- `docs/demo-script.md` — the exact demo/story requirements that shape what the app must visibly demonstrate.
- `docs/RESOURCE PLAYLISTS.md` — references and optional ideas, not a substitute for the plan.
