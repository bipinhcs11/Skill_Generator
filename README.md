# Skill Generator v2

Turns a Java repository into feature-based SKILL.md files that AI assistants can
read before answering feature questions. A developer types one sentence. The
agent walks the repo, produces auditable evidence per feature, generates
reviewable skills with confidence and dependency metadata, self-validates, and
keeps the dependency graph ready for future updates.

The enterprise value is straightforward: save developer hours, improve the
quality of generated code changes, reduce repeated GitHub Copilot premium-token
spend on repo rediscovery, and give every approved coding agent durable feature
context before it edits code.

**Status:** v2 foundation complete and ready for second-team evaluation. Not yet
ready for unsupervised enterprise-wide rollout. See `docs/v2-progress-report.md`
for current state and next actions.

---

## The developer experience

1. Open VS Code, IntelliJ, or any IDE with Claude Code / Copilot Chat / Codex
2. Open the target Java repository
3. Type: *"Analyze this project and generate the feature skills"*
4. Agent walks the repo and emits **structured evidence per candidate feature**
5. Review the evidence and any LOW-confidence review queue.
6. Agent generates one SKILL.md per feature, self-validates, runs the dependency pass.
7. Agent shows the summary. Type "yes" to commit.

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
│   ├── skill-tracker/SKILL.md      ← PR/change impact detection, no edits
│   ├── skill-updater/SKILL.md      ← In-place updates from approved impact plans
│   ├── file-delivery/SKILL.md      ← Reference skill
│   ├── invoice-compare/SKILL.md    ← Reference skill
│   └── payment-method-determination/SKILL.md  ← Reference skill
├── lib/                            ← Deterministic structural spine (~494 LOC)
│   ├── validate.py                 ← Frontmatter + section order + format checks
│   ├── citation_check.py           ← ClassName.methodName() / FQCN citation presence
│   ├── frontmatter.py              ← Parse/serialize YAML frontmatter
│   └── audit_log.py                ← Format evidence-phase audit artifacts
├── examples/                       ← Reference Java examples
└── docs/                           ← Guides, flow diagrams, templates, design history
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
- **Not in `lib/`:** crawler logic, feature inference, feature grouping heuristics,
  planner logic, semantic analysis of any kind

---

## Agent roles

| Agent skill | When to use it | Output |
|---|---|---|
| `skills/skill-generator/SKILL.md` | First run on a Java repo with no generated skills | Feature map, SKILL.md files, dependency graph, audit log |
| `skills/skill-tracker/SKILL.md` | PR review or local change check: "which skills are impacted?" | Impact report, stale-skill findings, review queue, recommended next step |
| `skills/skill-updater/SKILL.md` | After tracker or human approval says skills need updates | Minimal edits to affected SKILL.md files and dependency metadata |
| `skills/skill-validator/SKILL.md` | Quality review after generation or update | PASS / NEEDS_REVIEW / BLOCKING_ISSUES verdicts |

The tracker is intentionally read-only. It helps teams avoid rewriting every
skill for every PR, which is where the steady-state time and premium-token
savings come from.

---

## The headline risk

**Silent plausible wrongness.** A pure-agent system can fail *beautifully* —
coherent but wrong, persuasive but incomplete. Six layers defend against this:

1. **Evidence phase** — the agent produces auditable structured reasoning per
   candidate feature before generation
2. **Confidence metadata** — every generated skill carries `confidence` and
   `review_required`, so LOW-confidence skills become reviewable drafts rather
   than hidden uncertainty
3. **Dependency graph** — generated skills maintain `depends_on` and
   `depended_on_by`, so updates propagate across feature boundaries
4. **Tracker pass** — PR changes can be checked for stale or missing skills
   before any rewrite happens
5. **Halt gates** — human reviews evidence + plan, and reviews output before commit
6. **Deterministic spine** — structural errors caught before output reaches the human

See `skills/skill-generator/SKILL.md` for the complete agent contract.

For Copilot rollout, copy `docs/templates/copilot-instructions.md` into each
target repo as `.github/copilot-instructions.md` so Copilot reads feature skills
before answering or editing.

For later code changes, use `skills/skill-tracker/SKILL.md` first when you need
to know whether a PR affects any skills. If updates are needed, use
`skills/skill-updater/SKILL.md`. The updater maps git diffs across Java,
properties/YAML, MyBatis mapper XML, SQL/migrations, Spring Batch, and scripts
to affected feature skills, propagates through dependencies, bumps versions,
and records `.github/skills/.skill-update-audit.md`.

---

## Recommended host for first-run generation

| Workload | Recommended host |
|---|---|
| Unknown, large, or XML-heavy repo | Claude Opus-class or Codex high-reasoning |
| Clean Spring Boot service | Claude Sonnet-class or Codex |
| PR impact tracking | Sonnet-class, Codex, or Copilot Chat |
| Incremental update | Sonnet-class, Codex, or Copilot Chat |
| Daily skill consumption | Any host — Copilot Chat, Claude, Codex |

See `docs/enterprise-agent-selection-guide.md` for the full recommendation.

---

## For enterprise teams

See `docs/enterprise-agent-selection-guide.md` for the 10-team rollout model
and `docs/release-readiness-checklist.md` for the gate checklist before
rolling out to more than one team.
