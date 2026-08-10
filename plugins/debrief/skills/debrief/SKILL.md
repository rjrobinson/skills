---
name: debrief
description: >-
  Second brain for code changes, so the user owns a change instead of just having
  it merged — they can explain the problem, defend the solution, name the
  alternatives, and answer a skeptical senior engineer without the agent present.
  Two modes. Change mode: after-action review of work just done (read the real
  diff, explain in three layers, Mermaid diagrams, write the debrief doc, then
  flip roles and interview the user). Comment mode: work through PR review
  feedback until the claim is understood, its risk is triaged, and a decision is
  made together. Output always goes to the separate debrief repo, never into the
  project. Trigger on: /debrief, "debrief this", "after-action review", "walk me
  through what we just did", "quiz me on this change", "help me own this PR", "I
  need to defend this in review", "what is this reviewer actually saying", "triage
  these comments", "work through this PR feedback".
---

# debrief

The user's second brain for code changes. Two things happen to them repeatedly:
an agent does a body of work they now have to own, and a reviewer leaves comments
they have to evaluate. Both need the same thing — real understanding, held by the
user, with a written record that survives the session.

**Everything written by this skill goes to the debrief repo, never into the
project repo.** These are the user's private notes, not team documentation.

## Where output goes

```
$DEBRIEF_HOME/<repo>/debriefs/YYYY-MM-DD-<slug>.md
$DEBRIEF_HOME/<repo>/adr/NNNN-<kebab-title>.md
```

`$DEBRIEF_HOME` defaults to `~/Code/github.com/debrief`. If that directory does
not exist and the env var is unset, ask where to write rather than guessing.

Derive `<repo>` from the **origin remote**, not the working directory, so
worktrees collapse into the parent project:

```bash
basename -s .git "$(git remote get-url origin 2>/dev/null)" 2>/dev/null \
  || basename "$(git rev-parse --show-toplevel 2>/dev/null)" \
  || echo _no-repo
```

Never write to `docs/`, `CONTEXT.md`, or anything else inside the project repo.
If the change introduced new domain vocabulary and the project has a glossary,
*tell the user the term is worth adding* — do not edit their repo to do it.

## Which mode

| The user is… | Mode |
|---|---|
| sitting on work just finished, needing to own it | **Change mode** |
| holding review comments they need to evaluate | **Comment mode** |

`/debrief comments` selects comment mode explicitly. Otherwise infer, and say
which one you're running in one line before you start. If a session has both —
a change was made *and* it drew review — run comment mode first: the decisions it
produces are part of the story change mode has to tell.

---

# Change mode

Five phases, in order. **Do not skip the last one** — the verification round is
the point, not an optional extra.

| Phase | Goal |
|---|---|
| 1. Evidence | read the actual diff, never trust memory |
| 2. Explanation | problem, solution, alternatives, in three layers |
| 3. Diagrams | Mermaid, the right diagram type for the change |
| 4. Paper trail | debrief doc always; ADRs only when gated in |
| 5. Verification | flip roles: interview the user, grade, fill gaps |

## Phase 1 — Evidence

Ground everything in what actually changed, not what you remember intending.
Memory of a session drifts; the diff does not.

- **In a git repo:** run `git status`, then `git diff` (or `git diff <base>...HEAD`,
  or `git log --oneline` + `git show` for committed work) to enumerate every
  touched file. Ask the user which range covers "the change" if it's ambiguous —
  a session often contains more than one logical change, and a debrief covers
  exactly one.
- **Not in a repo, or the change came from conversation only:** reconstruct from
  the conversation, but say so explicitly and flag anything you can't verify.
- **Read the surrounding code, not just the hunks.** A debrief that only
  describes the diff lines produces "we changed X to Y" trivia; the user needs to
  know why the code around it made this the right move.
- **Check for existing context:** the project's `CONTEXT.md`, `README`, and any
  prior debriefs in `$DEBRIEF_HOME/<repo>/`. Use the project's own vocabulary. If
  it has a glossary, ignoring it creates the terminology drift the glossary exists
  to prevent.

Every factual claim below should be traceable to a file and line. When you state
something about the change, cite it (`src/pipeline/retry.ts:41`) so the user can
go look.

## Phase 2 — Explanation

Three layers, in this order, all three every time. The layering is not padding —
each layer is a different real situation the user will be in.

**Layer 1 — The elevator pitch** (~30 seconds spoken). Two or three sentences:
what was broken or missing, what the change does about it, and the one-line "why
this way." This is what the user says when a director asks "what did you ship
this week?"

**Layer 2 — The standup version** (~2 minutes spoken). The problem with enough
mechanism to be credible: how the problem manifested (bug report, failing
metric, blocked feature, smell), what the root cause actually was, the shape of
the fix, and what got touched. This is what the user says to their team.

