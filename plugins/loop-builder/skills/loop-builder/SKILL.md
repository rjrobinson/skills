---
name: loop-builder
description: Use when designing, structuring, or hardening a Claude Code /loop — i.e. the user wants a recurring/self-paced task to run safely and asks for help shaping it ("help me set up a loop", "make this loop safe", "what should my loop prompt be", "turn this into a /loop", "design a loop that..."). Forces the request through 7 ingredients before emitting a runnable /loop invocation. Do NOT use to merely execute an already-specified loop like `/loop 5m /foo` — that is the built-in /loop skill's job.
risk: safe
source: rj
---

# loop-builder

Turn a vague "I want a loop that does X" into a loop that fails safe, proves its work, and stops on its own. The output is a filled spec plus a ready-to-run `/loop` invocation.

## When this fires vs. the built-in /loop

- **loop-builder (this skill)** = *design* the loop. The user is asking for help shaping a recurring task, or their loop idea is missing a queue / refusal rules / verification / exit.
- **built-in /loop** = *run* a loop the user already specified (`/loop 10m /babysit-prs`). Don't invoke loop-builder for that.

If the user hands you a fully-formed loop with all 7 ingredients already present, skip the interrogation and just emit the invocation.

## The job

A loop runs unattended. Every weakness compounds across ticks: a missing refusal rule means it acts on garbage every cycle; a missing verification gate means it ships broken work repeatedly; a missing exit means it never stops. So **do not emit a `/loop` until all 7 ingredients are filled.** Each ingredient maps to a specific failure mode it prevents.

Interrogate the request against the 7. For each one the user hasn't given you, either infer it from context (and state the assumption) or ask — but never leave one blank.

## The 7 ingredients

| # | Ingredient | What "good" looks like | Failure it prevents |
|---|-----------|------------------------|---------------------|
| 1 | **Objective** | One sentence, one outcome. If it needs "and", it's two loops. | Scope drift — the loop slowly does more than intended. |
| 2 | **Source of truth** | Where "the queue" lives, queried *every tick* (a PR list, a label, a failing-test list, a file). Never a snapshot taken once at start. | Acting on stale state; missing items added mid-run. |
| 3 | **One unit per tick** | Pick exactly one item per tick. Never batch. | One bad item poisons a whole batch; no clean point to stop or verify. |
| 4 | **The recipe** | Deterministic steps for that one item. Same input → same actions. | Nondeterministic behavior you can't predict, reproduce, or trust unattended. |
| 5 | **Refusal rules** | Explicit "skip when… / stop when…" so it fails safe by default. State what makes an item ineligible and what makes the whole loop abort. | Acting on items it shouldn't; charging ahead through errors. |
| 6 | **Verification gate** | Prove the change before any outward action (tests pass, diff matches intent, build green). Outward = commit, push, comment, send, deploy. | Shipping broken work every tick, multiplied by the cadence. |
| 7 | **Exit + cadence** | When to stop (queue empty N ticks / count reached / budget hit) **and** how long to wait between ticks. | Infinite loops; hammering a resource; burning tokens. |

### Ingredient 7 — picking the cadence

Map cadence to what the loop is actually waiting on, not a round number. The Anthropic prompt cache has a ~5-minute TTL, so:

- **Self-paced (no interval)** — let the model decide each tick via `ScheduleWakeup`. Best when "is there work?" depends on judgment.
- **60–270s** — cache stays warm. Use only when actively polling external state the harness can't notify you about (CI run, deploy, remote queue).
- **300–3600s** — pays a cache miss but right when checking sooner is pointless. Default idle tick: **1200–1800s**.
- **Avoid exactly 300s** — worst of both: cache miss without amortizing it. Drop to 270s or commit to 1200s+.

If the loop is waiting on harness-tracked work (a background Bash/Agent/Workflow you started), you'll be re-invoked on completion — don't poll. Set a long fallback only.

### Exit condition — make it concrete

Pick one and bind it to the source of truth:
- **Drain**: stop after the queue returns empty for K consecutive ticks (K≥2 to absorb late arrivals).
- **Count**: stop at N items processed.
- **Budget**: stop when remaining token budget drops below a floor.
- **Deadline/condition**: stop when an external state flips (CI green, PR merged).

A loop with no written exit is a bug, not a loop.

## Output format

Produce this, then the invocation:

```
Objective:        <one sentence>
Source of truth:  <where the queue lives; how it's queried each tick>
Unit per tick:    <the one item; selection rule if queue has many>
Recipe:           1. … 2. … 3. …   (deterministic)
Refusal rules:    skip when … ; stop when …
Verification:     <proof required before any outward action>
Exit:             <drain/count/budget/condition>
Cadence:          <self-paced | Ns> — <why, in cache-window terms>
```

Then the runnable command:

```
/loop [interval] <prompt that encodes recipe + refusal + verification + exit>
```

The `/loop` prompt itself must restate the refusal rules, verification gate, and exit — the running loop only sees the prompt, not this spec.

## Refusal (this skill's own fail-safe)

Do not emit a `/loop` invocation if, after asking, the request still lacks:
- a verification gate but performs an **outward action** (commit/push/comment/send/deploy), or
- any exit condition.

Surface the gap instead of guessing a default for those two — they're the ones that do real damage unattended.

## Worked example

Request: *"Loop through my open PRs and fix the failing CI."*

```
Objective:        Get each of my open PRs to green CI.
Source of truth:  `gh-axi pr list --author @me`, re-queried every tick.
Unit per tick:    One PR — oldest with red CI not touched this run.
Recipe:           1. Read failing job logs. 2. Reproduce locally. 3. Apply
                  minimal fix. 4. Run the failing test(s).
Refusal rules:    skip when failure is infra/flaky (not my diff) or PR is
                  draft; stop when the same PR fails twice in a run.
Verification:     Targeted failing test(s) pass locally before pushing.
Exit:             Drain — stop after 2 consecutive ticks find no red PRs.
Cadence:          Self-paced — "is CI red?" needs a judgment call, and CI
                  runs take minutes; poll at ~270s when watching a run.
```

```
/loop Re-query `gh-axi pr list --author @me` each tick. Pick the oldest PR
with red CI you haven't touched this run. Read the failing logs, reproduce
locally, apply the minimal fix, and run the failing test(s). SKIP infra/flaky
failures and drafts. STOP a PR after two failures in this run. Only push once
the failing test passes locally. STOP the loop after two ticks with no red PRs.
```

Note: no interval passed → self-paced. The prompt restates refusal + verification + exit because that's all the running loop sees.
