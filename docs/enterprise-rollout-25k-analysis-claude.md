# Enterprise rollout analysis — 25K developers, 150-dev June pilot

**Author:** Claude (Opus 4.7, 1M context)
**Date:** 2026-05-18
**Scope:** Independent AI-architect read of Skill Generator v2, framed for the
upcoming 150-developer pilot in June and the eventual 25,000-developer
organisation-wide rollout. Frozen as written before exchanging notes with
Codex's parallel analysis.

**What was reviewed:** `README.md`, `CLAUDE.md`, all four agent skills
(`skill-generator`, `skill-tracker`, `skill-updater`, `skill-validator`), the
`lib/` spine, `docs/enterprise-agent-selection-guide.md`, `docs/v2-progress-report.md`,
`docs/release-readiness-checklist.md`, `docs/agent-invocation-flow.md`,
`docs/petclinic-v2-test-report.md`, and `docs/templates/copilot-instructions.md`.

**What this is not:** a code-review or PR. No code changes were made. This is a
decision document intended to be diffed against Codex's analysis to surface
agreements and gaps.

---

## 1. What we're actually optimizing for

The product framing in the README is correct but soft: "save developer hours,
reduce premium-token spend, give every approved coding agent durable feature
context." For a 25K-developer rollout, the north stars need to be sharper,
because they determine what to build next:

| North star | What it means at scale | How we'd know we're winning |
|---|---|---|
| Fewer rediscovery turns per feature question | A Copilot/Claude question about feature X should resolve in 1 turn, not 4 | Measure premium-request count per ticket/feature touch before vs after `.github/skills/` exists |
| Consistent answers across host AIs | The same SKILL.md should produce comparable answers from Copilot Chat, Claude, and Codex | Conformance tests — golden Q&A set per reference repo |
| Skill freshness without manual effort | A repo with committed skills should not drift silently | % of skills with `last_updated` within N days of last touched `key_class` |
| Onboarding time to first useful answer | A dev new to a repo should ask one question and get the right context | Time-to-first-merged-PR for new joiners on repos with skills vs without |

If the product can't move those four numbers, the 25K rollout will be
unsellable to leadership regardless of how good the agent contract is. Right
now there is no telemetry to move any of them — that is the single biggest
gap (see §5).

---

## 2. What the v2 foundation already does well for enterprise

Crediting these before listing gaps:

- **Halt gates with human approval** — at 25K-dev scale, every form of
  "autonomous AI commits to repo" attracts security and risk review. Two-gate
  human approval is the right default.
- **Confidence + `review_required` as first-class metadata** — converts
  "AI was confident and wrong" into "AI flagged itself; lead reviewed."
  Single most defensible design choice for regulated enterprises.
- **Dependency graph (`depends_on` / `depended_on_by`)** — durable,
  machine-readable, and the foundation for any future cross-repo or
  impact-analysis tooling.
- **Lib boundary (500 LOC cap)** — keeps the agent portable across Claude,
  Codex, and Copilot. A Python crawler would have locked the product into a
  single host. This decision pays off at scale.
- **Tracker / updater split** — "PR reviewer runs read-only tracker, then
  approves targeted updates" is exactly how you keep premium-request budgets
  sane across thousands of repos.
- **Audit logs (`.skill-gen-audit.md`, `.skill-update-audit.md`)** —
  already gives the compliance story enterprise legal and security teams will
  ask for.

These are not table stakes. Most internal AI tooling at 25K-dev orgs has none
of them.

---

## 3. Gaps that block the 150-dev June pilot

The release-readiness checklist already says "unsupervised enterprise-wide
rollout: not yet." Below are the specific items I would want closed before
June, in priority order.

### 3.1 Bootstrap is too manual for 150 devs

Today: a developer copies `docs/templates/copilot-instructions.md` into each
repo's `.github/copilot-instructions.md`. For 150 devs across 20-40 repos,
that's 20-40 copy-paste events with no enforcement. Multiple repos will skip
it or stale-copy it.

**Add:** a `skill-bootstrap` one-shot that:

- Creates `.github/copilot-instructions.md` from the canonical template
- Creates `.github/skills/.gitkeep`
- Creates a `.github/skills/README.md` pointing developers and Copilot at the
  right starting place
- Optionally registers the repo in an org-level "repos using Skill_Generator"
  registry

### 3.2 No discovery for Copilot, Claude, or Codex consumers

