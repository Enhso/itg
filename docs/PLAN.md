# ITG-IIMA: hackathon plan (living document)

Microsoft × Premier League "Inside the Game" hackathon. Started 2026-10-20 and revised each day.

## Hard dates

| What                    | When (PT)             | When (UTC)                    |
| ----------------------- | --------------------- | ----------------------------- |
| **Registration closes** | **Tue Oct 20, 12:00** | **Tue Oct 20, 19:00 (today)** |
| Submission closes       | Tue Oct 27, 23:59     | Wed Oct 28, 06:59             |
| Our own submit target   | Tue Oct 27, 12:00     | Tue Oct 27, 19:00             |

## Rules that shape the plan

1. **New code only.** The project must be created after Sep 29, 2026. a-tad dates from Feb–Apr 2026, so we carry over its _ideas_ (windowed features, HMM or change-point regimes, state annotation) and write the code fresh. Don't copy modules across.
2. **Synthetic data only.** No StatsBomb or real match data in the product. The synthetic match generator is required, and it is also scored ("creativity and optimized synthetic data creation").
3. **Microsoft stack, checked pass/fail in Stage One.** Hero tech: Foundry, Agent Framework, Azure MCP, GitHub Copilot Agent Mode, Azure apps/AI services, Azure databases.
4. **Deliverables:** public GitHub repo, a demo video under 2:00 (YouTube/Vimeo), a written pitch, and a live demo link that stays up until Nov 10.
5. **Judges may decide on the video and text alone.** The video is the product, so plan backwards from it.
6. **Scoring:** five equal criteria: tech implementation, agentic design, real-world impact, UX and presentation, category fit. A project can win one grand prize and one category prize.
7. **No third-party trademarks in the video.** All clubs and players are fictional, which also suits the synthetic-data rule.

## The concept

> Scorelines tell you _what_ happened. ITG tells you **when the game turned, and why**, with evidence, for every kind of fan.

Most entries will have an LLM narrate events. Our edge is the a-tad brain. Deterministic code detects tactical regime shifts (control vs chaos, pressure surges, rhythm changes). Agents then explain those shifts, and every claim cites the stats behind it.

Because the data is synthetic, we plant the truth. The generator injects known tactical shifts (for example, "the away team switches to a high press at 60'") and writes a ground-truth file. The system is then scored on whether it finds and explains them. That gives an explainability metric few teams can show, and it serves the data-innovation, quality and enterprise-trust criteria at once.

### Five required stages → components

| Stage       | Component                                                                                                                                                 | Type                             |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Ingest      | Synthetic match engine with team-style knobs and planted shifts. Streams events as JSONL at replay speed                                                  | Python, deterministic            |
| Interpret   | Rolling stats (possession, field tilt, pass accuracy and difficulty, pressure, xG-lite) and a regime/moment detector                                      | Python, deterministic            |
| Explain     | Analyst agent turns a moment and its evidence into "why it matters". Fact-checker agent checks every number against match state and sends bad drafts back | Agent Framework + Foundry models |
| Render      | Timed, machine-readable overlay JSON and a web second-screen (timeline, momentum strip, overlay cards)                                                    | FastAPI + small web UI           |
| Personalize | Persona agent: analyst vs casual fan, favourite club or player (player-focus mode), language                                                              | Agent Framework + Foundry models |

LLMs never compute stats. They call tools that read the deterministic match state.

### Target prizes

- **Grand prize.**
- **Category: Best Multi-Agent System (decided).** Its criteria (distinct roles, shared state, handoffs, failure recovery) are what the Analyst → Fact-checker → Persona loop shows. The work also counts toward the 20% agentic-design criterion.
- Natural second fit: Best Use of Foundry. Judges can reassign a project to another category.

### Cost and the live demo

The $100 Azure for Students credit has to cover the build and keep the demo up until Nov 10.

- **The public demo replays pre-generated matches with cached agent outputs.** A "new match" button runs the live pipeline behind a rate limit. This protects the budget and the model quota, keeps the demo fast, and gives the enterprise story a cost control to point at.
- **Hosting:** one container on Azure Container Apps (consumption plan, scale to zero). Pull the image from GHCR, which is free for public images, rather than paying for a container registry.
- **Budget alerts** at $25 and $50.
- Every model call logs its cached and uncached input tokens.

### Explicitly not doing

Auto-eventing from video, real footage or data, Fabric, AKS, Event Hubs, user accounts, a mobile app, and the M and T layers beyond generator knobs.

## Where this sits in HATIM

