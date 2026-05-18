---
skill_id: skill-validator
version: 2
last_updated: "2026-05-18"
feature_name: "Validate generated SKILL.md files"
primary_packages:
  - lib
key_classes:
  - lib.validate
  - lib.citation_check
---

# Skill Validator

## Purpose

This skill runs a semantic review pass on one or more generated SKILL.md files.
It complements the deterministic spine in `lib/validate.py` and
`lib/citation_check.py`. Where the deterministic spine catches structural
errors (wrong format, missing fields, invalid confidence metadata, no
citations), this skill catches semantic errors (wrong feature boundary,
incomplete integration points, dependency gaps, claims that cannot be verified
against the source code).

Run this skill after `skill-generator` has committed the initial skill files,
or at any point where you want a structured second opinion on a set of SKILL.md
files.

---

## What this skill does and does not do

**Does:**
- Check that every class named in a SKILL.md actually exists in the target repo
- Check that every responsibility claim is consistent with what the class actually does
- Check that integration points are bidirectional (if A calls B, B's skill mentions A)
- Check that configuration keys exist in the actual config files
- Surface quality issues using the standard verdict format below
- Self-correct on first failure before surfacing to the developer

**Does not:**
- Rewrite SKILL.md files without developer approval except for the two allowed self-corrections below
- Replace the deterministic spine checks; it invokes `lib/validate.py` and `lib/citation_check.py` first
- Judge whether feature grouping decisions were optimal — that is a planning question,
  not a validation question
- Flag style preferences (word choice, sentence length, heading phrasing)

---

## Artifact-3 contract enforcement

Every generated SKILL.md must satisfy the artifact-3 contract. The validator
checks this contract by reading both the SKILL.md and the source code.

The contract requires:

| Field / Section | Contract rule |
|---|---|
| `skill_id` frontmatter | Matches the directory name exactly (kebab-case) |
| `version` frontmatter | Integer >= 1 |
| `last_updated` frontmatter | ISO-8601 date (YYYY-MM-DD) matching the commit date |
| `confidence` frontmatter | HIGH, MEDIUM, or LOW; copied from the evidence phase |
| `review_required` frontmatter | true or false; must be true when confidence is LOW |
| `primary_packages` frontmatter | Every package listed exists in the repo's source tree |
| `key_classes` frontmatter | Every class listed exists as a `.java` file in the repo |
| `depends_on` frontmatter | Optional non-empty list of provider feature ids this skill depends on |
| `depended_on_by` frontmatter | Optional non-empty list of dependent feature ids that rely on this skill |
| `## Overview` | 2-4 sentences, no placeholder text |
| `## Key Classes and Responsibilities` | Every class in `key_classes` frontmatter appears here; no class is listed here that is absent from frontmatter |
| `## Data Flow` | At least one class-qualified citation: `ClassName.methodName()` or fully qualified class name |
| `## Configuration` | Either real config keys/env vars OR the exact fallback: "No runtime configuration for this feature." |
| `## Integration Points` | Agrees with `depends_on` and `depended_on_by`; either real integration points OR the exact fallback: "This feature has no integration points with other features." |
| Optional `## Error Handling` | If present, exception/status claims must be source-backed |
| Optional `## Business Rules and Edge Cases` | If present, rules must tie back to Java, config, MyBatis XML, SQL, Spring Batch, or scripts |
| Optional `## AI Agent Instructions` | If present, instructions must be feature-specific and source-backed |
| `## Update Expectations` | At least two specific triggers for updating this SKILL.md |

---

## Deterministic checklist (run in this order)

Run each check completely before proceeding to the next. Do not skip steps even
if earlier steps surface no issues.

### Check 1 — Run the deterministic spine

```bash
python3 "$SKILL_GENERATOR_HOME/lib/validate.py" .github/skills/<feature-id>/SKILL.md
python3 "$SKILL_GENERATOR_HOME/lib/citation_check.py" .github/skills/<feature-id>/SKILL.md
```

If either fails: do not proceed to Check 2. Fix the structural issue, verify
the fix passes both tools, then continue.

### Check 2 — Package and class existence

For every package in `primary_packages` frontmatter:

```bash
find . -type d -path "*/<package-as-path>" | grep -v "target\|build"
```

For every fully qualified class in `key_classes` frontmatter, convert the package
to a path and verify the exact class file exists. Do not validate by simple class
name only; duplicate class names across modules are common.

```bash
find . -path "*/<package-as-path>/<SimpleClassName>.java" | grep -v "target\|build\|Test"
```

If a package or class is not found: record it in the verdict as a **blocking**
issue. Do not suppress it.

### Check 3 — Responsibility consistency

For each class listed in `## Key Classes and Responsibilities`, read the actual
`.java` file. Compare the responsibility claim in the SKILL.md against what
the class actually does.

Flag as a **consistency issue** if:
- The responsibility claim describes what a different class does
- The class has a clearly different primary concern than stated
- The class is a test class, infrastructure bootstrap, or utility that was
  incorrectly included as a feature entity

### Check 4 — Integration point and dependency bidirectionality

For each integration point named in `## Integration Points`, find the other
feature's SKILL.md and verify the current feature is named there. Also verify the
frontmatter graph agrees:

- If current skill `depends_on: other-skill`, then `other-skill` must list the
  current skill in `depended_on_by`.
- If current skill `depended_on_by: caller-skill`, then `caller-skill` must list
  the current skill in `depends_on`.
- The prose in both `## Integration Points` sections must explain the direction
  and source-backed reason for the dependency.

If the other feature's SKILL.md does not mention the current feature:
record as a **link gap** issue. This can be self-corrected (add missing
dependency metadata or prose to the other SKILL.md) without developer approval —
but record the self-correction in the verdict.

### Check 5 — Configuration existence

For each configuration key or environment variable named in `## Configuration`,
check whether it appears in:

```bash
grep -r "<key-name>" . --include="application*.yml" --include="application*.properties"
```

If a configuration key is not found in any config file: record as a
**configuration gap** issue.

### Check 6 — Business rules, MyBatis, SQL, batch, scripts, and AI instructions

For optional `## Error Handling`, `## Business Rules and Edge Cases`, and
`## AI Agent Instructions` sections, verify each important claim against the
source evidence named or implied by the skill:

- Java methods, annotations, exceptions, DTOs, controllers, services, entities
- properties/YAML keys and values
- MyBatis mapper XML statements, result maps, dynamic SQL, joins, and stored procedure calls
- SQL tables, constraints, seed data, indexes, stored procedures, migrations
- Spring Batch Job/Step/Tasklet/ItemReader/ItemProcessor/ItemWriter definitions, listeners, job parameters, restart behavior, and metadata table usage
- scripts/jobs that load files, deliver reports, reconcile data, or call feature
  endpoints

Flag a **consistency issue** when a rule is plausible but not source-backed.

---

## Self-correction rules

The validator may self-correct exactly two types of issues without developer
approval:

1. **Link gaps** (Check 4): add missing `depends_on` / `depended_on_by` metadata
   and the matching Integration Points prose to the other feature's SKILL.md.
   Record the addition in the verdict.

2. **Stale last_updated date**: update `last_updated` in the frontmatter to
   today's date if the content of the file was modified during this session.
   Record the update in the verdict.

All other issues require developer approval before the validator modifies any
file.

Self-correction attempt limit: two per file per run. If self-correction fails
twice on the same issue, surface the issue to the developer and stop.

---

## Verdict format

After completing all checks, produce a verdict for each SKILL.md using this
exact format:

```
## Verdict: <feature-id>

Status: PASS | PASS_WITH_SELF_CORRECTIONS | NEEDS_REVIEW | BLOCKING_ISSUES

Deterministic spine: PASS | FAIL
Package/class existence: PASS | FAIL
Responsibility consistency: PASS | ISSUES_FOUND
Integration bidirectionality: PASS | GAPS_FOUND | SELF_CORRECTED
Configuration existence: PASS | GAPS_FOUND
Business/source-backed rules: PASS | ISSUES_FOUND

Issues (if any):
- [BLOCKING] <issue description>
- [CONSISTENCY] <issue description>
- [LINK GAP] <issue description>
- [CONFIG GAP] <issue description>

Self-corrections applied (if any):
- <what was changed and why>

Recommendation:
<one or two sentences on what the developer should do next>
```

Use `BLOCKING_ISSUES` status when Check 1 or Check 2 fails. Use
`NEEDS_REVIEW` when consistency or configuration issues are found but nothing
blocks the skill from being used. Use `PASS_WITH_SELF_CORRECTIONS` when the
only action taken was the two allowed self-correction types. Use `PASS` when
no issues were found and no self-corrections were needed.

---

## Multi-file validation

To validate an entire `.github/skills/` directory, run the skill once with the
directory path. The skill validates each SKILL.md in alphabetical order and
produces one verdict per feature.

After all individual verdicts, produce a summary:

```
## Validation summary

Files checked: N
PASS: X
PASS_WITH_SELF_CORRECTIONS: X
NEEDS_REVIEW: X
BLOCKING_ISSUES: X

Cross-file issues:
- <any issues that span multiple features, e.g. link gaps>
```

---

## When to run this skill

Run `skill-validator` at these points in the workflow:

| When | What to validate |
|---|---|
| After `skill-generator` completes | All newly generated SKILL.md files |
| Before a PR that modifies SKILL.md files | The modified files only |
| After a `skill-updater` run | The updated files only |
| On a periodic cadence (quarterly, or after major refactors) | All files in `.github/skills/` |

Running it more often than these points is not harmful, but the value of each
run decreases as the gap between the code and the skills shrinks.

---

## Update expectations

Update this SKILL.md when:

- The artifact-3 contract changes (adds, removes, or renames required sections
  or frontmatter fields)
- The self-correction rules change (additional allowed self-corrections, or
  existing ones removed)
- The verdict format changes
- A new check is added (add it to the deterministic checklist and the verdict format)
- The two-attempt self-correction limit changes
