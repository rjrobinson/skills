---
description: Create a runnable git worktree at ../<repo>-worktrees/<branch> with symlinked env, configs, and deps
argument-hint: <branch-name>
---

# Worktree: $ARGUMENTS

Create a git worktree for branch `$ARGUMENTS` at `../<repo-name>-worktrees/$ARGUMENTS` with all gitignored
files symlinked back to the main repo so the app and tests can run from the new worktree.

The file/dir lists below are tuned for the Trainual repo but harmless elsewhere — missing files are
silently skipped, so this works in any Rails/JS repo.

## Strategy (decided with RJ)

- **Env / secrets / split configs**: symlink from main repo (single source of truth)
- **`.env.development.local`**: COPY (not symlink) and append per-worktree port/Redis overrides
- **`node_modules`, `vendor/bundle`, build dirs**: symlink (hybrid) — verify lockfiles match main, warn if drift
- **Database**: shared with main repo (`trainual_development`) — no per-worktree isolation
- **Redis**: per-worktree logical DB (1–14, main keeps DB 0) — prevents Sidekiq job collisions
- **Sidekiq**: do NOT run Sidekiq in worktrees. Main repo runs the one and only Sidekiq against DB 0. Worktrees that need async behavior should use `Sidekiq::Testing.inline!` in specs or swap the queue adapter to `:inline`.
- **Ports**: deterministic from branch name hash — OPS-325 always gets the same port across sessions. Rails in 3001–3899, Vite = Rails+1000 (4001–4899).
- **Cookies**: verified safe. Trainual's session config uses `domain: :all, tld_length: 3`, which on a 3-segment host like `wt-ops-325.localtest.me` scopes cookies to the exact host. Each worktree subdomain gets an isolated session jar.

## Steps

### 1. Validate args and resolve paths

```bash
BRANCH="$ARGUMENTS"
if [ -z "$BRANCH" ]; then
  echo "Usage: /worktree <branch-name>"
  exit 1
fi

MAIN_REPO=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$MAIN_REPO")
WORKTREE_BASE="$(dirname "$MAIN_REPO")/${REPO_NAME}-worktrees"
WORKTREE_PATH="$WORKTREE_BASE/$BRANCH"

mkdir -p "$WORKTREE_BASE"

if [ -e "$WORKTREE_PATH" ]; then
  echo "ERROR: $WORKTREE_PATH already exists. Remove it or pick a different branch name."
  exit 1
fi
```

### 2. Create the worktree

Handle three cases: branch exists locally, exists on remote, or is brand new.

```bash
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "==> Using existing local branch '$BRANCH'"
  git worktree add "$WORKTREE_PATH" "$BRANCH"
elif git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  echo "==> Checking out remote branch 'origin/$BRANCH'"
  git fetch origin "$BRANCH"
  git worktree add "$WORKTREE_PATH" -b "$BRANCH" --track "origin/$BRANCH"
else
  echo "==> Creating new branch '$BRANCH' from current HEAD"
  git worktree add -b "$BRANCH" "$WORKTREE_PATH"
fi
```

### 3. Symlink gitignored env, secrets, and split configs

```bash
echo "==> Symlinking env and config files"

# Symlink most env files (single source of truth).
# NOTE: .env.development.local is intentionally NOT symlinked — we copy it in step 3b
# and append per-worktree overrides (PORT, VITE_RUBY_PORT, REDIS_URL).
# NOTE: .tool-versions is gitignored globally, so worktrees don't inherit it — symlink
# it so asdf can resolve node/ruby/pi/etc. versions (without it, commands like pi fail
# with "No version is set for command pi").
ENV_FILES=(
  ".env"
  ".env.development"
  ".env.test"
  ".tool-versions"
)

CONFIG_FILES=(
  "config/secrets.yml"
  "config/master.key"
  "config/google_service_account_config.json"
  "config/vertex_ai_service_account_config.json"
  "config/rpush_firebase_google_service_account_config.json"
  "config/split.yaml"
  "config/split.local.yaml"
  "config/split.temp.yaml"
  "config/split.test.yaml"
  "config/split.test.temp.yaml"
)

for f in "${ENV_FILES[@]}" "${CONFIG_FILES[@]}"; do
  if [ -f "$MAIN_REPO/$f" ]; then
    mkdir -p "$WORKTREE_PATH/$(dirname "$f")"
    ln -sf "$MAIN_REPO/$f" "$WORKTREE_PATH/$f"
    echo "    linked $f"
  fi
done
```

