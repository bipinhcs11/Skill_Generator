"""
lib/validate.py — Structural enforcement for generated SKILL.md files.

Architectural boundary: checks structure, not semantics. Does not understand
features, infer responsibilities, or judge content quality.

Checks: required frontmatter fields, integer version >= 1, quoted ISO-8601
last_updated, confidence/review metadata, non-empty list fields, required
sections in order, no PLACEHOLDER text, no 'none found' text, no ```java code
fences.

Does NOT check: feature correctness, citation accuracy, semantic completeness.

Usage: python3 lib/validate.py path/to/SKILL.md
Exit 0 = pass. Exit 1 = failures printed to stdout.
"""

import re
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

try:
    from frontmatter import parse as parse_frontmatter
except ImportError:  # pragma: no cover - supports package-style imports
    from .frontmatter import parse as parse_frontmatter

REQUIRED_FM_FIELDS = [
    "skill_id", "version", "last_updated",
    "feature_name", "confidence", "review_required",
    "primary_packages", "key_classes",
]
OPTIONAL_LIST_FIELDS = ["depends_on", "depended_on_by"]

REQUIRED_SECTIONS = [
    "## Overview",
    "## Key Classes and Responsibilities",
    "## Data Flow",
    "## Configuration",
    "## Integration Points",
    "## Update Expectations",
]

ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
KEBAB_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
JAVA_FENCE_RE = re.compile(r'^```java', re.MULTILINE)
PLACEHOLDER_RE = re.compile(r'\bPLACEHOLDER\b', re.IGNORECASE)
NONE_FOUND_RE = re.compile(r'\bnone\s+found\b', re.IGNORECASE)
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
BOOL_VALUES = {"true", "false"}


def _raw(value: object) -> str:
    return str(value).strip().strip('"').strip("'")


def _check_frontmatter(fm: dict, errors: list[str]) -> None:
    for field in REQUIRED_FM_FIELDS:
        if field not in fm:
            errors.append(f"Missing required frontmatter field: '{field}'")
            continue
        v = fm[field]
        if isinstance(v, list):
            if not v:
                errors.append(f"Frontmatter '{field}' is an empty list")
        elif not str(v).strip():
            errors.append(f"Frontmatter '{field}' is empty")

    if "skill_id" in fm and not KEBAB_RE.match(_raw(fm["skill_id"])):
        errors.append(f"'skill_id' must be kebab-case, got: {fm['skill_id']!r}")

    if "version" in fm:
        try:
            if int(fm["version"]) < 1:
                errors.append(f"'version' must be >= 1, got: {fm['version']}")
        except (ValueError, TypeError):
            errors.append(f"'version' must be an integer, got: {fm['version']!r}")

    if "last_updated" in fm:
        if not ISO_DATE_RE.match(_raw(fm["last_updated"])):
            errors.append(f"'last_updated' must be YYYY-MM-DD in quotes, got: {fm['last_updated']!r}")

    confidence = _raw(fm.get("confidence", "")).upper()
    if "confidence" in fm and confidence not in CONFIDENCE_VALUES:
        errors.append("'confidence' must be HIGH, MEDIUM, or LOW")

    review_required = _raw(fm.get("review_required", "")).lower()
    if "review_required" in fm and review_required not in BOOL_VALUES:
        errors.append("'review_required' must be true or false")
    if confidence == "LOW" and review_required != "true":
        errors.append("LOW-confidence skills must set 'review_required: true'")

    for field in OPTIONAL_LIST_FIELDS:
        if field not in fm:
            continue
        value = fm[field]
        if not isinstance(value, list) or not value:
            errors.append(f"Optional frontmatter '{field}' must be a non-empty list when present")
            continue
        for item in value:
            if not KEBAB_RE.match(_raw(item)):
                errors.append(f"Dependency id in '{field}' must be kebab-case, got: {item!r}")


def _check_sections(body: str, errors: list[str]) -> None:
    positions = []
    for sec in REQUIRED_SECTIONS:
        idx = body.find(sec)
        if idx == -1:
            errors.append(f"Missing required section: '{sec}'")
        positions.append(idx)
    found = [(p, s) for p, s in zip(positions, REQUIRED_SECTIONS) if p != -1]
    for i in range(1, len(found)):
        if found[i][0] < found[i - 1][0]:
            errors.append(f"Section order violation: '{found[i][1]}' before '{found[i-1][1]}'")
    for _, sec in found:
        if not _section(body, sec).strip():
            errors.append(f"Required section '{sec}' is empty")


def _section(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return ""
    start = body.find("\n", start) + 1
    nxt = body.find("\n## ", start)
    return body[start:] if nxt == -1 else body[start:nxt]


def _check_body(body: str, errors: list[str]) -> None:
    if PLACEHOLDER_RE.search(body):
        errors.append("Contains 'PLACEHOLDER' text — replace with real content")
    if NONE_FOUND_RE.search(body):
        errors.append("Contains 'none found' — use explicit fallback text instead")
    if JAVA_FENCE_RE.search(body):
        errors.append("Contains ```java fences — use ClassName.methodName() inline notation")


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    result = parse_frontmatter(text)
    fm, body, errors = result.frontmatter, result.body, list(result.errors)
    if not errors:
        _check_frontmatter(fm, errors)
    _check_sections(body, errors)
    _check_body(body, errors)
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 lib/validate.py path/to/SKILL.md")
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 1
    errors = validate(path)
    if errors:
        print(f"FAIL: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
