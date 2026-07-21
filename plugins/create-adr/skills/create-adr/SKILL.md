---
name: create-adr
description: >-
  Interactively facilitate writing a short Architecture Decision Record (ADR).
  Use when the user wants to make and document an upfront technical or
  architecture decision — capturing the problem, constraints, 2-3 realistic
  options with tradeoffs, the chosen decision and why, risks/consequences
  consciously accepted, and a concrete revisit trigger. Trigger on:
  /create-adr, "create ADR", "write an ADR", "architecture decision record",
  "document this decision", "let's decide how to build X".
---

# create-adr

Run a Staff+ decision interview, then write a short ADR file. The ADR is the
receipt: "here's what we did, why we did it, and when we'll know it's wrong."

**This is NOT RPI.** No codebase research, no planning docs, no implementation.
Just surface the decision, weigh the tradeoffs, and leave the record. Keep the
whole thing a 2-minute read — **2 pages max.**

## The ADR shape

Six sections, in this order. Nothing more:

1. **Problem** — the issue/pain being addressed, in plain terms.
2. **Constraints** — what limits the options: latency, budget, compliance,
   team skills, deadlines, existing infra.
3. **Options** — **at least 2-3 realistic approaches**, not just the favorite.
   One line of tradeoff each (what it's good at / what it costs).
4. **Decision** — the path chosen, and *why* — tie it to a business or
   reliability/performance need, not just taste.
5. **Risks / Consequences** — what could go wrong and which tradeoffs are being
   consciously accepted.
6. **Revisit when** — a concrete trigger to re-evaluate: a metric threshold,
   a scale point, or a new-context event. Must be measurable, not "someday."

Plus a one-line header: title, status (`Proposed` → `Accepted`), and date.

## How to run the interview

Be a thinking partner, not a form. Ask in small batches, adapt to answers, and
push where a Staff+ reviewer would push. Don't dump all six questions at once.

Suggested flow:

1. **Frame the problem.** Ask what they're building/changing and what pain
   forces a decision now. Restate it in one sentence and confirm.
2. **Pin the constraints.** Ask what actually limits the options — dig for the
   real numbers (latency target, budget, deadline, compliance, team skill). Use
   `AskUserQuestion` when the constraints fall into clear buckets.
3. **Generate options.** Propose 2-3 realistic approaches with one-line
   tradeoffs — including ones they *didn't* already pick. If they only have one
   idea, add credible alternatives so the record shows real comparison. This is
   a good place for `AskUserQuestion` (options as choices, one clearly framed
   per option, tradeoffs in the descriptions).
4. **Force the decision.** Get them to commit to one option and articulate the
   *why*. Push if the reasoning is thin ("because it's simplest" isn't a why —
   simplest for what constraint?). Tie it back to reliability/performance/cost.
5. **Name the risks.** What breaks, what backlog grows, what they're knowingly
   trading away. Every real decision accepts something.
6. **Set the revisit trigger.** Insist on a measurable one. "Revisit when retry
   backlog > 100k or queue throughput < 1k msg/sec" — not "revisit later."

Push back on: only-one-option ADRs, vague constraints, "why" that's taste not
need, and un-measurable revisit triggers. Those are the four ways an ADR stops
being a receipt.

## Where to save it

1. Look for an existing ADR directory in the repo, in this order:
   `docs/adr/`, `doc/adr/`, `docs/architecture/decisions/`, `adr/`,
   `docs/decisions/`. Use the first that exists.
2. If none exists, propose `docs/adr/` and confirm before creating it.
3. Filename: `NNNN-kebab-title.md`, where `NNNN` is the next 4-digit number
   after the highest existing ADR (start at `0001`). E.g. `0007-stream-distribution.md`.

Write the file, then show the path. If the user only wanted to talk it through,
skip the file — but the default deliverable is the written ADR.

## Template

```markdown
# NNNN. <Title>

- Status: Proposed
- Date: YYYY-MM-DD

## Problem
<1-3 sentences.>

## Constraints
- <constraint with real numbers where possible>

## Options
1. **<Option A>** — <one-line tradeoff>
2. **<Option B>** — <one-line tradeoff>
3. **<Option C>** — <one-line tradeoff>

## Decision
<Chosen option> — <why, tied to a constraint/business/reliability need>.

## Risks / Consequences
- <what could go wrong; what tradeoff is consciously accepted>

## Revisit when
- <measurable trigger: metric threshold, scale point, or new-context event>
```

## Example (for reference, don't copy verbatim)

> **Problem:** Notification retries are overwhelming the database.
> **Constraints:** Retries under 100ms avg; latency < 500ms for 99% of users.
> **Options:** (1) DB table — simple, cheap, risky. (2) Redis buffer — fast, no
> durability. (3) Queue + worker pool — reliable, more infra.
> **Decision:** Queue + worker pool — meets the latency target without risking
> durability under spike load.
> **Risks:** Queue backlog can grow unbounded → needs monitoring + retry caps.
> **Revisit when:** Retry backlog > 100k or queue throughput < 1k msg/sec.

## Scope

Do the decision and the document — nothing else. A future staff-engineer skill
handles organizing/indexing ADRs over time; this skill just produces clean,
comparable records for it to work with.
