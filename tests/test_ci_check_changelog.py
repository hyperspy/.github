"""Tests for scripts/ci-check-changelog.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "ci-check-changelog.py"

HYPERSPY_PYPROJECT = """
[tool.towncrier]
directory = "upcoming_changes/"
filename = "CHANGES.rst"
package = "hyperspy"
type = [
    { directory = "new", name = "New features", showcontent = true },
    { directory = "bugfix", name = "Bug Fixes", showcontent = true },
]
"""

EXSPY_PYPROJECT = """
[tool.towncrier]
directory = "upcoming_changes/"
filename = "CHANGES.rst"
package_dir = "exspy"
type = [
    { directory = "new", name = "New features", showcontent = true },
    { directory = "maintenance", name = "Maintenance", showcontent = true },
]
"""

BOTH_KEYS_PYPROJECT = """
[tool.towncrier]
directory = "upcoming_changes/"
package = "hyperspy"
package_dir = "src"
type = [
    { directory = "new", name = "New features", showcontent = true },
]
"""

EQUAL_KEYS_PYPROJECT = """
[tool.towncrier]
directory = "upcoming_changes/"
package = "pkg"
package_dir = "pkg"
type = [
    { directory = "new", name = "New features", showcontent = true },
]
"""

NO_TOWNCIER_PYPROJECT = """
[project]
name = "nope"
"""


try:
    import tomllib
except ImportError:
    tomllib = None

requires_tomllib = pytest.mark.skipif(
    tomllib is None, reason="pyproject-derivation tests need tomllib (Python >= 3.11)"
)


def git_init(path: Path) -> None:
    subprocess.run(
        ["git", "init", "-q", str(path)],
        cwd=path,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "base",
        ],
        check=False,
        capture_output=True,
    )


def commit(
    path: Path, msg: str, files: dict[str, str], delete: list[str] | None = None
) -> str:
    for name, content in files.items():
        target = path / name
        if content is None:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    for name in delete or []:
        (path / name).unlink(missing_ok=True)
    subprocess.run(
        ["git", "-C", str(path), "add", "-A"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            msg,
        ],
        check=False,
        capture_output=True,
    )
    proc = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def shas(path: Path) -> tuple[str, str]:
    proc = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD~1", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    base, head = proc.stdout.split()
    return base, head


def run_script(path: Path, *args: str, pyproject: str | None = None) -> int:
    cmd = [sys.executable, str(SCRIPT)]
    if pyproject is not None:
        cmd += ["--pyproject", str(path / pyproject)]
    cmd += list(args)
    proc = subprocess.run(cmd, cwd=path, capture_output=True, text=True, check=False)
    return proc.returncode


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    git_init(tmp_path)
    return tmp_path


@requires_tomllib
def test_hyperspy_style_package(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(
        repo,
        "add source",
        {"hyperspy/foo.py": "x = 1\n", "upcoming_changes/1.new.rst": "entry\n"},
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 0


@requires_tomllib
def test_hyperspy_style_missing_fragment(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(repo, "add source", {"hyperspy/foo.py": "x = 1\n"})
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


@requires_tomllib
def test_exspy_style_package_dir(repo: Path):
    (repo / "pyproject.toml").write_text(EXSPY_PYPROJECT)
    commit(
        repo,
        "add source",
        {"exspy/bar.py": "y = 2\n", "upcoming_changes/7.maintenance.rst": "entry\n"},
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 0


@requires_tomllib
def test_both_keys_nests_package_dir(repo: Path):
    (repo / "pyproject.toml").write_text(BOTH_KEYS_PYPROJECT)
    commit(repo, "add source", {"src/hyperspy/foo.py": "x = 1\n"})
    base, head = shas(repo)
    # src/hyperspy/foo.py is a source change; missing fragment -> 1
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


@requires_tomllib
def test_equal_keys_still_nest(repo: Path):
    (repo / "pyproject.toml").write_text(EQUAL_KEYS_PYPROJECT)
    commit(repo, "add source", {"pkg/pkg/foo.py": "x = 1\n"})
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


def test_explicit_source_dir_override(repo: Path):
    (repo / "pyproject.toml").write_text(NO_TOWNCIER_PYPROJECT)
    commit(
        repo,
        "add source",
        {"mypkg/foo.py": "x = 1\n", "upcoming_changes/2.new.rst": "e\n"},
    )
    base, head = shas(repo)
    assert (
        run_script(
            repo,
            "--pyproject",
            "pyproject.toml",
            "--source-dir",
            "mypkg",
            "--changelog-dir",
            "upcoming_changes",
            base,
            head,
        )
        == 0
    )


@requires_tomllib
def test_tests_directory_excluded(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(repo, "only tests", {"hyperspy/tests/test_x.py": "def t():\n    pass\n"})
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 0


@requires_tomllib
def test_docs_only_not_source(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(repo, "docs", {"doc/index.rst": "hi\n"})
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 0


@requires_tomllib
def test_readme_fragment_does_not_count(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(
        repo,
        "readme edit",
        {
            "hyperspy/foo.py": "x = 1\n",
            "upcoming_changes/README.rst": "guide\n",
        },
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


@requires_tomllib
def test_deleted_fragment_still_missing(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(
        repo,
        "base with fragment",
        {
            "upcoming_changes/3.new.rst": "gone soon\n",
        },
    )
    commit(
        repo,
        "delete fragment + source",
        {
            "hyperspy/foo.py": "x = 1\n",
            "upcoming_changes/3.new.rst": None,
        },
        delete=["upcoming_changes/3.new.rst"],
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


@requires_tomllib
def test_helper_extension_ignored(repo: Path):
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    commit(
        repo,
        "helper file",
        {
            "hyperspy/foo.py": "x = 1\n",
            "upcoming_changes/helper.txt": "not a fragment\n",
        },
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 1


@requires_tomllib
def test_diverged_base_excluded(repo: Path):
    # Base branch gains a source change AFTER the PR branch point; the PR
    # itself touches only docs -> merge-base diff must not count it.
    (repo / "pyproject.toml").write_text(HYPERSPY_PYPROJECT)
    pr_branch = "pr"
    subprocess.run(
        ["git", "-C", str(repo), "checkout", "-q", "-b", pr_branch],
        check=False,
        capture_output=True,
    )
    commit(repo, "pr docs", {"doc/index.rst": "hi\n"})
    subprocess.run(
        ["git", "-C", str(repo), "checkout", "-q", "master"],
        check=False,
        capture_output=True,
    )
    commit(repo, "base gains source", {"hyperspy/base_only.py": "z = 3\n"})
    subprocess.run(
        ["git", "-C", str(repo), "checkout", "-q", pr_branch],
        check=False,
        capture_output=True,
    )
    base, head = shas(repo)
    assert run_script(repo, "--pyproject", "pyproject.toml", base, head) == 0


@requires_tomllib
def test_missing_pyproject_without_source_dir(repo: Path, tmp_path):
    missing = tmp_path / "elsewhere"
    missing.mkdir()
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--pyproject",
            str(missing / "p.toml"),
            "HEAD~1",
            "HEAD",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2


def test_help_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "changelog" in proc.stdout.lower()


def test_wrong_argv_exits_two():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2


def test_unreachable_base_exits_two(repo: Path):
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "0000000000000000000000000000000000000000",
            "HEAD",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "fetch-depth: 0" in proc.stderr