### 3b. Compute deterministic ports + Redis DB, copy .env.development.local, append overrides

```bash
echo "==> Computing per-worktree ports and Redis DB"

# Hash the branch name to get deterministic ports and Redis DB.
# cksum gives a stable 32-bit int across runs. cut to get just the number.
BRANCH_HASH=$(echo -n "$BRANCH" | cksum | cut -d' ' -f1)

# Rails: 3001–3899 (avoids 3000 which main uses). Vite: Rails + 1000.
RAILS_PORT=$((3001 + (BRANCH_HASH % 899)))
VITE_PORT=$((RAILS_PORT + 1000))

# Redis logical DB: 1–14 (0 is reserved for main, 15 for ad-hoc).
REDIS_DB=$((1 + (BRANCH_HASH % 14)))

# Collision check — if the computed Rails port is already LISTENing, bump to next free.
# (Vite port follows Rails port + 1000 so we only need to check one.)
while lsof -iTCP:$RAILS_PORT -sTCP:LISTEN >/dev/null 2>&1; do
  RAILS_PORT=$((RAILS_PORT + 1))
  VITE_PORT=$((RAILS_PORT + 1000))
done

echo "    Rails port:  $RAILS_PORT"
echo "    Vite port:   $VITE_PORT"
echo "    Redis DB:    $REDIS_DB"

# Copy .env.development.local (don't symlink — we need to append overrides).
if [ -f "$MAIN_REPO/.env.development.local" ]; then
  cp "$MAIN_REPO/.env.development.local" "$WORKTREE_PATH/.env.development.local"
  echo "    copied .env.development.local from main"
else
  touch "$WORKTREE_PATH/.env.development.local"
  echo "    created empty .env.development.local (main had none)"
fi

# Append per-worktree overrides. Idempotent — strip any prior block first.
sed -i.bak '/^# === WORKTREE OVERRIDES (auto-generated) ===/,/^# === END WORKTREE OVERRIDES ===/d' \
  "$WORKTREE_PATH/.env.development.local" 2>/dev/null || true
rm -f "$WORKTREE_PATH/.env.development.local.bak"

cat >> "$WORKTREE_PATH/.env.development.local" <<EOF

# === WORKTREE OVERRIDES (auto-generated) ===
# Branch: $BRANCH  |  Hash: $BRANCH_HASH
# Do not edit this block directly; re-run /worktree to regenerate.
PORT=$RAILS_PORT
VITE_RUBY_PORT=$VITE_PORT
REDIS_URL=redis://localhost:6379/$REDIS_DB
# Sidekiq should NOT run in this worktree — main repo owns Sidekiq on DB 0.
# If you absolutely must run Sidekiq here, it will read this REDIS_URL and use DB $REDIS_DB,
# which is isolated from main. But prefer Sidekiq::Testing.inline! instead.
# === END WORKTREE OVERRIDES ===
EOF

echo "    appended worktree overrides to .env.development.local"
```

### 4. Symlink shared dep directories (safe to share across running apps)

```bash
echo "==> Symlinking shared dependency directories"

# These can be shared because they're read-mostly or content-addressable.
SHARED_DIRS=(
  "node_modules"
  "vendor/bundle"
  ".bundle"
  "storage"
  "public/uploads"
  "public/bulk_upload_results"
)

for d in "${SHARED_DIRS[@]}"; do
  if [ -e "$MAIN_REPO/$d" ]; then
    mkdir -p "$WORKTREE_PATH/$(dirname "$d")"
    rm -rf "$WORKTREE_PATH/$d"
    ln -s "$MAIN_REPO/$d" "$WORKTREE_PATH/$d"
    echo "    linked $d"
  fi
done
```

### 4b. Create per-worktree dirs (must NOT be shared — would collide if 2 apps run)

