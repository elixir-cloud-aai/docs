"""Checks the spelling of the project names in the prose of the repository.

The names are "ELIXIR On-Cloud", "ELIXIR" and "ELIXIR Europe". The script
reports every other spelling, e.g., "Elixir", "ELIXIR-On-Cloud",
"ELIXIR-on-Cloud", "ELIXIR on-Cloud", "ELIXIR on Cloud" and "ELIXIR Cloud".
Code, URLs, link targets, reference labels and identifiers such as
`elixir-cloud-aai` are not prose and are ignored.

Usage:
    python scripts/check_names.py [PATH ...]

Without arguments, the script checks `README.md`, `mkdocs.yml`, `docs` and
`includes`. It exits with status 1 if it finds a wrong spelling or a path does not exist.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_PATHS = ["README.md", "mkdocs.yml", "docs", "includes"]
SUFFIXES = {".md", ".yml", ".yaml"}

# Parts that are not prose, replaced by spaces to keep the column positions
IGNORED = re.compile(
    r"""
      ```.*?```                      # fenced code blocks
    | ~~~.*?~~~                      # fenced code blocks (tildes)
    | `[^`\n]*`                      # inline code
    | https?://[^\s<>"')\]]+         # URLs
    | \]\([^)\n]*\)                  # link targets
    | \]\[[^\]\n]*\]                 # reference link labels
    | ^[ \t]*\[[^\]\n]+\]:[^\n]*$   # reference definitions
    | \b(?:href|src|icon|image)=?\s*["':][^"'\n]*   # attributes and keys
    """,
    re.VERBOSE | re.DOTALL | re.MULTILINE,
)

# A name is a word that is not part of an identifier, path or domain. A name
# may be wrapped over two lines
SEP = r"(?:[ \t-]|\n[ \t>]*)*"
NAME = re.compile(
    rf"(?<![\w./@-])elixir(?:{SEP}(?:on)?{SEP}cloud|(?:[ \t]|\n[ \t>]*)+europe)?"
    r"(?![\w./@-])",
    re.IGNORECASE,
)

CORRECT = {"ELIXIR", "ELIXIR Europe", "ELIXIR On-Cloud"}


def blank(match: re.Match[str]) -> str:
    """Replaces a match by spaces and keeps its line breaks.

    Args:
        match: The match to replace.

    Returns:
        The replacement text.
    """
    return re.sub(r"[^\n]", " ", match.group(0))


def check_file(path: Path) -> list[str]:
    """Finds the wrong spellings of the names in a file.

    Args:
        path: The file to check.

    Returns:
        One message per wrong spelling.
    """
    text = path.read_text(encoding="utf-8")
    prose = IGNORED.sub(blank, text)
    problems = []
    for match in NAME.finditer(prose):
        name = re.sub(r"\s+", " ", match.group(0))
        if name in CORRECT:
            continue
        line = prose.count("\n", 0, match.start()) + 1
        problems.append(f"{path}:{line}: '{name}' is not a valid name")
    return problems


def main(args: list[str]) -> int:
    """Checks the given paths.

    Args:
        args: Files and directories to check; the defaults if empty.

    Returns:
        The exit status: 1 if there are wrong spellings, otherwise 0.
    """
    files: list[Path] = []
    for arg in args or DEFAULT_PATHS:
        path = Path(arg)
        if path.is_dir():
            files += sorted(p for p in path.rglob("*") if p.suffix in SUFFIXES)
        elif path.is_file():
            files.append(path)
        else:
            print(f"{arg}: no such file or directory")
            return 1
    problems = [p for file in files for p in check_file(file)]
    for problem in problems:
        print(problem)
    if problems:
        print(
            'Use "ELIXIR On-Cloud", "ELIXIR" or "ELIXIR Europe" exactly as '
            "written."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
