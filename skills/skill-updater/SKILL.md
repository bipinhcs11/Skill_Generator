---
skill_id: skill-updater
version: 1
last_updated: "2026-05-18"
trigger_phrases:
  - "update feature skills"
  - "refresh skills for this change"
  - "sync skills with this enhancement"
  - "run skill updater"
target_language: Java
artifact_contract: artifact-3
---

# Skill Updater v2

## Purpose

This skill updates existing feature-based SKILL.md files after code changes. It
does not re-run first generation unless a new feature appears. It reads the code
diff, maps changed Java/properties/MyBatis XML/SQL/Spring Batch/script files to
affected feature skills, propagates impact through skill dependencies, updates
only the needed sections, and records what changed in an audit trail.

Use this after the first-run `skill-generator` has already committed
`.github/skills/<feature-id>/SKILL.md` files. If `skill-tracker` produced an
impact report, use it as the starting plan, then re-check source evidence before
editing.

---

## Core rule

First generation creates the full skill map. Update keeps that map accurate.

If invoice comparison depends on participant data, a participant API, schema, or
business-rule change may require updating both `participant` and
`invoice-compare`. The dependency graph in `depends_on` and `depended_on_by` is
the durable signal that makes this propagation possible.

---

## Pipeline overview

```
Step 1  Pre-flight
Step 2  Diff intake
Step 3  Impact analysis
-- HALT GATE 1 -- Human reviews affected skills + dependency propagation
Step 4  Update affected SKILL.md files
Step 5  Dependency maintenance
Step 6  Self-validate
Step 7  Write update audit log
-- HALT GATE 2 -- Human reviews output, approves commit
Step 8  Commit
```

---

## Step 1 - Pre-flight

Before updating anything, confirm:

1. **Target repo.** You are in the Java repo that contains `.github/skills/`.
   If not, ask for the path.

2. **Existing skills.** `.github/skills/` contains one or more generated
   `SKILL.md` files. If not, stop and run `skill-generator` first.

3. **Tracker report.** If the developer provides a `skill-tracker` report,
   read it first. Treat it as the approved starting scope, but verify evidence
   before editing any SKILL.md file.

4. **Diff base.** Determine what to compare:
   - If the developer provides a base branch or commit, use that.
   - Otherwise use `git merge-base HEAD origin/main` when available.
   - If no base is clear, ask the developer for the base commit or branch.

5. **Generator tools path.** Locate the Skill_Generator checkout and set
   `SKILL_GENERATOR_HOME` so validation can run from the target repo.

---

## Step 2 - Diff intake

Collect all changed files, including unstaged changes if the developer asks to
include local work.

Recommended commands:

```bash
git diff --name-status <base>...HEAD
git diff --name-status
```

Classify changed files by type:

| File type | Why it matters |
|---|---|
| Java source | Controllers, services, entities, repositories, DTOs, mappers, config classes |
| Properties/YAML | Feature flags, service names, cache TTLs, queue names, provider URLs, model settings |
| MyBatis XML | Mapper statements, result maps, joins, dynamic SQL, stored procedure calls |
| SQL/migrations | Tables, constraints, indexes, seed data, status values, stored procedures |
| Spring Batch | Job/Step/Tasklet/ItemReader/ItemProcessor/ItemWriter flows and job parameters |
| Scripts/jobs | Batch launchers, file delivery, reconciliation, report generation, scheduled operations |
| Tests | Do not define ownership by tests, but use tests as clues for changed behavior |
| Docs only | Usually no skill update unless docs reveal a behavior contract changed |

Do not update every skill by default. The updater exists to reduce noise.

---

## Step 3 - Impact analysis

Build an impact plan before editing files.

### Direct impact rules

A skill is directly affected when a changed file matches any of these signals:

1. The changed Java class appears in `key_classes`.
2. The changed Java package is under `primary_packages`.
3. The changed endpoint, method, DTO, mapper statement, config key, table,
   queue, script, job name, step name, or file path is named in the SKILL.md
   body.
4. A MyBatis mapper XML change alters SQL, dynamic conditions, result maps,
   joins, parameters, stored procedure calls, or statement ids used by the
   feature.
5. A SQL migration changes a table, column, constraint, status value, or seed row
   used by the feature.
6. A property/YAML change alters runtime behavior described by the feature,
   including `mybatis.mapper-locations`, batch chunk sizes, input/output paths,
   or scheduler toggles.
7. A Spring Batch job/step/reader/processor/writer/listener change alters the
   feature's ingest, transform, reconciliation, report, delivery, or restart
   behavior.
8. A script/job change changes the feature's batch launch, file, report, or
   delivery behavior.

### Dependency propagation rules

After direct impacts are found, propagate to dependent skills when the change is
visible across a feature boundary.

Propagate when a change affects:

- REST endpoint path, request shape, response shape, or status behavior
- DTO/event/file contract consumed by another feature
- MyBatis mapper SQL contract, result shape, or stored procedure behavior used
  by another feature
- Database table or reference data read by another feature
- Spring Batch input/output file contract, job parameter, restart behavior, or
  produced report/file consumed by another feature
- Validation/business rule that a dependent feature assumes
- Config key, queue, topic, file path, or script output used by another feature
- Error/fallback behavior a caller handles

Do not propagate for purely internal refactors where the public contract and
business behavior did not change.

Use `depends_on` and `depended_on_by` as the starting graph, then verify with the
actual source and skill prose. If the graph is missing a real dependency, update
the graph in Step 5.

