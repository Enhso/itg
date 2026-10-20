# ITG-IIMA demo video script (and product spec for the week)

Draft 1, 2026-10-20. Target length 1:50, hard limit 2:00 (rule 4.4: "less than two minutes"; judges need not watch past 2:00).

How to use this file: the script is the spec. A feature that no shot needs is not built this week. A shot that needs something PLAN.md does not list is flagged in section 3 and not added quietly.

Conventions:
- `[N]`, `[M]`, `[k]` are filled from the real run after Friday's detector score. Never write a number the screen does not show.
- Figures such as 61', 38% to 71%, "81 vs 71" and the 1-1 scoreline are targets for the demo match. If the captured match differs, change the voiceover to match the screen. The screen wins over the script.
- Command and tool names (`itg generate`, `get_window_stats`) are illustrative.
- Fictional only: Corvane FC (home) vs Tessaly Athletic (away), forward Idris Kovac. Names are generator config, not hard-coded, so they can be swapped (see open question 5).

## 1. Shot list

| # | Time | Beat | VO words |
|---|---|---|---|
| 1 | 0:00-0:08 | Hook | 18 |
| 2 | 0:08-0:19 | Ingest | 24 |
| 3 | 0:19-0:30 | Interpret | 25 |
| 4 | 0:30-0:58 | Explain (multi-agent core) | 55 |
| 5 | 0:58-1:10 | Render | 18 |
| 6 | 1:10-1:30 | Personalize | 38 |
| 7 | 1:30-1:44 | Stack and deployment | 26 |
| 8 | 1:44-1:50 | Close | 8 |
| | **1:50** | | **about 212** |

212 words over 110 s is about 116 wpm. That leaves roughly 45 words of slack against the 260-word budget, so dense screens (shots 3, 4, 5) get silent beats to read.

### Shot 1: Hook (0:00-0:08)
- **On screen:** 0:00-0:03, the web second-screen header fills the frame: "Corvane FC 1-1 Tessaly Athletic, full time". 0:03-0:08, pull back to the 90-minute momentum strip. It swings hard toward Tessaly at 61'. A card pops up under the swing: "61'  The game turned. Tessaly Athletic start pressing high."
- **VO:** "This match ended one-one. Scorelines tell you what happened. ITG-IIMA tells you when the game turned, and why."
- **Proves:** UX and Presentation (the video states the value in the first 8 s). Challenge 4.1 framing ("football stories do not start and end with the scoreline"). By 0:10 a skimming judge has seen the finished product and the pitch line.

### Shot 2: Ingest (0:08-0:19)
- **On screen:** Terminal, split. Left: the generator streams JSONL events at replay speed (pass, pressure, tackle lines with timestamps and fictional player names). Right: `ground_truth.json` with one entry highlighted: minute 61, Tessaly Athletic, high press. Lower-third caption: "Synthetic data. Fictional clubs and players."
- **VO:** "ITG-IIMA starts with a synthetic match engine. It streams events, and plants a tactical shift on purpose: Tessaly start pressing high at minute sixty-one."
- **Proves:** Stage Ingest (4.1(i)(a)). Technological Implementation: "creativity and optimized synthetic data creation". Rule 4.7 (synthetic data only).

### Shot 3: Interpret (0:19-0:30)
- **On screen:** Terminal. `itg detect demo` prints the moment table; the 61' row is highlighted: "regime change, TES high press, field tilt 38% to 71%, pressure events per 5 min 4 to 11". Then `itg score` prints "[N] of [M] planted shifts found within +/-[k] min".
- **VO:** "Plain code, not a language model, computes the stats and spots the change at minute sixty-one. Against the answer key: [N] of [M] shifts found."
- **Proves:** Stage Interpret (4.1(i)(b)). Explainability (4.1(iv): control vs chaos, pressure changes). Technological Implementation: a measured result against ground truth, and a clean split between deterministic stats and LLM prose.

### Shot 4: Explain (0:30-0:58)
The multi-agent core. This is the longest shot on purpose.

**4a (0:30-0:39) Analyst drafts**
- **On screen:** Trace view opened on the 61' moment. Three lanes: Analyst, Fact-checker, Persona. A shared "MatchState" node sits between them. The Analyst lane shows the tool call `get_window_stats(team=TES, 61'-66')`, then its draft text, which contains "field tilt 81%".
- **VO:** "Now the agents. An Analyst agent queries the shared match state and drafts why this moment mattered."
- **Proves:** Multi-Agent: distinct roles, shared state.

