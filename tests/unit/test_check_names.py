"""Tests of the name check in `scripts/check_names.py`."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

import check_names


def write(tmp_path: Path, text: str, name: str = "page.md") -> Path:
    """Writes a file with the given text.

    Args:
        tmp_path: Directory to write to.
        text: Content of the file.
        name: Name of the file.

    Returns:
        The path of the file.
    """
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "text",
    [
        "ELIXIR On-Cloud is a federation.",
        "Run by ELIXIR Europe and ELIXIR.",
        "See `Elixir cloud` in code.",
        "```\nElixir on cloud\n```",
        "Visit https://elixir-cloud-aai.github.io/ now.",
        "A [link](https://example.org/Elixir-On-Cloud) here.",
        "[ELIXIR][elixir-cloud-aai]",
        "[elixir-cloud]: <https://example.org/Elixir Cloud>",
        '<img src="Elixir-On-Cloud.svg">',
        "The elixir-cloud-aai organisation.",
        "",
    ],
)
def test_check_file_accepts(tmp_path: Path, text: str) -> None:
    """Accepts correct names and text that is not prose."""
    assert check_names.check_file(write(tmp_path, text)) == []


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("Elixir is wrong.", "Elixir"),
        ("The ELIXIR-On-Cloud site.", "ELIXIR-On-Cloud"),
        ("The ELIXIR on Cloud site.", "ELIXIR on Cloud"),
        ("The ELIXIR Cloud site.", "ELIXIR Cloud"),
        ("The elixir europe site.", "elixir europe"),
        ("ELIXIR\nCloud", "ELIXIR Cloud"),
    ],
)
def test_check_file_rejects(tmp_path: Path, text: str, name: str) -> None:
    """Reports wrong spellings, also wrapped over lines."""
    problems = check_names.check_file(write(tmp_path, text))
    assert len(problems) == 1
    assert f"'{name}' is not a valid name" in problems[0]


def test_check_file_reports_line_number(tmp_path: Path) -> None:
    """Reports the line of the wrong spelling."""
    path = write(tmp_path, "fine\n\nElixir here\n")
    assert check_names.check_file(path) == [
        f"{path}:3: 'Elixir' is not a valid name"
    ]


def test_blank_keeps_line_breaks() -> None:
    """Replaces everything but line breaks by spaces."""
    match = check_names.IGNORED.search("```a\nb```")
    assert match is not None
    assert check_names.blank(match) == "    \n    "


def test_main_ok(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Returns 0 for files and directories without problems."""
    write(tmp_path, "ELIXIR On-Cloud\n")
    write(tmp_path, "Elixir\n", name="ignored.txt")
    assert check_names.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_main_reports_problems(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Returns 1 and prints the problems and the hint."""
    path = write(tmp_path, "Elixir\n")
    assert check_names.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert f"{path}:1: 'Elixir' is not a valid name" in out
    assert "exactly as written" in out


def test_main_missing_path(capsys: pytest.CaptureFixture[str]) -> None:
    """Returns 1 for a path that does not exist."""
    assert check_names.main(["does/not/exist"]) == 1
    assert "does/not/exist: no such file or directory" in capsys.readouterr().out


def test_main_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Checks the default paths without arguments."""
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "ELIXIR\n", name="README.md")
    write(tmp_path, "site_name: ELIXIR\n", name="mkdocs.yml")
    (tmp_path / "docs").mkdir()
    (tmp_path / "includes").mkdir()
    assert check_names.main([]) == 0


def test_script_entry_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exits with the status of `main` when run as a script."""
    path = write(tmp_path, "Elixir\n")
    monkeypatch.setattr(sys, "argv", ["check_names.py", str(path)])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(check_names.__file__, run_name="__main__")
    assert exit_info.value.code == 1