### New feature detection

If changed code forms a cohesive feature that no current skill owns, stop before
editing and ask the developer whether to:

- create a new feature skill,
- attach the code to an existing feature,
- or leave it untracked for now.

Do not silently hide new feature work inside an unrelated SKILL.md.

### Impact plan format

```
## Skill update impact plan

Base: <base ref>
Head: <head ref>

Changed files considered:
- <path> - <file type> - <summary>

Directly affected skills:
| Skill | Evidence | Sections likely changed |
|-------|----------|-------------------------|
| participant | ParticipantService.updateEligibility() changed | Data Flow, Business Rules and Edge Cases |

Dependency propagation:
| Source skill | Dependent skill | Why propagate? |
|--------------|-----------------|----------------|
| participant | invoice-compare | invoice-compare depends on participant eligibility before comparison |

New or unowned feature candidates:
- <none, or candidate with reason>

Review-required updates:
- <skill-id> - <why confidence is MEDIUM/LOW or review_required should remain true>
```

---

## Halt Gate 1 - Impact review

Present the impact plan before editing. Ask:

```
Do you approve this update plan?
- "yes" - update the listed skills
- changes in plain English - revise the impact plan
- "stop" - leave files unchanged
```

If the developer says yes, proceed. If the developer is unavailable but has asked
for autonomous update, proceed only for HIGH-confidence direct impacts and mark
any propagated or ambiguous skill as `review_required: true`.

---

## Step 4 - Update affected SKILL.md files

For each affected skill:

1. Read the current SKILL.md completely.
2. Read the changed source files and the surrounding unchanged code needed to
   understand the feature behavior.
3. Update only sections affected by the change.
4. Preserve useful human edits and stable wording when still correct.
5. Increment `version` by 1.
6. Set `last_updated` to today's `YYYY-MM-DD` date.
7. Preserve or update `confidence` based on the new evidence.
8. Set `review_required: true` if the change is ambiguous, propagated through a
   dependency, or LOW confidence.

Never overwrite a whole SKILL.md just because one class changed. This is an
update workflow, not first generation.

---

## Step 5 - Dependency maintenance

After content updates, re-check dependencies for every touched skill and every
skill connected to it.

For each real dependency:

1. The dependent skill lists the provider in `depends_on`.
2. The provider skill lists the dependent skill in `depended_on_by`.
3. Both `## Integration Points` sections describe the direction and evidence.
4. `## Update Expectations` names the kind of upstream/downstream change that
   should trigger future updates.

For removed dependencies, remove both sides and update the prose. If uncertain,
keep the dependency and set `review_required: true` rather than deleting a real
update path.

---

## Step 6 - Self-validation

Run validation on every edited skill and every dependency counterpart edited by
Step 5.

```bash
python3 "$SKILL_GENERATOR_HOME/lib/validate.py" .github/skills/<feature-id>/SKILL.md
python3 "$SKILL_GENERATOR_HOME/lib/citation_check.py" .github/skills/<feature-id>/SKILL.md
```

On failure:

1. Fix the specific structural issue.
2. Re-run validation.
3. If the same file fails twice, stop and surface the issue to the developer.

Do not commit a skill that fails structural validation.

---

## Step 7 - Update audit log

Append a new entry to `.github/skills/.skill-update-audit.md`.

Template:

```markdown
## <YYYY-MM-DD> update

Base: <base ref>
Head: <head ref>

Changed files:
- <path> - <summary>

Skills updated:
| Skill | Version | Reason | Review required |
|-------|---------|--------|-----------------|
| participant | 3 -> 4 | eligibility business rule changed | false |
| invoice-compare | 2 -> 3 | propagated participant dependency | true |

Dependency changes:
| Dependent | Provider | Action | Evidence |
|-----------|----------|--------|----------|
| invoice-compare | participant | kept | participant eligibility still gates comparison |

Validation:
| Skill | validate.py | citation_check.py |
|-------|-------------|-------------------|
| participant | PASS | PASS |
```

---

## Halt Gate 2 - Output review before commit

Present a concise summary:

```
## Skill update complete

Updated N skills:
- .github/skills/participant/SKILL.md - version 3 -> 4, validation PASS
- .github/skills/invoice-compare/SKILL.md - version 2 -> 3, validation PASS, review_required true

Dependency graph changes:
- invoice-compare depends_on participant - kept and revalidated

Audit log updated: .github/skills/.skill-update-audit.md

Ready to commit. Do you approve?
- "yes" - commit the skill updates
- changes in plain English - revise before committing
- "stop" - leave files in place for manual review
```

Do not run `git add` or `git commit` until the developer approves.

---

## Step 8 - Commit

When approved:

```bash
git add .github/skills/
git commit -m "docs: update feature skills for recent changes

Updated affected feature skills based on code/config/MyBatis/SQL/batch/script changes.
Maintained cross-feature dependencies and validation results.
Audit entry added to .github/skills/.skill-update-audit.md."
```

---

## What this skill must not do

- Do not edit application code.
- Do not add crawler, planner, or semantic logic to `lib/`.
- Do not update every skill when only one feature changed.
- Do not remove a dependency unless source evidence proves the feature boundary
  no longer exists.
- Do not mark a propagated or ambiguous update as fully reviewed.

---

## Update expectations

Update this SKILL.md when:

- The artifact-3 frontmatter changes
- Dependency metadata changes
- The update audit format changes
- New source types become first-class evidence
- A real repo test reveals missed propagation or over-propagation
