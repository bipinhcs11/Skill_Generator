"""
lib/citation_check.py — Citation presence check for SKILL.md files.

Architectural boundary: verifies that citation-required sections contain at
least one class-qualified citation such as ClassName.methodName() or
com.example.ClassName. Does NOT verify that the cited class exists in the target
codebase — that is a semantic check for the skill-validator agent.

Citation-required sections: "## Key Classes and Responsibilities", "## Data Flow"
Optional sections: Overview, Configuration, Integration Points, Update Expectations

Usage: python3 lib/citation_check.py path/to/SKILL.md
Exit 0 = pass. Exit 1 = failures printed to stdout.
"""

import re
import sys
from pathlib import Path

METHOD_CITATION_RE = re.compile(r'\b[A-Z][A-Za-z0-9_]*\.[a-z][A-Za-z0-9_]*\(\)')
FQCN_CITATION_RE = re.compile(r'\b[a-z][A-Za-z0-9_]*(?:\.[a-z][A-Za-z0-9_]*)+\.[A-Z][A-Za-z0-9_]*\b')

CITATION_REQUIRED = [
    "## Key Classes and Responsibilities",
    "## Data Flow",
]


def _body(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text[end + 4:] if end != -1 else text


def _section(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return ""
    start = body.find("\n", start) + 1
    nxt = body.find("\n## ", start)
    return body[start:] if nxt == -1 else body[start:nxt]


def _has_citation(text: str) -> bool:
    return bool(METHOD_CITATION_RE.search(text) or FQCN_CITATION_RE.search(text))


def check_citations(path: Path) -> list[str]:
    body = _body(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for heading in CITATION_REQUIRED:
        text = _section(body, heading)
        if text.strip() and not _has_citation(text):
            errors.append(
                f"Section '{heading}' has no class-qualified citations. "
                "Use ClassName.methodName() or a fully qualified class name."
            )
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 lib/citation_check.py path/to/SKILL.md")
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 1
    errors = check_citations(path)
    if errors:
        print(f"FAIL: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
