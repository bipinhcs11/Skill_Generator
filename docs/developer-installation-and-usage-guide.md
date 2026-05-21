# Developer installation and usage guide

This guide explains how a Java team installs Skill Generator v2 into a target
repository and how developers use the generated feature skills from VS Code,
IntelliJ, Copilot Chat, Claude, Codex, or another approved coding agent.

The important idea: developers do not install a heavy runtime in every repo.
The platform or repo owner runs Skill Generator once to create durable feature
context under `.github/skills/`. After that, normal IDE assistants read those
skills before answering feature questions or changing code.

---

## Quickstart

For a repo owner who just wants to see the flow work:

1. Set `SKILL_GENERATOR_HOME` to the central Skill Generator checkout.
2. Bootstrap the target repo with the instruction files.
3. Run `skill-generator` from an approved host AI session.
4. Validate every generated `SKILL.md` and the catalog.
5. Commit `.github/skills/` only after feature-lead review.

Developers who only consume skills usually start at "VS Code usage" or
"IntelliJ usage" below.

---

## Audience

| Reader | What you do |
|---|---|
| Platform / architecture team | Own the Skill Generator checkout, templates, rollout rules, and support path. |
| Repo owner / feature lead | Bootstrap the target repo, run first generation, review skills, and commit them. |
| Developer | Use committed skills from VS Code, IntelliJ, Copilot Chat, Claude, Codex, or another approved agent. |
| PR reviewer | Run `skill-tracker` or require a tracker-clean report when a PR changes feature behavior. |

Most developers should not regenerate all skills. They should consume committed
skills and run the tracker/updater only when a change actually affects feature
behavior.

---

## What gets installed

| Location | Artifact | Purpose |
|---|---|---|
| Central/tooling checkout | `Skill_Generator/` | Holds the agent contracts, templates, and deterministic validators. |
| Target Java repo | `.github/skills/<feature-id>/SKILL.md` | Feature context committed with the application code. |
| Target Java repo | `.github/skills/catalog.md` | Maps business language, aliases, and acronyms to skill IDs. |
| Target Java repo | `.github/copilot-instructions.md` | Tells GitHub Copilot to read feature skills first. |
| Target Java repo | `CLAUDE.md` | Tells Claude Code to read feature skills first. |
| Target Java repo | `AGENTS.md` | Tells Codex and generic agents to read feature skills first. |
| Target Java repo | `.github/skills/.skill-gen-audit.md` | Records evidence, confidence decisions, exclusions, validation, and dependency choices. |

There is no npm package, Python package, Maven plugin, or IDE plugin owned by
Skill Generator v2. The IDE plugin is the normal host assistant, such as
GitHub Copilot in VS Code or IntelliJ.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Git access | Required for the target repo and the central Skill Generator checkout. |
| Python 3 | Used only for deterministic validation scripts in `lib/`. No third-party Python dependencies are required. |
| Approved host AI | Copilot Chat, Claude, Codex, or another enterprise-approved agent with repo file access. |
| Language scope (v2) | Java repositories only: Spring, MyBatis, Spring Batch, SQL/migrations, config, and scripts. |
| Java repo opened locally | First-run generation needs filesystem access to Java, config, SQL, MyBatis XML, Spring Batch, and scripts. |
| Clean target branch | First generation creates many docs; start clean so review is obvious. |
| Security review path | Generated skills must not contain passwords, tokens, client secrets, real customer data, or real personal data. |

Approval is your organization's call. In most enterprises, "approved host AI"
means the platform or security team's vetted list of AI tools that may read
local source code. Do not run first-generation against a repo with an
unapproved assistant.

Skill Generator v2 is not designed for Python, TypeScript, Go, or polyglot
service analysis yet. If your team has non-Java services, talk to the platform
team before running this workflow. Running v2 against non-Java code will
produce low-quality skills.

Set this environment variable once in the shell or IDE terminal used by the
agent:

```bash
export SKILL_GENERATOR_HOME=/path/to/Skill_Generator
```

Quick validation:

