#!/usr/bin/env python3
"""CI check: scan all commits in a pull request for AI ``Co-authored-by`` trailers.

This is the CI counterpart of ``scripts/check-ai-co-author.py`` (the commit-msg
hook).  The hook catches trailers at commit time; commits made with
``--no-verify`` are caught here.  The job fails if any commit in
``BASE..HEAD`` contains a ``Co-authored-by:`` trailer referencing a known AI
tool.

Usage (in CI)::

    ci-check-ai-trailers.py BASE_REF HEAD_REF

Exit codes:

* 0 - all commits clean
* 1 - violations found (offending lines and fix instructions on stderr)
* 2 - usage error, or BASE is not reachable (shallow checkout)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

POLICY_URL = "https://github.com/hyperspy/.github/blob/main/AI-POLICY.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from hyperspy_ai_patterns import (  # type: ignore[import-not-found]
        AI_PATTERNS,
        CO_AUTHORED_RE,
        is_ai_co_author_line,
    )
except ImportError:
    # ---- INLINE FALLBACK -------------------------------------------------
    # Mirror of scripts/hyperspy_ai_patterns.py; used only when the shared
    # module is unavailable (e.g. the script is copied on its own).  Keep the
    # semantics identical to the shared module.
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

    def is_ai_co_author_line(line: str) -> bool:
        """Return True if ``line`` is a Co-authored-by trailer naming an AI tool."""
        line = line.rstrip("\r")
        if not CO_AUTHORED_RE.match(line):
            return False
        return any(re.search(p, line, re.IGNORECASE) for p in AI_PATTERNS)

    # ---- END INLINE FALLBACK ---------------------------------------------


def base_is_reachable(base: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{base}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def get_commit_messages(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", f"{base}..{head}", "--format=%B"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def check_commits(base: str, head: str) -> int:
    if not base_is_reachable(base):
        print(
            f"ERROR: BASE commit not reachable - checkout with fetch-depth: 0 ({base})",
            file=sys.stderr,
        )
        return 2

    violations = [
        line.strip()
        for line in get_commit_messages(base, head)
        if is_ai_co_author_line(line)
    ]

    if violations:
        err = sys.stderr
        print(
            "ERROR: Prohibited Co-authored-by trailers found in this pull request:",
            file=err,
        )
        for v in violations:
            print(f"  {v}", file=err)
        print(file=err)
        print(
            "HyperSpy uses Assisted-by: for AI tool attribution, not Co-authored-by:.",
            file=err,
        )
        print(
            "Several AI tools add Co-authored-by: by default "
            "(Claude Code, VS Code Copilot, Cursor, OpenCode).",
            file=err,
        )
        print(file=err)
        print("Fix instructions:", file=err)
        print(file=err)
        print(
            "  1. Rebase your branch and amend every offending commit to replace",
            file=err,
        )
        print(
            "     Co-authored-by: <AI tool> with Assisted-by: <tool>:<model>.",
            file=err,
        )
        print(
            f"  2. Disable auto-injection in your tool's settings (see {POLICY_URL}).",
            file=err,
        )
        print("  3. Force-push the corrected branch.", file=err)
        return 1

    print("All commits clean - no prohibited AI Co-authored-by trailers.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if any commit in BASE..HEAD carries an AI Co-authored-by trailer.",
    )
    parser.add_argument(
        "base", metavar="BASE_REF", help="merge-base / target branch ref"
    )
    parser.add_argument("head", metavar="HEAD_REF", help="pull request head ref")
    # argparse exits 2 on wrong argument count and 0 on --help.
    args = parser.parse_args(argv)
    return check_commits(args.base, args.head)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