| Layer                                 | This week                                                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **H**istorical (player profiles)      | Seed only: synthetic player attributes drive the generator and feed player-focus mode               |
| **A**synchronous (post-match tactics) | Post-match recap (stretch)                                                                          |
| **T**eleological (tactics in silico)  | Seed only: the generator's team-style knobs are a first match simulator                             |
| **I**mmediate (in-match)              | **Core:** live regime detection and explanation. The audience is fans and broadcasters, not coaches |
| **M**agnificent (integration)         | Not this week                                                                                       |

This hackathon builds the first slice of **I**, with seeds of H, A and T. It does not build the whole suite.

## Azure setup (proven 2026-10-20)

| Item             | Value                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| Subscription     | Azure for Students ($100 credit)                                                                                 |
| Resource group   | `rg-hatim.eljazouli-5601`                                                                                        |
| Foundry resource | `itg-iima-resource` (AIServices, Switzerland North)                                                              |
| Foundry project  | `hatimeljazouli-7666`                                                                                            |
| Project endpoint | `https://itg-iima-resource.services.ai.azure.com/api/projects/hatimeljazouli-7666`                               |
| Model deployment | `gpt-5-mini` (version 2025-08-07, GlobalStandard, 200K TPM of the 500K quota; retires 2027-02-09)                |
| Auth             | `AzureCliCredential` (your `az login`), no keys in code                                                          |
| Python packages  | `agent-framework-foundry` (pre-release) and `azure-identity`; client `agent_framework.foundry.FoundryChatClient` |

What the smoke test showed:

- One call took 4.6 s. **256 of the 319 output tokens were reasoning tokens.** For the Persona and narration agents, set a low reasoning effort to cut latency and cost.
- `result.usage_details` reports cached and uncached input tokens, which covers the token-logging rule.
- **Run Python through a uv-managed interpreter only.** Anaconda's base Python is on PATH. Its old Brotli 1.0.9 leaked into a uv temporary environment and broke HTTP decoding (`process() takes no keyword arguments`). Pin the project with `uv python pin --managed-python 3.12` and always use `uv run`.

## Workflow

**Who drives:** GitHub Copilot (Agent Mode in VS Code, plus Copilot CLI) writes most of the code, because it is a judged hero technology. Claude Code plans, reviews diffs, verifies, and red-teams the pitch.

**Daily loop:**

1. **Start (10 min, with Claude):** read this file and the log, then pick 1–2 goals for the day. Each goal comes with a check that proves it done.
2. **Build (with Copilot):** conventions live in `.github/copilot-instructions.md`.
3. **End (10 min):** run the check, commit and push, and record a 15–30 s screen clip of what works. The clips become b-roll for the video. Add a line to the log below.

**Rule from Saturday on:** `main` always holds a working demo.

## Schedule (solo: 1.5 h on weekdays, longer at the weekend)

Each weekday session is one small unit that ends in a check. The weekend carries the agent and UI work.

| Day                | Time  | Goal                                                                                                                     | Done when                                                                                                  |
| ------------------ | ----- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Tue 20** (today) | 2 h   | Azure check, ending in one Agent Framework call to a Foundry model. Video script. Repo skeleton and Copilot instructions | An agent replies from this machine; `docs/demo-script.md` reviewed; `uv run pytest` passes on the skeleton |
| Wed 21             | 1.5 h | Event schema and generator v1: fictional teams and players, team-style knobs                                             | 10 generated matches have event counts and outcome rates in realistic bands                                |
| Thu 22             | 1.5 h | Planted shifts with a ground-truth file; rolling stats                                                                   | A planted shift shows up in the rolling stats at the planted minute                                        |
| Fri 23             | 1.5 h | Regime/moment detector, scored against ground truth                                                                      | Detector finds planted shifts within ±N min in most matches (set N and the bar on the day)                 |
| Sat 24             | long  | Agents: Analyst → Fact-checker loop and Persona; overlay JSON; precompute one demo match                                 | One match end to end gives timed overlay JSON; the fact-checker catches a planted wrong number             |
| Sun 25             | long  | Web second-screen; deploy to Container Apps; record raw video takes. **Feature freeze tonight**                          | Public URL works from a phone; analyst and casual-fan views are clearly different                          |
| Mon 26             | 1.5 h | Edit the video (<2:00); README with architecture diagram                                                                 | Someone who hasn't seen it can say what it does after one viewing                                          |
| Tue 27             | 1.5 h | Pitch text; submit by 12:00 PT. Buffer                                                                                   | Repo public, video public, demo live, form complete                                                        |

**Minimum winning slice:** generator with planted shifts, detector, three agents with the fact-check loop, two personas × two languages, the web replay, a deployed URL, and the video. It also needs two things the video script asks for (`docs/demo-script.md`, flags F1 and F2):

