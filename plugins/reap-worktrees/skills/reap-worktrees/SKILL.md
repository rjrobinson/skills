---
name: reap-worktrees
description: Find git worktrees whose PR is already merged, then transition their Jira ticket and delete the worktree. Use when cleaning up finished worktrees / "reap merged worktrees" / "any worktrees I can delete?".
---

# Reap merged worktrees

Cross-reference open worktrees against GitHub. For any worktree whose PR is **merged**, move its Jira ticket forward and delete the worktree — with guards so no uncommitted/unpushed work is lost.

Use `gh-axi` for GitHub. Jira lives at `https://<site>.atlassian.net` — use the Atlassian MCP tools (load via ToolSearch: `getTransitionsForJiraIssue`, `transitionJiraIssue`, `getJiraIssue`, `getAccessibleAtlassianResources` for the cloudId).

## 1. Gather worktrees

```
git worktree list --porcelain
```

- **Ignore the main checkout** — the path that is NOT under `.../trainual-worktrees/` (it's on `development`/`pre-release` and has no `WORKTREE_INFO.md`). Never delete it.
- For each remaining worktree capture: path, branch.
- Read `<path>/WORKTREE_INFO.md` if present for the **Ticket** key and the tmux **Session name**.
- Derive the ticket key: prefer the `Ticket:` line in `WORKTREE_INFO.md`; else match `[A-Z]+-\d+` in the branch name; else **no ticket** (still check the PR, just skip the Jira step for it).

## 2. Find the PR + state

For each worktree branch:

```
gh-axi pr list --head <branch> --state all
```

- Read the `state` column from the default output. **Do not pass `--fields`** — it rejects `state` (only supports `body, createdAt, labels, mergedAt, milestone, url`).
- `state == merged` → **reap candidate**. (`merged` is distinct from `closed`.)
- `open` / `closed` (not merged) / no PR → leave it; note why in the report.
- If multiple PRs match, use the most recent merged one. Grab its number/url from the same row for the report.

## 3. Look up Jira status (candidates only)

For each candidate with a ticket key, fetch current status + available transitions (`getTransitionsForJiraIssue`). This is the prompt the user asked for: surface that these are already merged and show where the ticket stands.

## 4. Report before touching anything

Print a table of reap candidates:

| Worktree | Branch | Ticket | PR | Jira status |
|---|---|---|---|---|

Also list the worktrees you're skipping and why (open PR, no PR, not merged). Do not delete anything yet.

## 5. Per-candidate confirm + guards

For **each** candidate, before deleting, run the guards and surface anything risky:

- **Uncommitted work:** `git -C <path> status --porcelain` — non-empty = dirty.
- **Unpushed commits:** `git -C <path> log @{u}.. --oneline 2>/dev/null` — non-empty = local commits not on the remote (the merged PR may predate them).
- **Running dev server:** `tmux has-session -t <session-name> 2>/dev/null` (session name from `WORKTREE_INFO.md`, e.g. `trainual-maint-910`).

Then ask the user to confirm this worktree, including which Jira transition to apply. **Default the transition to `Done`**, but show the ticket's real available transitions so picking `QA` (or anything else) later needs zero code change. If the worktree is dirty or has unpushed commits, call it out loudly and require an explicit go-ahead.

## 6. Execute (only on confirmation)

In this order, per confirmed candidate:

1. **Jira:** `transitionJiraIssue` to the chosen transition (skip if no ticket).
2. **Kill dev server:** `tmux kill-session -t <session-name>` if it was alive.
3. **Delete worktree:** `git worktree remove <path>` (add `--force` only if the user explicitly approved deleting despite a dirty/unpushed warning).

Report what was transitioned and removed. Never bulk-delete — one confirmation per worktree.

## Notes

- Read-only steps (worktree list, pr list, jira lookups) can run in parallel across worktrees.
- A branch with no ticket key still gets reaped if its PR is merged — just skip step 1's Jira transition.
- If `gh-axi` can't resolve a branch (never pushed), treat it as "no PR" and skip.