```bash
echo "==> Creating per-worktree runtime dirs"

# tmp/log/pids would collide across running apps.
# vite/packs are branch-specific build output — sharing corrupts builds.
PER_WORKTREE_DIRS=(
  "tmp"
  "tmp/pids"
  "tmp/cache"
  "tmp/sockets"
  "log"
  "public/packs"
  "public/packs-test"
  "public/vite"
  "public/vite-dev"
  "public/vite-test"
)

for d in "${PER_WORKTREE_DIRS[@]}"; do
  mkdir -p "$WORKTREE_PATH/$d"
  echo "    created $d"
done
```

### 5. Verify lockfiles haven't drifted (hybrid mode safety check)

```bash
echo "==> Checking for dependency drift"

DRIFT=0
for lock in yarn.lock Gemfile.lock package.json; do
  if [ -f "$MAIN_REPO/$lock" ] && [ -f "$WORKTREE_PATH/$lock" ]; then
    if ! diff -q "$MAIN_REPO/$lock" "$WORKTREE_PATH/$lock" >/dev/null 2>&1; then
      echo "    WARN: $lock differs from main repo"
      DRIFT=1
    fi
  fi
done

if [ "$DRIFT" -eq 1 ]; then
  cat <<EOF

WARNING: lockfiles differ between this worktree and the main repo.
The symlinked node_modules / vendor/bundle may be wrong for this branch.

To use this worktree's deps without affecting the main repo, run:
  cd "$WORKTREE_PATH"
  rm node_modules vendor/bundle
  bundle install --path vendor/bundle
  yarn install

EOF
else
  echo "    OK: lockfiles match main repo, symlinked deps are valid"
fi
```

### 5b. Write WORKTREE_INFO.md — agent-facing briefing

Agent sessions working in the worktree drift when they don't know what ticket they're on. A pinned info file at the worktree root prevents this. It's gitignored per-worktree (won't leak into commits/PRs).

