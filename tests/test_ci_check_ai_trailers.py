"""Tests for scripts/ci-check-ai-trailers.py (self-contained git fixture)."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci-check-ai-trailers.py"

CLEAN_MSG = "feat: clean change\n\nAssisted-by: OpenCode:deepseek-4.0-pro\n"
VIOLATING_LINE = "Co-authored-by: Claude <noreply@anthropic.com>"
VIOLATING_MSG = f"fix: violating change\n\n{VIOLATING_LINE}\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Callable[[str, dict[str, str]], str]:
    """Initialise a git repo in ``tmp_path`` and return a ``commit(msg, files)`` helper."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.org")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "commit.gpgsign", "false")

    def commit(msg: str, files: dict[str, str]) -> str:
        for name, content in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            _git(tmp_path, "add", name)
        subprocess.run(
            ["git", "commit", "-q", "--no-verify", "-F", "-"],
            cwd=tmp_path,
            input=msg,
            capture_output=True,
            text=True,
            check=True,
        )
        return _git(tmp_path, "rev-parse", "HEAD")

    commit.repo = tmp_path  # type: ignore[attr-defined]
    return commit


@pytest.fixture
def history(git_repo) -> dict[str, object]:
    """Commits [clean, violating, clean]; returns shas and the repo path."""
    c1 = git_repo(CLEAN_MSG, {"a.txt": "1\n"})
    c2 = git_repo(VIOLATING_MSG, {"b.txt": "2\n"})
    c3 = git_repo(CLEAN_MSG, {"c.txt": "3\n"})
    return {"repo": git_repo.repo, "shas": [c1, c2, c3]}


def run_script(repo: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_script_is_executable():
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & 0o111, "script must be chmod 755"


def test_range_spanning_violator_exits_1_and_lists_line(history):
    c1, _, c3 = history["shas"]
    result = run_script(history["repo"], [c1, c3])
    assert result.returncode == 1
    assert VIOLATING_LINE in result.stderr.splitlines()[1].strip()
    assert "Assisted-by: <tool>:<model>" in result.stderr
    assert "https://github.com/hyperspy/.github/blob/main/AI-POLICY.md" in result.stderr
    assert "doc/dev_guide/coding_with_ai.rst" not in result.stderr


def test_range_excluding_violator_exits_0(history):
    _, c2, c3 = history["shas"]
    result = run_script(history["repo"], [c2, c3])
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


def test_empty_range_exits_0(history):
    _, _, c3 = history["shas"]
    result = run_script(history["repo"], [c3, c3])
    assert result.returncode == 0, result.stderr


def test_wrong_argv_length_exits_2(history):
    c1, _, _ = history["shas"]
    assert run_script(history["repo"], []).returncode == 2
    assert run_script(history["repo"], [c1]).returncode == 2
    assert run_script(history["repo"], [c1, c1, c1]).returncode == 2


def test_unreachable_base_exits_2(history):
    _, _, c3 = history["shas"]
    bogus = "0123456789abcdef0123456789abcdef01234567"
    result = run_script(history["repo"], [bogus, c3])
    assert result.returncode == 2
    assert "BASE commit not reachable - checkout with fetch-depth: 0" in result.stderr


def test_help_exits_0(history):
    result = run_script(history["repo"], ["--help"])
    assert result.returncode == 0
    assert "BASE_REF" in result.stdout and "HEAD_REF" in result.stdout


def test_human_co_author_is_not_flagged(git_repo):
    c1 = git_repo(CLEAN_MSG, {"a.txt": "1\n"})
    c2 = git_repo(
        "fix: pair work\n\nCo-authored-by: Jane Doe <jane@example.org>\n",
        {"b.txt": "2\n"},
    )
    result = run_script(git_repo.repo, [c1, c2])
    assert result.returncode == 0, result.stderr
