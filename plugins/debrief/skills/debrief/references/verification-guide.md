# Verification guide

How to run the inverse grill in Phase 5: question archetypes, targeting, and
honest grading.

The goal is not to make the user feel tested. It is to find the two or three
spots where their understanding is thinner than they think, **before a reviewer
finds them.** A round where every answer is perfect was a wasted round — the
questions were too soft.

## Mechanics

- **One question at a time.** Wait for the answer. A dumped list gets skimmed and
  answered shallowly, which defeats the point.
- **3–5 questions total.** Fewer for a small change. Two good questions on a
  10-line fix is right; five is padding.
- **Target the weak spots deliberately.** In order of value:
  1. Anything the user asked *you* about during Phase 2 — their question marks
     the boundary of what they know.
  2. Anything you glossed over or summarised.
  3. The parts of Layer 3 with the most mechanism (the actual control flow).
  4. Any judgment call where the reasoning, not the code, is the answer.
- **Ask for the *why*, never the *what*.** "What does this function do?" is
  readable off the screen. "Why is the write after the render rather than before?"
  is not.

## Question archetypes

Draw from these. The parenthetical is what a weak answer looks like.

**Why not the obvious alternative.** The single most likely reviewer question.
Name the alternative *they* would reach for and make the user defend against it.
(*Weak: "because this way is better." Strong: names the specific cost of the
alternative under a stated constraint.*)

**The failure mode.** "This raises / times out / returns nil. Then what?" Probes
whether they traced the unhappy path or only the happy one.
(*Weak: "it's handled." Strong: names where, and what state is left behind.*)

**The what-happens-when, on a specific path.** Pick a real line and a real input.
"Two requests arrive in the same second — walk me through both." Concrete beats
abstract; abstract questions get abstract answers.

**The tradeoff.** "What did this make worse?" A user who says "nothing" does not
own the change yet. Every change costs something.

**The assumption.** "This leans on something being true. What is it, and what
happens if it stops being true?" Often the highest-value question in the set,
because the assumption is usually implicit in the code and explicit nowhere.

**The nasty edge case.** Use whenever the change touched anything concurrent,
cached, retried, batched, distributed, or transactional. Savepoint semantics,
partial batch failure, a retry after a partial write, cache invalidation ordering.
This is where real incidents live.

**The blast radius.** "Who else calls this?" Tests whether they looked outward or
only at the diff.

## Grading calibration

Grade against **"could this answer survive a sharp reviewer,"** not "did they say
something related."

| Verdict | Looks like | Your move |
|---|---|---|
| **Owned** | Names mechanism *and* reasoning, unprompted. Cites roughly the right place. | Confirm in one sentence. Move on. Do not gush. |
| **Partial** | Right conclusion, thin or missing reasoning. Describes *what* when asked *why*. | Say so plainly: "that's the what — a reviewer will push for the why. Try again." Let them retry before you fill it in. |
| **Gap** | Wrong, or a guess dressed as an answer. | Correct it directly, teach that spot again, then move on. Do not re-ask the same question immediately; ask a variant later. |

Rules that keep the grading worth anything:

- **Never praise a vague answer.** Doing it once teaches the user that vague
  answers pass, and the whole round becomes theatre.
- **Correct wrong things immediately and without softening.** They will repeat
  this in review.
- **Keep the teaching short.** A paragraph, not a lecture. The round has momentum
  and re-explaining everything kills it.
- **If they say "I don't know," that's a good answer.** Reward the honesty, fill
  the gap, move on. It's strictly better than a confident guess and you want that
  habit in review too.

## Closing verdict

End with a short, specific summary:

- Which questions they **owned** — name them, so the confidence is earned rather
  than general.
- Which to **rehearse** before review — the exact question, not the topic.
- Anything that turned out to be a **real gap in the change itself** rather than
  in their understanding. Sometimes the grill surfaces an actual bug or an
  undocumented assumption. That is a finding: log it, don't bury it in the
  debrief prose.

Then update the debrief doc's anticipated-questions section with every question
they struggled with, plus the strong answer. The doc should reflect where the
difficulty actually was, not where you predicted it would be.

## If the user declines the round

Respect it, no second ask. Write the questions and strong answers into the doc
anyway and tell them plainly: that section is the rehearsal script, and the
questions in it are the ones they should expect to be asked.
