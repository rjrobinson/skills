# rjrobinson-skills

My personal marketplace of Claude Code / Codex skills. One installable **plugin per skill**, so I can enable, disable, review, and version each one independently.

This repo **is** the marketplace — add it once, then install any skill from it by name.

## Layout

```
.claude-plugin/marketplace.json   Claude Code marketplace catalog  (generated)
.codex-plugin/marketplace.json    Codex catalog                    (generated, mirror)
.agents/plugins/marketplace.json  cross-agent catalog              (generated, mirror)
plugins/<skill>/                  one plugin per skill  ← source of truth
  ├─ .claude-plugin/plugin.json   (generated)
  └─ skills/<skill>/SKILL.md      the skill itself (copied in, reviewable)
bin/skills                        curate: add / remove / list / sync
bin/generate_manifests.py         rebuilds all 3 catalogs from plugins/
```

**`plugins/` is the single source of truth.** The three catalog files are derived
artifacts — never hand-edit them. `bin/skills` mutates `plugins/` and then
regenerates every catalog, so they can't drift.

## Curating skills

```bash
bin/skills add          # fzf-pick skills from ~/.claude/skills, copy them in
bin/skills add --from /some/other/skills/dir
bin/skills list         # what's in the marketplace
bin/skills remove       # fzf-pick skills to drop
bin/skills sync         # rebuild catalogs after a manual edit
```

`add` copies the selected skill folder into `plugins/<name>/skills/<name>/`.
Because it's a copy under git, every skill is reviewable in diffs and decoupled
from `~/.claude`. Re-running `add` on the same skill refreshes it from source.

## Installing

See [INSTALL.md](INSTALL.md). Short version:

```bash
# Claude Code (verified path)
claude plugin marketplace add rjrobinson/skills     # or a local path
claude plugin install graphify@rjrobinson-skills
```

## Adding a brand-new skill you wrote

1. Create `plugins/<name>/skills/<name>/SKILL.md` (add a `description:` in the frontmatter).
2. `bin/skills sync`.

That's it — the catalogs pick it up.