```bash
echo "==> Writing WORKTREE_INFO.md for agent sessions"

# Try to fetch the ticket summary if BRANCH matches an OPS-/PROJ- pattern (Jira).
TICKET_KEY=""
TICKET_SUMMARY=""
if [[ "$BRANCH" =~ ^([A-Z]+-[0-9]+) ]]; then
  TICKET_KEY="${BASH_REMATCH[1]}"
  # Try acli if available; skip if not — the commander can fill this in later.
  if command -v acli >/dev/null 2>&1; then
    TICKET_SUMMARY=$(acli jira workitem view "$TICKET_KEY" --fields summary 2>/dev/null | grep -i '^summary' | cut -d: -f2- | sed 's/^ *//')
  fi
fi

# tmux session + overmind socket names — must match exactly what /start computes.
SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-' | tr '[:upper:]' '[:lower:]')

cat > "$WORKTREE_PATH/WORKTREE_INFO.md" <<EOF
# IMPORTANT: Worktree-specific info

**You are an agent session operating inside a git worktree. Before doing anything, read this file.**

## What this worktree is for

- **Branch:** \`$BRANCH\`
${TICKET_KEY:+- **Ticket:** [$TICKET_KEY](https://trainual.atlassian.net/browse/$TICKET_KEY)}
${TICKET_SUMMARY:+- **Summary:** $TICKET_SUMMARY}
- **Main-repo path:** \`$MAIN_REPO\`
- **This worktree path:** \`$WORKTREE_PATH\`

## SCOPE — stay on ticket

Work **only** on the scope of this branch's ticket. Do NOT pick up adjacent tickets, fix unrelated bugs, or refactor things that are not part of this ticket — even if you notice them. Log them for later and stay focused.

If you realize you're about to work on a different ticket number than the branch name indicates, STOP. You're probably in the wrong worktree. Confirm with the user before proceeding.

## Runtime configuration (already applied)

- **Rails port:** \`$RAILS_PORT\`
- **Vite port:** \`$VITE_PORT\`
- **Redis DB:** \`$REDIS_DB\` (main repo uses DB 0; do not cross these streams)
- **URL:** http://app.localtest.me:$RAILS_PORT/growth

These values are baked into \`.env.development.local\`, and \`/start\` injects the ports into overmind's env so the rails + vite processes agree on them.

## How to start the dev server

**Run the \`/start\` slash command.** It detects the worktree, reads this worktree's ports, spins up overmind in a detached tmux session with a per-worktree socket (so it won't collide with main or other worktrees), waits until Rails + Vite are both serving, then opens the browser to the URL above.

\`\`\`
/start
\`\`\`

Session name: \`trainual-$SAFE_BRANCH\`. Attach manually with \`tmux a -t trainual-$SAFE_BRANCH\`. Stop with \`tmux kill-session -t trainual-$SAFE_BRANCH\`.

Fallback if \`/start\` isn't available — note you must inject the ports yourself, or you'll hit \`ViteRuby::MissingEntrypointError\`:
\`\`\`
PORT=$RAILS_PORT VITE_RUBY_PORT=$VITE_PORT OVERMIND_NO_PORT=1 \\
  overmind start -f Procfile.worktree -s .overmind-$SAFE_BRANCH.sock
\`\`\`

## Shared with main repo (be careful)

- **Database** (\`trainual_development\`) — running \`db:migrate\` here mutates main's schema too. Don't migrate unless the ticket requires it, and coordinate with the user first.
- **\`node_modules\`, \`.bundle\`, \`storage\`, \`public/uploads\`** — symlinked from main. Modifying these modifies main.
- **Everything else** is per-worktree: \`tmp/\`, \`log/\`, \`public/packs*\`, \`public/vite*\`, and \`.env.development.local\`.

## Isolated from main (safe to mess with)

- **Redis DB $REDIS_DB** — your Sidekiq queues, cache keys, and ActionCable channels do not collide with main or other worktrees.
- **Git branch** — you have your own working tree; commits here don't affect main until merged.

## DO NOT run Sidekiq in this worktree

Main repo owns the one and only Sidekiq, on Redis DB 0. If a spec needs async job execution, use \`Sidekiq::Testing.inline!\` or swap the queue adapter to \`:inline\`.

## Sibling worktrees

Run \`git worktree list\` from anywhere in this repo to see what other branches are checked out in parallel. Do NOT read or modify files in their directories.
EOF

# Make WORKTREE_INFO.md invisible to git in this worktree only (not global).
EXCLUDE_PATH="$MAIN_REPO/.git/worktrees/$BRANCH/info/exclude"
mkdir -p "$(dirname "$EXCLUDE_PATH")"
for pattern in "WORKTREE_INFO.md" "Procfile.worktree" ".overmind-*.sock" "log/overmind-startup.log"; do
  grep -qxF "$pattern" "$EXCLUDE_PATH" 2>/dev/null || echo "$pattern" >> "$EXCLUDE_PATH"
done

echo "    wrote WORKTREE_INFO.md (gitignored locally)"
```

### 5c. Write Procfile.worktree — the per-worktree procfile used by /start

\`\`\`bash
cat > "$WORKTREE_PATH/Procfile.worktree" <<'PROCFILE_EOF'
# Auto-generated by /worktree skill. Gitignored per-worktree.
#
# Start this with `/start` — NOT a bare `overmind start`. /start injects PORT and
# VITE_RUBY_PORT into overmind's env with OVERMIND_NO_PORT=1, so both the rails
# process and the vite process (and the Rails-side ViteRuby helper) agree on the
# port. Without that injection, overmind forces PORT=5000 on rails and bin/vite
# falls back to vite.json's 3036 — the two disagree and you get
# ViteRuby::MissingEntrypointError.
#
# NO sidekiq here — main repo owns the one Sidekiq on DB 0.
rails: bundle exec rails s -p $PORT
vite:  bin/vite dev
PROCFILE_EOF

echo "    wrote Procfile.worktree"
\`\`\`

### 6. Print next steps

```bash
cat <<EOF

==> Worktree ready at: $WORKTREE_PATH

# Start everything (Rails + Vite) and open the browser:
  cd "$WORKTREE_PATH"
  /start          # boots overmind in tmux, waits for readiness, opens http://app.localtest.me:$RAILS_PORT/growth

