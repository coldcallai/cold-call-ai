"""Health test #1 — No industry-specific business logic in universal/.

Greps universal/ source for vertical nouns appearing inside CONDITIONALS.
Industry strings as data (e.g., dict keys) are allowed; industry strings
inside `if`/`elif`/`match` statements are forbidden.
"""
from __future__ import annotations
import os
import re

FORBIDDEN = (
    "merchant", "clover", "square", "toast", "fiserv", "stripe",
    "roofing", "storm", "shingle",
    "dental", "insurance",
    "agency", "campaign performance",
    "saas",
)

UNIVERSAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "universal"))


def iter_py_files(root: str):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py") and not f.startswith("_"):
                yield os.path.join(dirpath, f)


def test_no_industry_in_conditionals():
    violations = []
    cond_re = re.compile(r"^\s*(if|elif|match)\b.*", re.IGNORECASE)
    for path in iter_py_files(UNIVERSAL_DIR):
        with open(path) as fh:
            for i, line in enumerate(fh, 1):
                if not cond_re.match(line):
                    continue
                lower = line.lower()
                for noun in FORBIDDEN:
                    if noun in lower:
                        violations.append(f"{path}:{i}: forbidden noun {noun!r} in conditional: {line.strip()!r}")
    assert not violations, "Industry nouns in universal/ conditionals:\n  " + "\n  ".join(violations)


if __name__ == "__main__":
    test_no_industry_in_conditionals()
    print("PASS: test_no_industry_in_conditionals")
