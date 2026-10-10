"""Shared AI-attribution patterns for the HyperSpy organization tooling.

HyperSpy uses ``Assisted-by:`` trailers for AI attribution.  ``Co-authored-by:``
is reserved for human co-authors.  This module is the single source of truth for
the patterns used by the commit-msg hook (``check-ai-co-author.py``) and the CI
trailer scan (``ci-check-ai-trailers.py``).
"""

from __future__ import annotations

import re

# Patterns that match AI tools in a Co-authored-by trailer line.
# Case-insensitive; word-boundary anchored where applicable.
AI_PATTERNS: list[str] = [
    r"claude",
    r"copilot",
    r"cursor",
    r"\bcodex\b",
    r"gemini",
    r"\baider\b",
    r"\bcline\b",
    r"windsurf",
    r"\bopencode\b",
    r"anthropic",
    r"openai",
    r"\bgpt\b",
    r"\bqwen\b",
    r"deepseek",
    r"mistral",
    r"\bamp\b",  # Sourcegraph Amp
    r"amazon q",
    r"noreply@anthropic\.com",
    r"copilot@github\.com",
    r"cursoragent@cursor\.com",
    r"codex@openai\.com",
    r"kilo ?code",
]

CO_AUTHORED_RE = re.compile(r"^Co-authored-by:", re.IGNORECASE)
ASSISTED_BY_RE = re.compile(r"^Assisted-by:\s*\S+:\S+", re.IGNORECASE)


def is_ai_co_author_line(line: str) -> bool:
    """Return True if ``line`` is a ``Co-authored-by:`` trailer naming an AI tool."""
    line = line.rstrip("\r")
    if not CO_AUTHORED_RE.match(line):
        return False
    for pattern in AI_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def find_ai_co_author_lines(text: str) -> list[str]:
    """Return the stripped offending ``Co-authored-by:`` lines found in ``text``."""
    return [line.strip() for line in text.splitlines() if is_ai_co_author_line(line)]
