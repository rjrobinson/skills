---
description: Start the Trainual dev server. Auto-detects main repo vs worktree, uses per-worktree socket + Procfile to avoid collisions.
argument-hint: (no arguments)
---

# Start the dev server

Detect whether we're in the main repo or a worktree, then start overmind with the right Procfile and a unique socket so multiple worktrees can run simultaneously.

**IMPORTANT:** run the Bash block below with `run_in_background: true` so you get control back immediately. Overmind will keep running; its output streams into `log/overmind-startup.log`. The user can attach manually later with `tmux a -t trainual-<branch>` if they started it through tmux, or just `tail -f log/overmind-startup.log` to watch.

```bash
set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Detect context: worktree vs. main repo
if [[ "$REPO_ROOT" == *"/trainual-worktrees/"* ]]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
  PROCFILE="Procfile.worktree"
  SOCKET=".overmind-${SAFE_BRANCH}.sock"
  SESSION="trainual-${SAFE_BRANCH}"
  LABEL="WT: $BRANCH"
else
  # Main repo — hand off to RJ's existing start.sh, which uses Procfile.robinson
  exec ./start.sh
fi

# Pre-flight: Procfile must exist
if [ ! -f "$PROCFILE" ]; then
  echo "ERROR: $PROCFILE not found in $REPO_ROOT — re-run /worktree to regenerate it."
  exit 1
fi

# Read this worktree's dedicated ports + Redis URL from the auto-generated override block
# in .env.development.local. tail -1 wins (the override block is appended at the end, which
# is also what dotenv resolves to when a key appears twice in one file).
ENV_LOCAL="$REPO_ROOT/.env.development.local"
RAILS_PORT=$(grep -E '^PORT=' "$ENV_LOCAL" 2>/dev/null | tail -1 | cut -d= -f2)
VITE_PORT=$(grep -E '^VITE_RUBY_PORT=' "$ENV_LOCAL" 2>/dev/null | tail -1 | cut -d= -f2)
REDIS_URL=$(grep -E '^REDIS_URL=' "$ENV_LOCAL" 2>/dev/null | tail -1 | cut -d= -f2-)

if [ -z "$RAILS_PORT" ] || [ -z "$VITE_PORT" ]; then
  echo "ERROR: PORT / VITE_RUBY_PORT missing from $ENV_LOCAL — re-run /worktree to regenerate the override block."
  exit 1
fi

URL="http://app.localtest.me:${RAILS_PORT}/growth"

toilet -f pagga -F border "Starting $LABEL" 2>/dev/null | lolcat 2>/dev/null \
  || echo "==> Starting $LABEL  |  Rails :$RAILS_PORT  Vite :$VITE_PORT  Redis ${REDIS_URL##*/}"

# --- Clean up any previous run of THIS worktree ---
# Only touches this worktree's dedicated socket/session and its dedicated ports
# ($RAILS_PORT / $VITE_PORT are branch-specific), so this never kills main or sibling worktrees.
overmind kill -s "$SOCKET" 2>/dev/null || true
tmux kill-session -t "$SESSION" 2>/dev/null || true
[ -S "$SOCKET" ] && rm -f "$SOCKET"
for p in "$RAILS_PORT" "$VITE_PORT"; do
  pid=$(lsof -tiTCP:"$p" -sTCP:LISTEN 2>/dev/null || true)
  [ -n "$pid" ] && { echo "    freeing orphaned :$p (pid $pid)"; kill "$pid" 2>/dev/null || true; }
done

# --- Launch overmind in a detached tmux session ---
# WHY the inline env + OVERMIND_NO_PORT=1 (this is the fix for the old MissingEntrypointError):
#   * Overmind otherwise injects PORT=5000 (its default base port) into every child. dotenv
#     loads non-overwriting, so Rails kept 5000 and ignored the worktree's PORT. NO_PORT=1 stops that.
#   * bin/vite never boots Rails, so it never loads .env.development.local — it would fall back to
#     vite.json's default (3036) while the Rails-side ViteRuby helper looked for the dev server at
#     VITE_RUBY_PORT. Mismatch => dev server unreachable => MissingEntrypointError.
#   Injecting PORT + VITE_RUBY_PORT into overmind's OWN env makes it propagate them uniformly to
#   BOTH processes, so the rails server, the vite server, and the ViteRuby helper all agree.
#   The vars are inlined into the command string (not `export`ed) so they survive even when a
#   tmux server is already running with a stale environment.
tmux new-session -d -s "$SESSION" -c "$REPO_ROOT" \
  "PORT=$RAILS_PORT VITE_RUBY_PORT=$VITE_PORT REDIS_URL=$REDIS_URL OVERMIND_NO_PORT=1 overmind start -f $PROCFILE -s $SOCKET 2>&1 | tee -a log/overmind-startup.log"

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "✗ tmux session failed to start — check log/overmind-startup.log"
  exit 1
fi

echo "✓ overmind started in tmux session: $SESSION"
echo "    Attach: tmux a -t $SESSION   |   Logs: tail -f log/overmind-startup.log   |   Stop: tmux kill-session -t $SESSION"

# --- Wait until BOTH Rails and Vite are listening on their expected ports, then open the browser ---
# Both-ports-listening is the definitive signal — it's exactly the thing that used to be wrong.
# The final non-500 curl confirms the page renders (vite manifest resolves) rather than erroring.
echo -n "==> Waiting for Rails (:$RAILS_PORT) + Vite (:$VITE_PORT)"
ready=0
for i in $(seq 1 90); do
  if lsof -iTCP:"$RAILS_PORT" -sTCP:LISTEN -P >/dev/null 2>&1 \
     && lsof -iTCP:"$VITE_PORT" -sTCP:LISTEN -P >/dev/null 2>&1; then
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL" || echo 000)
    if [ "$code" != "000" ] && [ "$code" != "500" ] && [ "$code" != "502" ]; then
      ready=1; break
    fi
  fi
  echo -n "."
  sleep 2
done
echo

if [ "$ready" = 1 ]; then
  echo "✓ Ready (HTTP $code) — opening $URL"
  open "$URL"
else
  echo "⚠ Server didn't report ready in time. Watch: tail -f log/overmind-startup.log"
  echo "  Open manually once up: $URL"
fi
```

After running, report the URL and session name back to the user so they can open the browser and/or attach to the tmux session.
