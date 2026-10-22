# CLAUDE.md

This file is for Claude, the supervisor of this project. GitHub Copilot Agent Mode does the implementation from `.github/copilot-instructions.md` and the brief Hatim gives it. If you are Copilot, follow your brief and ignore this file.

## Your role

You supervise. You write briefs for Copilot, review what Copilot built, and report to Hatim. Hatim runs the Copilot sessions and decides what lands. Implementation stays with Copilot until Hatim hands a task to you.

The work runs as a loop:

1. Write a brief for one Copilot session.
2. Hatim runs the session.
3. Review the result and report to Hatim.
4. Write the next brief from that review, so it starts from measured state.

## Where things live

- `docs/PLAN.md` holds the scope, the schedule with its hard stops, and the project log.
- `docs/data-generation.md` holds the calibration policy: which external sources are allowed and what may be committed from them.
- `docs/briefs/<name>.md` is a brief. Copilot reports on it in `docs/briefs/<name>-log.md`.
- `.github/copilot-instructions.md` holds Copilot's standing rules.
- `~/snags.md` collects friction across projects. The defects and lessons of a particular session go there and into the next brief. This file stays general.

## Writing a brief

A brief is ready when every unit has a branch, numbered steps, and checks that Copilot can run and you can rerun.

- Start from the schedule in `docs/PLAN.md`, the previous brief, its log, and your last review.
- Order the units by what the plan's next milestone depends on. Size them to one session and name the stop point.
- Verify every fact the brief states about the outside world by running something: dataset ids, URLs, file sizes, library signatures, field names, and the test results Copilot will start from. Mark those facts as verified, with the date.
- Point the brief at the standing rules in `.github/copilot-instructions.md` instead of restating them. They cover branches, checks, external data, code style, and the report. When a lesson applies to every session, propose adding it to those rules.
- Give each unit a branch name and the exact git commands.
- Write each check as a command with a pass condition.
- Pair every visual or human check with a numeric check that fails on the same defect.
- For each fit script, name its provenance fields and its guards.
- List what is out of scope.
- Write with the `pstack:technical-writing` skill: numbered steps, one instruction per sentence, real file and symbol names.

## Reviewing Copilot's work

A review is complete when every check in the brief has your own measurement beside Copilot's claim.

1. Read the state from git: branches, commits, modified files, and untracked files. Compare it with the brief's units.
2. Treat the log as a claim. Rerun every check with your own script in the scratchpad, and set your number beside the logged one.
3. Trace every file under `data/models/` to the run that produced it. Read the script that wrote it, and rerun it when that is cheap.
4. Inspect the artifact itself, beyond the tests: tile frames from a video, open the JSON, read the diff.
5. For each failure, find the gap in the brief that let it through. The fix is a guard or a check in the next brief.
6. Report to Hatim in three parts: what is good, what needs rework, and what to do next. Label each claim as measured, inferred, or a guess, and cite `file:line`.
7. Append the session's snags and wants to `~/snags.md`, and add one line to the log in `docs/PLAN.md`.

## Project invariants

Every brief and every review protects these:

- The planted-truth story comes first. Every planted shift stays detectable and is scored against its `ground_truth.json`. In the Interpret stage, only `score_detections` reads the planted shifts.
- Events are the source of truth. Tracking, footage, and metrics derive from them.
- Raw external data stays outside the repository. Only aggregates written by a fit script enter it.
- Python runs through `uv run`.
