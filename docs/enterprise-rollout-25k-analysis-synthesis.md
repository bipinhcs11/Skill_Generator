# Enterprise rollout analysis — synthesis of Claude + Codex reviews (v3)

**Author:** Claude (Opus 4.7, 1M context), synthesizing across three review passes.
**Date:** 2026-05-18
**Version:** v3 — incorporates Codex's sign-off on v2 with two wording
corrections (PII rule extends to validator contract; Copilot metrics by
org/team not repo) and one addition (autocomplete-exclusion disclaimer in
leadership pager and ROI math).
**Inputs (frozen, do not edit):**
- `docs/enterprise-rollout-25k-analysis-claude.md` — Claude's independent first read
- `docs/enterprise-rollout-25k-analysis-codex.md` — Codex's independent first read
**Iteration record:** v1 (Claude's first comparison) was reviewed by Codex,
who corrected three stale facts and five framing issues; the measurement
approach was refined through a follow-up exchange. v2 was reviewed by Codex
again and signed off with two wording corrections + one addition. v3 below is
the converged plan after that sign-off pass and is intended to be the
decision artifact for the platform team.

---

## The big context Claude missed in the first round

Codex caught the **June 1, 2026 GitHub billing model change** — Copilot
Business/Enterprise moves to usage-based billing (input/output/cached tokens)
with enterprise budget controls. Claude misread the user's "from June onwards
copilot is rolling based on usage" as "the Copilot rollout phases based on
usage data."

This reframes the urgency:

- **Before June 1:** "premium request" counts are an abstraction.
- **After June 1:** redundant Copilot chat turns create budget pressure
  inside the enterprise's pooled AI credit budget. Note (Codex correction):
  this is budget pressure, not always direct marginal cash — enterprises get
  pooled credits and budget controls. But the budget is finite, and waste is
  visible.

The 150-dev pilot launching in June lines up exactly with the billing change.
That is why this is time-sensitive.

---

## What Codex caught that Claude got wrong in v1

| Issue | Correction |
|---|---|
| **v1 listed "Error Handling + AI Agent Instructions" as must-land** | Stale fact. Both are already in the artifact-3 contract as optional sections (`skills/skill-generator/SKILL.md` section list; `skills/skill-validator/SKILL.md` validation table). Petclinic test report's 2026-05-17 recommendation was already implemented. Dropped from must-land. |
| **v1 said catalog is what Copilot/Claude/Codex "actually look at first"** | Too strong. Reality: they look there reliably *only if* bootstrap instructions tell them to, and even then Copilot custom instructions are not deterministic. Reframed below. |
| **v1 proposed putting a PII regex check in lib/** | Violates the 500 LOC architectural boundary that CLAUDE.md explicitly defends. Scrub rule goes in generator/updater contracts. If deterministic scanning is later needed, it requires a design-history decision. |
| **v1 proposed self-logging via `.consumption-log.csv`** | Noisy, unreliable, politically awkward. Replaced with central telemetry approach (§Measurement below). |
| **v1 proposed bootstrap as a fifth agent** | Preserves the 4-agent mental model. Bootstrap is a template/script/runbook, not a SKILL.md. |
| **v1's phrasing "cannot honestly tell 150 devs use whichever host"** | Too absolute. Honest phrasing: "Pilot is supported on \<approved host\>; broader portability is a scale gate." |
| **v1's phrasing "30-line template task"** | Files are small; adoption and maintenance are the hard parts. |
| **v1's phrasing "every redundant chat turn directly debits budget"** | Directionally true after June 1, but enterprises have pooled credits + budget controls. Phrase as "budget pressure inside the org's pool." |
| **v1 missed the Petclinic re-test + simulated PR tracker test** | Codex right. These are in the release-readiness checklist as `❌ Real PR diff tracker test` and `❌ Real PR diff updater test`. Added to must-land. |

---

## Where Codex's first review was sharper than Claude's first read

| Codex's point | Why it beat Claude's version |
|---|---|
| **Skill catalog/manifest per repo (`.github/skills/catalog.md`)** | Per-repo, immediately useful; solves the "INVCOMP -> invoice-compare" mapping on day one. Claude had only an org-wide catalog as a future item. |
| **Aliases + `business_terms` in frontmatter** | Single highest-leverage addition Codex named. Claude did not think of it. Bridges natural-language to skill-ID. |
| **Owner governance metadata (`owner_team`, `business_owner`, `technical_owner`) + CODEOWNERS** | Concrete and adoptable. Wires to existing GitHub primitive. |
| **PR policy framed as engineering hygiene** | Workflow rule, not just a CI job. "Java/MyBatis/SQL/batch PRs need a tracker-clean report OR updated skills + audit." |
| **Distinction: Copilot autocomplete (included) vs Chat/agent (paid)** | Makes the ROI claim more defensible because it does not overclaim. Claude lumped all Copilot usage together. |
| **"AI context infrastructure" positioning** | The right narrative for 25K-scale and leadership conversations. Claude called it "context for AI." |
| **Specific pilot repo mix** | "One Spring Boot microservice, one Spring Batch app, one MyBatis/XML-heavy repo." Concrete; matches v2 architecture coverage. |

## Where Claude's first read added things Codex did not cover

| Claude's point | Why it still belongs in the plan |
|---|---|
| **Java-only is the addressable-population ceiling** | If only ~40% of 25K devs touch Java, the rollout pitch caps at 10K, not 25K. Strategic-scope decision should be in writing before the leadership pager. |
| **Cross-repo dependency model** | `depends_on` is intra-repo today. In a microservices org, that's the whole point of "feature context." Post-pilot, but on the scale-gate list. |
| **PII / secrets scrub as a pilot blocker** | Real `application.yml` files have connection strings. The generator will faithfully write them into SKILL.md. The kind of incident that ends pilots. Codex agreed it's needed, just disagreed on placement (correctly). |
| **Conformance test across host AIs** | Pilot-blocking *only if* pilot is multi-host. If pilot is single-host, conformance moves to scale-gate. Decide before June. |
| **Pre-flight token-budget guard** | Prevents a dev burning $200 of Opus tokens on a 3000-class repo by accident. Post-pilot for now. |
| **Schema migration runbook** | When artifact-3 becomes artifact-4, 50K committed skills need a story. Placeholder runbook today saves a year of pain later. Post-pilot. |
| **Wave-2 "consumption-only pilot"** | Separates generators from consumers; proves daily-consumption ROI without conflating it with generation effort. Folded into pilot structure below. |

---

## Where both reviews strongly agreed (the convergence list)

Two independent analyses landed on the same diagnosis. High-confidence inputs:

1. The 4-agent split (generator, tracker, updater, validator) is correct; do not add more.
2. Some form of catalog / index / discoverability layer is the next-biggest unlock.
3. CI / PR integration is needed for the tracker.
4. Measurement is required — without it, no leadership case.
5. Per-skill ownership is needed for governance at scale.
6. Security / PII rules must be added.
7. Pilot needs measurable before / after on real teams.
8. The product is a "context layer," not "a script that generates docs."

---

## Must land before June (pilot blockers) — reordered per Codex

| # | Item | Source | Notes |
|---|---|---|---|
| 1 | **PII / secret scrub rule in generator, updater, and validator contracts** | Both (Codex's placement correction; validator coverage added in v3) | Security incident risk before discoverability. *Not in lib/.* Defense-in-depth: generator + updater are the prevention layer (do not write secrets); validator is the safety net (flag any sensitive-looking value that still appears in generated or updated skills). Contract prose should label this explicitly so contract authors do not let prevention atrophy on the assumption the validator will catch it. If deterministic scanning later needed, design-history decision required. |
| 2 | **Aliases + `business_terms` in artifact-3 frontmatter + per-repo `.github/skills/catalog.md`** | Codex | Single schema/discovery change. Catalog is the *intended* discovery layer for Copilot/Claude/Codex *when bootstrap instructions point at it* — not magic. |
| 3 | **Bootstrap package (template/runbook, NOT a fifth agent)** | Both | Drops `.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`, `.github/skills/README.md`, and catalog skeleton. Small to write, ongoing to maintain. |
| 4 | **Owner metadata** | Codex | Minimum `owner_team`; add `business_owner` / `technical_owner` if org can maintain. Wire to CODEOWNERS. |
| 5 | **Written PR policy** | Codex | "Java / MyBatis / SQL / batch / script behavior changes need a tracker-clean report OR updated skills + audit." Doc first; CI enforcement is post-pilot. |
| 6 | **Regenerate Petclinic baseline + simulated PR tracker test + simulated PR updater test** | Codex (missing from v1) | Closes 3 `❌` items in release-readiness checklist. Must precede second-team pilot. |
| 7 | **Measurement plan with central telemetry** | Both (refined) | See §Measurement below. |
| 8 | **Leadership one-pager** | Both | ROI model with *your* enterprise numbers (not Claude's $39 / $0.10 placeholders). Pilot waves, risks, go/no-go criteria. Includes the multi-language scope decision in writing. **Must include the autocomplete-exclusion disclaimer:** *"This does not reduce included Copilot autocomplete usage; it targets paid/usage-sensitive chat and agent workflows where repeated context discovery burns turns/tokens."* The same disclaimer must appear wherever ROI is quantified, not only in the pager — otherwise the pager disclaimer reads as ass-covering after the fact. |

**Conformance test:** pilot-blocking *if* the pilot is multi-host (Copilot + Claude + Codex). If pilot standardizes on one approved host, it moves to scale-gate. Decide which before June.

---

## Measurement plan (the refined approach)

The original "self-log via `.consumption-log.csv`" idea was wrong. The replacement, converged with Codex:

### Architectural rule (codify this)

> **In-repo audit artifacts** = review evidence the team needs for *that repo*. They stay in-repo. Examples: `.skill-gen-audit.md`, `.skill-update-audit.md`.
>
> **Central telemetry** = operational measurement for the platform team. Stays central. Examples: tracker-run events, validation results, host-turn counts.
>
> The distinction is whether the data is for *that repo's team* or for *the platform*.

### Storage by scale

| Scale | Telemetry location |
|---|---|
| Pilot (5-10 repos) | `Skill_Generator/reporting/` folder (simple JSON dumps; good enough) |
| Mid-scale (50-500 repos) | Separate `Skill_Generator_Telemetry` repo |
| 25K scale | Enterprise data store fed by GitHub Copilot Usage Metrics API + audit-artifact aggregation |

### Event schema (no PII, no source code, no prompts)

```
event_type:    tracker_run | skill_generated | skill_updated | validation_run | pilot_feedback
repo:          billing-service          # or hashed if org policy requires
team:          payments
feature_id:    invoice-compare
skill_version: 3
host:          copilot | claude | codex
confidence:    HIGH | MEDIUM | LOW
review_required: true | false
result:        pass | needs_review | blocking
host_turns_used: 3                       # for billing-model traceability
input_tokens_estimated:  ...             # if host exposes
output_tokens_estimated: ...             # if host exposes
timestamp:     2026-06-10T14:30:00Z
```

### Telemetry data contract (write this up-front, one page)

- **Collected:** the fields above
- **Not collected:** prompts, generated code, source code excerpts, secrets, customer data, file contents, model responses, developer identity beyond team membership
- **Retention:** to be defined by security review before pilot
- **Access:** to be defined by the platform team

This is cheap to write now; impossible to bolt on cleanly when security asks.

### Precondition: verify what your Copilot SKU exposes

GitHub Copilot Usage Metrics surfaces vary by SKU (Business vs Enterprise) and
admin permissions. Enterprise/org/user-level metrics are documented; team-level
is constructed by joining; repo-level direct attribution is not surfaced.
Before the leadership pager promises specific metrics, verify with whoever
administers Copilot for the org which breakdowns are actually queryable on
your SKU and admin scope. Promise only what is queryable.

### Pilot metrics (what the dashboard actually reports)

- Tracker runs per repo, per week
- PRs that required skill updates vs tracker-clean
- Most reused skills (read-frequency proxy)
- Skills frequently `review_required`
- Average host turns to complete a feature task — before vs after skill adoption
- Copilot AI credit usage before vs after by org/team where available; repo-level impact inferred from tracker reports, update audits, pilot cohort mapping, and surveys (GitHub's Copilot Usage Metrics API does not expose direct repo-level attribution)
- Developer survey: "Did the first answer have enough context?"
- Qualitative case studies — concrete examples where skill context prevented a wrong change

### Future "skill-measurement" capability

If a measurement skill is later added, its job is to *collect and summarize existing telemetry/audit artifacts* — not to ask Copilot to log every time it reads a skill. Even then, the mental model stays at four agents; measurement is platform plumbing, not a fifth agent in the diagram.

---

## Must land before scale beyond pilot (25K-readiness)

| # | Item | Source |
|---|---|---|
| 9 | **Conformance test across host AIs** | Claude — if pilot single-host, this becomes the multi-host gate |
| 10 | **CI gate enforcing the PR policy** | Both — wraps tracker + validator |
| 11 | **Pre-flight token-budget guard** | Claude — extends existing 300-class warning |
| 12 | **Java-only scope decision *in writing*** | Claude — three options laid out; pick one. Even Java-only is a valid answer if written down. |
| 13 | **Cross-repo dependency notation** | Claude — `repo#feature` qualification in `depends_on` |
| 14 | **Skill migration runbook** | Claude — placeholder is enough |
| 15 | **Drift-detection scheduled scan** | Claude — quarterly cron |
| 16 | **Contract registry doc** | Codex — short doc listing `artifact-3`, `tracker-report-1`, future `catalog-1`. Platform teams want explicit contracts. |
| 17 | **Pilot operating runbook** | Codex — Slack/support owner, office hours, approved host(s), security reviewer, repo selection criteria, exit criteria. |

---

## Reframe the positioning (Codex's win)

The product is **AI context infrastructure**, not "a skill generator." All user-facing docs should be re-edited with that lens. The README first paragraph is the place to start.

---

## What this synthesis still does not cover

- It does not pick which 5-10 pilot repos to use. That is a list only the platform team can name.
- It does not assign owners. Codex flagged this; it remains open.
- It does not estimate effort in person-days. The must-land lists are sequenced by leverage, not by cost.
- It does not consider alternatives to Skill Generator (e.g., GitHub's own Copilot Spaces). That comparison should happen before broader rollout but is out of scope for this synthesis.
- It does not specify the security review process. Codex correctly notes that for 150 devs, support model matters as much as technical design — that includes a named security reviewer for the PII/secret scrub work.

---

## Open questions the platform team must answer before June

1. Is the pilot single-host (Copilot Chat only?) or multi-host? Determines whether conformance is pilot-blocker or scale-gate.
2. What's the actual language mix of the 25K devs? Determines whether Java-only is a 40% ceiling or a 90% ceiling.
3. Who owns platform support for the 150-dev pilot? Without a named owner, there is no support model.
4. What's the security review path for the PII/secret scrub work? Cheap if started now; expensive if it surfaces at week 5.
5. What's the measurement infrastructure for Copilot usage today? GitHub Copilot Usage Metrics API exists; who in your org has access?
6. Which 5-10 repos for the pilot? Codex's mix recommendation: at least one Spring Boot microservice, one Spring Batch app, one MyBatis/XML-heavy repo.
