from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def git_repo(tmp_path: Path) -> Callable[[str, dict[str, str]], str]:
    """Initialise a git repository in ``tmp_path`` and return a commit helper.

    The helper writes ``files`` (relative path -> content), stages them and
    commits with ``msg``, returning the new commit sha.
    """

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "test@example.org")
    git("config", "user.name", "Test User")
    git("config", "commit.gpgsign", "false")

    def commit(msg: str, files: dict[str, str]) -> str:
        for rel, content in files.items():
            target = tmp_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            git("add", rel)
        git("commit", "-q", "--allow-empty", "-m", msg)
        return git("rev-parse", "HEAD")

    return commit
