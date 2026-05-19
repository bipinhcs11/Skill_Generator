# PR policy for skill-impacting changes

A written workflow rule for any repository that has adopted Skill Generator
v2. This is documentation first; CI enforcement is a scale-gate item (see
`docs/enterprise-rollout-25k-analysis-synthesis.md` §Must land before scale).

The principle: **skill freshness is engineering hygiene, like tests or
CODEOWNERS.** If your code change affects feature behavior, the skill that
describes that feature must move with it.

---

## The rule (one paragraph)

> A pull request that changes Java source, properties / YAML, MyBatis mapper
> XML, SQL or migration files, Spring Batch jobs, or operational scripts in a
> way that affects feature behavior must include **one of**:
>
> 1. A `skill-tracker` report showing no skill impact, OR
> 2. The updated `SKILL.md` file(s) for impacted features plus the matching
>    entry in `.github/skills/.skill-update-audit.md`, OR
> 3. A `skill-tracker` report flagging impact plus a feature lead's explicit
>    written override (label `skills-override-approved` plus a comment
>    explaining why the skill update was deferred).

---

## What counts as a "behavior-affecting" change

Use this table to decide whether the PR needs to satisfy the rule.

| Change type | Triggers the rule? | Notes |
|---|---|---|
| New / modified controller endpoint | Yes | Public contract changes always trigger |
| New / modified service method signature or behavior | Yes | Even internal signature changes if a dependent feature consumes them |
| New / modified entity field, relationship, or persistence behavior | Yes | Database shape is feature evidence |
| New / modified MyBatis mapper statement, result map, dynamic SQL, or stored procedure call | Yes | First-class evidence per `skill-generator` Step 2 |
| New / modified Flyway / Liquibase migration | Yes | Schema is part of feature behavior |
| New / modified properties / YAML key that changes runtime behavior | Yes | Feature-flag, cache TTL, queue name, etc. |
| New / modified Spring Batch `Job` / `Step` / `Tasklet` / `ItemReader` / `ItemProcessor` / `ItemWriter` | Yes | Batch flows are feature behavior |
| New / modified script under `scripts/`, `bin/`, `jobs/` that touches feature data | Yes | If app or deployment references it |
| Pure formatting (whitespace, import reordering) | No | No behavior change |
| Logging-only changes (added log lines, log-level adjustments) | No | Unless a log statement is itself a documented integration |
| Private helper refactor with unchanged public contract | No | But re-running tracker is still cheap |
| Test-only changes | No | Tests follow features, not the other way around |
| CI workflow files (`.github/workflows/`) | No | Not feature code |
| Docker / Kubernetes / monitoring config | No | Infrastructure, not feature code |

When in doubt, run `skill-tracker`. It is read-only and one host-AI turn.

---

## How to satisfy each path

### Path A — tracker-clean report

```
## Skill tracker report

Base: <base ref>
Head: <head ref>

Summary: 0 directly impacted skills, 0 propagated skills, 0 stale findings.

Recommended next action: No skill update needed.
```

Paste this (or attach the tracker's full output) into the PR description.
This is the cheapest path and should be the default for refactors and
narrow bug fixes.

### Path B — updated skills + audit entry

The PR includes:

- Edits to `.github/skills/<feature-id>/SKILL.md` for each affected
  feature, produced by `skill-updater` (not by hand)
- A new entry appended to `.github/skills/.skill-update-audit.md`
- Updated `catalog.md` if discovery metadata changed
- Version bumps on every edited skill

### Path C — override

For genuine emergencies (production hotfix where the skill update will
follow in a separate PR within 48 hours), a feature lead may approve an
override:

1. Add label `skills-override-approved` to the PR
2. Comment from the feature lead explaining:
   - Why the skill update is deferred
   - When the follow-up PR will land (no more than 48 hours out)
   - Who owns the follow-up PR
3. Link the follow-up PR / ticket

The override is **not** a blanket exemption. If a team uses it more than
twice per quarter, the platform team should escalate — that pattern means
the rule is being routed around, not followed.

---

## Reviewer responsibilities

PR reviewers check, in this order:

1. Does the diff touch any file type in the table above?
2. If yes: does the PR description include a tracker report, updated
   skills, or an override?
3. If a tracker report: does it actually correspond to this PR's diff?
   (Reviewer can re-run the tracker to confirm.)
4. If updated skills: do the changes look proportionate to the diff?
   (Skill rewrites for a one-line code change suggest the updater
   overcorrected.)
5. If override: is the follow-up PR linked, with an owner and date?

Reviewers should not approve PRs that touch feature behavior without
satisfying one of the three paths.

---

## Author responsibilities

PR authors run the tracker (Path A) by default. The tracker takes one
host-AI turn and produces the report. Paste it into the description even
when it shows no impact — it tells reviewers you did the check.

If the tracker reports impact, run the updater (Path B). Review the
updater's halt-gate output before committing.

If you cannot run the updater (no host-AI session available, blocked on
something else), use Path C honestly. Do not skip the rule silently.

---

## What this rule does not cover

- **First-time generation** for repos that do not yet have
  `.github/skills/`. Run `skill-generator` separately; that work is its
  own PR.
- **Skill metadata cleanup PRs** (aliases, business_terms, owner_team
  edits). These are skill-only changes and do not need a tracker report,
  but should bump skill versions and update the catalog.
- **Renames and moves with no behavior change**. Run the tracker anyway;
  it should report no impact, and the report belongs in the PR
  description.

---

## Why this rule exists

After June 1, 2026 the cost of every redundant AI-rediscovery turn shows
up in the org's Copilot AI Credits budget. Skills are the durable context
that prevents rediscovery. A drifted skill is worse than no skill:
plausible-but-wrong context misdirects AI more than missing context does.

This rule keeps the skill graph honest. Without it, the platform team
will spend more time fixing stale skills than the team saves by having
skills at all.

---

## CI enforcement (planned, not in this rule)

The synthesis lists CI enforcement as a scale-gate item, post-pilot. When
that ships, the GitHub Action will:

- Detect changed files matching the table above
- Require the PR description to include a tracker report or skill diff
- Require the `skills-override-approved` label + a feature lead comment
  for Path C

Until then, this is a written-policy rule enforced by reviewers.