The README and Copilot template assume the host AI "knows" to read
`.github/skills/` first. In practice:

- Copilot Chat's behavior depends on whether `.github/copilot-instructions.md`
  is actually loaded into the conversation (depends on IDE state)
- Claude reads `CLAUDE.md` and project files; if there is no `CLAUDE.md` in
  the target repo, it won't know
- Codex reads `AGENTS.md`

**Add:** a target-repo bootstrap that drops the right instruction file for
each approved host (`.github/copilot-instructions.md`, `CLAUDE.md`,
`AGENTS.md`) all pointing to `.github/skills/`. One source of truth, three
target files. This is a 30-line template task, not a deep feature.

### 3.3 No CI integration for stale-skill detection

Release checklist already flags this. At 150-dev pilot scale, this is
survivable manually. But the moment one team commits drifted skills and
another team's Copilot reads them and answers wrong, trust dies. A simple
GitHub Action that runs `skill-tracker` on every PR and posts a comment
("This PR may affect: `participant`, `invoice-compare`") is high-leverage.
The tracker is already read-only and designed for exactly this.

### 3.4 No PII / secrets guardrail

The generator reads `application.yml`, properties files, SQL seed data.
Real-repo configs sometimes contain:

- Connection strings with credentials
- API keys for dev environments
- Internal hostnames and AWS account IDs
- Customer-specific reference data

Nothing in the current contract prevents the generator from writing
`database.url=jdbc:oracle://prod-db.internal:1521/orders?user=admin&password=...`
into a Configuration section. For a 25K-dev org, this WILL happen.

**Add to generator contract:** a "sensitive-value scrub" rule — when emitting
Configuration values, mask anything matching common secret patterns
(password, secret, token, key, connection-string-with-credentials). Either
redact or just name the key without the value.

### 3.5 The artifact-3 schema gap the Petclinic test already identified

Petclinic test report lines 142-156 already name this: v2 lost two high-value
sections that v1 had — **Error Handling table** and **AI Agent Instructions**.
The test report's recommendation (add both as optional sections) is correct
and should land before pilot. For an AI consuming the skill at use time,
"AI Agent Instructions" is the single most valuable section, and v2 currently
does not have it.

### 3.6 No conformance test across host AIs

The product's portability claim is "any host AI with file-read, grep, bash
works." This is unverified. Before the 150-dev pilot, I would want a small
golden test:

- 10 questions per reference repo (Petclinic + one more)
- Run them through Copilot Chat, Claude, and Codex with the committed skills
  loaded
- Pass = all three give substantively correct answers

Without this, you cannot honestly tell 150 developers "use whichever host you
have." You would be guessing.

### 3.7 No exec / leadership brief

"We're rolling out an AI tool to 150 devs in June, going to 25K" will get
asked about by directors and VPs. Today the closest artifact is
`docs/enterprise-agent-selection-guide.md`, which is dev-facing. Need a
1-page brief covering: the problem in money terms, what we're building, the
rollout plan, the risk model, what success looks like, what the next
funding/staffing ask is.

---

## 4. Gaps that block the 25K rollout (not blockers for June, but on the roadmap)

### 4.1 Java-only is the single biggest scope limit

Among 25K devs, a meaningful fraction don't touch Java. If the product stays
Java-only, the addressable population caps at maybe 30-50% of the org (rough
guess; depends on stack). Three options:

| Approach | Effort | When |
|---|---|---|
| Stay Java-only, accept the ceiling | None | Now |
| Add a "language-agnostic mode" — weaker crawl rules, no MyBatis/Spring Batch awareness, works on any source tree | Medium (rewrite Step 2 crawl rules per language) | Q3-Q4 |
| Per-language artifact-3 variants (Python, TypeScript) sharing the same lib spine | Large | 2027 |

For the June pilot this does not matter. For the 25K decision it is the most
important thing to commit to in writing.

### 4.2 No cross-repo dependency model

Today's `depends_on` is intra-repo. In a microservices org, a real feature
dependency spans repos. `invoice-compare` in repo A actually depends on
`participant` in repo B. The skill in A says `depends_on: participant`, but
`participant` does not exist in A.

