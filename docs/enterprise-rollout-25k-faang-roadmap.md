# Enterprise rollout — FAANG-scale roadmap (post-pilot vision)

**Author:** Claude (Opus 4.7, 1M context), synthesizing FAANG-architect
think-tank passes from both Claude and Codex.
**Date:** 2026-05-18
**Status:** Forward-looking. Not for June. Revisit *after* the June pilot has
delivered and the converged synthesis (`docs/enterprise-rollout-25k-analysis-synthesis.md`)
has been executed.
**Audience:** Platform team architects, engineering leadership, anyone asking
"what's the two-year vision once the pilot proves the loop?"

---

## What this document is and is not

**Is:** The forward-looking architecture for what Skill Generator becomes
when it scales from a 150-dev pilot to 25K-dev paved-road infrastructure.
Combines the strongest FAANG-architect ideas from independent Claude and
Codex think-tank passes.

**Is not:** A plan for June. The synthesis is the June plan. Do not let this
document re-open settled questions in the synthesis. Read this only after
the pilot is in flight.

**Also is not:** A commitment. The world will move between now and when the
pilot finishes. Revisit and edit before adopting any of this.

---

## The strategic frame

Skill Generator should not be positioned as "a repo tool." It should become
**a paved-road AI context platform** — the durable layer every enterprise
coding agent reads from before editing code.

The killer phrase for leadership (Codex):

> *"We are not generating documentation. We are creating a governed,
> source-backed AI context layer that reduces repeated repo discovery and
> improves agent-assisted code changes."*

Once that framing is accepted, the natural follow-up is: *"what
infrastructure-grade capabilities does this need that markdown-files-in-repos
cannot provide?"* This document is the answer.

---

## The three-layer architecture (Codex's frame, expanded)

| Layer | What lives here | Owner |
|---|---|---|
| **Repo layer** | `.github/skills/SKILL.md`, `catalog.md`, bootstrap-dropped instruction files, audit logs | Repo team |
| **Platform layer** | Skill Graph Service, MCP server, Trust Score computation, lifecycle automation, Task Context Pack API, production-grounded validator, semantic PR reviewer, Golden Task Benchmark, central telemetry, pilot dashboard | Central platform team |
| **Governance layer** | Owners + CODEOWNERS, PR policy, security scrub, classification, lifecycle status enforcement, risk taxonomy | Platform team + security + compliance |

Each layer has different versioning, different ownership, and different
SLOs. Don't conflate them.

---

## Schema additions (frontmatter, beyond what's in the synthesis)

The synthesis already adds `aliases`, `business_terms`, `owner_team`,
`business_owner`, `technical_owner`. The FAANG-grade additions:

| Field | Source | Purpose |
|---|---|---|
| `trust_score` (integer 0-100) | Codex | Single composite primitive combining confidence, freshness, validator status, PII scan, ownership, usage. The number a developer checks before relying on a skill. |
| `trust_level: trusted \| review_required \| stale \| blocked` | Codex | Human-readable categorical derived from `trust_score`. |
| `lifecycle: draft \| trusted \| stale \| deprecated \| archived` | Codex | Explicit state machine. Prevents zombie skills for sunset features from polluting agent context at scale. |
| `last_validated` (ISO date) | Codex | When validator last ran end-to-end (separate from `last_updated`). |
| `changed_key_classes_since_validation` (integer) | Codex | Auto-computed drift signal. |
| `data_classification: public \| internal \| confidential \| restricted` | Codex | Operationalizes security classification. Required for regulated industries. |
| `pii_review_required` (boolean) | Codex | Surfaces skills needing privacy review. |
| `confidence_aged_to` (ISO date) | Claude | Records automatic confidence decay events ("HIGH aged to MEDIUM on 2026-09-18"). |

The principle: trust is computed, not asserted. A skill cannot claim
`trust_level: trusted` if it has stale validation, drifted classes, or
failing PII scan. The computation is platform-team logic, not author choice.

---

## Tier 1 — Platform-layer build-outs (next 6 months post-pilot)

### 1. Skill Graph Service

Central nightly crawler that ingests every `.github/skills/**/SKILL.md`
across the org, parses frontmatter, and lands it in a graph database
(Neo4j or PostgreSQL with recursive CTEs).

