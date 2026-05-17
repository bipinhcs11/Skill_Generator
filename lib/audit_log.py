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


@dataclass
class ValidationResult:
    domain_id: str
    validate_py: str      # "PASS" | "FAIL: <reason>"
    citation_check: str   # "PASS" | "FAIL: <reason>"


@dataclass
class CrossDomainLink:
    caller: str
    called: str
    both_sides_present: bool


@dataclass
class AuditLog:
    repo_name: str
    repo_path: str
    class_count: int
    domain_count: int
    evidence: list[EvidenceBlock] = field(default_factory=list)
    plan_revisions: list[str] = field(default_factory=list)   # plain-text strings
    validation_results: list[ValidationResult] = field(default_factory=list)
    cross_domain_links: list[CrossDomainLink] = field(default_factory=list)
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

    lines += ["", "## Cross-domain links", ""]
    if log.cross_domain_links:
        lines += ["| Caller | Called | Both sides? |",
                  "|--------|--------|-------------|"]
        for lnk in log.cross_domain_links:
            both = "yes" if lnk.both_sides_present else "NO — fix needed"
            lines.append(f"| {lnk.caller} | {lnk.called} | {both} |")
    else:
        lines.append("(no cross-domain links found)")

    lines.append("")
    return "\n".join(lines)