Not fatal — the skill can still be useful. But for the 25K pitch ("durable
cross-feature context") it limits depth. At minimum, allow `depends_on`
entries to be qualified with a repo:
`depends_on: bipinhcs11/participant-service#participant`.

### 4.3 No org-wide skill catalog or search

50,000+ SKILL.md files scattered across thousands of repos is unsearchable.
A developer asking "which features in our org handle PCI tokenization?" has
nowhere to ask. At 25K-dev scale you need:

- A nightly crawler that pulls every `.github/skills/**/SKILL.md` into a
  central index
- Search by feature name, dependency, repo, owner, confidence, staleness
- Dashboard: % repos with skills, % stale, % LOW-confidence still in review
  queue

Separate downstream product, but the difference between "we have a tool" and
"we have a platform."

### 4.4 No skill-quality gate before commit

Today the validator self-corrects two issue types. Everything else surfaces
to the human, who can choose to commit anyway. At 25K-dev scale, "human
ignores warning and commits" will happen. Need a CI gate: PR with
NEEDS_REVIEW or BLOCKING_ISSUES verdict from `skill-validator` cannot merge
without an "approved override" label from a feature lead. The lib spine
already supports this — just needs a workflow wrapping it.

### 4.5 No premium-request budget guard

The current selection guide explains *which* host to use. It does not
prevent a developer from running `skill-generator` against a 3000-class repo
at Opus tier and burning the team's monthly Copilot budget in 90 minutes.
Pre-flight already does a "300-class warning" — that should also estimate
token spend and require explicit acknowledgement.

### 4.6 Drift detection beyond PRs

Tracker runs when a PR is opened. But code can drift via merges from other
branches, or `last_updated` can go stale because a feature was not touched
but its dependencies were. Need a periodic scheduled scan — quarterly is
fine — that produces a "skills health" report per repo: how many skills
have not been re-validated this quarter, how many `key_classes` were
renamed, etc.

### 4.7 Skill versioning / migration story

Today's artifact-3 might become artifact-4. With 1000+ repos and 50,000+
committed skills, in-place migration becomes its own engineering project.
Need a migration runbook now, before the schema needs to change. Even if
the answer is "we'll provide a `skill-migrate` script when the time comes,"
writing that down today is what makes the rollout durable.

### 4.8 Skill template library for common patterns

Most internal Spring Boot CRUD services look alike. A library of
"feature-skill templates" (REST CRUD service, batch ingestion job, event
consumer, scheduled reconciler) could short-circuit first-gen — the
generator picks the matching template and fills in specifics. This drops
first-gen cost from ~12 Opus turns to ~3. At 1000+ repos that is a real
number.

---

## 5. The premium-request economics — sharpen the ROI math

The current enterprise guide gives a directional answer ("12-ish initial
turns replace dozens or hundreds"). For a 25K-dev rollout decision,
leadership will want numbers. Back-of-envelope to refine:

**Assumptions (plug in your real values):**

- Copilot Business: ~$39/dev/month → $11.7M/year for 25K devs
- Each dev currently spends ~50 premium requests/month rediscovering context
  (industry-ish guess)
- After skills are committed, that drops 30% to ~35 requests/month
  (conservative)
- First-run cost per repo: ~12 Opus-tier turns (already in your guide)
- Tracker cost per PR: ~1 Sonnet/Codex turn
- Update cost per affected PR: ~1-2 turns per affected skill

**Math:**

- 15 premium requests/dev/month saved × 25K devs × 12 months = 4.5M saved
  premium requests/year
- If you value each at $0.10 in upstream cost (rough), that is $450K/year in
  API spend avoided
- Dev-hours: 15 requests/month × 2 minutes saved per request = 30 min/dev/month
  = 6 hours/dev/year = 150K dev-hours/year
- At a $100/hr loaded cost, that is **$15M/year in dev-time recovery**

The $15M number is what gets leadership attention. The $450K API number is
the budget pitch. The model is approximate but defensible because every
input is something you can measure once the pilot is running. Without
measurement (§3.6) you cannot prove it; with measurement you can write the
case.

**Add to roadmap:** a "measurement skill" — a tiny instrumentation layer
that asks Copilot/Claude/Codex to log when they read a skill. Even an
opt-in CSV in `.github/skills/.consumption-log.csv` would let you build the
ROI case from real data instead of estimates.

---

## 6. The pilot sequencing I would run differently

The current "10-team operating model" in
`docs/enterprise-agent-selection-guide.md` is good for steady state, but
the 150-dev June launch needs a sub-pilot waterfall. Each wave has a
measurable go/no-go gate:

| Wave | Population | Duration | Go/no-go gate |
|---|---|---|---|
| 0 — Platform proves the loop | 5 platform engineers, their own repos | 1 week | All 5 successfully generated + committed skills; tracker correctly flagged one real PR |
| 1 — Feature leads, supported | 10 feature leads, their team repos, with platform support on Slack | 2-3 weeks | 10/10 generated; ≥80% NEEDS_REVIEW issues resolved within 1 week; one cross-feature dependency working in practice |
| 2 — Consumption-only pilot | 50 devs on repos that already have skills, no generation work | 2-3 weeks | Telemetry shows skill-reads >0; pre/post survey on "first answer was useful"; ≥1 documented case where a skill prevented a wrong code change |
| 3 — Multi-team integration | 150 devs across 5-10 teams | 4 weeks | Tracker run on every PR; updater run on impacted ones; at least one cross-team feature change goes through the full loop |
| 4+ — Wider rollout | Wave-based expansion to 1000, 5000, 25K | Q3-Q4 | Org-wide telemetry shows the four north-star metrics moving in the right direction |

The big shift vs the current guide: **separate "people who generate skills"
from "people who consume them."** Wave 2 is consumption-only, with skills
produced in Waves 0-1. This decouples skill quality from skill economics —
you can prove the daily-consumption value before asking 150 people to
learn the generator workflow.

---

## 7. What I would add (priority-ordered list, no code yet)

1. **Bootstrap one-shot** (§3.1, §3.2) — single command/skill that drops
   Copilot/Claude/Codex instruction files into a target repo. Half-day of
   doc work.
2. **PII/secret scrub rule in generator contract** (§3.4) — prose addition to
   `skills/skill-generator/SKILL.md`, plus a regex sanity check in
   `lib/validate.py`. Hours of work, prevents an embarrassing incident.
3. **Add `Error Handling` and `AI Agent Instructions` as optional sections in
   artifact-3** (§3.5) — already recommended in the Petclinic test report.
4. **GitHub Action that runs `skill-tracker` on PR open** (§3.3) — tracker is
   already read-only, just needs a workflow wrapper and a PR-comment template.
5. **Conformance test across host AIs** (§3.6) — 10 golden questions per
   reference repo, run quarterly. Confirms portability before scaling.
6. **Exec / leadership brief** (§3.7) — 1 page, ROI math from §5, the pilot
   waterfall from §6.
7. **Measurement layer** (§5) — opt-in consumption log so you can build the
   real ROI case.
8. **Skill-validator as CI merge gate** (§4.4) — wrap existing validator in a
   GitHub Action.
9. **Multi-language roadmap decision** (§4.1) — pick one of the three options
   and write it down. Not building yet, just committing to scope.
10. **Cross-repo dependency notation** (§4.2) — extend `depends_on` syntax to
    support `repo#feature` qualification.
11. **Premium-request budget guard in pre-flight** (§4.5) — extend the
    existing 300-class warning to include estimated spend.
12. **Org-wide skill catalog/search** (§4.3) — separate downstream product,
    but flag the scope now.
13. **Drift detection scheduled scan** (§4.6) — quarterly cron, produces a
    per-repo health report.
14. **Schema migration runbook** (§4.7) — even a placeholder runbook today
    saves a year of pain later.
15. **Skill template library** (§4.8) — drops first-gen cost; nice-to-have,
    not pilot-blocking.

---

## 8. The open questions only you can answer

1. **What's the actual language mix of those 25K devs?** This determines
   whether Java-only is a 50% ceiling or a 90% ceiling. If the latter, the
   Java-only product can ship as-is.
2. **Is there an internal "approved AI hosts" registry already?** If yes,
   the host-selection guide should reference it directly. If no, we should
   help create it during the pilot.
3. **Who owns the platform team that will run support for 150 devs in
   June?** This is the person who answers Slack questions when a generator
   run goes wrong. Without naming them, the pilot has no support model.
4. **What's the security/compliance review status?** The PII/secret-scrubbing
   gap (§3.4) becomes urgent if the answer is "we haven't talked to security
   yet." Cheap to fix; expensive if it surfaces in a security review at
   week 5.
5. **What's the measurement infrastructure for Copilot usage today?**
   Microsoft's Copilot admin dashboard shows aggregate request counts. If we
   can correlate those with repos that have/don't have skills, the ROI case
   writes itself.

---

## Top three things I would push for before June

The bootstrap one-shot (§3.1-3.2), the PII/secret scrub (§3.4), and the
measurement layer (§5). Each is small in code terms and huge in rollout
terms.