**Layer 3 — The deep dive.** This is the layer that makes the user dangerous in
code review. Cover, with `file:line` citations:

- **The problem's anatomy.** Why did the problem exist? What earlier decision,
  missing abstraction, or changed requirement created it? If the answer is
  "someone made a reasonable call in 2024 and the world changed," say that — it's
  almost always more true and more useful than "the old code was bad."
- **The solution's mechanism.** Walk the actual control flow / data flow of the
  new code. Name the key functions, types, and boundaries. If the change is a
  refactor, what invariant does the new shape protect that the old shape didn't?
- **Alternatives considered and rejected.** At least two real ones, with the
  honest reason each lost. "We could have X but chose Y because Z" is the single
  sentence that distinguishes an engineer who owns a change from one who watched
  it happen. If the session never actually considered alternatives, construct the
  ones a reviewer would raise — the user will be asked about them regardless.
- **Tradeoffs accepted.** What got worse or riskier on purpose: performance,
  complexity, a new dependency, a migration burden. Never present a change as
  costless.
- **Risks and unknowns.** What could break, what wasn't tested, what assumption
  the change leans on. What would you watch after deploy?
- **Blast radius.** What else in the system touches this code path? Who else's
  code or team is affected?

Deliver Layer 3 conversationally — prose, not a wall of bullets — and pause after
it to ask if any part deserves a closer look before moving on. If the user asks a
question at any point, answer it fully before resuming; their questions are
signal about where the verification round should probe.

## Phase 3 — Diagrams

Produce one or two Mermaid diagrams — the ones that carry the most explanation
for **this particular change**, not a fixed set. Read
[references/mermaid-guide.md](references/mermaid-guide.md) for diagram-type
selection, syntax constraints, and before/after conventions. The short version:

| The change is mostly about… | Reach for |
|---|---|
| A runtime interaction between components | `sequenceDiagram` |
| Branching logic or a pipeline | `flowchart` |
| Architecture / component relationships | `flowchart` with subgraphs (C4-ish) |
| Lifecycle or status transitions | `stateDiagram-v2` |
| Schema or data model | `erDiagram` |

For refactors and architectural changes, a before/after pair of small diagrams
beats one large annotated diagram. Embed the diagrams in the debrief doc; also
render them in the conversation so the user sees them now.

## Phase 4 — Paper trail

**The debrief doc — always.** Write
`$DEBRIEF_HOME/<repo>/debriefs/YYYY-MM-DD-<slug>.md` using
[references/debrief-template.md](references/debrief-template.md). It carries all
three explanation layers, the diagrams, the alternatives/tradeoffs/risks, and the
anticipated-questions section. Six months from now this is what reloads the
context.

**ADRs — gated, usually zero.** An ADR is warranted only when a decision passes
**all three** gates: hard to reverse, AND surprising without context, AND
involved a real tradeoff. Most changes produce no ADR, and that is correct
behavior. When one qualifies, write it to `$DEBRIEF_HOME/<repo>/adr/` using
[references/adr-template.md](references/adr-template.md), numbered sequentially
after the existing ADRs in that directory. The gates exist because a directory of
trivial ADRs trains the reader to ignore the directory.

Create directories lazily. Show the path when you're done.

## Phase 5 — Verification (the inverse grill)

Now flip roles. You've been teaching; become the skeptical reviewer. This phase
is what turns "I read an explanation" into "I can talk about this in depth."

Read [references/verification-guide.md](references/verification-guide.md) for
question archetypes and grading calibration. The mechanics:

- **Ask one question at a time and wait for the answer.** Never dump a list.
- **Ask 3–5 questions**, drawn from what a sharp senior engineer would actually
  probe: the why-not-the-obvious-alternative question, the failure-mode question,
  the what-happens-when question about a specific code path, the tradeoff
  question, and — if the change touched anything concurrent, cached, retried, or
  distributed — the nasty edge-case question.
- **Target the weakest spots:** anything the user asked about earlier, anything
  glossed over, the parts of Layer 3 with the most mechanism.
- **Grade honestly.** After each answer: confirm what was right, correct what was
  wrong, fill what was missing — briefly, then move on. Do not praise vague
  answers. A gentle "that's the *what* — a reviewer will push for the *why*; try
  again" is worth more than letting it slide.
- **If an answer reveals a real gap, teach that spot again** before the next
  question.
- **Close with a verdict:** which questions the user owned, which to rehearse.
  Add any question they struggled with, plus the strong answer, to the doc's
  anticipated-questions section so it reflects where the real difficulty was.

