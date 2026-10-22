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

## Practical expectations for future sessions

- Prefer the simplest file or module split that preserves the five-stage architecture and makes evidence flows easy to inspect.
- When adding tests, keep them focused on deterministic behavior (generator output, rolling-stat windows, detector logic, and fact-check evidence) before adding broad integration tests.
- Make the trace view and fault-injection flow observable; the plan treats these as critical demo features for explaining multi-agent behavior.
- Keep the app budget-friendly: cached replays, rate-limited live generation, and token logging are part of the design intent.

## Source-of-truth files

- `docs/PLAN.md` — product concept, architecture, Azure setup, schedule, and implementation constraints.
- `docs/demo-script.md` — the exact demo/story requirements that shape what the app must visibly demonstrate.
- `docs/RESOURCE PLAYLISTS.md` — references and optional ideas, not a substitute for the plan.
