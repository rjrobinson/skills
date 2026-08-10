---
name: build-response-standard
description: Interview a person about how they want an agent to write to them, then generate their Response Standard profile. Twenty questions across five sets, covering answer shape, depth, structure, evidence, tone, and forbidden constructs. Use when someone wants their own response standard, wants to change an existing one, or asks how to make an agent write the way they think. Trigger on: /build-response-standard, "build my response standard", "how should you talk to me", "make your own standard for me".
---

# Build a Response Standard

Interview the user, then write their profile. The output is a `SKILL.md` in the same shape as `response-standard`.

Do not guess an answer. Do not skip a question because you think you know the person. The value is in their reason, not in the rule.

## How to run it

1. Show the twelve domains below. Ask the user to add or cut any before you start.
2. Ask the questions in sets of four, using `AskUserQuestion`.
3. Put the recommended option first in each question and label it `(Recommended)`. Base the recommendation on what you already know about the person. Say why in the option description.
4. After each set, restate the answers in one line. Keep the momentum.
5. Watch for collisions with rules the person already gave you, in memory or in a `CLAUDE.md`. Surface a collision as its own question. Never resolve it silently.
6. Record every custom answer verbatim. A typed answer beats a selected option, and it usually carries the reason.

## The twelve domains

| # | Domain | The decision |
|---|---|---|
| 1 | Answer order | Verdict first, or evidence first |
| 2 | Depth | Minimum answer, or answer plus risk |
| 3 | Structure | Table, bullets, or prose |
| 4 | Options | When to show alternatives instead of one answer |
| 5 | Uncertainty | How to mark an unverified claim |
| 6 | Evidence | When to cite a file, a line, or command output |
| 7 | Length | How length follows the request |
| 8 | Humor | Where humor is welcome |
| 9 | Corrections | How to correct your own error |
| 10 | Forbidden constructs | Filler, praise, hedging, punctuation |
| 11 | Sentence mechanics | How strict the STE limits are |
| 12 | Scope | Which outputs the standard governs |

## Set 1: shape

1. **Answer order.** Where does the conclusion go? Verdict first / verdict then only the facts that could change it / evidence then verdict.
2. **Depth.** What is the default before they ask for more? Answer plus risk / answer only / full context.
3. **Structure.** What shape by default? Table to compare and prose to explain / bullets / prose / tables wherever possible.
4. **Options.** When do they want alternatives? Only for calls they own / always / only on request.

## Set 2: truth and tone

5. **Uncertainty.** How to mark an unverified claim? Inline on the claim / one caveats block at the end / only when it changes their decision.
6. **Evidence.** When must you prove instead of assert? Every claim about code or state / only surprising claims / only on request.
7. **Length.** How does length follow the request? Obey the ask literally / always err shorter / always err more complete.
8. **Humor.** Where is it welcome? Conversation only / anywhere / only after they joke / none.

## Set 3: collisions and density

Adapt this set to the collisions you actually found. The three below recur.

9. **Estimates.** Time and effort estimates, or none? Check for an existing ban before you ask.
10. **Lead line.** When a reply has both a conclusion and an action, which comes first?
11. **Density.** STE avoids jargon. Many engineers read jargon faster. Keep technical terms and simplify grammar only, or simplify vocabulary too?
12. **Tangents.** What happens to a second problem found while solving the first? Finish then offer / log silently / list at the end.

## Set 4: prohibitions and behavior

13. **Never write.** Use `multiSelect`. Offer filler openers and closings, empty praise, hedging on verified facts, and em dashes. Expect a custom answer that narrows one of them.
14. **Corrections.** State and continue / state with the cause / silent.
15. **State.** Restate progress every turn / only during a numbered plan / never.
16. **List cap.** Five then split / no cap but ranked / three then split.

## Set 5: strictness, scope, failures, name

17. **Strictness.** Are the STE word limits targets or hard caps?
18. **Scope.** Use `multiSelect`. Replies, commits and PRs, tickets, agent briefs and prompts.
19. **Failures.** Cause then fix / cause, fix, and what you already tried / fix only.
20. **Name.** The standard needs a name. It becomes the skill name.

## Writing the profile

Produce a `SKILL.md` with these sections, in this order:

1. **The shape of a reply** as a three-row table: first line, body, last block.
2. **Length**
3. **Truth**
4. **Judgment**
5. **Structure**
6. **Language**, derived from ASD-STE100 and adjusted by answers 11 and 17.
7. **Never write these**
8. **Humor**
9. **Scope**
10. **Known tensions**, one row per collision, with the resolution. This section stops a future agent from reopening a settled question.

Two rules for the profile itself:

- Write the profile in the standard it describes. A standard that breaks its own rules will not be followed.
- Keep the reason attached to any rule that could be misapplied. Drop the reason from a rule that is self-evident.

## Baseline STE rules

Carry these into every profile unless an answer overrides one.

1. One idea in each sentence.
2. Active voice. Imperative mood for steps.
3. Simple tenses only. No perfect forms. No progressive forms.
4. One term for one concept. No synonyms for variety.
5. Always include the articles.
6. Maximum three words in a noun cluster.
7. Maximum six sentences in a paragraph.
8. No idiom. No slang.
9. Avoid contractions.
10. Technical names are permitted. Code and paths do not change.

## After the interview

1. Write the profile to `plugins/<name>/skills/<name>/SKILL.md`.
2. Add a `plugin.json` with the name, the description, and the trigger phrases.
3. Register the plugin in the marketplace manifests. Ask first if those files have uncommitted changes.
4. Ask the user to review the profile before you commit anything.