```bash
test -f "$SKILL_GENERATOR_HOME/skills/skill-generator/SKILL.md"
test -f "$SKILL_GENERATOR_HOME/lib/validate.py"
```

---

## One-time platform setup

The platform or architecture team should keep one approved checkout of this
repo and publish its path to pilot teams.

```bash
git clone https://github.com/bipinhcs11/Skill_Generator.git
cd Skill_Generator

# Use the platform-approved branch or release tag.
# Pilot example before this work is merged. Update this checkout instruction
# when the branch merges to main or when the platform team publishes a release.
git checkout feat/v2-enterprise-rollout-foundation

export SKILL_GENERATOR_HOME="$PWD"
python3 -m py_compile lib/*.py
```

For enterprise rollout, publish the environment-variable setup in the team's
standard shell profile, IDE terminal profile, or internal onboarding page.

---

## One-time target repo bootstrap

Run this from the root of the Java repo that will receive skills.

```bash
mkdir -p .github/skills
touch .github/skills/.gitkeep

cp "$SKILL_GENERATOR_HOME/docs/templates/copilot-instructions.md" \
   .github/copilot-instructions.md

cp "$SKILL_GENERATOR_HOME/docs/templates/CLAUDE.md" \
   CLAUDE.md

cp "$SKILL_GENERATOR_HOME/docs/templates/AGENTS.md" \
   AGENTS.md

cp "$SKILL_GENERATOR_HOME/docs/templates/skills-README.md" \
   .github/skills/README.md
```

If the target repo already has `.github/copilot-instructions.md`, `CLAUDE.md`,
or `AGENTS.md`, do not overwrite it. Merge carefully: keep repository-specific
rules at the top, then append the feature-skills section as a new section near
the end. If the existing file already has an AI-context section, merge the
Skill Generator rules into that section instead of duplicating headings.

Commit bootstrap separately from generated skills:

```bash
git add .github/copilot-instructions.md CLAUDE.md AGENTS.md \
        .github/skills/README.md .github/skills/.gitkeep
git commit -m "chore: bootstrap Skill Generator v2"
```

Detailed bootstrap guidance lives in `docs/bootstrap-runbook.md`.

---

## First-run generation

First-run generation is normally done by a repo owner or feature lead using a
stronger host AI session. It is a reviewed architecture artifact, not a casual
per-developer action.

Open the target repo in the approved agent session and use this prompt:

```text
Use $SKILL_GENERATOR_HOME/skills/skill-generator/SKILL.md.

First verify the target repo has been bootstrapped: check that
.github/copilot-instructions.md, CLAUDE.md, and AGENTS.md exist.
If any are missing, stop and tell me to run the bootstrap runbook first.

Run Skill Generator v2 for this Java repository.
Generate feature skills under .github/skills/.
Create or refresh .github/skills/catalog.md.
Create .github/skills/.skill-gen-audit.md.
Read Java, config/properties/YAML, MyBatis mapper XML, SQL/migrations,
Spring Batch jobs, and scripts before deciding feature boundaries.
Do not include secrets, tokens, passwords, or real personal data.
Run the deterministic validators.
Stop before commit and show me the generated summary.
```

After generation, run validation from the target repo:

```bash
for f in .github/skills/*/SKILL.md; do
  python3 "$SKILL_GENERATOR_HOME/lib/validate.py" "$f"
  python3 "$SKILL_GENERATOR_HOME/lib/citation_check.py" "$f"
done
```

Run a catalog sanity check too. The deterministic `lib/` validators check
individual `SKILL.md` files; the catalog also needs to point at real skills:

```bash
test -f .github/skills/catalog.md
python3 - <<'PY'
from pathlib import Path
import re

catalog = Path(".github/skills/catalog.md")
missing = []
for target in re.findall(r"\]\(([^)#]+/SKILL\.md)\)", catalog.read_text()):
    path = catalog.parent / target
    if not path.exists():
        missing.append(str(path))

if missing:
    print("Catalog links missing:")
    for item in missing:
        print(f"  - {item}")
    raise SystemExit(1)

print("PASS: catalog links resolve")
PY
```

