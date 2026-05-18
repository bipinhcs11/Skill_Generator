"""
lib/audit_log.py — Format the evidence-phase artifact for the audit trail.

Architectural boundary: produces stable, diff-friendly Markdown for
.github/skills/.skill-gen-audit.md. Does not interpret evidence content.
The agent fills in the data; this module formats it consistently.

Why stable formatting matters: the audit log lives in git. Consistent output
means `git diff` shows only real content changes, not whitespace churn.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EvidenceBlock:
    domain_id: str
    confidence: str                            # HIGH | MEDIUM | LOW
    reasons: list[str]
    primary_packages: list[str]
    primary_entities: list[tuple[str, str]]    # (FullyQualified.Class, responsibility)
    inbound_callers: list[str]
    excluded_classes: list[tuple[str, str]]    # (FullyQualified.Class, reason)
    java_sources: list[str] = field(default_factory=list)
    config_sources: list[str] = field(default_factory=list)
    mybatis_sources: list[str] = field(default_factory=list)
    sql_sources: list[str] = field(default_factory=list)
    batch_sources: list[str] = field(default_factory=list)
    script_sources: list[str] = field(default_factory=list)
    outbound_dependencies: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class ValidationResult:
    domain_id: str
    validate_py: str      # "PASS" | "FAIL: <reason>"
    citation_check: str   # "PASS" | "FAIL: <reason>"


@dataclass
class CrossFeatureDependency:
    dependent: str
    provider: str
    evidence: str
    both_sides_present: bool


@dataclass
class ReviewQueueItem:
    domain_id: str
    confidence: str
    review_required: bool
    reason: str


@dataclass
class AuditLog:
    repo_name: str
    repo_path: str
    class_count: int
    domain_count: int
    evidence: list[EvidenceBlock] = field(default_factory=list)
    plan_revisions: list[str] = field(default_factory=list)   # plain-text strings
    validation_results: list[ValidationResult] = field(default_factory=list)
    review_queue: list[ReviewQueueItem] = field(default_factory=list)
    cross_feature_dependencies: list[CrossFeatureDependency] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _evidence(e: EvidenceBlock) -> str:
    out = [f"## {e.domain_id} evidence", "", f"Confidence: {e.confidence}", "Reason:"]
    out += [f"- {r}" for r in e.reasons]
    out += ["", "Primary packages:"] + [f"- {p}" for p in e.primary_packages]
    out += ["", "Primary entities + responsibilities:"]
    out += [f"- {cls} — {resp}" for cls, resp in e.primary_entities]
    out += ["", "Business evidence sources:"]
    out += ["- Java:"] + [f"  - {src}" for src in e.java_sources] if e.java_sources else ["- Java: (none observed)"]
    out += ["- Config/properties:"] + [f"  - {src}" for src in e.config_sources] if e.config_sources else ["- Config/properties: (none observed)"]
    out += ["- MyBatis mapper XML:"] + [f"  - {src}" for src in e.mybatis_sources] if e.mybatis_sources else ["- MyBatis mapper XML: (none observed)"]
    out += ["- SQL/migrations:"] + [f"  - {src}" for src in e.sql_sources] if e.sql_sources else ["- SQL/migrations: (none observed)"]
    out += ["- Spring Batch:"] + [f"  - {src}" for src in e.batch_sources] if e.batch_sources else ["- Spring Batch: (none observed)"]
    out += ["- Scripts/jobs:"] + [f"  - {src}" for src in e.script_sources] if e.script_sources else ["- Scripts/jobs: (none observed)"]
    out += ["", "Outbound dependencies:"]
    out += [f"- {domain} — {reason}" for domain, reason in e.outbound_dependencies] \
        if e.outbound_dependencies else ["- (none observed)"]
    out += ["", "Inbound callers:"]
    out += [f"- {c}" for c in e.inbound_callers] if e.inbound_callers else ["- (none)"]
    out += ["", "Excluded classes:"]
    out += [f"- {cls} — {r}" for cls, r in e.excluded_classes] if e.excluded_classes else ["- (none)"]
    return "\n".join(out)


def format_audit_log(log: AuditLog) -> str:
    lines = [
        "# Skill generation audit log",
        f"Generated: {log.generated_at}",
        f"Repo: {log.repo_name} ({log.repo_path})",
        f"Class count: {log.class_count}",
        f"Domain count: {log.domain_count}",
        "",
        "## Evidence artifacts",
        "",
    ]
    for e in log.evidence:
        lines += [_evidence(e), ""]

    lines += ["## Plan revisions", ""]
    lines += [f"- {r}" for r in log.plan_revisions] if log.plan_revisions \
        else ["(none — developer approved the first proposal)"]
    lines += ["", "## Validation results", ""]

    if log.validation_results:
        lines += ["| Domain | validate.py | citation_check.py |",
                  "|--------|-------------|-------------------|"]
        for r in log.validation_results:
            lines.append(f"| {r.domain_id} | {r.validate_py} | {r.citation_check} |")
    else:
        lines.append("(no results recorded)")

    lines += ["", "## Review queue", ""]
    if log.review_queue:
        lines += ["| Domain | Confidence | Review required | Reason |",
                  "|--------|------------|-----------------|--------|"]
        for item in log.review_queue:
            review = "true" if item.review_required else "false"
            lines.append(f"| {item.domain_id} | {item.confidence} | {review} | {item.reason} |")
    else:
        lines.append("(no review-required skills)")

    lines += ["", "## Cross-feature dependencies", ""]
    if log.cross_feature_dependencies:
        lines += ["| Dependent feature | Provider feature | Evidence | Both sides? |",
                  "|-------------------|------------------|----------|-------------|"]
        for lnk in log.cross_feature_dependencies:
            both = "yes" if lnk.both_sides_present else "NO — fix needed"
            lines.append(f"| {lnk.dependent} | {lnk.provider} | {lnk.evidence} | {both} |")
    else:
        lines.append("(no cross-feature dependencies found)")

    lines.append("")
    return "\n".join(lines)
