---
name: start-worktree
description: Set up a repo-tailored git-worktree dev loop. Run ONCE in any repo to generate a /worktree command (creates an isolated, runnable worktree) and a /start command (boots that worktree's dev server). Detects the stack, confirms choices, writes both into .claude/commands/. Trigger on /start-worktree, "set up worktrees for this repo", "wire up /worktree and /start", "make worktrees runnable here".
source: rj
risk: safe
argument-hint: (no arguments)
---

# start-worktree — generate a worktree dev loop for THIS repo

Run once per repo. The output is two commands written into `.claude/commands/`:

- **`/worktree <branch>`** — create a git worktree that can actually *run*: gitignored
  env/secrets/deps symlinked back to main, deterministic per-worktree ports so sibling
  worktrees never collide, and a `WORKTREE_INFO.md` briefing so an agent session knows
  what it's working on.
- **`/start`** — detect worktree-vs-main and boot the dev server for the current worktree
  in a detached tmux session, wait until it's actually serving, then open the browser.

This skill does **not** run a server. It writes the two commands, tailored to the repo it's
run in. You review them, then use them.

## Why this exists (the lessons to preserve)

A naive "just `git worktree add`" leaves a worktree that won't boot: no `.env`, no
`node_modules`, and two worktrees fighting over the same port. The generated commands must
carry these hard-won rules — port them into whatever stack this repo uses:

1. **Deterministic ports per branch.** Hash the branch name (`cksum`) → a stable port in a
   chosen range. The same branch always gets the same port across sessions; different
   branches never collide. Bump on a live collision.
2. **Inject the port into the process manager's OWN env, and disable its default port.**
   The classic failure: the process manager (overmind/foreman) forces its own base port
   (e.g. 5000) onto children, `dotenv` loads non-overwriting, so the app ignores the
   worktree's port and the front-end dev server (Vite/webpack) lands elsewhere → broken
   assets / "missing entrypoint". Fix: pass `PORT`/front-end-port **into the manager's
   environment** and set its no-inject flag (overmind: `OVERMIND_NO_PORT=1`). Inline the
   vars into the command string so they survive a pre-existing tmux server.
3. **Symlink vs copy.** Symlink single-source-of-truth files (secrets, `.env`, tool-version
   files, content-addressable dep dirs like `node_modules`/`vendor/bundle`). **Copy** the
   one env file you must append per-worktree overrides to — never symlink that, or you'll
   mutate main.
4. **Per-worktree vs shared.** `tmp/`, `log/`, build output (`public/packs`, `public/vite`)
   MUST be per-worktree or two running apps corrupt each other. DB is usually shared (warn
   before migrating); give each worktree its own logical Redis DB / namespace if the stack
   uses one.
5. **Unique socket + tmux session per worktree**, keyed on a sanitized branch name, so
   `/start` in one worktree never kills another.
6. **`WORKTREE_INFO.md`** at the worktree root, gitignored *locally* (via
   `.git/worktrees/<branch>/info/exclude`, NOT the shared `.gitignore`), briefing the agent:
   ticket, scope-lock, ports, how to start, what's shared vs isolated.
7. **Readiness gate before opening the browser** — wait until the port(s) listen AND a
   request returns non-5xx. "Both ports listening" is the real signal.

## Procedure

### 1. Inspect the repo — don't assume

Gather, reading only (report what you find):

- **Process manager / dev command**, in priority order: `Procfile.dev`/`Procfile` (foreman
  vs overmind — is `overmind` on PATH?), `bin/dev`, `package.json` scripts (`dev`/`start`;
  which package manager from the lockfile — `pnpm-lock.yaml`/`yarn.lock`/`package-lock.json`),
  `docker-compose.yml`, a bespoke `start.sh`.
- **Framework**: `Gemfile`+`bin/rails` (Rails), `bin/vite`/`vite.config.*` (Vite),
  `next.config.*`, etc. — determines the front-end dev-server port question.
- **Gitignored runtime files** that a fresh worktree would be missing: parse `.gitignore`
  and look for `.env*`, `config/*.key`, `config/master.key`, service-account JSON,
  `.tool-versions`/`.mise.toml`, `node_modules`, `vendor/bundle`, `.bundle`, `storage`,
  `public/uploads`.
- **Port source**: does the app read `PORT`? Is there a separate front-end dev-server port?
- **Datastores**: Redis? A dev database whose name could be per-worktree?
- **Existing** `.claude/commands/worktree.md` or `start.md` — if present, show the user and
  ask before overwriting.

### 2. Confirm the plan (one short round)

Present what you detected and confirm the handful of things you can't infer with confidence:

- Worktree location — default `../<repo-name>-worktrees/<branch>`.
- Base branch to cut from (`main`/`master`/`development`?).
- Port range (default: primary in 3001–3899, front-end = primary+1000).
- Redis/DB isolation — apply it, or share with main?
- Process manager choice if ambiguous.

Keep it to the open questions. Don't re-ask what the repo clearly answered.

### 3. Write `.claude/commands/worktree.md`

Tailored to the detections. It must:

1. Resolve `MAIN_REPO=$(git rev-parse --show-toplevel)`, `WORKTREE_PATH=<base>/$BRANCH`;
   refuse if the path exists.
2. Create the worktree, handling three cases: existing local branch, remote branch
   (`--track`), or brand-new branch off the confirmed base.
3. Symlink the detected env/secret/tool-version files and content-addressable dep dirs
   (skip silently if a file is absent — keeps it portable).
4. If the app uses `PORT`: compute `BRANCH_HASH=$(echo -n "$BRANCH" | cksum | cut -d' ' -f1)`,
   derive the port(s) in the confirmed range, bump on a live `lsof` collision. **Copy** the
   per-worktree env file and append an idempotent override block (strip a prior block first)
   with the port(s) and per-worktree Redis URL/DB if applicable.
5. Create the per-worktree runtime dirs (`tmp`, `tmp/pids`, `tmp/cache`, `log`, build-output
   dirs) so running apps don't collide.
6. Lockfile drift check: if `yarn.lock`/`Gemfile.lock`/`package.json` differ from main, warn
   that symlinked deps may be wrong and print the un-symlink + reinstall commands.
7. Write `WORKTREE_INFO.md` (ticket if the branch matches `[A-Z]+-\d+`, scope-lock,
   ports, "how to start" pointing at `/start`, shared-vs-isolated list, datastore warnings).
8. Add `WORKTREE_INFO.md` and the per-worktree procfile/socket/log patterns to
   `.git/worktrees/$BRANCH/info/exclude` (local ignore — never the shared `.gitignore`).
9. Print next steps + the port/URL summary.

If the process manager is overmind/foreman, also write a `Procfile.worktree` (the processes
minus any singleton like a background-job worker that should only run in main).

### 4. Write `.claude/commands/start.md`

Tailored `/start`. It must:

1. `cd` to the repo root; detect worktree-vs-main (path under the worktree base, or the
   presence of `WORKTREE_INFO.md`). In the **main** repo, hand off to the repo's normal dev
   command (`bin/dev`, `./start.sh`, `npm run dev`, …) — don't reinvent it.
2. In a **worktree**: read the port(s)/Redis URL from the override block (`tail -1` wins),
   error clearly if missing ("re-run /worktree").
3. Clean up only THIS worktree's prior run (its socket, its tmux session, its own ports) —
   never main or siblings.
4. Launch the process manager in a **detached tmux session** with a unique socket, injecting
   the port(s) into the manager's env (+ its no-inject flag). Inline the vars into the
   command string. Tee output to `log/…-startup.log`. Advise running with
   `run_in_background: true` so control returns immediately.
5. Wait (bounded loop) until the port(s) listen and a `curl` returns non-000/5xx, then `open`
   the URL. On timeout, print how to watch the log and the URL to open manually.
6. Report URL + tmux session name.

### 5. Report

List the files written, the detected stack, the port scheme, and the exact next command
(`/worktree <branch>`). Remind the user these are a tailored first draft — worth a read
before trusting them on a real branch.

## Notes

- **Portability first.** Every file-list is "symlink if present, skip if absent," so a
  generated command is harmless in a repo that lacks some of the files.
- **Never ship secrets.** The generated commands *reference* secret filenames to symlink
  them; they never read or embed secret contents.
- The Trainual-specific `worktree` and `start` commands shipped elsewhere in this marketplace
  are the reference implementation this skill generalizes — consult them for the concrete
  overmind/Rails/Vite wiring, then adapt to the repo at hand.