**4b (0:39-0:51) Fact-checker rejects, Analyst recovers**
- **On screen:** A visible label, "fault injected: Analyst figure altered". The Fact-checker lane calls the same `get_window_stats`. Red verdict: "Rejected: draft says field tilt 81%, match state says 71%". An arrow returns to the Analyst lane. The Analyst's revised draft shows 71%. Green verdict: "Approved: 5 of 5 claims verified".
- **VO:** "To test the loop, we plant a bad number: eighty-one percent. The Fact-checker re-queries the data, finds seventy-one, and sends the draft back. Only a verified rewrite moves on."
- **Proves:** Multi-Agent: handoffs (Analyst to Fact-checker and back), failure recovery. Agentic Design (20%): a verifier with its own tool access, not a self-grading model.

**4c (0:51-0:58) Card with evidence**
- **On screen:** The approved overlay card at 61'. Each claim has an evidence chip under it (for example "field tilt 71%, 61'-66'", "pressure events 11 per 5 min"). *Stretch:* a caption "First drafts rejected: [k] of [N] across [M] matches".
- **VO:** "Every claim on the final card cites its evidence."
- **Proves:** Stage Explain (4.1(i)(c)). Explainability. Multi-Agent: an end-to-end outcome (verified, cited output). Enterprise-trust story for the pitch text.

### Shot 5: Render (0:58-1:10)
- **On screen:** 0:58-1:03, the second screen replays the match at speed: timeline moves, momentum strip fills, cards appear at their timestamps. 1:03-1:10, a terminal pane beside it runs `curl .../overlays | jq` and shows the JSON for the 61' card: start time, end time, card type, text, evidence array.
- **VO:** "The verified card becomes timed, machine-readable overlay data a broadcast graphics engine could render, and this second screen."
- **Proves:** Stage Render (4.1(i)(d): "timed and machine-readable ... synchronized graphical overlays"). UX and Presentation, including "balanced blend of frontend and backend". Real-World Impact (a studio or broadcast use). The VO says "could render" because no graphics-engine integration exists.

### Shot 6: Personalize (1:10-1:30)

**6a (1:10-1:18) Two personas**
- **On screen:** The same 61' card. Toggle Analyst, then Casual fan. Analyst view: figures, window, evidence chips. Fan view: one plain sentence, no jargon. The trace corner shows the handoff "Fact-checker to Persona (persona=fan, lang=en)".
- **VO:** "Same verified facts, two experiences. The analyst gets the numbers. The casual fan gets one plain sentence."
- **Proves:** Stage Personalize (4.1(i)(e): "two genuinely different experiences"). Multi-Agent: third role and handoff.

**6b (1:18-1:24) Language**
- **On screen:** Language switch from EN to FR. The card re-renders in French. An English gloss appears as a lower-third, added in the edit.
- **VO:** "Switch language, and the same card reads in French."
- **Proves:** Multi-language storytelling (4.1(vi)). Rule 4.9 (non-English material needs an English translation).

**6c (1:24-1:30) Player focus (stretch)**
- **On screen:** Pick "Idris Kovac" from a favourite-player selector. The card list narrows to moments involving him, and one card names him with a stat from the match state.
- **VO:** "Pick a favourite player, and the match is told around that player."
- **Proves:** Personalize: favourite player and player-focused mode (4.1(i)(e)).
- **If cut:** delete 6c and its VO. The video ends at 1:44 and shot 7 follows 6b. Do not pad.

### Shot 7: Stack and deployment (1:30-1:44)
- **On screen:** Four cuts of about 3.5 s each.
  1. VS Code with Copilot Agent Mode mid-task (b-roll from a daily clip).
  2. The agent definitions file, showing Analyst, Fact-checker and Persona with their instructions and tools, then the Foundry project's model deployment page.
  3. Azure portal: the Container App, status Running, public URL visible.
  4. A real phone screen recording of the public URL playing the demo match.
- **VO:** "Built with GitHub Copilot Agent Mode. Three agents on Microsoft Agent Framework, models on Microsoft Foundry, deployed to Azure Container Apps, and open on any phone."
- **Proves:** Technological Implementation (hero technologies). Rule 4.4 ("footage that shows the Project functioning on the device and platform for which it was built"). Real-World Impact (deployed, reachable). Category fit (Multi-Agent on Agent Framework).

### Shot 8: Close (1:44-1:50)
- **On screen:** End card. Product name, the pitch line, repo URL, live demo URL. Footer: "All clubs, players and data are synthetic."
- **VO:** "ITG-IIMA. Explanations you can check, for every fan." (VO ends at about 1:48; the card holds 2 s in silence.)
- **Proves:** Rule 4.4 (public repo and demo URLs shown). Rule 4.7 (disclosure). Real-World Impact (trust).

