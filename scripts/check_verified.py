"""Reports docs pages whose operational facts are due for verification.

Pages with operational facts carry `last_verified` in their front matter:
the date when someone last verified those facts (`YYYY-MM-DD`), or `null`
until someone has (see "Last verified dates" in `README.md`). The script
lists the pages whose date is older than 6 months, or another number of
months, and the pages that are still `null`. Pages without the key are
left out.

The front matter is read without a YAML parser, so that the check needs
the standard library only: the key must be at the top level of the front
matter, unquoted and set once, and its value a date, `null`, `~` or
empty, on the same line and optionally followed by a comment. The build
(`hooks/last_verified.py`) rejects other values; this script rejects
them too, and the other forms of the key.

Usage:
    python scripts/check_verified.py [--months N] [--today YYYY-MM-DD]
        [--output FILE] [PATH ...]

Without paths, the script checks the Markdown files in `docs`. The report,
in Markdown, goes to standard output and, with `--output`, to a file.

Exit status: 0 if no page is due, 2 if the report lists some, 1 if the
check could not run (e.g. a path doesn't exist or a value is malformed).
"""

from __future__ import annotations

import argparse
import calendar
import datetime
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from check_services import CheckError, code, find_files

DEFAULT_PATHS = ["docs"]
SUFFIXES = {".md"}
MONTHS = 6
README = (
    "https://github.com/elixir-cloud-aai/docs/blob/main/README.md#last-verified-dates"
)

# As MkDocs reads front matter (`mkdocs.utils.meta.YAML_RE`)
FRONT_MATTER = re.compile(r"^-{3}[ \t]*\n(.*?\n)(?:\.{3}|-{3})[ \t]*\n", re.DOTALL)
# The key at the top level, its value up to a comment
KEY = re.compile(
    r"^last_verified[ \t]*:(?P<value>[^\n#]*?)[ \t]*(?:#[^\n]*)?$", re.MULTILINE
)
# Forms of the key that YAML reads but this script doesn't: a quoted key, and
# a value on the next, indented line
OTHER_KEY = re.compile(r"""^["']last_verified["'][ \t]*:""", re.MULTILINE)
NEXT_LINE = re.compile(r"\n[ \t]+\S")
NULLS = {"", "null", "Null", "NULL", "~"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class Page:
    """A page with a `last_verified` key.

    Attributes:
        path: The file of the page.
        verified: The date of the last verification, or None if the page
            hasn't been verified yet.
    """

    path: str
    verified: datetime.date | None


def months_before(day: datetime.date, months: int) -> datetime.date:
    """Goes back a number of calendar months.

    Args:
        day: The day to start from.
        months: The number of months.

    Returns:
        The same day of the month that many months earlier, or the last day
        of that month if it is shorter.
    """
    index = day.year * 12 + day.month - 1 - months
    year, month = divmod(index, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day.day, last))


def read_page(path: Path) -> Page | None:
    """Reads the `last_verified` date of a page.

    Args:
        path: The Markdown file.

    Returns:
        The page, or None if its front matter doesn't set `last_verified`.

    Raises:
        CheckError: If the value is neither a valid date nor null, or the
            key is set more than once or in a form that the script can't
            read.
    """
    # MkDocs drops a byte order mark too
    front_matter = FRONT_MATTER.match(path.read_text(encoding="utf-8-sig"))
    if not front_matter:
        return None
    text = front_matter.group(1)
    if OTHER_KEY.search(text):
        raise CheckError(f"{path}: write the key `last_verified` without quotes")
    keys = list(KEY.finditer(text))
    if not keys:
        return None
    if len(keys) > 1:
        raise CheckError(f"{path}: `last_verified` is set more than once")
    key = keys[0]
    value = key["value"].strip()
    if not value and NEXT_LINE.match(text, key.end()):
        raise CheckError(f"{path}: put the value of `last_verified` on its line")
    if value in NULLS:
        return Page(str(path), None)
    if not DATE.fullmatch(value):
        raise CheckError(
            f"{path}: `last_verified` must be a date (YYYY-MM-DD, unquoted) "
            f"or null, not {value!r}"
        )
    try:
        return Page(str(path), datetime.date.fromisoformat(value))
    except ValueError as exc:
        raise CheckError(f"{path}: `last_verified` is an invalid date: {exc}") from exc