If the catalog drifts from the skills, run `skill-tracker` first and then
`skill-updater`; the updater refreshes `catalog.md` when discovery metadata,
aliases, business terms, owner metadata, or dependencies change.

### When the host can't read everything

Some hosts deny access to part of the source tree mid-run because of corporate
sandboxes, macOS Privacy permissions, missing submodules, or repo-specific
ACLs. When that happens, `skill-generator` should fail safe:

- Set `confidence: MEDIUM` or `confidence: LOW` on affected skills.
- Set `review_required: true`.
- Add a generation note explaining what was observed versus inferred.
- Record the access limitation in `.github/skills/.skill-gen-audit.md`.

Treat those skills as drafts. They may still contain useful structure, but
behavior claims must be verified against source before developers rely on them
for code generation.

Review before commit:

| Review item | What to check |
|---|---|
| Feature boundaries | Skills match business capabilities, not random packages. |
| Confidence | LOW or `review_required: true` skills are explicitly reviewed by a feature lead. |
| Dependencies | `depends_on` and `depended_on_by` capture cross-feature impact. |
| Ownership | `owner_team`, `business_owner`, and `technical_owner` are populated where derivable; gaps are documented; team identifiers match CODEOWNERS conventions. |
| Evidence | Audit explains why features were generated or excluded. |
| Secrets / PII | No password values, token values, client secrets, customer data, or real personal data. |
| Source citations | Key classes and data flow reference real classes and methods. |

Commit generated skills only after review:

```bash
git add .github/skills
git commit -m "docs: generate feature skills"
```

Example of what a generated skill looks like:

```markdown
---
skill_id: invoice-compare
version: 1
last_updated: "2026-05-20"
feature_name: "Invoice Compare"
confidence: HIGH
review_required: false
primary_packages:
  - com.example.billing.invoice
key_classes:
  - com.example.billing.invoice.InvoiceCompareService
depends_on:
  - participant-eligibility
aliases:
  - invoice comparison
  - invoice compare report
business_terms:
  - participant eligibility
---

## Overview
Invoice Compare owns the reconciliation rules for invoice comparison reports.
```

---

## VS Code usage

### Install / enable the host assistant

Use the normal enterprise-approved extension, such as GitHub Copilot, Claude
Code, or Codex. Skill Generator does not install a VS Code extension of its own.

For GitHub Copilot, keep the extension current and make sure repository custom
instructions are enabled. VS Code supports `.github/copilot-instructions.md`
and path-specific `.github/instructions/*.instructions.md` files. This repo's
bootstrap uses the repository-wide file for broad compatibility.

Official reference: <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions?tool=vscode>

### Daily developer workflow

Open the target repo in VS Code and ask normal feature questions:

```text
Modify invoice comparison to include participant eligibility status.
Read .github/skills/catalog.md first, then read the matching skill and dependencies.
```

Expected assistant behavior:

1. Reads `.github/skills/catalog.md`.
2. Maps the developer's words to a feature skill through `aliases` and `business_terms`.
3. Reads `.github/skills/<feature-id>/SKILL.md`.
4. Reads any `depends_on` skills.
5. Opens only relevant source files from `key_classes` and `primary_packages`.
6. Verifies source before editing code.

If the assistant starts guessing from package names, interrupt it and say:

```text
Stop. Use the Skill Generator workflow.
Read .github/skills/catalog.md and the matching SKILL.md before answering.
```

### Running tracker in VS Code

Before or during a PR that changes feature behavior:

```text
Use $SKILL_GENERATOR_HOME/skills/skill-tracker/SKILL.md.
Review my current git diff and report which feature skills are impacted.
Do not edit files.
```

If the tracker reports impact:

```text
Use $SKILL_GENERATOR_HOME/skills/skill-updater/SKILL.md.
Update only the impacted skills approved in the tracker report.
Run validation and update the skill update audit.
Stop before commit.
```

---

## IntelliJ usage

### Install / enable the host assistant

Use the normal enterprise-approved IntelliJ assistant, most commonly the GitHub
Copilot plugin. Skill Generator does not install an IntelliJ plugin of its own.