### Capture conventions
- Record at 1080p. Browser zoom at 125% or more, terminal font 18 pt or larger, so text survives YouTube compression.
- Use a clean browser profile. Blur or crop subscription IDs, keys, endpoints and email addresses in the Azure and Foundry screens.
- No music (rule 4.4). Voice: see open question 7.
- Take the trace footage from a genuine run, with the fault injected. Do not mock a trace the app cannot produce.
- Never show or say "Premier League". Never expand the "ITG" part of the name in the video.

## 2. Coverage checklist

The "Clip" column is for ticking off raw footage as it is recorded.

### Five required stages (4.1)

| Stage | Shot | What the viewer sees | Clip |
|---|---|---|---|
| Ingest | 2 | JSONL event stream and the planted-shift answer key | [ ] |
| Interpret | 3 (and 1) | Rolling stats, detected regime change, detector score | [ ] |
| Explain | 4 | Analyst draft, fact-check, evidence-cited card | [ ] |
| Render | 5 (and 1) | Second screen plus timed overlay JSON | [ ] |
| Personalize | 6 | Analyst vs fan, EN vs FR, player focus (stretch) | [ ] |

### Best Multi-Agent System criteria (4.2)

| Criterion | Shot | What the viewer sees | Clip |
|---|---|---|---|
| Distinct roles | 4a, 6a | Three named lanes (Analyst, Fact-checker, Persona), each with a different job | [ ] |
| Shared state | 4a, 4b | Both agents call the same `get_window_stats` on one MatchState node | [ ] |
| Handoffs | 4b, 6a | Analyst to Fact-checker, back to Analyst, then Fact-checker to Persona | [ ] |
| Failure recovery | 4b | Rejected draft (81% vs 71%), revision, approval | [ ] |
| End-to-end outcome one agent could not reach | 1 to 6 as one chain; 4c stretch stat | Raw events become a verified, cited, personalized card in one run | [ ] |

The last row is argued, not proven. One rejected draft shows the checker works. It does not show a single agent would do worse. The optional stat in 4c ("first drafts rejected: [k] of [N]") is the only measured support. See open question 9.

### Microsoft technologies (4.4: the pitch must name them)

| Technology | Shot | What the viewer sees | Clip |
|---|---|---|---|
| Microsoft Foundry | 7 (cut 2) | Foundry project's model deployment page; VO names it | [ ] |
| Microsoft Agent Framework | 7 (cut 2), 4 | Agent definitions in code; trace lanes; VO names it | [ ] |
| Azure Container Apps | 7 (cuts 3, 4) | Container App running, public URL on a phone | [ ] |
| GitHub Copilot (Agent Mode) | 7 (cut 1) | VS Code Agent Mode clip from a daily b-roll recording | [ ] |

Not in the video: Azure MCP (stretch), Azure databases (none planned). Cost controls (scale to zero, cached replays, rate-limited new-match button, token logging) go in the written pitch, not the video.

### Rules and judging criteria not covered above

| Item | Shot | How |
|---|---|---|
| Under 2:00 (4.4) | all | Total 1:50 |
| Functions as depicted (4.3) | all | Every shot is captured from the running app or terminal; the injected fault is labelled |
| No third-party trademarks or music (4.4) | all | Fictional names, no music, no league marks |
| English (4.9) | 6b | English VO; French card has an English gloss |
| Technological Implementation | 2, 3, 7 | Planted-truth generator, measured detector, hero tech |
| Agentic Design and Innovation | 4, 6a | Verifier with tool access, planted-error test, three-role chain |
| Real-World Impact | 5, 7, 8 | Overlay data for broadcast, deployed URL, checkable claims. Problem significance is carried by the written pitch |
| UX and Presentation | 1, 5, 6 | Hook, second screen, clearly different persona views, both frontend and backend on screen |
| Adherence to Category | 4 | Multi-Agent criteria shown in order, in one continuous shot |

## 3. What this script commits us to

Must = in PLAN.md's minimum winning slice. Stretch = in PLAN.md's stretch list or, where flagged, new and droppable.

