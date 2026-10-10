from __future__ import annotations

import sys

import pytest
from conftest import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

import hyperspy_ai_patterns as pat


@pytest.mark.parametrize(
    "line",
    [
        "Co-authored-by: Claude <noreply@anthropic.com>",
        "Co-authored-by: GitHub Copilot <copilot@github.com>",
        "Co-authored-by: Cursor Agent <cursoragent@cursor.com>",
        "co-authored-by: codex <x@y>",
        "Co-authored-by: Amazon Q <q@amazon.com>",
        "Co-authored-by: Claude <noreply@anthropic.com>\r",
    ],
)
def test_ai_co_author_lines_are_detected(line: str) -> None:
    assert pat.is_ai_co_author_line(line)


@pytest.mark.parametrize(
    "line",
    [
        "Co-authored-by: Jane Doe <jane@example.org>",
        "Assisted-by: Claude:claude-opus",
        "This change was drafted with help from claude.",
    ],
)
def test_non_ai_lines_are_not_flagged(line: str) -> None:
    assert not pat.is_ai_co_author_line(line)


def test_find_ai_co_author_lines_returns_stripped_offenders() -> None:
    text = (
        "fix: thing\n"
        "\n"
        "Body mentioning claude without a trailer.\n"
        "Co-authored-by: Jane Doe <jane@example.org>\n"
        "Co-authored-by: Claude <noreply@anthropic.com>\r\n"
        "Assisted-by: Claude:claude-opus\n"
    )
    assert pat.find_ai_co_author_lines(text) == [
        "Co-authored-by: Claude <noreply@anthropic.com>"
    ]


def test_assisted_by_re_requires_tool_and_model() -> None:
    assert pat.ASSISTED_BY_RE.match("Assisted-by: Claude:claude-opus")
    assert pat.ASSISTED_BY_RE.match("assisted-by: OpenCode:deepseek-4.0-pro")
    assert not pat.ASSISTED_BY_RE.match("Assisted-by: Claude")


def test_upstream_patterns_are_preserved() -> None:
    upstream = [
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
        r"\bamp\b",
    ]
    assert pat.AI_PATTERNS[: len(upstream)] == upstream
