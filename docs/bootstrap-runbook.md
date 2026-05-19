# Bootstrap runbook — wire a target repo for Skill Generator v2

A 10-minute, copy-paste runbook that wires one target Java repository for
Skill Generator v2. After this runs, AI assistants (Copilot Chat, Claude,
Codex) in that repo will read feature skills first before answering or
editing.

This is intentionally a runbook, not a fifth agent. Bootstrap is a one-time
setup; it does not need its own agent loop.

---

## When to run this

- Once per target Java repository, before the first `skill-generator` run
- Re-run only when the templates here change (rare)

---

## What gets created in the target repo

| File | Source template | Purpose |
|---|---|---|
| `.github/copilot-instructions.md` | `docs/templates/copilot-instructions.md` | Tells Copilot Chat to read `.github/skills/` first |
| `CLAUDE.md` (at repo root) | `docs/templates/CLAUDE.md` | Tells Claude Code to read `.github/skills/` first |
| `AGENTS.md` (at repo root) | `docs/templates/AGENTS.md` | Tells Codex and generic agents to read `.github/skills/` first |
| `.github/skills/README.md` | `docs/templates/skills-README.md` | Human-facing explanation of what lives under `.github/skills/` |
| `.github/skills/.gitkeep` | (empty) | Keeps the directory tracked before the first skill is generated |

Catalog (`.github/skills/catalog.md`) and per-feature `SKILL.md` files are
created by the first `skill-generator` run — not by bootstrap.

---

## Prerequisites

- `$SKILL_GENERATOR_HOME` is set in your shell, pointing at the Skill_Generator
  checkout. Example: `export SKILL_GENERATOR_HOME=~/Documents/Customized_Agent_For_Developers/Skill_Generator`
- You are at the root of the target Java repository, on a clean working tree
- You have permission to create files under `.github/` and at the repo root
- The target repo does not already have a conflicting `CLAUDE.md` or
  `AGENTS.md` — if it does, see "Handling conflicts" below

---

## The runbook

Run these commands from the root of the target Java repository.

```bash
# 1. Create the skills directory structure
mkdir -p .github/skills
touch .github/skills/.gitkeep

# 2. Drop the per-host instruction files
cp "$SKILL_GENERATOR_HOME/docs/templates/copilot-instructions.md" \
   .github/copilot-instructions.md

cp "$SKILL_GENERATOR_HOME/docs/templates/CLAUDE.md" \
   CLAUDE.md

cp "$SKILL_GENERATOR_HOME/docs/templates/AGENTS.md" \
   AGENTS.md

# 3. Drop the skills/README.md
cp "$SKILL_GENERATOR_HOME/docs/templates/skills-README.md" \
   .github/skills/README.md

# 4. Verify
ls -la .github/skills/ CLAUDE.md AGENTS.md .github/copilot-instructions.md

# 5. Commit
git add .github/skills/.gitkeep \
        .github/skills/README.md \
        .github/copilot-instructions.md \
        CLAUDE.md \
        AGENTS.md
git commit -m "chore: bootstrap Skill Generator v2 (instruction files + skills dir)"
```

That is the entire bootstrap. The repo is now ready for the first
`skill-generator` run.

---

## Handling conflicts

### The target repo already has a `CLAUDE.md`

Don't overwrite it. Two safer options:

1. **Append the skill-context section** from `docs/templates/CLAUDE.md`
   to the existing file. Preserve everything else.
2. **Keep the existing file and rely on `.github/copilot-instructions.md`
   plus `AGENTS.md` for cross-host coverage.** Claude Code will still
   read `.github/skills/` if you mention the path in the existing
   `CLAUDE.md`.

### The target repo already has an `AGENTS.md`

Same approach as `CLAUDE.md` — append, do not overwrite.

### The target repo already uses `.github/copilot-instructions.md`

Append the feature-skills section. The file is allowed to contain multiple
instruction blocks.

---

## After bootstrap

1. Run the first `skill-generator` against the repo. This produces
   `.github/skills/<feature>/SKILL.md` files, the catalog, and the
   gen-audit log.
2. Review and commit per the generator's halt gates.
3. Tell the team to start using their AI assistant in the repo — Copilot
   Chat, Claude Code, or Codex. The assistant will pick up the skills via
   the instruction files dropped during bootstrap.

---

## How to verify bootstrap worked

Open the target repo in a fresh AI-assistant session. Ask:

> "What features are in this repo?"

A correctly bootstrapped repo with at least one generated skill should
return the list from `.github/skills/catalog.md`, not a guess based on
package names. If the assistant guesses package-based, the instruction
files were not loaded — verify the files are at the paths above.

---

## When to re-run this runbook

- The templates in `$SKILL_GENERATOR_HOME/docs/templates/` change (e.g.,
  the catalog format evolves)
- A new approved host AI is added to the org and needs its own
  instruction file
- The target repo's `.github/` is rewritten by a CI migration

Re-running is safe: the runbook re-copies templates over existing files
(except where conflict guidance above applies).

---

## What this runbook explicitly does not do

- Does not run `skill-generator` — that is a separate step requiring an
  approved host AI session
- Does not regenerate skills — the updater handles that
- Does not configure CI — the PR-policy runbook (`docs/pr-policy.md`)
  handles that
- Does not configure CODEOWNERS — that is a per-repo decision; see
  ownership guidance in `docs/enterprise-agent-selection-guide.md`
