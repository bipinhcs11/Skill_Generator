---
skill_id: skill-tracker
version: 1
last_updated: "2026-05-18"
trigger_phrases:
  - "which skills are impacted by this change"
  - "does this PR require skill updates"
  - "track skill impact"
  - "check stale feature skills"
  - "run skill tracker"
target_language: Java
artifact_contract: tracker-report-1
---

# Skill Tracker v2

## Purpose

This skill detects which feature skills are stale, impacted, or missing after a
code change. It reads git diffs, existing `.github/skills/<feature>/SKILL.md`
files, and the dependency graph, then produces an impact report for the
developer or PR reviewer.

Use this skill after first-run generation and before `skill-updater` when the
team wants a reviewable answer to: "Does this change require a skill update?"

The tracker does **not** edit application code and does **not** rewrite
SKILL.md files. It plans and explains. `skill-updater` applies approved edits.

---

## Role in the product flow

```
skill-generator  -> creates the initial feature skill map
skill-tracker    -> detects stale / impacted / missing skills after changes
skill-updater    -> updates only the approved affected skills
skill-validator  -> reviews generated or updated skills for quality
```

This separation keeps premium-request usage focused. A PR reviewer can run the
tracker to avoid regenerating or rewriting every skill when only one feature
changed.

---

## Pipeline overview

```
Step 1  Pre-flight
Step 2  Build skill inventory and dependency graph
Step 3  Diff intake
Step 4  Direct impact detection
Step 5  Dependency propagation review
Step 6  Stale / missing skill detection
Step 7  Tracker report
Step 8  Recommendation: no update, run skill-updater, or run skill-generator
```

---

## Step 1 - Pre-flight

Before analyzing impact, confirm:

1. **Target repo.** You are in the Java repo that contains `.github/skills/`.
   If not, ask for the repo path.

2. **Existing generated skills.** `.github/skills/` contains one or more
   feature `SKILL.md` files. If not, stop and recommend `skill-generator`.

3. **Diff base.** Determine the comparison point:
   - Use the base branch or commit provided by the developer.
   - Otherwise use `git merge-base HEAD origin/main` when available.
   - If no base is clear, ask for the base ref.

4. **Scope.** Ask whether to include unstaged local changes when the developer
   did not specify PR-only or committed-only analysis.

---

## Step 2 - Build skill inventory and dependency graph

Read every `.github/skills/<feature-id>/SKILL.md` and collect:

- `skill_id`
- `version`
- `confidence`
- `review_required`
- `primary_packages`
- `key_classes`
- `depends_on`
- `depended_on_by`
- `## Integration Points`
- `## Update Expectations`

Build two maps:

- **Ownership map:** packages, classes, mapper XML, SQL tables, config keys,
  batch jobs, scripts, endpoints, queues, topics, and file paths named by each
  skill.
- **Dependency map:** `depends_on` and `depended_on_by` relationships, checked
  both ways.

If dependency frontmatter is one-sided, flag it as a tracker finding. Do not fix
it in tracker mode.

---

## Step 3 - Diff intake

Collect changed files:

```bash
git diff --name-status <base>...HEAD
git diff --name-status
```

Classify each changed file:

| File type | Impact signal |
|---|---|
| Java source | Controllers, services, entities, repositories, DTOs, mapper interfaces, config classes |
| Properties/YAML | Feature flags, service names, cache TTLs, queue names, provider URLs, mapper locations, batch settings |
| MyBatis XML | Statement ids, result maps, joins, dynamic SQL, stored procedure calls, parameter/result mappings |
| SQL/migrations | Tables, columns, constraints, status values, seed data, stored procedures |
| Spring Batch | Job, Step, Tasklet, ItemReader, ItemProcessor, ItemWriter, listener, scheduler, job parameters |
| Scripts/jobs | Batch launchers, file delivery, reconciliation, report generation, scheduled operations |
| Tests | Behavior clues only; tests do not define feature ownership |
| Docs only | Usually no skill update unless they change or reveal a behavior contract |

Read the changed diff plus enough surrounding source to understand whether the
change affects behavior, contract, configuration, persistence, batch flow, or
only internal implementation.

---

## Step 4 - Direct impact detection

Mark a skill as directly impacted when a changed artifact matches any of these:

1. Changed class appears in `key_classes`.
2. Changed package is under `primary_packages`.
3. Changed endpoint, method, DTO, mapper statement, config key, table, queue,
   topic, script, batch job, step, file path, or status value is named in the
   skill body.
4. MyBatis XML changes SQL, dynamic conditions, result maps, joins, parameters,
   or stored procedure calls used by the feature.
5. SQL/migration changes persistence shape or reference data used by the
   feature.
6. Properties/YAML changes runtime behavior described by the feature.
7. Spring Batch or script changes ingest, transform, reconciliation, reporting,
   restart, or delivery behavior described by the feature.

Do not mark a skill stale for formatting-only, logging-only, or private helper
refactors unless the feature's external behavior or operating rule changed.

---

## Step 5 - Dependency propagation review

For each directly impacted skill, inspect downstream skills in `depended_on_by`.
Propagate impact only when the changed behavior crosses a feature boundary.

Propagate when the change affects:

- REST endpoint path, request shape, response shape, or status behavior
- DTO/event/file contract consumed by another feature
- MyBatis result shape, SQL contract, or stored procedure behavior used by
  another feature
- Database table, column, status value, reference data, or constraint read by
  another feature
- Batch input/output file contract, job parameter, restart behavior, or produced
  report/file consumed by another feature
- Validation or business rule a dependent feature assumes
- Config key, queue, topic, file path, or script output used by another feature
- Error/fallback behavior a caller handles

Do not propagate for internal refactors where public contract and business
behavior are unchanged.

---

## Step 6 - Stale / missing skill detection

Flag these conditions:

- **Stale skill:** A skill names a class, mapper statement, table, config key,
  batch job, script, endpoint, or file path that changed behavior.
- **Missing skill:** Changed production code forms a cohesive feature that no
  current skill owns.
- **Unowned source:** Changed production files are not covered by any
  `primary_packages`, `key_classes`, or source-backed skill prose.
- **Broken dependency graph:** `depends_on` and `depended_on_by` disagree.
- **Review queue:** Any impacted skill with `confidence: LOW`,
  `review_required: true`, ambiguous ownership, or propagated impact.

If a new feature appears, recommend `skill-generator` for that feature or a
targeted new-skill generation run. Do not hide new feature behavior inside an
unrelated skill.

---

## Step 7 - Tracker report

Produce this report and stop before edits:

```markdown
## Skill tracker report

Base: <base ref>
Head: <head ref>
Scope: <PR diff only | committed + unstaged>

Summary:
- <N> changed production files considered
- <N> directly impacted skills
- <N> propagated skills
- <N> stale or missing skill findings

Changed files considered:
| File | Type | Behavior impact |
|------|------|-----------------|
| src/main/java/.../ParticipantService.java | Java source | Eligibility rule changed |

Directly impacted skills:
| Skill | Evidence | Recommended action |
|-------|----------|--------------------|
| participant | ParticipantService.updateEligibility() changed | Run skill-updater |

Dependency propagation:
| Source skill | Dependent skill | Propagate? | Reason |
|--------------|-----------------|------------|--------|
| participant | invoice-compare | yes | Invoice comparison reads participant eligibility |

Stale / missing skill findings:
- <none, or finding with evidence>

Review queue:
- <skill-id> - <why human review is needed>

Recommended next action:
- <No skill update needed | Run skill-updater for listed skills | Run skill-generator for new feature candidate>
```

---

## Step 8 - Recommendation

Use these decision rules:

- If no production behavior, contract, config, SQL, batch, or script behavior
  changed: recommend **no skill update**.
- If existing skills are impacted: recommend `skill-updater` with the exact
  approved skill list.
- If a new feature is present: recommend `skill-generator` or a targeted
  new-feature generation pass before updating dependencies.
- If ownership is unclear: recommend human review and keep the impacted skills
  in the review queue.

---

## What this skill must not do

- Do not edit application code.
- Do not edit `.github/skills/**/SKILL.md`.
- Do not commit files.
- Do not add crawler or semantic analysis logic to `lib/`.
- Do not recommend updating every skill unless the diff truly changes a shared
  contract used by every skill.
- Do not mark a propagated or ambiguous impact as fully reviewed.

---

## Update expectations

Update this SKILL.md when:

- The generated skill frontmatter schema changes.
- New source types become first-class evidence.
- Dependency propagation rules change.
- Real PR tests reveal missed stale-skill or over-propagation cases.
