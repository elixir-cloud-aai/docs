"""Tests of the verification check in `scripts/check_verified.py`."""

from __future__ import annotations

import datetime
import runpy
import sys
from pathlib import Path

import check_verified
import pytest
from check_services import CheckError
from check_verified import Page

ROOT = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "scripts" / "check_verified.py"
TODAY = datetime.date(2026, 11, 17)


def write(path: Path, text: str) -> Path:
    """Writes a file with the given text, creating its directory.

    Args:
        path: The file.
        text: Its content.

    Returns:
        The path of the file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("day", "months", "expected"),
    [
        (TODAY, 6, datetime.date(2026, 5, 17)),
        (datetime.date(2026, 3, 10), 6, datetime.date(2025, 9, 10)),
        (datetime.date(2026, 8, 31), 6, datetime.date(2026, 2, 28)),
        (datetime.date(2028, 8, 31), 6, datetime.date(2028, 2, 29)),
        (datetime.date(2026, 12, 31), 6, datetime.date(2026, 6, 30)),
        (datetime.date(2026, 1, 15), 13, datetime.date(2024, 12, 15)),
        (TODAY, 0, TODAY),
    ],
)
def test_months_before(
    day: datetime.date, months: int, expected: datetime.date
) -> None:
    """Goes back whole months, to the last day of a shorter month."""
    assert check_verified.months_before(day, months) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("---\nlast_verified: 2026-05-01\n---\n# X\n", datetime.date(2026, 5, 1)),
        (
            "---\ntitle: X\nlast_verified: 2026-05-01  # checked\n---\n",
            datetime.date(2026, 5, 1),
        ),
        ("---\nlast_verified: null\n---\n", None),
        ("---\nlast_verified: Null\n---\n", None),
        ("---\nlast_verified: NULL\n---\n", None),
        ("---\nlast_verified: ~\n---\n", None),
        ("---\nlast_verified:\n---\n", None),
        ("---\nlast_verified:   # not yet\n---\n", None),
        ("---\nlast_verified : null\n...\n", None),
    ],
)
def test_read_page(tmp_path: Path, text: str, expected: datetime.date | None) -> None:
    """Reads dates and nulls from the front matter."""
    path = write(tmp_path / "page.md", text)
    assert check_verified.read_page(path) == Page(str(path), expected)


@pytest.mark.parametrize(
    "text",
    [
        "# No front matter\n\nlast_verified: null\n",
        "---\ntitle: X\n---\n\nlast_verified: null\n",
        "---\ntitle: X\n  last_verified: null\n---\n",
        "---\nlast_verified_by: someone\n---\n",
        "\n---\nlast_verified: null\n---\n",
        "---\nlast_verified: null\n",
    ],
)
def test_read_page_without_key(tmp_path: Path, text: str) -> None:
    """Ignores pages whose front matter doesn't set the key."""
    assert check_verified.read_page(write(tmp_path / "page.md", text)) is None


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ('"2026-05-01"', "must be a date"),
        ("2026-05-01T10:00:00", "must be a date"),
        ("yes", "must be a date"),
        ("2026-13-01", "invalid date"),
    ],
)
def test_read_page_malformed(tmp_path: Path, value: str, message: str) -> None:
    """Fails on values that the build would reject."""
    path = write(tmp_path / "page.md", f"---\nlast_verified: {value}\n---\n")
    with pytest.raises(CheckError, match=message) as info:
        check_verified.read_page(path)
    assert str(path) in str(info.value)


def test_due() -> None:
    """Splits the pages due for verification into stale and unverified."""
    cutoff = datetime.date(2026, 5, 17)
    pages = [
        Page("b.md", datetime.date(2026, 1, 1)),
        Page("fresh.md", datetime.date(2026, 11, 1)),
        Page("edge.md", cutoff),
        Page("z.md", None),
        Page("a.md", datetime.date(2026, 1, 1)),
        Page("old.md", datetime.date(2025, 1, 1)),
        Page("y.md", None),
    ]
    stale, unverified = check_verified.due(pages, cutoff)
    assert [p.path for p in stale] == ["old.md", "a.md", "b.md"]
    assert [p.path for p in unverified] == ["y.md", "z.md"]


def test_report_without_due() -> None:
    """Says that all is fine."""
    text = check_verified.report([], [], 3, datetime.date(2026, 5, 17))
    assert text == (
        "3 pages have a `last_verified` date. All of them were verified on "
        "or after 2026-05-17.\n"
    )


