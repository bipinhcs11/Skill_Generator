# Measurement plan — central telemetry for Skill Generator v2

How the platform team measures whether Skill Generator is actually working at
scale, without burdening business repos with noisy logs or asking AI agents
to self-report.

This document defines the architectural rule, the event schema, what gets
collected and what does not, where telemetry is stored at each scale, and
the pilot metrics that prove (or disprove) the ROI case before the wider
rollout.

The rule of thumb to remember: **audit artifacts live in-repo; telemetry
lives centrally.** Get that distinction right and most of the rest follows.

---

## The architectural rule

> **In-repo audit artifacts** = review evidence the team needs for *that
> repo*. Examples: `.skill-gen-audit.md`, `.skill-update-audit.md`. They
> stay in-repo because the team for that repo is who reads them.
>
> **Central telemetry** = operational measurement for the platform team.
> Examples: tracker-run events, validation results, host-turn counts,
> review-required counts across teams. It stays central because no single
> repo's team owns the aggregate view.

The distinction is whether the data is for *that repo's team* or for *the
platform*. When in doubt, ask: "would a developer in repo X want to read
this file when they open repo X?" If yes, it's an audit artifact (in-repo).
If no, it's telemetry (central).

---

## Storage by scale

Different stages need different storage. Pick the cheapest option that
works for your current stage. Migrate up when the current option breaks.

| Stage | Telemetry location | Why |
|---|---|---|
| Pilot (5-10 repos) | `Skill_Generator/reporting/` folder — simple JSON dumps committed to the generator repo | Cheapest; no infra to set up; easy to grep |
| Mid-scale (50-500 repos) | Separate `Skill_Generator_Telemetry` repo | Keeps generator repo clean; still git-based, no DB needed |
| 25K scale | Enterprise data store (BigQuery, Snowflake, internal dashboard tool) fed by GitHub Copilot Usage Metrics API + audit-artifact aggregation | Real querying; joins with existing observability; SLO-grade reliability |

Do not jump to the enterprise data store on day one. The pilot's whole
point is to prove the loop is worth measuring before investing in the
infrastructure to measure it well.

---

## Event schema

A flat, append-only event stream. One event per measurable action.

```yaml
event_type:    tracker_run | skill_generated | skill_updated | validation_run | pilot_feedback
repo:          billing-service          # or hashed if org policy requires
team:          payments                 # team identifier; aligns with CODEOWNERS
feature_id:    invoice-compare          # the skill being acted on (when applicable)
skill_version: 3                        # post-action version
host:          copilot | claude | codex
confidence:    HIGH | MEDIUM | LOW
review_required: true | false
result:        pass | needs_review | blocking
host_turns_used: 3                      # for post-June-1 billing-model traceability
input_tokens_estimated:  ...            # if host exposes
output_tokens_estimated: ...            # if host exposes
timestamp:     2026-06-10T14:30:00Z
```

`host_turns_used` is the critical field for connecting telemetry to the
post-June-1 billing model. Even when token counts are not exposed by the
host, `host_turns_used` is something the agent can self-report at the end
of a run and is the next best proxy.

---

## Telemetry data contract (write this up-front)

For a 25K-dev org, this gets reviewed by privacy and compliance early. A
one-page data contract makes that review fast.

### Collected

- Event type and timestamp
- Repo identifier (raw or hashed depending on org policy)
- Team membership (not individual developer identity)
- Feature ID being acted on
- Skill version, confidence, review_required
- Host AI used
- Result of the action
- Host turns consumed (and token counts when exposed)

### NOT collected — never, under any circumstance

- Prompt text
- Generated code
- Source-code excerpts
- Secrets, credentials, API keys
- Customer data
- File contents
- Model responses
- Developer identity beyond team membership

### Retention

To be defined by security review before the pilot. Suggested default:
13 months rolling, sufficient for year-over-year comparison. Aggregated
metrics (counts, rates) may be retained indefinitely.

### Access

To be defined by the platform team. Suggested default: platform team has
read/write; engineering leadership and finance have read on aggregates;
individual developers have read on their own team's metrics.

---

