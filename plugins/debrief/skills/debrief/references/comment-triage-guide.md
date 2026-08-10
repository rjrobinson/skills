# Comment triage guide

Risk calibration and decision vocabulary for comment mode.

## The problem this solves

Code review used to be bounded by a human's attention. It isn't any more.
Reviewers paste agent-generated findings, and agent review has **no termination
condition** — there is always another finding, and the next pass will produce
more. A human reviewer stops because they form a judgment that the code is good
enough; that stopping function *is* the review. Remove it and "an AI found
something" becomes an infinitely renewable blocking resource.

So: **the number of findings carries no information about whether the code should
ship.** What carries information is, per item, whether the claim is true and what
it costs. That is the work.

Two consequences for how you behave here:

- Never treat volume as severity. Nine items is what a tool emits when pointed at
  a data-retention path; it is not nine problems.
- Never treat a severity label as a verdict. "blocking" is a claim, and a claim
  needs someone holding it. If the reviewer relayed it without holding it, the
  user is entitled to ask which ones they actually block on — and that is a normal
  collegial question, not an accusation.

You are the same kind of tool that generated the findings. Say so when it's
relevant. The defense against unbounded machine output is not rejecting it, it's
insisting each item earns its place.

## Claim types

Classify before triaging. The type usually decides the outcome.

| Type | Test | Usual outcome |
|---|---|---|
| **Current defect** | breaks today, for a real user/account/request | fix now |
| **Latent defect** | correct today; breaks under conditions that will arrive (scale, a rescue, a second caller) | fix if cheap, else log with the trigger |
| **Hardening** | no defect; closes a hole that needs future code to become reachable | log, unless trivial |
| **Convention / taste** | style, naming, structure with no behavioral claim | fix if you agree, decline with a reason if not |
| **Question** | asks, doesn't assert | answer it; no code change |

Watch for a comment's own text conceding it isn't current — "nothing is missed
today", "behaviour is fine today", "harmless for now". That concession is the most
useful fact in the whole item, and reviewers often bury it in the last paragraph.
Surface it.

## Verifying a claim

Open the file. Every time. The three outcomes:

- **Verified** — the code does what the comment says. Cite the line.
- **Refuted** — the code disproves it. Say so plainly and show why. A
  confident-sounding claim the code contradicts is itself a finding, and letting
  it stand unchallenged teaches the user to distrust their own reading.
- **Unresolved** — needs data you don't have (production behavior, real volumes).
  Say which data would settle it rather than guessing.

Common ways an agent-generated finding is wrong: it cites a line that moved, it
describes a code path the guard above it prevents, it assumes a default the
project overrides, or it reasons about a framework behavior that differs in this
version. All of those are only visible by reading the code.

## Cost, on both sides

Both halves matter. An item with a real cost of ignoring and a trivial fix cost
is easy; the judgment is in the rest.

**Cost of ignoring** — name the failure and who feels it. Useful: "a hard-delete
that times out fails the erasure permanently, and the worker is `retry: false`."
Useless: "could cause issues at scale." If you cannot name the failure, the item
is probably hardening, not a defect.

**Cost of fixing** — effort, but also: new risk, new surface, new indexes on a
write path, a migration, a dependency, more code to maintain, and *noise*. An
alarm that fires on a known-benign case every deploy costs more than it's worth,
because it trains people to ignore alarms.

## The stop rule

State it out loud so the round can end:

- **Fix now** — cheap *and* closes a failure with real cost.
- **Log** — real, but conditional on scale or on code that doesn't exist yet.
  Record the trigger that would make it urgent.
- **Decline** — the cost of fixing exceeds the risk of not.

And the gate: **merge on a human judgment that residual risk is acceptable, not
on the absence of tool output.** A reviewer can always generate more findings;
that cannot be the condition for shipping.

## Recommending a different fix

When the reviewer's suggested fix is worse than an alternative, say so and show
both with the tradeoff. Adopting a suggestion verbatim because it came from a
reviewer is abdication, not deference.

Two shapes that come up constantly:

- **"Add indexes on all three columns."** Often the better move is to narrow the
  query so one index serves it. Ask what makes the scan wide before you make the
  table wider.
- **"Alarm when X is skipped."** Fine only if X being skipped is genuinely
  unexpected. If it's a known, reasonable case, the fix is to make the exclusion
  *explicit and reasoned* rather than to alarm on it — a declared exclusion is
  visible in review; an alarm that always fires is invisible in practice.

## Declining well

The hardest and most valuable output. A decline needs three things:

1. **What the reviewer is right about** — concede the real part first.
2. **Why it isn't worth acting on now** — the specific cost, or the condition that
   would have to be true.
3. **What would change your mind** — a measurable trigger, so it's a deferral with
   a tripwire rather than a dismissal.

Written that way, a decline is stronger than a fix: it demonstrates the user
weighed it. A triage where every item is "fix now" did not triage anything, and a
reviewer reading it learns nothing about the user's judgment.