| # | Feature the video needs | Shot | Priority | In PLAN.md? |
|---|---|---|---|---|
| 1 | Generator with fictional clubs and players, streaming JSONL at replay speed | 2 | Must | Yes (Ingest) |
| 2 | Planted shift plus `ground_truth.json` | 2, 3 | Must | Yes |
| 3 | Rolling stats (field tilt, pressure events) and regime detector | 3 | Must | Yes (Interpret) |
| 4 | Detector output that prints before/after window values per moment | 3 | Must | Implied: the same values are the Fact-checker's evidence. Flag F4 |
| 5 | Score command: planted shifts found within a tolerance | 3 | Must | Yes (Fri check) |
| 6 | Analyst and Fact-checker agents reading one MatchState via tools, with the reject-and-revise loop | 4 | Must | Yes |
| 7 | Persona agent (analyst vs fan, EN plus one other language) | 6 | Must | Yes |
| 8 | Overlay card with an evidence chip per claim | 4c, 6a | Must | Yes ("every claim cites the stats") |
| 9 | Timed overlay JSON endpoint, curl-able | 5 | Must | Yes (Render) |
| 10 | Web second-screen: scoreline header, timeline, momentum strip, replay, cards, persona and language controls | 1, 5, 6 | Must | Yes. The scoreline header is not named but trivial |
| 11 | Public URL on Azure Container Apps that works on a phone | 7 | Must | Yes (Sun check) |
| 12 | Raw clips: daily b-roll including a Copilot Agent Mode session; Foundry and Container Apps portal captures | 7 | Must | Yes (daily clip habit). Portal captures are new footage, not features |
| 13 | **Agent trace view**: lanes per agent, shared MatchState node, tool calls, verdict chips | 4, 6a | Must (minimal form) | **No. Flag F1** |
| 14 | **Visible fault injection**: a flag or button that corrupts one Analyst figure, with an on-screen label | 4b | Must | **Partly.** PLAN's Saturday check needs a "planted wrong number"; the label and a way to trigger it on demand are new. Flag F2 |
| 15 | Player-focus selector and re-ranked cards | 6c | Stretch | Yes (stretch #1) |
| 16 | First-draft rejection stat across the precomputed matches | 4c | Stretch | **No. Flag F3** |

Flags, with a recommended handling for each:

- **F1, trace view.** PLAN's Render list is timeline, momentum strip and overlay cards. The multi-agent criteria need on-screen proof of roles, shared state and handoffs. Recommendation: have the agents emit structured trace events from Saturday (they should anyway, for debugging). Render them as a UI drawer on Sunday. If Sunday runs short, fall back to a `rich` terminal trace with the same lanes. Shots 4 and 6a work with either.
- **F2, fault injection.** Without it, the rejection can only be captured if the model happens to get a number wrong on camera. With it, the take is repeatable. The label keeps the video honest under rule 4.3.
- **F3, rejection stat.** Count of first drafts rejected, taken from the loop's own logs. If the count is zero, drop the caption.
- **F4, before/after values.** Confirm the detector's moment object carries them. Shot 3 and the Fact-checker both need them.
- **F5, demo match shape.** The script wants an away-team high press planted at about 61', visible in the stats, with the equaliser after it. The match comes from the precomputed set on Saturday, so choose a seed that tells this story. If no seed does, any final score works; only the hook's first sentence changes.

If time cuts the scope, cut in this order: 4c stat, 6c player focus (and its 6 s), then the F1 UI drawer (use the terminal trace). Do not cut the fault injection or the Fact-checker loop. Shot 4 is the prize category.

## 4. Open questions (places I guessed)

1. **Second language.** Settled: French (Hatim reads it). Latin script, so no right-to-left layout work.
2. **Labelled fault injection.** I assumed the bad number is injected and labelled. The alternative (wait for a natural error) is unreliable. Confirm.
3. **Trace as UI or terminal.** I assumed the UI drawer is preferred and a terminal trace is acceptable. Confirm the fallback.
4. **Placeholder numbers.** 61', 38% to 71%, 81 vs 71, 1-1 and `[N] of [M]` are targets. The voiceover must be re-read against the final capture before recording audio.
5. **Fictional names.** Corvane FC, Tessaly Athletic and Idris Kovac are my inventions. I did not search for collisions with real clubs or players. A 30-second search before filming would close this, since rule 4.4 bans third-party marks.
6. **Microsoft names on screen.** Settled: showing the sponsor's product names and portal screens is fine, since rule 4.4 requires naming the Microsoft technologies used. Still never show the Premier League name.
7. **Voice.** The script is voice-agnostic. Hatim's own voice or a synthetic voice both avoid copyrighted audio. Decide before Monday's edit.
8. **Replay vs live.** The public demo replays cached output. I wrote the VO as "streams" and "replay" and avoided "live". I assumed the trace in shot 4 comes from a genuine run that the cache then replays. Confirm the "new match" button shows the same trace UI, or the shot should say nothing about it.
9. **Single-agent claim.** The category asks for an outcome "a single agent could not achieve as effectively". The video can argue this but not prove it. A small ablation on Saturday (Analyst alone vs Analyst plus Fact-checker over the precomputed moments, counting wrong figures) would give a real number for 4c and the pitch. Worth about 20 minutes if the loop logs outcomes.
10. **Timing slack.** The cut is exactly 1:50 with no spare seconds. Dropping 6c gives 6 s back. Otherwise the edit should trim silences before it trims words.
