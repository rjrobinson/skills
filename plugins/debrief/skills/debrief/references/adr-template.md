# ADR template

**Read the gates before using this file.** An ADR is warranted only when a
decision passes all three:

1. **Hard to reverse** — undoing it costs a migration, a deprecation, or a
   coordinated change across teams.
2. **Surprising without context** — a competent reader would ask "why on earth is
   it like this?"
3. **A real tradeoff** — something was consciously given up.

Fails any one of them → no ADR. Most changes produce zero, and that is the
correct outcome. A directory of trivial ADRs trains people to skip the directory,
which costs you the one ADR that mattered.

**If the decision is still being made** rather than already made, stop and use
the `create-adr` skill instead — it runs the decision interview and writes into
the *project* repo. This template is for recording, in the user's second brain, a
decision the shipped change already embodies.

## Where it goes

`$DEBRIEF_HOME/<repo>/adr/NNNN-kebab-title.md`, where `NNNN` is the next 4-digit
number after the highest existing ADR in that directory, starting at `0001`.

Never into the project repo. Create the `adr/` directory lazily.

Keep the whole thing a 2-minute read. **2 pages max.**

---

```markdown
# NNNN. <Title as a decision, not a topic>

**Status:** Accepted
**Date:** YYYY-MM-DD

## Problem

The issue or pain being addressed, in plain terms. One short paragraph.

## Constraints

What actually limits the options: latency targets, budget, compliance, team
skills, deadlines, existing infrastructure. Real numbers where they exist —
"p99 under 200ms" beats "needs to be fast."

## Options

At least 2–3 realistic approaches, not just the favourite. One line of tradeoff
each: what it's good at, what it costs.

1. **<Option>** — good at X, costs Y.
2. **<Option>** — good at X, costs Y.
3. **<Option>** — good at X, costs Y.

## Decision

The path chosen and *why*, tied to a business, reliability, performance, or cost
need rather than taste. "Simplest" is not a why — simplest against which
constraint?

## Risks / Consequences

What could go wrong, and which tradeoffs are being consciously accepted. Every
real decision accepts something.

## Revisit when

A concrete, measurable trigger: a metric threshold, a scale point, or a
new-context event. "Revisit when the audit table passes 50M rows or a purge
exceeds 30s" — not "revisit later."
```

## The four ways an ADR stops being useful

Push back on all of them, including in your own draft:

- **One option.** If only the chosen path is listed, no comparison happened.
- **Vague constraints.** "Must scale" constrains nothing.
- **A "why" that's taste, not need.** Tie it to a constraint above.
- **An unmeasurable revisit trigger.** If nobody can tell when it fires, it never
  fires.