Unlocks:
- "Which features in our org touch PCI data?" — one query
- "What depends on `participant-service`?" — works across repos, which today's `depends_on` cannot
- "Show me all LOW-confidence skills owned by the billing team" — one query
- Powers dashboards, Slack bots, CLI tools — each consumes the graph instead of reinventing the crawl

### 2. Expose the Skill Graph as an MCP server

The unlock that makes this *the* AI context layer, not just a Copilot-aware
doc system. Expose tools:

```
skill.search          # natural language -> skill IDs
skill.get             # full skill content by ID
skill.dependencies    # depends_on + depended_on_by chain
skill.find_by_class   # FQCN -> owning skill
skill.task_context    # task description -> Task Context Pack
```

Any AI client (Claude, Cursor, Copilot agents, internal tools) gets uniform
API access. Token-efficient (load only what's needed). Version-stable.
Largely makes the cross-host conformance problem disappear because the API
*is* the standardization layer.

### 3. Task Context Pack (Codex)

When a developer types "modify invoice compare to include participant
eligibility," the platform builds a focused bundle:

```
Primary skill:        invoice-compare
Dependency skills:    participant
Likely files:         InvoiceCompareService.java, ParticipantClient.java,
                      InvoiceMapper.xml
Risk:                 cross-feature dependency
Required validation:  invoice compare tests + participant contract check
Trust signals:        invoice-compare trust_score 87, participant 92
```

Delivered to the agent (via MCP `skill.task_context` or as a fetched
`.task-context-pack.md`). Replaces the agent's "rediscover the repo every
turn" with "start with the right bundle."

### 4. Skill Trust Score computation (Codex)

Nightly job computes `trust_score` per skill from:
- Confidence level (40% weight)
- Validator pass/fail (20%)
- Freshness — days since `last_validated` (20%)
- PII scan result (10%)
- Owner team responsiveness — % of impact PRs reviewed within SLO (10%)

Trust score drives `trust_level` thresholds:
- `≥ 80` → `trusted`
- `60-79` → `review_required`
- `40-59` → `stale`
- `< 40` → `blocked` (agents should not load this skill)

Auto-blocking is the killer feature. A skill with `trust_level: blocked`
gets filtered out of agent context, preventing plausible-but-wrong context
from poisoning answers.

### 5. Lifecycle automation (Codex)

Background process advances skills through states:
- `draft` → `trusted` when first validator pass + first review approval
- `trusted` → `stale` when `last_validated > 90 days` AND `changed_key_classes_since_validation > 0`
- `stale` → `deprecated` when owner team marks
- `deprecated` → `archived` after 90 days deprecated with no consumer reads

Archived skills move out of `.github/skills/` to `.github/skills/.archive/`
so agents stop loading them but the audit trail survives.

### 6. Production-grounded skill validation (Claude)

Cross-check skills against production reality, not just code:

| Signal | What it catches |
|---|---|
| Distributed traces | Skill says "no dependency on X" but traces show 80% of calls hit X |
| Production logs | Skill names endpoint `/v2/foo` but logs show traffic on `/v1/foo` too |
| Observability metrics | Skill says "uses Redis" but cache hit rate is 0 |
| Feature-flag exposure | Skill describes behavior gated by a flag at 0% |

The move from "docs mirror code" to "docs mirror behavior." Catches the
class of error code-only validation cannot find.

### 7. Skills-aware semantic PR review (Claude)

Beyond the tracker's "this PR may affect these skills." The semantic
reviewer reads:
- The diff
- Each affected skill's `## AI Agent Instructions`, `## Business Rules`, `depends_on` chain

Then posts a PR comment like:

> "PR #4521 changes `ParticipantService.eligibility()`. The `invoice-compare`
> skill (which depends on this) says: *'Invoice comparison must fail closed
> when eligibility returns null — never approve an invoice with unknown
> eligibility.'* Your change returns an empty result on null. This appears
> to violate the rule. Recommend reviewer verify."

AI reviewer #2 on every PR. Cheap (one Sonnet call per affected skill).
High signal because it's grounded in the rules the team wrote.

### 8. Golden Task Benchmark (Codex)

10 standard tasks per pilot repo, run before and after skills:

- Explain a feature
- Modify a validation rule
- Update a MyBatis query
- Change a batch file output
- Trace error handling
- Update a dependent feature
- Diagnose a stack trace
- Identify the right config key for a behavior
- Propose a test for a business rule
- Find the owner of a code path

Measure: answer quality (rubric-scored), host turns, defects shipped.
Compare before/after. This is the *experiment* that proves ROI to
leadership — not opinion, not correlation.

---

## Tier 2 — Value expansion beyond engineering (Claude)

The skill graph is reusable infrastructure. Same artifacts, different
consumers, different ROI stories.

### 9. Skills-driven incident response

When an incident fires, the on-call gets a Slack alert with the stack
trace. Bolt on:

1. Stack trace → identify likely feature (via skill `key_classes` lookup)
2. Pull that feature's SKILL.md, especially `## Error Handling`,
   `## AI Agent Instructions`
3. Pull all features in the `depends_on` chain
4. Post to the incident channel: "This stack trace looks like
   `invoice-compare`. Here's the context, the dependencies, and likely
   root-cause candidates from the rules."

MTTR reduction is a dollarable metric ops leadership cares about.
Different stakeholder than dev productivity; same infrastructure.

### 10. Skills as RAG corpus for non-engineering AI

Same files, different consumers:

- **Customer support:** CSR types "why didn't invoice #123 reconcile?" → AI reads `invoice-compare` skill, explains in plain English without exposing internal class names
- **Product managers:** PM asks "what changes if we modify payment terms by 5 days?" → AI reads affected skills, returns impact summary
- **New hires:** onboarding bot generates a personalized reading list from the skills the new hire's team owns

Significantly expands the addressable population beyond the 25K engineers.

### 11. Conway's Law made visible

`owner_team` on every skill + dependency graph = the *real* org chart.
Team A's skill depends on Team B's skill → there's a real coordination
need between A and B. If A and B don't talk, that's a Conway's Law gap.

Generate this view quarterly. Take it to engineering leadership. It's the
most defensible org-design artifact a platform team can produce, and it
comes free from infrastructure you're already building.

---

## Tier 3 — Strategic stance

### 12. Build / buy / partner on Copilot Spaces

GitHub is moving toward something Spaces-like. The platform team needs an
explicit position:

| Stance | Rationale |
|---|---|
| Build & own (current path) | Full control, 25K-dev specific, but maintaining infrastructure GitHub will eventually provide |
| Adopt Spaces when mature | Lower TCO long-term, loses catalog/graph/MCP advantages |
| Build now, contribute back upstream | Open-source contracts, become a GitHub partner, influence the standard |
| **Build the wrapper layer, swap engines** | Keep schema + catalog + MCP server as durable infrastructure; treat agent skills themselves as portable; swap Spaces in as a generation engine when it matures |

Recommendation: **option 4.** The schema, catalog, graph, and MCP server
are durable infrastructure. The agent contracts are replaceable. When
Spaces matures, swap engines — keep the platform layer.

Bridge with Spaces opportunistically (Codex's framing): treat generated
skills as a clean input into Spaces for pilot teams that already use
GitHub-native workflows. Don't depend only on it.

### 13. Token budget gamification

After June 1, every team has a Copilot AI Credits pool. Use skill quality
as a multiplier:

| Skill coverage of repo | Token budget effect |
|---|---|
| 90%+ HIGH confidence | +20% pool (reward) |
| 50-90% any confidence | Standard pool |
| < 50% coverage | Standard pool + Slack nudge to invest |

Aligns team incentives with platform success. Teams that invest in skills
get more budget; teams that don't, don't get penalized but feel friction.

---

## Tier 4 — Moonshots (12-18 months)

### 14. Auto-generation from production traces

Instead of crawling code to infer features, ingest a week of OTLP traces.
The traces *show* you what the real feature boundaries are: which services
call which, what RPCs cluster together, what data flows where. Feed that
to the generator alongside code. The skill becomes grounded in actual
production behavior, not just static analysis.

This is a real research project but it's a moat: nobody else can do this
because nobody else has your traces.

### 15. AI red-team for skills

Hire an internal AI red-team (or contract one) whose job is: try to make
Copilot/Claude/Codex give wrong answers about your features *with* skills
loaded. Find the failures. Patch the skills. This is how the airline
industry hardens checklists; do the same for AI context.

### 16. Skill-based action authorization

Make skills the access control layer for autonomous AI agents. Before an
agent commits a destructive change, check: does the relevant skill's
`AI Agent Instructions` authorize this kind of mutation? If not, halt and
ask a human. Skills become not just *context* but *policy*. The move that
makes you defensibly safer than competitors with looser agent governance.

### 17. Cross-repo "find similar features" / dedupe

Run a similarity scan across the skill graph. If 7 features in 7 repos
all have similar `key_classes`, `business_terms`, and patterns, you
probably have organizational duplication. Surface it. The kind of insight
that justifies a platform team to executives.

### 18. Skill quality as an SLI/SLO

Once you have a graph and a measurement layer, turn skill freshness into
a real SLO:

- 95% of skills `last_validated` within 90 days
- 99% of skills with `trust_level ∈ {trusted, review_required}`
- 99.9% of skills pass validator weekly

Page someone when the SLO is missed. Now it's infrastructure.

---

## FAANG-scale risk taxonomy

Risks the synthesis lists at pilot scale; here they get the full
taxonomy a 25K-dev rollout will face.

| Risk | Why it matters at 25K | Mitigation |
|---|---|---|
| IP exposure via third-party LLM APIs | Skills sent to Copilot/Claude/Codex on every interaction. Org-level data egress controls need to know. | Run through enterprise-tenanted Azure OpenAI; classify skills (`data_classification`); audit egress |
| Talent/morale impact of skill maintenance | Engineers hate docs. If skills become required overhead, productivity suffers or attrition spikes. | Heavy automation; generator does the work; lifecycle automation reduces busywork; token budget gamification turns it into reward |
| Skills as supply-chain attack surface | Malicious skill could mislead AI into writing exploit code. | Supply-chain controls equivalent to code: review, signing, provenance; CODEOWNERS-required review for `.github/skills/**` |
| Drift becomes plausible-but-wrong context | At 25K scale, stale-but-confident skills misdirect AI more than they help. | Trust Score + auto-blocking; production-grounded validation |
| Vendor lock-in by accident | If skills evolve to be Copilot-shaped, switching to Cursor or future tools becomes hard. | MCP server abstraction; portable schema; agent contracts that work across hosts |
| Regulatory classification | Features may map to regulated processes (HIPAA, PCI, SOX). Skills inherit that classification. | `data_classification` frontmatter + access controls + audit retention policy |
| Platform-team becomes a bottleneck | All change flows through platform team → scaling pain. | Federate ownership: skill schema/lifecycle owned centrally, skill content owned by feature teams |
| Observability gap | Without telemetry, no leadership case post-June 1. | Synthesis must-land item already covers; this layer adds Golden Task Benchmark for proof |

---

## What this roadmap explicitly is NOT

(Codex's "what I would NOT do" list, expanded.)

- Do **not** add a fifth core agent. Telemetry, lifecycle, and trust are
  platform plumbing; they don't need to be skills.
- Do **not** build a vector database before the graph proves need. The
  graph itself is the first investment; vector lookup comes only if
  semantic search beats structured query.
- Do **not** rely on agents self-logging skill reads. Central telemetry
  via host-provided metrics + audit-artifact aggregation only.
- Do **not** expand beyond Java until the Java/Spring/MyBatis/Batch story
  is provably strong at 1000+ devs. Multi-language is a scope decision,
  not a default.
- Do **not** let generated skills include secrets, real customer data,
  or full config values. Scrub at generator + updater + validator.
- Do **not** centralize all control in the platform team. Schema and
  trust computation are central; skill content is federated.
- Do **not** ship without observability. If you can't measure adoption
  and freshness, you can't defend the investment.
- Do **not** optimize only for the 80% case. Regulated industries,
  monorepos, and polyglot teams are the 20% where the platform either
  earns its scale or doesn't.

---

## The integrated stack diagram (text version)

```
+--------------------------------------------------+
| GOVERNANCE LAYER                                 |
| owners | CODEOWNERS | PR policy | security scrub |
| classification | lifecycle | risk taxonomy       |
+--------------------------------------------------+
                       |
+--------------------------------------------------+
| PLATFORM LAYER                                   |
| Skill Graph Service ----- MCP Server             |
|       |                       |                  |
| Trust Score ---- Lifecycle ---- Task Context Pack|
|       |                       |                  |
| Production-grounded validator ---- Semantic PR   |
|       |                       |                  |
| Central telemetry ---- Golden Task Benchmark     |
|       |                       |                  |
| Pilot dashboard ---- Build/buy/partner stance    |
+--------------------------------------------------+
                       |
+--------------------------------------------------+
| REPO LAYER                                       |
| .github/skills/SKILL.md (per feature)            |
| .github/skills/catalog.md (alias + discovery)    |
| .github/copilot-instructions.md (Copilot bridge) |
| CLAUDE.md / AGENTS.md (host instructions)        |
| .skill-gen-audit.md / .skill-update-audit.md     |
+--------------------------------------------------+
                       |
+--------------------------------------------------+
| CONSUMERS                                        |
| Coding agents (Copilot/Claude/Codex/Cursor)      |
| Incident response bot                            |
| Customer support AI                              |
| PM impact analysis                               |
| New-hire onboarding bot                          |
| Architecture review dashboard                    |
+--------------------------------------------------+
```

---

## When to revisit this document

Read this only after:

1. The June pilot has delivered (the synthesis's must-land items are shipped)
2. Pilot measurement has produced real ROI data (not estimates)
3. Leadership has asked "what's next" (not before)

Anything in this roadmap that still makes sense at that point is worth
considering. Anything overtaken by GitHub Spaces, model improvements, or
org changes should be dropped without ceremony.

The document is a snapshot, not a contract.

---

## Codex addendum — FAANG-scale architecture read

This addendum preserves the roadmap above and adds the Codex-side view: what to
prioritize, what to defer, and where to be careful so the platform does not
become too heavy before the June pilot proves value.

### The core product shift

At 25K-developer scale, Skill Generator should not be explained as "generated
docs." It should be explained as:

> A governed, source-backed AI context layer that gives coding agents the right
> feature knowledge before they answer, plan, review, or edit code.

That framing matters because it makes the investment comparable to build
systems, service catalogs, observability, and code search — not to wiki pages.

### What I strongly agree with

**Skill Graph Service is the platform foundation.**

Markdown in repos is the seed format. The enterprise value appears when the
skills become centrally queryable. The graph should answer:

- What features depend on participant eligibility?
- Which features touch PCI, SOX, HIPAA, or customer-impacting flows?
- Which skills are stale, blocked, or review-required?
- Which teams own high-risk dependency chains?
- Which repos have no feature coverage?

**MCP is the right interface, but not the first build.**

The MCP server is how Copilot, Claude, Codex, Cursor, internal agents, incident
bots, and review tools all consume the same context contract. But the graph
must exist first. Build the index, prove the query patterns, then expose MCP.

Recommended order:

1. Repo-local catalog + aliases + trust fields
2. Central crawler and index
3. Task Context Pack API
4. MCP server

**Task Context Pack is the developer-experience unlock.**

The best experience is not "agent, search the repo." It is:

```text
User task: Modify invoice compare report to include participant eligibility.

Primary skill: invoice-compare
Dependency skills: participant
Likely files:
- InvoiceCompareService.java
- ParticipantClient.java
- InvoiceMapper.xml
Risk:
- Cross-feature dependency
Required validation:
- Invoice compare tests
- Participant contract check
Trust:
- invoice-compare: trusted, 87
- participant: trusted, 92
```

This is the compact context bundle every coding agent should start with.

**Trust Score and confidence decay are mandatory at scale.**

Confidence alone is a point-in-time claim. Trust is a current operating state.
At enterprise scale, agents should prefer or reject skills based on trust level,
not just `confidence`.

Useful derived state:

```yaml
trust_level: trusted | review_required | stale | blocked
trust_score: 87
freshness_status: current | aging | stale
last_validated: "2026-06-01"
decay_review_required: false
```

A stale HIGH-confidence skill is more dangerous than no skill because it gives
the agent plausible but wrong context. Trust scoring is the mitigation.

### Where I would sequence differently

**Start with PostgreSQL before a graph database.**

Neo4j may become useful, but I would not start there. For the first central
index, PostgreSQL with JSONB, full-text search, and recursive CTEs is enough:

- simpler enterprise operations
- easier reporting and joins with team/repo metadata
- easier security review
- lower platform-maintenance burden

Move to a dedicated graph database only after query volume or relationship
depth proves PostgreSQL is painful.

**Production-grounded validation is powerful, but not near-term.**

Using traces, logs, feature flags, and observability to validate skill claims is
the right long-term direction. It is also sensitive: it touches production data,
security boundaries, telemetry ownership, and platform APIs. Treat it as a
year-two capability unless the org already has clean, approved observability
interfaces.

**Budget gamification should wait.**

Rewarding teams with larger AI credit pools for better skill coverage is
interesting, but too early it can feel bureaucratic. Start with positive
visibility:

- Teams with skills needed fewer turns.
- Teams with trusted skills had better first-pass answers.
- Teams with stale skills had more review churn.

Use incentives only after the platform has earned trust.

**Do not page teams for stale skills until adoption is real.**

Skill SLOs are correct eventually. Early on, dashboards and nudges are better
than paging. If engineers get paged for a platform they do not yet trust, the
platform loses politically.

### Extra bets I would add

#### 1. Skill Trust Score as the main enterprise primitive

Trust Score should become the number leadership, developers, and agents all
understand.

Example inputs:

| Input | Why it matters |
|---|---|
| `confidence` | Quality of original feature boundary |
| `last_validated` | Freshness |
| validator result | Structural and semantic quality |
| PII/security scan | Safety |
| owner metadata present | Governance |
| dependency graph consistency | Cross-feature correctness |
| tracker impact frequency | Change pressure |
| unresolved `review_required` age | Review debt |

Agents should receive the trust level with the skill. A blocked skill should
not be loaded silently.

#### 2. Sanitized business-facing projections

Raw SKILL.md files are for engineering agents. Customer support, PMs,
business analysts, and onboarding bots should not consume raw implementation
detail.

Create derived projections:

- `engineering` view: full classes, packages, SQL, batch flows
- `business` view: behavior, inputs, outputs, rules, owners, no internal code
- `support` view: customer-impacting outcomes and error scenarios
- `exec` view: feature purpose, owner, dependency risk, trust status

Same source-backed skill, multiple safe projections.

#### 3. Skills-aware PR review as the first active-governance feature

After tracker/updater is stable, the first high-value active feature should be
semantic PR review grounded in skills:

- reads the diff
- reads affected skills
- reads dependency skills
- checks business rules and AI Agent Instructions
- comments only when a rule may be violated

This is more valuable than generic AI code review because it is feature-aware.

#### 4. Build-vs-buy guardrail

Keep the durable assets vendor-neutral:

- schema
- catalog
- trust score
- graph
- telemetry
- governance rules
- MCP/API layer

Treat Copilot Spaces, Copilot coding agent, Claude, Codex, Cursor, and future
tools as consumers or engines. The platform should survive vendor changes.

#### 5. Golden Task Benchmark before big investment

Before funding a large graph/MCP platform, prove the value with a benchmark:

- 10 tasks per pilot repo
- run before and after skills
- measure turns, correctness, files touched, review comments, and developer
  confidence

This gives leadership a clean before/after story and prevents roadmap work from
becoming belief-driven.

### My post-pilot priority stack

If June succeeds, I would prioritize like this:

| Priority | Build | Why |
|---|---|---|
| 1 | Trust Score + confidence decay | Prevents stale skills from poisoning agent context |
| 2 | Per-repo catalog + aliases hardened from pilot feedback | Fixes discovery before centralizing |
| 3 | Central PostgreSQL skill index | Turns repo artifacts into platform data |
| 4 | Task Context Pack API | Gives agents compact, task-specific context |
| 5 | Skills-aware PR review | Converts passive context into active governance |
| 6 | MCP server | Standardizes context access across AI tools |
| 7 | Cross-repo dependency notation | Makes microservice dependency context real |
| 8 | Sanitized non-engineering projections | Expands value beyond developers safely |

### My caution list

- Do not expand beyond Java until Java/Spring/MyBatis/Batch is trusted at
  meaningful scale.
- Do not centralize skill content ownership in the platform team; feature teams
  must own truth, platform owns schema and tooling.
- Do not ship a vector database before structured graph/query needs are proven.
- Do not treat telemetry as surveillance; keep it team/repo-level and
  business-value oriented.
- Do not let Skills become a mandate to write docs manually. Automation is
  load-bearing.
- Do not let low-trust skills flow into agents without visible warnings.

### The concise FAANG pitch

If this works, the company gets more than cheaper Copilot usage. It gets a
living, governed map of how software features actually work:

- developers use it for coding
- reviewers use it for PR risk
- on-call uses it for incidents
- architects use it for dependency maps
- leaders use it for ownership and investment decisions
- AI agents use it as their trusted operating context

That is the long-term prize.
