# Skill Generator v2 — leadership one-pager (template)

A template for the executive brief. Replace every `<placeholder>` with your
organisation's real numbers before sending. Keep it to one printed page when
exported.

**Status of this document:** Template. Numbers below are illustrative only.

---

## The problem

Starting **June 1, 2026**, GitHub Copilot Business / Enterprise moves to
usage-based billing. Every redundant Copilot chat or agent turn — every time
a developer asks an AI to rediscover the same repo, feature, or business rule
— directly debits the organisation's AI credit pool.

For `<organisation>` at `<25,000>` developers, this turns repeated context
discovery from an invisible productivity tax into a visible budget line.

*This shift affects paid Copilot Chat, CLI, and agent workflows. It does
**not** reduce included Copilot autocomplete usage.*

---

## What we're proposing

Skill Generator v2 — a governed, source-backed AI context layer that
captures feature knowledge once and reuses it across every approved coding
agent (Copilot Chat, Claude, Codex). Developers do not write the context by
hand. The generator agent walks each Java repo, extracts feature behavior
from code + config + MyBatis XML + SQL + Spring Batch + scripts, and
produces reviewable `SKILL.md` files committed to `.github/skills/`. AI
assistants read those skills first before answering.

The killer one-liner:

> *"We are not generating documentation. We are creating a governed,
> source-backed AI context layer that reduces repeated repo discovery and
> improves agent-assisted code changes."*

---

## What we're asking for

| Ask | Detail |
|---|---|
| **Pilot funding** | `<N>` engineer-weeks for platform team during the 150-dev June pilot |
| **Approved host AI** | Confirmation of which Copilot SKU and which Claude / Codex tiers the pilot may use |
| **Pilot teams (5-10 repos)** | Mix per pilot plan: one Spring Boot microservice, one Spring Batch app, one MyBatis / XML-heavy module |
| **Security review slot** | One reviewer for PII/secret scrub work (small scope, blocking) |
| **Decision: build, buy, or partner** | Stance on GitHub Copilot Spaces; see "Strategic stance" below |
| **Decision: multi-language scope** | Java-only for pilot. Three options for 2027: stay Java-only, add language-agnostic mode, build per-language variants. Pick one in writing. |

---

## ROI model (replace numbers with your enterprise's actuals)

> *This model targets paid Copilot Chat / agent workflows. Copilot
> autocomplete usage is included in the SKU and is not affected.*

| Input | Value |
|---|---|
| Developer count | `<25,000>` |
| Copilot Business cost per developer per month | `$<39>` |
| Annual Copilot spend | `$<11.7M>` |
| Current premium-request rate per developer per month | `<50>` |
| Expected reduction with skills committed | `<30%>` → `<15>` requests / dev / month saved |
| Estimated upstream cost per request | `$<0.10>` |
| Estimated time saved per request | `<2>` minutes |
| Loaded developer cost per hour | `$<100>` |

| Outcome | Annual value |
|---|---|
| Saved premium requests | `<15 × 25,000 × 12>` = `<4.5M>` requests |
| API spend avoided | `<4.5M × $0.10>` = `$<450K>` |
| Developer-hours recovered | `<15 × 2 / 60 × 25,000 × 12>` = `<150K>` hours |
| Time recovery in money | `<150K × $100>` = `$<15M>` |

**The $15M is the leadership number.** The $450K is the budget pitch. Both
are estimates; the pilot's job is to convert them to measured outcomes.

The model is approximate but defensible because every input is something
your organisation can measure once the pilot is running. See
`docs/measurement-plan.md` for the schema and the GitHub Copilot Usage
Metrics dependency.

---

## Pilot plan (waves)

| Wave | Population | Duration | Go/no-go gate |
|---|---|---|---|
| 0 — Platform proves the loop | 5 platform engineers, their own repos | 1 week | All 5 generated + committed skills; tracker correctly flagged one real PR |
| 1 — Feature leads, supported | 10 feature leads, their team repos, platform on Slack | 2-3 weeks | 10 / 10 generated; ≥ 80% review issues resolved within 1 week; one cross-feature dependency working in practice |
| 2 — Consumption-only pilot | 50 devs on repos that already have skills, no generation work | 2-3 weeks | Telemetry shows skill-reads > 0; pre/post survey on first-answer usefulness; ≥ 1 documented case where a skill prevented a wrong change |
| 3 — Multi-team integration | 150 devs across 5-10 teams | 4 weeks | Tracker run on every PR; updater run on impacted ones; ≥ 1 cross-team feature change goes through the full loop |
| 4+ — Wider rollout | Wave-based expansion to 1,000, 5,000, 25,000 | Q3-Q4 | Telemetry shows the four north-star metrics moving in the right direction |