def test_report_with_due() -> None:
    """Lists the stale pages with their dates, then the unverified pages."""
    text = check_verified.report(
        [Page("docs/a`b.md", datetime.date(2025, 1, 2))],
        [Page("docs/c.md", None)],
        5,
        datetime.date(2026, 5, 17),
    )
    assert text.startswith(
        "5 pages have a `last_verified` date. Due for verification: 2"
    )
    assert "\n- `docs/a'b.md`: verified on 2025-01-02\n" in text
    assert "\n- `docs/c.md`\n" in text
    assert text.index("2025-01-02") < text.index("docs/c.md")
    assert "README.md#last-verified-dates" in text


def test_report_only_unverified() -> None:
    """Leaves out the section of stale pages if there are none."""
    text = check_verified.report([], [Page("c.md", None)], 1, TODAY)
    assert "before" not in text
    assert "Not verified yet" in text


def test_report_only_stale() -> None:
    """Leaves out the section of unverified pages if there are none."""
    text = check_verified.report([Page("c.md", TODAY)], [], 1, TODAY)
    assert "Verified before" in text
    assert "Not verified yet" not in text


@pytest.fixture
def site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Builds a repository with one fresh page, as the working directory.

    Args:
        tmp_path: The pytest fixture.
        monkeypatch: The pytest fixture.

    Returns:
        The repository.
    """
    write(tmp_path / "docs" / "fresh.md", "---\nlast_verified: 2026-11-01\n---\n")
    write(tmp_path / "docs" / "plain.md", "# No key\n")
    write(tmp_path / "docs" / "notes.txt", "---\nlast_verified: null\n---\n")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_main_without_due(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exits with 0 and says so."""
    assert check_verified.main(["--today", "2026-11-17"]) == 0
    assert "1 pages have" in capsys.readouterr().out


def test_main_with_due(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exits with 2 and writes the report."""
    write(site / "docs" / "sub" / "new.md", "---\nlast_verified: null\n---\n")
    output = site / "out" / "verified.md"
    assert check_verified.main(["--today", "2026-11-17", "--output", str(output)]) == 2
    out = capsys.readouterr().out
    assert "`docs/sub/new.md`" in out
    assert output.read_text(encoding="utf-8") == out


def test_main_months(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Takes the maximum age in months."""
    assert check_verified.main(["--today", "2027-05-01", "--months", "6"]) == 0
    assert check_verified.main(["--today", "2027-05-02", "--months", "6"]) == 2
    assert "Verified before 2026-11-02" in capsys.readouterr().out


def test_main_today_default(
    site: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Uses the current date without `--today`."""

    class Date(datetime.date):
        """A date whose today is fixed."""

        @classmethod
        def today(cls) -> Date:
            """Returns a fixed day.

            Returns:
                The day.
            """
            return cls(2030, 1, 1)

    monkeypatch.setattr(datetime, "date", Date)
    assert check_verified.main([]) == 2
    assert "Verified before 2029-07-01" in capsys.readouterr().out


def test_main_paths(site: Path) -> None:
    """Checks only the paths given."""
    write(site / "other" / "old.md", "---\nlast_verified: 2020-01-01\n---\n")
    assert check_verified.main(["--today", "2026-11-17", "docs"]) == 0
    assert check_verified.main(["--today", "2026-11-17", "other"]) == 2


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--today", "2026-11-17", "missing.md"], "no such file"),
        (["--today", "2026-11-17", "bad.md"], "must be a date"),
    ],
)
def test_main_errors(
    site: Path, args: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exits with 1 if the check can't run."""
    write(site / "bad.md", "---\nlast_verified: soon\n---\n")
    assert check_verified.main(args) == 1
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    "args", [["--today", "17.11.2026"], ["--months", "-1"], ["--months", "x"]]
)
def test_main_bad_options(site: Path, args: list[str]) -> None:
    """Rejects malformed options like any other usage error."""
    with pytest.raises(SystemExit) as info:
        check_verified.main(args)
    assert info.value.code == 2


def test_script(site: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Runs as a script and exits with the status of `main`."""
    monkeypatch.setattr(sys, "argv", ["check_verified.py", "missing.md"])
    with pytest.raises(SystemExit) as info:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert info.value.code == 1
