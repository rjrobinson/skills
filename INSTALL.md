# Installing rjrobinson-skills

This repo is a plugin marketplace. Add the marketplace once, then install
individual skills (each is its own plugin) by name: `<skill>@rjrobinson-skills`.

## Claude Code — verified

From a local checkout:

```bash
git clone <your-repo-url> ~/Code/github.com/rjrobinson/skills   # once pushed
claude plugin marketplace add ~/Code/github.com/rjrobinson/skills
claude plugin install graphify@rjrobinson-skills
```

Or straight from GitHub once pushed:

```bash
claude plugin marketplace add rjrobinson/skills
claude plugin install graphify@rjrobinson-skills
```

List / verify:

```bash
claude plugin marketplace list      # shows rjrobinson-skills
claude plugin list                  # shows installed skills
```

Update after you curate more skills:

```bash
cd ~/Code/github.com/rjrobinson/skills && git pull
# a local-path marketplace re-reads the checkout on the next session
```

Uninstall:

```bash
claude plugin uninstall graphify
claude plugin marketplace remove rjrobinson-skills
```

## Codex — mirror

`.codex-plugin/marketplace.json` carries the same catalog data. Depending on your
Codex version:

```bash
codex plugin marketplace add rjrobinson/skills --ref main
codex plugin add graphify@rjrobinson-skills
```

> **Note:** the Claude Code path above is the one fully verified against
> installed marketplaces on this machine. The Codex and `.agents` catalogs are
> generated mirrors of the same data. If Codex's current plugin schema differs,
> the fix is in one place — `bin/generate_manifests.py` — and `bin/skills sync`
> re-emits all three. No skill content needs to move.

## Cross-agent (`.agents`)

`.agents/plugins/marketplace.json` follows the shared cross-agent plugin standard
(same shape as other multi-agent plugin repos), pointing at the same `plugins/<name>`
directories. Agents that read that standard can install from this repo directly.