## Precondition: verify what your Copilot SKU exposes

GitHub Copilot Usage Metrics surfaces vary by SKU (Business vs Enterprise)
and admin permissions. Enterprise / org / user-level metrics are
documented; team-level is constructed by joining; repo-level direct
attribution is **not** surfaced by GitHub's API.

Before promising any specific metric in the leadership pager:

1. Identify who administers Copilot for your org
2. Confirm which breakdowns are actually queryable on your SKU and admin
   scope
3. Promise only what is queryable; document the rest as "inferred from
   tracker reports and surveys"

Skipping this step produces a leadership pager that promises metrics that
do not exist. Fix it now; do not fix it after the pager is reviewed.

---

## Pilot metrics (what the dashboard actually reports)

These are the numbers that prove or disprove the ROI case during the
150-dev pilot.

- **Tracker runs per repo, per week** — does the team use it at all?
- **PRs requiring skill updates vs tracker-clean** — measure of churn
- **Most-reused skills (read-frequency proxy)** — derived from PR-context
  reads + tracker runs + audit-artifact aggregation
- **Skills frequently `review_required`** — quality signal; high count
  means generation is producing too many drafts
- **Average host turns to complete a feature task** — before vs after
  skill adoption (this is the headline number)
- **Copilot AI credit usage before vs after by org/team where available;
  repo-level impact inferred from tracker reports, update audits, pilot
  cohort mapping, and surveys** (GitHub's Copilot Usage Metrics API does
  not expose direct repo-level attribution)
- **Developer survey: "Did the first answer have enough context?"** —
  qualitative pre/post measurement
- **Concrete case studies — documented examples where skill context
  prevented a wrong change** — qualitative proof that's hard to argue
  with in leadership reviews

---

## What this plan deliberately does NOT do

- **Does not ask Copilot/Claude/Codex to self-log skill reads.** That
  data would be noisy, unreliable, and politically awkward. Use the
  GitHub Usage Metrics API + audit artifacts + surveys instead.
- **Does not write a `.consumption-log.csv` inside business repos.**
  Operational telemetry goes central; only audit artifacts stay in-repo.
- **Does not store prompts, generated code, or any model output.** Those
  belong to the host AI's logs, not ours.
- **Does not promise repo-level Copilot metrics.** GitHub's API does not
  expose them; surveys and inferred metrics fill the gap honestly.
- **Does not create a fifth core agent.** Telemetry is platform plumbing,
  not a skill (see "Future skill-measurement" below).

---

## Future "skill-measurement" capability

If a measurement skill is later added, its job is to *collect and
summarize existing telemetry and audit artifacts* — not to ask Copilot to
log every time it reads a skill. Even then, the mental model stays at
four agents; measurement is platform plumbing, not a fifth agent in the
diagram. Whether the implementation lives as a `SKILL.md` under `skills/`
or as a tool under `lib/tools/` is a detail; the user-facing model
("four agents do the work, the platform aggregates the data") stays
constant.

---

## How this measurement plan ties to the leadership pager

The leadership one-pager (`docs/leadership-one-pager.md`) makes claims
that this measurement plan must support. If a leadership claim cannot
be backed by the metrics above plus the survey data plus the case
studies, do not make the claim. The pilot's whole purpose is to convert
estimates into measured outcomes.

The two-way coupling: the leadership pager drives what we measure; the
measurement plan determines what the pager can honestly say.

---

## What success looks like at the end of the pilot

Three pieces, in order of weight:

1. **Quantitative:** the average-host-turns metric drops measurably for
   pilot repos vs. control repos. Anything from 15-40% reduction is a
   plausible win; below 10% is a flat result that needs investigation.
2. **Qualitative:** developer survey shows ≥ 70% "first answer had
   enough context" on pilot repos vs. baseline on control repos.
3. **Stories:** at least 3 documented cases where a skill prevented a
   wrong code change. Numbers move budget conversations; stories move
   adoption.

If two of these three move, the rollout case is strong. If only one,
investigate before scaling. If zero, stop and re-evaluate the whole
approach — the pilot's job is to surface that signal early, not to
produce vanity metrics.