# Do NOT run a bare 'bin/rails s' or 'overmind start' — without the port injection /start does,
# Vite and Rails land on different ports and you get ViteRuby::MissingEntrypointError.

# Run tests (isolated from main via the overridden REDIS_URL):
  bin/rspec spec/...
  yarn test ...

# Remove this worktree later:
  git worktree remove "$WORKTREE_PATH"
  # delete branch too:
  git worktree remove "$WORKTREE_PATH" && git branch -D "$BRANCH"

# Quick reference for this worktree:
#   Rails port:  $RAILS_PORT
#   Vite port:   $VITE_PORT
#   Redis DB:    $REDIS_DB    (main uses DB 0)
#   URL:         http://app.localtest.me:$RAILS_PORT/growth
#   Sidekiq:     DO NOT run here. Use Sidekiq::Testing.inline! in specs if needed.

EOF
```

## DNS / cookies notes

- `*.localtest.me` always resolves to `127.0.0.1` — no `/etc/hosts` edits needed.
- We use `app.localtest.me:<port>/growth` for every worktree (same subdomain as main, different port). Session cookies are scoped to `app.localtest.me` and ignore the port, so main + all worktrees **share one login** against the shared `trainual_development` DB. This is intentional — it's the seamless path and reuses main's proven cross-origin setup (browser on `app.localtest.me:<port>` → Vite on `127.0.0.1:<viteport>`).
- If you ever want isolated session jars per worktree, point the URL at a unique subdomain instead (e.g. `wt-mybranch.localtest.me:<port>`); host auth is disabled in dev (`config.hosts.clear` in `config/environments/development.rb`), so any subdomain resolves. Tradeoff: a separate login per worktree.

## Notes

- **Database** is shared with main repo. If this branch has uncommitted migrations, running them affects main too. Commander can run `fleet drift` (see below) to compare `db/schema.rb` against main before starting a server.
- If you need an **isolated DB**, add `DATABASE_NAME=trainual_${BRANCH//\//_}` to the WORKTREE OVERRIDES block in `.env.development.local` and run `bin/rails db:setup`.
- **Redis** is logically isolated per worktree via the DB number (`REDIS_URL=redis://localhost:6379/$REDIS_DB`). Cache keys, Sidekiq queues, ActionCable channels won't collide with main or other worktrees.
- **Sidekiq** should not run in worktrees as a convention — keep the single Sidekiq in main on DB 0. If a spec needs job execution, use `Sidekiq::Testing.inline!` or set the queue adapter to `:inline`.
- `config/master.key`, `vertex_ai_service_account_config.json`, and `rpush_firebase_google_service_account_config.json` are skipped if missing in main — they're optional.

## Commander fleet commands (run from the main repo)

Once you have worktrees created with this skill, the commander session (in the main repo) can manage them:

```bash
# Status: show all worktrees, their ports, and whether Rails is listening
for wt_path in $(git worktree list --porcelain | awk '/^worktree / && !/trainual$/ {print $2}'); do
  port=$(grep -E '^PORT=' "$wt_path/.env.development.local" 2>/dev/null | cut -d= -f2)
  branch=$(basename "$wt_path")
  if [ -n "$port" ] && lsof -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[RUNNING] $branch → http://wt-${branch}.localtest.me:$port/growth"
  else
    echo "[stopped] $branch (port $port)"
  fi
done

# Drift check: compare schema.rb across all worktrees to flag migration divergence
for wt_path in $(git worktree list --porcelain | awk '/^worktree / {print $2}'); do
  branch=$(basename "$wt_path")
  if ! diff -q "$MAIN_REPO/db/schema.rb" "$wt_path/db/schema.rb" >/dev/null 2>&1; then
    echo "DRIFT: $branch has a different db/schema.rb"
  fi
done

# Start a worktree's Rails server in a detached tmux session (survives Claude restarts):
tmux new-session -d -s "tr-$BRANCH" -c "$WORKTREE_PATH" "bin/rails s"
# Attach to it manually with: tmux a -t tr-$BRANCH

# Stop it:
tmux kill-session -t "tr-$BRANCH"

# Tail logs:
tail -f "$WORKTREE_PATH/log/development.log"
```
