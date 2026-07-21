#!/usr/bin/env python3
"""Regenerate every marketplace/plugin manifest from the plugins/ tree.

The plugins/ directory is the single source of truth. Each skill lives at:

    plugins/<name>/skills/<name>/SKILL.md

This script scans those directories, reads each SKILL.md's frontmatter for a
description (and optional category), and (re)writes:

  * plugins/<name>/.claude-plugin/plugin.json   (per-plugin manifest)
  * .claude-plugin/marketplace.json             (Claude Code marketplace)
  * .codex-plugin/marketplace.json              (Codex, mirror)
  * .agents/plugins/marketplace.json            (cross-agent standard, mirror)

Nothing here is hand-edited; running `bin/skills sync` calls this so the
manifests can never drift from what is actually on disk.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

# ── repo layout ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "plugins"

MARKETPLACE_NAME = "rjrobinson-skills"
MARKETPLACE_DESC = "R.J. Robinson's personal library of Claude Code / Codex skills — one installable plugin per skill."
DEFAULT_VERSION = "0.1.0"
DEFAULT_CATEGORY = "general"


def git_config(key: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(ROOT), "config", key],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out or None
    except Exception:
        return None


def owner() -> dict:
    name = git_config("user.name") or "R.J. Robinson"
    email = git_config("user.email")
    o = {"name": name}
    if email:
        o["email"] = email
    return o


def parse_frontmatter(skill_md: Path) -> dict:
    """Return {name, description, category, trigger} from SKILL.md frontmatter.

    Deliberately small: skill frontmatter is flat `key: value`. Values may be
    quoted; a `>` / `|` block scalar or wrapped line is flattened to its first
    line, which is all a manifest needs.
    """
    if not skill_md.is_file():
        return {}
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    data: dict[str, str] = {}
    current: str | None = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        # continuation of a wrapped/indented value
        if raw[:1] in (" ", "\t") and current:
            data[current] += " " + raw.strip()
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            val = ""  # block scalar; continuation lines fill it in
        data[key] = val
        current = key
    return data


def discover() -> list[dict]:
    """One record per plugin dir, sorted by name.

    A plugin may ship a skill (skills/<name>/SKILL.md) and/or one or more
    slash commands (commands/*.md). The description is read from whichever
    exists (skill wins if both are present).
    """
    records: list[dict] = []
    if not PLUGINS_DIR.is_dir():
        return records
    for plugin_dir in sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir()):
        name = plugin_dir.name
        skills_root = plugin_dir / "skills"
        commands_root = plugin_dir / "commands"

        skill_md = next(skills_root.glob("*/SKILL.md"), None) if skills_root.is_dir() else None
        command_files = sorted(commands_root.glob("*.md")) if commands_root.is_dir() else []

        source_md = skill_md or (command_files[0] if command_files else None)
        fm = parse_frontmatter(source_md) if source_md else {}
        kind = "skill" if skill_md else ("command" if command_files else "plugin")
        desc = fm.get("description") or f"{name} {kind}"
        records.append({
            "name": name,
            "description": desc.strip(),
            "category": (fm.get("category") or DEFAULT_CATEGORY).strip(),
            "rel": f"./plugins/{name}",
            "has_skills": skill_md is not None,
            "has_commands": bool(command_files),
        })
    return records


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build(records: list[dict]) -> None:
    own = owner()

    # per-plugin plugin.json
    for r in records:
        write_json(
            PLUGINS_DIR / r["name"] / ".claude-plugin" / "plugin.json",
            {
                "name": r["name"],
                "description": r["description"],
                "version": DEFAULT_VERSION,
                "author": own,
            },
        )

    # Claude Code marketplace (verified schema)
    write_json(
        ROOT / ".claude-plugin" / "marketplace.json",
        {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": MARKETPLACE_NAME,
            "description": MARKETPLACE_DESC,
            "owner": own,
            "plugins": [
                {
                    "name": r["name"],
                    "description": r["description"],
                    "source": r["rel"],
                    "category": r["category"],
                    "author": own,
                }
                for r in records
            ],
        },
    )

    # Codex marketplace (mirror — same data, Codex plugin-marketplace shape)
    def codex_entry(r: dict) -> dict:
        e = {
            "name": r["name"],
            "description": r["description"],
            "source": r["rel"],
            "category": r["category"],
        }
        if r["has_skills"]:
            e["skills"] = f"{r['rel']}/skills/"
        if r["has_commands"]:
            e["commands"] = f"{r['rel']}/commands/"
        return e

    write_json(
        ROOT / ".codex-plugin" / "marketplace.json",
        {
            "name": MARKETPLACE_NAME,
            "description": MARKETPLACE_DESC,
            "owner": own,
            "plugins": [codex_entry(r) for r in records],
        },
    )

    # Cross-agent standard (mirror of i-have-adhd/.agents/plugins/marketplace.json)
    write_json(
        ROOT / ".agents" / "plugins" / "marketplace.json",
        {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "R.J. Robinson's Skills"},
            "plugins": [
                {
                    "name": r["name"],
                    "source": {"source": "directory", "path": r["rel"]},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": r["category"],
                }
                for r in records
            ],
        },
    )


def main() -> None:
    records = discover()
    build(records)
    if not records:
        print("No skills yet. Run `bin/skills add` to pick some.")
        return
    print(f"Regenerated manifests for {len(records)} plugin(s):")
    for r in records:
        kind = "skill" if r["has_skills"] else ("command" if r["has_commands"] else "empty")
        print(f"  • {r['name']:<28} {kind:<8} {r['category']}")


if __name__ == "__main__":
    main()