For Copilot in JetBrains IDEs, keep the plugin current. JetBrains IDEs support
a single repository `.github/copilot-instructions.md` file, which is exactly
what the bootstrap runbook creates.

Official reference: <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions?tool=jetbrains>

### Daily developer workflow

Open the target repo in IntelliJ and ask Copilot Chat or the approved assistant:

```text
I need to change the course aggregation response.
Read .github/skills/catalog.md first, then read the matching SKILL.md and dependencies.
Tell me which source files matter before editing.
```

For IntelliJ, be more explicit in the prompt if the assistant does not show the
skill files as references. Some IDE assistants are less deterministic than a
terminal-based agent about which repo files they load.

### Running first generation from an IntelliJ team

There are two safe patterns:

| Pattern | When to use |
|---|---|
| IntelliJ for coding, external Claude/Codex session for generation | Recommended for first-run generation, older repos, or high-risk modules. |
| IntelliJ Copilot Chat for consumption and small tracker checks | Good after skills are already committed and the repo is indexed. |

If the team wants to run generation while working in IntelliJ, open an approved
terminal-based agent from the target repo root and use the first-run generation
prompt above. The generated files still land in the same IntelliJ project.

---

## What developers ask after skills exist

| Developer task | Prompt pattern |
|---|---|
| Understand a feature | `Read .github/skills/catalog.md, then explain the <feature> skill and its key classes.` |
| Modify a feature | `Read the matching skill and depends_on skills first. Then propose the source files to change.` |
| Check PR impact | `Use skill-tracker. Review my git diff and report impacted skills only. Do not edit.` |
| Update skills after a behavior change | `Use skill-updater for the tracker-approved skills only. Validate and update the audit.` |
| Add a new feature | `Run skill-generator for the new feature candidate or ask whether this belongs in an existing skill.` |
| Add a natural-language alias to a feature | `Edit .github/skills/<feature>/SKILL.md frontmatter, add the phrase to aliases or business_terms, then run skill-updater to refresh catalog.md.` |
| Review generated skill quality | `Use skill-validator and return PASS / NEEDS_REVIEW / BLOCKING_ISSUES.` |

Use `aliases` for phrases developers say casually, including acronyms,
internal nicknames, report names, and service names. Use `business_terms` for
domain concepts that should map to the feature even if they are not aliases.
For example, `INVCOMP` belongs in `aliases`; `participant eligibility` may
belong in `business_terms` if it is a concept the skill explains.

---

## PR policy

Any PR that changes business behavior should include one of these:

1. A tracker report saying no skills are impacted.
2. Updated impacted skills plus `.github/skills/.skill-update-audit.md`.
3. A feature lead note explaining why the skill update is intentionally deferred.

Behavior-changing files include Java, properties/YAML, MyBatis XML, SQL or
migrations, Spring Batch jobs, scheduler definitions, and operational scripts
that change feature behavior.

Detailed policy lives in `docs/pr-policy.md`.

---

## Measurement and telemetry

Skill Generator v2 should not write noisy per-developer consumption logs into
application repos. Do not ask Copilot, Claude, or Codex to self-log every time
they read a skill.

For pilot measurement, use central telemetry and existing artifacts:

- GitHub Copilot usage metrics where the enterprise SKU and admin scope expose them.
- `.skill-gen-audit.md` and `.skill-update-audit.md` counts.
- Tracker reports attached to PRs.
- Developer surveys and feature-lead review outcomes.

Measurement must not collect prompts, source code, secrets, or personal data.
Detailed measurement guidance lives in `docs/measurement-plan.md`.

---

## Uninstall or opt out

If a repo owner needs to remove Skill Generator from a target repo, do it as a
reviewed PR and preserve any pre-existing AI instructions that were not created
for Skill Generator.

For a repo that only used the bootstrap files for Skill Generator:

```bash
git rm -r .github/skills
git rm .github/copilot-instructions.md CLAUDE.md AGENTS.md
git commit -m "chore: remove Skill Generator v2 artifacts"
```