Separating Wave 1 (skill producers) from Wave 2 (skill consumers) is the
critical design choice. It lets us prove daily-consumption ROI before
asking 150 developers to learn the generator workflow.

---

## Risks and how we mitigate

| Risk | Mitigation |
|---|---|
| Generated skills contain secrets or PII | Defense-in-depth: scrub in generator + updater contracts; validator catches anything that slipped through (already shipped) |
| Stale skills mislead AI worse than no skills do | Tracker on every PR; mandatory PR policy (`docs/pr-policy.md`); confidence/review_required flags expose drift |
| Vendor lock-in to one host AI | All skills work across Copilot, Claude, Codex; the schema is portable; planned future MCP server abstraction |
| Java-only ceiling on addressable population | Explicit scope decision in writing (see "What we're asking for" above) |
| Platform team becomes a bottleneck | Federated ownership: schema central, skill content owned by feature teams (CODEOWNERS) |
| ROI claims cannot be backed by data | Measurement plan ships before pilot; GitHub Copilot Usage Metrics API + audit-artifact aggregation; survey + case studies fill repo-level gaps |

---

## Strategic stance: build, buy, or partner

GitHub Copilot Spaces is moving toward similar functionality. The four
options:

| Option | Trade-off |
|---|---|
| Build & own (current path) | Full control, 25K-dev specific, but maintaining infrastructure GitHub will eventually provide |
| Adopt Spaces when mature | Lower TCO long-term, loses catalog / graph / portability advantages |
| Build now, contribute back upstream | Open-source contracts, become a GitHub partner, influence the standard |
| **Recommended: build the wrapper layer, swap engines** | Keep schema + catalog + future MCP server as durable infrastructure; treat agent skills as portable; when Spaces matures, swap engines |

Decision needed before quarterly planning.

---

## What success looks like at end-of-pilot

Three pieces, in order of weight:

1. **Quantitative:** average host-turns per feature task drops measurably
   on pilot repos vs. control repos. 15-40% reduction = plausible win;
   below 10% = flat, investigate.
2. **Qualitative:** developer survey shows ≥ 70% "first answer had enough
   context" on pilot repos vs. baseline on control repos.
3. **Stories:** at least 3 documented cases where a skill prevented a
   wrong code change.

Two of three moving = scale to Wave 4. One moving = investigate. Zero
moving = stop and re-evaluate.

---

## What this is not (set expectations honestly)

- *This does not reduce included Copilot autocomplete usage; it targets
  paid / usage-sensitive chat and agent workflows where repeated context
  discovery burns turns and tokens.*
- This does not eliminate Copilot AI credit consumption; it concentrates
  expensive reasoning in a few up-front generation runs instead of
  spreading it across thousands of repeated developer-prompt rediscovery
  sessions.
- This does not write code for developers; it gives the AI agents that
  write code the context they need to write it correctly.
- This does not replace code review, architecture review, or CODEOWNERS;
  it gives those processes a machine-readable artifact to refer to.

---

## Decision needed by

`<date>` — the pilot timeline assumes platform-team work begins by `<date>`
and the first pilot wave starts by `<date>`. Delays past `<date>` push
the wider rollout into post-June-1 billing reality without measured
data to defend the budget impact.

---

## More detail

- Full plan: `docs/enterprise-rollout-25k-analysis-synthesis.md` (v3, signed
  off by two independent reviewers)
- Forward-looking vision (post-pilot): `docs/enterprise-rollout-25k-faang-roadmap.md`
- Measurement architecture: `docs/measurement-plan.md`
- PR policy: `docs/pr-policy.md`
- Bootstrap runbook: `docs/bootstrap-runbook.md`
- Generator + tracker + updater + validator contracts: `skills/`
