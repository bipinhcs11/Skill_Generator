# Skill Generator v2

Turns a Java repository into a set of feature-based SKILL.md files.
A developer types one sentence. The agent walks the repo, produces
auditable evidence per domain, halts for human review, generates skill
files, and self-validates before committing.

**Status:** Foundation pass complete (Milestone 0 + Milestone 1 in progress).
Not yet ready for production use. See `docs/v2-progress-report.md` for
current state and next actions.

---

## The developer experience

1. Open VS Code, IntelliJ, or any IDE with Claude Code / Copilot Chat / Codex
2. Open the target Java repository
3. Type: *"Analyze this project and generate the feature skills"*
4. Agent walks the repo and emits **structured evidence per candidate domain**
5. Review the evidence. Type your approval or request changes.
6. Agent generates one SKILL.md per domain, self-validates, runs the dependency pass
7. Agent shows you the summary. Type "yes" to commit.

Five typed messages. No CLI to install. No Python dependencies for the agent workflow.

Set this once in any shell or IDE terminal where the agent will run validation:

```bash
export SKILL_GENERATOR_HOME=/path/to/Skill_Generator
```

The generator and updater call `$SKILL_GENERATOR_HOME/lib/validate.py` and
`$SKILL_GENERATOR_HOME/lib/citation_check.py` from inside the target Java repo.

---

## Repository layout

```
Skill_Generator/
├── skills/
│   ├── skill-generator/SKILL.md    ← The agent contract (start here)
│   ├── skill-validator/SKILL.md    ← Post-generation semantic review
│   ├── skill-updater/SKILL.md      ← Phase 2: in-place updates from git diffs
│   ├── file-delivery/SKILL.md      ← Reference skill
│   ├── invoice-compare/SKILL.md    ← Reference skill
│   └── payment-method-determination/SKILL.md  ← Reference skill
├── lib/                            ← Deterministic structural spine (~494 LOC)
│   ├── validate.py                 ← Frontmatter + section order + format checks
│   ├── citation_check.py           ← ClassName.methodName() / FQCN citation presence
│   ├── frontmatter.py              ← Parse/serialize YAML frontmatter
│   └── audit_log.py                ← Format evidence-phase audit artifacts
├── examples/                       ← Reference Java examples
├── docs/                           ← Guides, diagrams, design history
└── legacy/                         ← v1 Python pipeline (preserved, not deleted)
    └── FeatureBased_Skill_Generator_Agent/
```

---

## The architectural principle

Move deterministic enforcement to the narrowest possible layer.
Semantic understanding goes to the AI. Structural enforcement stays in `lib/`
— but only because deterministic code is genuinely better at
"does this frontmatter parse" than the agent is.

The `lib/` files have a 500 LOC combined hard cap for structural enforcement.
`audit_log.py` counts inside that cap for now, so there is intentionally little
headroom left. If the next enterprise test needs more deterministic support,
raise the cap with a design-history decision instead of quietly growing `lib/`.
The boundary is:

- **In `lib/`:** frontmatter parsing, section-order validation, citation regex,
  audit-log formatting
- **Not in `lib/`:** crawler logic, domain inference, feature grouping heuristics,
  planner logic, semantic analysis of any kind

---

## The headline risk

**Silent plausible wrongness.** The v1 Python pipeline failed loudly.
A pure-agent system fails *beautifully* — coherent but wrong, persuasive but
incomplete. Three layers defend against this:

1. **Evidence phase** — the agent produces auditable structured reasoning per
   candidate domain before generation
2. **Confidence metadata** — every generated skill carries `confidence` and
   `review_required`, so LOW-confidence skills become reviewable drafts rather
   than hidden uncertainty
3. **Dependency graph** — generated skills maintain `depends_on` and
   `depended_on_by`, so updates propagate across feature boundaries
4. **Halt gates** — human reviews evidence + plan, and reviews output before commit
5. **Deterministic spine** — structural errors caught before output reaches the human

See `skills/skill-generator/SKILL.md` for the complete agent contract.

For later code changes, use `skills/skill-updater/SKILL.md`. It maps git diffs
across Java, properties/YAML, MyBatis mapper XML, SQL/migrations, Spring Batch,
and scripts to affected feature skills, propagates through dependencies, bumps
versions, and records `.github/skills/.skill-update-audit.md`.

---

## What is in `legacy/`

The v1 Python pipeline: `crawler.py`, `planner.py`, `generator.py`,
`linker.py`, `doctor.py`. These are preserved in
`legacy/FeatureBased_Skill_Generator_Agent/` for reference and rollback.
They are not used by v2.

The eight defects found during the petclinic real-repo test drove the v2 pivot.
See `docs/design-history/` for the full record.

---

## Recommended host for first-run generation

| Workload | Recommended host |
|---|---|
| Unknown or legacy repo | Claude Opus-class or Codex high-reasoning |
| Clean Spring Boot service | Claude Sonnet-class or Codex |
| Incremental update | Sonnet-class, Codex, or Copilot Chat |
| Daily skill consumption | Any host — Copilot Chat, Claude, Codex |

See `docs/enterprise-agent-selection-guide.md` for the full recommendation.

---

## For enterprise teams

See `docs/enterprise-agent-selection-guide.md` for the 10-team rollout model
and `docs/release-readiness-checklist.md` for the gate checklist before
rolling out to more than one team.