If `.github/copilot-instructions.md`, `CLAUDE.md`, or `AGENTS.md` existed
before bootstrap, do not delete the whole file. Remove only the feature-skills
section and leave the repo's original rules intact.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python3: can't open file ... lib/validate.py` | `SKILL_GENERATOR_HOME` is not set in that shell or IDE terminal. | Export `SKILL_GENERATOR_HOME` again and verify `test -f "$SKILL_GENERATOR_HOME/lib/validate.py"`. |
| Agent suddenly reports `Operation not permitted` on files that worked earlier | macOS TCC / Files & Folders permission prompt timed out or was denied. | System Settings -> Privacy & Security -> Files and Folders, or Full Disk Access, then grant the host app access to the repo path and `~/Documents`. Restart the host app. |
| Copilot ignores skills | Custom instructions not loaded, or the prompt did not point at catalog. | Ask explicitly to read `.github/skills/catalog.md`; in Copilot Chat, check whether `.github/copilot-instructions.md` appears in references. |
| IntelliJ does not load path-specific instructions | JetBrains supports the repository instruction file; do not rely on VS Code-only path instruction behavior. | Keep the important Skill Generator rules in `.github/copilot-instructions.md`. |
| Generated skill says LOW confidence | Feature boundary or source evidence was ambiguous. | Treat as draft, review with feature lead, then regenerate or update once clarified. |
| Generated skill says MEDIUM / `review_required: true` because source files were inaccessible | Host had partial evidence during generation. | Fix access, then regenerate or verify the skill against source before relying on behavior claims. |
| Catalog maps the wrong feature | Missing alias or business term. | Update the skill frontmatter and regenerate catalog through `skill-updater`. |
| Skill mentions a secret or real user data | PII/secret scrub failed. | Block the PR, remove the value, add a validator/security finding, and fix the generating/updating contract before rollout. |
| Assistant wants to update every skill | Tracker/updater instructions were not followed. | Stop and rerun `skill-tracker`; update only directly impacted and dependency-impacted skills. |

---

## Security and privacy rules

Generated skills may describe:

- Property names
- Endpoint names
- Table names
- Class names
- Business rules
- Validation behavior
- Error-handling behavior

Generated skills must not include:

- Password values
- API keys
- Client secrets
- JWTs or bearer tokens
- Real customer data
- Real employee/user personal data
- Production-only credentials or connection strings

If a source file contains secrets, the skill should say the property exists and
that the value is redacted. The skill should not copy the value.

---

## Rollout checklist for one repo

| Step | Owner | Done when |
|---|---|---|
| 1. Set `SKILL_GENERATOR_HOME` | Repo owner | Validation scripts are reachable. |
| 2. Bootstrap target repo | Repo owner | Copilot, Claude, Codex instruction files exist. |
| 3. Run first generation | Repo owner / feature lead | Feature skills, catalog, and audit exist. |
| 4. Validate | Repo owner | `validate.py` and `citation_check.py` pass for every skill. |
| 5. Review | Feature lead | Feature boundaries, confidence, dependencies, and secrets are approved. |
| 6. Commit | Repo owner | `.github/skills` is committed on a reviewed branch. |
| 7. Enable developer use | Team lead | Developers know to start with catalog and feature skills. |
| 8. Enforce PR policy | PR reviewers | Behavior-changing PRs include tracker-clean report or updated skills. |

---

## Enterprise guidance

For a 150-developer pilot, do not ask every developer to run first generation.
Use this model:

1. Platform team owns Skill Generator version and templates.
2. Repo owners run generation once per repo.
3. Feature leads review business correctness.
4. Developers consume skills inside VS Code or IntelliJ.
5. PR reviewers use tracker before approving behavior-changing changes.
6. Platform team measures adoption through central telemetry and audit
   artifacts, not noisy in-repo consumption logs.

For 25K-developer scale, treat `.github/skills` as repo-local context and feed
catalog/audit metadata into a central skill graph later. The repo-local flow
must remain simple enough that a developer can use it without knowing the
platform internals.
