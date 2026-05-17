"""
lib/validate.py — Structural enforcement for generated SKILL.md files.

Architectural boundary: checks structure, not semantics. Does not understand
domains, infer responsibilities, or judge content quality.

Checks: required frontmatter fields, integer version >= 1, quoted ISO-8601
last_updated, non-empty list fields, required sections in order, no
PLACEHOLDER text, no 'none found' text, no ```java code fences.

Does NOT check: domain correctness, citation accuracy, semantic completeness.

Usage: python3 lib/validate.py path/to/SKILL.md
Exit 0 = pass. Exit 1 = failures printed to stdout.
"""

import re
import sys
from pathlib import Path

REQUIRED_FM_FIELDS = [
    "skill_id", "version", "last_updated",
    "feature_name", "primary_packages", "key_classes",
]

REQUIRED_SECTIONS = [
    "## Overview",
    "## Key Classes and Responsibilities",
    "## Data Flow",
    "## Configuration",
    "## Integration Points",
    "## Update Expectations",
]

ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
JAVA_FENCE_RE = re.compile(r'^```java', re.MULTILINE)
PLACEHOLDER_RE = re.compile(r'\bPLACEHOLDER\b', re.IGNORECASE)
NONE_FOUND_RE = re.compile(r'\bnone\s+found\b', re.IGNORECASE)


def _parse_frontmatter(text: str) -> tuple[dict, str, list[str]]:
    errors: list[str] = []
    if not text.startswith("---"):
        return {}, text, ["File does not start with '---'"]
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, ["Frontmatter closing '---' not found"]

    fm: dict = {}
    current_key: str | None = None
    current_list: list | None = None

    for line in text[3:end].strip().splitlines():
        if line.startswith("  - ") and current_list is not None:
            current_list.append(line[4:].strip())
        elif ": " in line or line.endswith(":"):
            if current_key and current_list is not None:
                fm[current_key] = current_list
            parts = line.split(":", 1)
            current_key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            if value:
                fm[current_key] = value
                current_list = None
            else:
                current_list = []
                fm[current_key] = current_list

    if current_key and current_list is not None:
        fm[current_key] = current_list

    return fm, text[end + 4:], errors


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

    if "version" in fm:
        try:
            if int(fm["version"]) < 1:
                errors.append(f"'version' must be >= 1, got: {fm['version']}")
        except (ValueError, TypeError):
            errors.append(f"'version' must be an integer, got: {fm['version']!r}")

    if "last_updated" in fm:
        raw = str(fm["last_updated"]).strip().strip('"').strip("'")
        if not ISO_DATE_RE.match(raw):
            errors.append(f"'last_updated' must be YYYY-MM-DD in quotes, got: {fm['last_updated']!r}")


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


def _check_body(body: str, errors: list[str]) -> None:
    if PLACEHOLDER_RE.search(body):
        errors.append("Contains 'PLACEHOLDER' text — replace with real content")
    if NONE_FOUND_RE.search(body):
        errors.append("Contains 'none found' — use explicit fallback text instead")
    if JAVA_FENCE_RE.search(body):
        errors.append("Contains ```java fences — use ClassName.methodName() inline notation")


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    fm, body, errors = _parse_frontmatter(text)
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