def due(pages: Iterable[Page], cutoff: datetime.date) -> tuple[list[Page], list[Page]]:
    """Selects the pages due for verification.

    Args:
        pages: The pages with a `last_verified` key.
        cutoff: The earliest date that is recent enough.

    Returns:
        The pages verified before the cutoff, oldest first, and the pages
        not verified yet, by path.
    """
    stale = sorted(
        (p for p in pages if p.verified is not None and p.verified < cutoff),
        key=lambda p: (p.verified, p.path),
    )
    unverified = sorted((p for p in pages if p.verified is None), key=lambda p: p.path)
    return stale, unverified


def report(
    stale: list[Page], unverified: list[Page], checked: int, cutoff: datetime.date
) -> str:
    """Renders the result as Markdown.

    Args:
        stale: The pages verified before the cutoff.
        unverified: The pages not verified yet.
        checked: The number of pages with a `last_verified` key.
        cutoff: The earliest date that is recent enough.

    Returns:
        The report.
    """
    summary = f"{checked} pages have a `last_verified` date."
    if not stale and not unverified:
        return f"{summary} All of them were verified on or after {cutoff}.\n"
    lines = [
        (
            f"{summary} Due for verification: {len(stale) + len(unverified)}. "
            "Check the operational facts of each page against their sources, "
            f"fix them and set the date, as described in [Last verified "
            f"dates]({README})."
        ),
    ]
    if stale:
        lines += ["", f"Verified before {cutoff}:", ""]
        lines += [f"- {code(p.path)}: verified on {p.verified}" for p in stale]
    if unverified:
        lines += ["", "Not verified yet (`null`):", ""]
        lines += [f"- {code(p.path)}" for p in unverified]
    return "\n".join(lines) + "\n"


def non_negative(text: str) -> int:
    """Parses a number of months.

    Args:
        text: The command line argument.

    Returns:
        The number.

    Raises:
        argparse.ArgumentTypeError: If it isn't a non-negative integer.
    """
    try:
        number = int(text)
    except ValueError:
        number = -1
    if number < 0:
        raise argparse.ArgumentTypeError(f"not a number of months: {text!r}")
    return number


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parses the command line.

    Args:
        args: The arguments, without the program name.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Report docs pages due for verification."
    )
    parser.add_argument("paths", nargs="*", help="files and directories")
    parser.add_argument(
        "--months",
        type=non_negative,
        default=MONTHS,
        help=f"maximum age of a date in months (default: {MONTHS})",
    )
    parser.add_argument(
        "--today",
        type=datetime.date.fromisoformat,
        help="the current date (YYYY-MM-DD; default: today)",
    )
    parser.add_argument("--output", type=Path, help="also write the report here")
    return parser.parse_args(args)


def main(args: list[str]) -> int:
    """Runs the check.

    Args:
        args: The command line arguments, without the program name.

    Returns:
        The exit status: 0 if no page is due, 2 if some are, 1 if the check
        could not run.
    """
    options = parse_args(args)
    today = options.today or datetime.date.today()
    cutoff = months_before(today, options.months)
    try:
        files = find_files(options.paths or DEFAULT_PATHS, SUFFIXES)
        pages = [page for path in files if (page := read_page(path)) is not None]
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    stale, unverified = due(pages, cutoff)
    text = report(stale, unverified, len(pages), cutoff)
    print(text, end="")
    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(text, encoding="utf-8")
    return 2 if stale or unverified else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