- **an agent trace view** showing each agent's lane, its tool calls and the fact-checker's verdicts. Agents emit trace events from Saturday. A UI drawer is preferred on Sunday, and a terminal trace is the fallback.
- **a fault-injection switch** that corrupts one Analyst figure on demand and labels it on screen, so the rejection can be filmed reliably and honestly.

**Stretch, in order:** single agent vs Analyst + Fact-checker comparison, counting wrong figures across the precomputed moments (about 20 min on Saturday; it backs the category's "one agent couldn't do this" claim with a number) → player-focus mode → post-match recap → MCP server exposing match-state tools → voice commentary (Azure AI Speech).

## Risks

1. ~~Student-subscription model quota.~~ **Resolved 2026-10-20.** Switzerland North gives gpt-5-mini 500K TPM and gpt-4.1-mini 200K (Legacy); every gpt-5.x model newer than gpt-5-mini has 0. See Azure setup.
2. **The agent work lands late (Saturday).** Partly retired: a real Agent Framework call through Foundry works from this machine.
3. **Budget until Nov 10.** See Cost and the live demo.
4. **Scope versus hours.** If a weekday unit overruns, cut in this order: the second extra language, then the recap, then UI polish. Never cut the video.

## Open questions

- [x] Open questions in `docs/demo-script.md` §4 (1 and 6 are settled; review the rest this afternoon).
- [x] Use StatsBomb Open Data only as temporary, external calibration input after checking its current license and attribution terms; retain no raw files or real-match fixtures. The shipped generator remains fictional, seedable, and tuned first for the planted demo story. See `docs/data-generation.md`.

Settled 2026-10-20: solo, registered, Azure for Students with $100 credit, 1.5 h on weekdays and 3–6 h on Sat and Sun, Best Multi-Agent System, product name **ITG-IIMA**, languages English and French.

## Log

- **2026-10-20:** Read the rules and wrote the plan. Registered. Azure check done: gpt-5-mini deployed, one Agent Framework call through Foundry succeeded. Video script drafted. Next (afternoon): review the script's open questions, then the repo skeleton and Copilot instructions.
- **2026-10-20:** Built the first deterministic slice: typed synthetic event contract, seedable JSONL generator, observable planted high-press shift, rolling evidence windows, moment detector, and ground-truth scoring. Four focused tests pass. StatsBomb calibration remains an external, non-committed follow-up; the current demo seed is tuned for the scripted story.
- **2026-10-20:** Wrote ten reproducible synthetic example matches to `data/examples/`, each with a JSONL event stream and paired ground-truth file. Added `scripts/generate_examples.py` so the batch can be regenerated rather than hand-maintained.
- **2026-10-20:** Varied the committed batch's planted truth across four detectable shift kinds (`high_press`, `possession_surge`, `direct_attack`, `low_block`), with 10/10 shifts still found within the detector tolerance.
- **2026-10-20:** Added a deterministic synthetic-footage renderer and generated `data/examples/example-01.mp4` with a frame-to-event manifest. The current Foundry resource has only `gpt-5-mini`, so model-generated video remains an optional experiment rather than a dependency.
- **2026-10-20:** Calibrated a compact Markov motion/type model from 120 StatsBomb Open Data matches (254,138 events), retained only aggregate parameters in `data/models/statsbomb_markov.json`, and wired the generator to produce correlated trajectories. Same-team mean spatial jumps fell by about 33% against the independent baseline; the full test suite and 20-match planted-shift stress check pass.
- **2026-10-20:** Corrected the pipeline to native StatsBomb `120x80` coordinates, added bounded StatsBomb 360 calibration from 32 matches (117,666 snapshots), and rewrote footage rendering around replay time with 22 role-aware markers plus a short event-time window. Raw 360 data remains external; only aggregate templates are stored.
- **2026-10-20:** Follow-up rendering redesign session: added `src/itg/pitch.py` as the canonical `120x80` coordinate seam; refit `data/models/statsbomb_markov.json` in native coordinates; added `scripts/fit_statsbomb_360.py` with parallel bounded downloads and produced `data/models/statsbomb_360_templates.json` from 32 matches, 117,666 snapshots, and 1,995,331 freeze-frame player observations. Added `src/itg/scene.py` for fictional role-aware 22-player scenes calibrated by 360 summaries, changed `src/itg/footage.py` to select events by replay timestamp and render a short time window, and replaced frame-by-frame random placement with smooth deterministic motion. Updated generator/interpret coordinate bounds, tests, and data-generation documentation. Validation: 9 tests pass; 22-player scenes stay in bounds; 0.1-second player movement is below 1 pitch unit; planted-shift detection remains valid. The result is better but still not sufficiently football-realistic: the next session should focus on possession-aware state, actual role identity/formation behavior, event timing/sequence fields, and a comparative model-quality evaluation.