If the user declines the round, respect it — write the anticipated questions and
strong answers into the doc anyway and tell them it's their rehearsal script.

---

# Comment mode

A reviewer left feedback. The user needs to understand what is actually being
claimed, know whether it is real, know what it would cost, and reach a decision
they can defend — before touching code.

This matters more than it used to. Reviewers increasingly paste agent-generated
findings, which are dense, plausible, and unbounded: there is always another
finding. Volume is not evidence. The user's defense is judgment applied per item,
and a record of the decision.

Read [references/comment-triage-guide.md](references/comment-triage-guide.md) for
risk calibration and the decision vocabulary.

## Phase 1 — Evidence

Get the comments **and** the code they point at. Never triage from the comment
text alone; a claim about `foo.rb:41` is verified or refuted at `foo.rb:41`.

Fetch inline (file-anchored) threads explicitly, not just conversation-level
comments — the inline ones are usually the substantive feedback. If the project
has a comment-fetching skill or command, use it rather than reinventing the
plumbing.

Number the items (C1, C2, …) so the user can refer to them.

## Phase 2 — Translate

For each item, state in plain language what is actually being claimed. Strip the
severity label and the tone; keep the mechanism. Many comments assert more than
they demonstrate, and separating the two is most of the work.

Then classify what kind of claim it is:

- a **current defect** — something breaks today for a real user or account
- a **latent defect** — correct today, breaks under conditions that will arrive
- a **hardening** — no defect, closes a future hole
- a **taste or convention** call
- a **question**, not a claim

Say when a comment's own text concedes it isn't current ("nothing is missed
today"). That concession is the single most useful fact in a triage.

## Phase 3 — Triage

For each item, three things, briefly:

1. **Is it true?** Verified against the code, refuted, or unresolved. Cite the
   line. A confident-sounding claim that the code disproves is a finding of its
   own — say so plainly.
2. **What does it cost if ignored?** Be specific about the failure and who feels
   it. "A failed compliance erasure that never retries" is a cost. "Suboptimal"
   is not.
3. **What does the fix cost?** Effort, new risk, new surface, and what it makes
   worse.

Then a stop rule, so the round terminates: **fix now** only if cheap *and* it
closes a failure with real cost; **log** if real but conditional on scale or on
code that doesn't exist yet; **decline** if the cost exceeds the risk. Say out
loud that the merge gate is a human judgment that residual risk is acceptable —
not the absence of tool output.

## Phase 4 — Decide together

Present the triage and let the user decide. Give an opinionated recommendation
per item with the reason attached, and be willing to argue for **decline** —
that's the option an agent is biased against and the user most needs supported
with evidence.

Where a reviewer's suggested fix is worse than an alternative, say so and show
both. Adopting a suggestion verbatim when a better option exists is not respect,
it's abdication.

## Phase 5 — Record

Write the decisions into
`$DEBRIEF_HOME/<repo>/debriefs/YYYY-MM-DD-<slug>-review.md` using the
review-decisions section of
[references/debrief-template.md](references/debrief-template.md): each item, the
claim in plain words, the verdict, the decision, and the reason. If the user later
gets asked "why didn't you fix that one?", this file is the answer.

Then offer the verification round on anything that got fixed — the same inverse
grill, targeted at the changes the review produced.

---

## Session shape and tone

- This is a **conversation**, not a report generator. Explanation and
  verification especially should feel like a strong colleague at a whiteboard:
  direct, concrete, citing real lines, willing to say "this part is genuinely
  subtle."
- **Never inflate.** If the change was small, the debrief is short. A 10-line fix
  gets a tight Layer 1/2, a paragraph of Layer 3, one diagram at most, and two
  verification questions. Matching depth to the change is part of the credibility.
- **Never invent history.** If you don't know why the old code was the way it
  was, say so and mark it an open question rather than fabricating a rationale — a
  confident false history in a debrief doc is worse than a gap, because it gets
  repeated in code review as fact.
- If the change was made by a different agent/session and you can't reconstruct
  intent from the diff, **interview the artifacts** (commit messages, PR
  description, linked tickets) before interviewing your imagination.
- **Never commit.** Not the project repo, not the debrief repo. Write the files,
  show the paths, let the user commit their own second brain.

## It's working if

- Every claim about the change traces to a file and line the user can open.
- The user gets asked at least one question they initially answer badly — if all
  five answers are perfect, the questions were too soft.
- `$DEBRIEF_HOME/<repo>/debriefs/` gains one dated doc per session; `adr/` gains
  few or none.
- The alternatives section names options a real reviewer would raise, not
  strawmen.
- In comment mode, at least one item gets **declined with a reason** — a triage
  where everything is "fix now" did not triage anything.
- Nothing was written into the project repo.
