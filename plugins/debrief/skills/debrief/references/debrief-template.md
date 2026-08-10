# Debrief template

Copy this into `$DEBRIEF_HOME/<repo>/debriefs/YYYY-MM-DD-<slug>.md` and fill it.
Never into the project repo.

Delete any section that genuinely does not apply rather than padding it — a
`## Blast radius` reading "n/a" is worse than no heading.

Depth follows the change. A 10-line fix fills this out in half a page. Do not
stretch a small change to fit the shape of the template.

**Comment mode** uses the same file with a different centre of gravity: keep the
header, the elevator pitch, and the diagrams if any, then use the *Review
decisions* section at the bottom as the body and drop the layers that don't apply.
Name the file `YYYY-MM-DD-<slug>-review.md`.

---

```markdown
# <Change title in plain language>

**Date:** YYYY-MM-DD
**Author:** <name>
**Change:** <PR link, branch, or commit range — the thing a reader can go open>
**Ticket:** <link, or "none">

## Elevator pitch

Two or three sentences. What was broken or missing, what this does about it, and
the one-line why-this-way. Written to be *spoken* — if it doesn't survive being
read aloud, rewrite it.

## Standup version

The problem with enough mechanism to be credible:

- **How it showed up:** bug report, failing metric, blocked feature, or a smell
  someone noticed.
- **Root cause:** what was actually wrong, as distinct from where the symptom
  appeared.
- **The fix, in shape:** the approach in two or three sentences.
- **What got touched:** the files or subsystems, with a word on why each.

## Deep dive

### The problem's anatomy

Why did this problem exist? Name the earlier decision, missing abstraction, or
changed requirement that created it. If a past call was reasonable at the time
and the world moved, say so — that is usually both truer and more useful than
"the old code was bad." If the history is genuinely unknown, write that here and
list it under Open questions. Do not invent a rationale.

### The solution's mechanism

Walk the control flow or data flow of the new code with `file:line` citations.
Name the key functions, types, and boundaries. For a refactor, state the
invariant the new shape protects that the old shape didn't.

### Alternatives considered

At least two real options with the honest reason each lost. Options a reviewer
would actually raise — not strawmen.

| Option | Why it lost |
|---|---|
| | |
| | |

### Tradeoffs accepted

What got worse or riskier on purpose: performance, complexity, a new dependency,
a migration burden, more surface to maintain. A change presented as costless is
a change nobody has finished thinking about.

### Risks and unknowns

What could break, what wasn't tested, what assumption this leans on. Be specific
about the assumption — "assumes a user belongs to exactly one account" is useful;
"assumes the data is well-formed" is not.

**Watch after deploy:** the specific metric, log line, or dashboard.

### Blast radius

What else touches this code path, and whose code or team is affected. Name the
callers. If a shared file changed, say who owns it.

## Diagrams

<!-- one or two; before/after pair for refactors. See references/mermaid-guide.md -->

## Anticipated questions

The questions a skeptical reviewer will ask, with answers strong enough to use.
After a verification round, **add every question that was answered badly**, plus
the strong answer — this section should reflect where the real difficulty was,
not where it was expected to be.

**Q:**
**A:**

**Q:**
**A:**

## Review decisions

<!-- Comment mode's main body. One row per item. Drop this section in change mode
     unless the change drew review. -->

Reviewer(s): <names> · Round: <date>

| # | The claim, in plain words | Verdict | Decision | Why |
|---|---|---|---|---|
| C1 | | verified / refuted / unresolved | fix now / log / decline | |
| C2 | | | | |

**Declined, with the tripwire.** For each decline: what the reviewer was right
about, why it isn't worth acting on now, and the measurable condition that would
change the answer. This is the part that gets asked about later.

**Logged for later.** What was deferred and the trigger that makes it urgent.

**Refuted.** Any claim the code disproved, and where. Worth keeping — it's
evidence for reading the code rather than the comment next time.

## Open questions

Things genuinely undecided or unknown, including any history that couldn't be
reconstructed. An honest gap here is worth more than a confident guess, because a
guess gets repeated in review as fact.
```
