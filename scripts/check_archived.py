"""Reports mentions of archived repositories of the organization in the docs.

The script collects the links to repositories of `elixir-cloud-aai` on
GitHub (`github.com/elixir-cloud-aai/<repo>`, also SSH clone URLs
`git@github.com:elixir-cloud-aai/<repo>.git` and
`raw.githubusercontent.com/elixir-cloud-aai/<repo>`) from the docs, asks
the GitHub API which repositories of the organization are archived, and
reports each link to an archived repository that is not marked as
historical.

A link is marked as historical by the HTML comment `<!-- historical -->`,
either on the same line or alone on the line right above it (e.g. above a
reference definition, which can't take a comment on its line; in YAML, as
a comment `# <!-- historical -->`). A marker covers every link on its line,
or on the line below if it stands alone.

Usage:
    python scripts/check_archived.py [--api-url URL] [--output FILE]
        [PATH ...]

Without paths, the script checks the Markdown, YAML, JSON and shell files
of `README.md`, `mkdocs.yml`, `docs` and `includes`. JSON has no comments,
so links there can't be marked: remove or replace them. Set `GITHUB_TOKEN`
to raise GitHub's rate limit (any token works; the repositories are
public); it is sent to the default API URL only. The report, in Markdown, goes to standard output and, with
`--output`, to a file.

Exit status: 0 if no unmarked link points to an archived repository, 2 if
the report lists some, 1 if the check could not run (e.g. the GitHub API
can't be reached).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from check_services import CheckError, code, fetch_json, find_files

ORG = "elixir-cloud-aai"
API_URL = "https://api.github.com"
DEFAULT_PATHS = ["README.md", "mkdocs.yml", "docs", "includes"]
SUFFIXES = {".json", ".md", ".sh", ".yaml", ".yml"}
PER_PAGE = 100
MAX_PAGES = 50

REPO_LINK = re.compile(
    # The host starts at a boundary (not e.g. `notgithub.com`)
    r"(?<![\w.-])(?:www\.)?"
    rf"(?:github\.com[/:]|raw\.githubusercontent\.com/){re.escape(ORG)}/"
    # A dot ends the name only if no name character follows (end of sentence)
    r"(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?(?![A-Za-z0-9_-]|\.[A-Za-z0-9_-])",
    re.IGNORECASE,
)
MARKER = re.compile(r"<!--[ \t]*historical[ \t]*-->", re.IGNORECASE)
# A marker alone on its line, also as a YAML or shell comment
ONLY_MARKER = re.compile(rf"^[ \t]*(?:#[ \t]*)?{MARKER.pattern}[ \t]*$", re.IGNORECASE)


@dataclass(frozen=True)
class Mention:
    """A link to an archived repository.

    Attributes:
        repo: The name of the repository, as in the organization.
        location: Where the docs name it (`file:line`).
    """

    repo: str
    location: str


def archived_repos(api_url: str, token: str | None) -> set[str]:
    """Fetches the names of the archived repositories of the organization.

    Args:
        api_url: The base URL of the GitHub REST API.
        token: A GitHub token, or None for anonymous requests.

    Returns:
        The names, in lower case.

    Raises:
        CheckError: If the API can't be reached, answers with something
            that isn't a list of repositories, or has more than
            `MAX_PAGES` pages.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # Not sent again on redirects, which may lead to other hosts
    secret = {"Authorization": f"Bearer {token}"} if token else {}
    names = set()
    for page in range(1, MAX_PAGES + 1):
        url = f"{api_url}/orgs/{ORG}/repos?type=public&per_page={PER_PAGE}&page={page}"
        try:
            repos = fetch_json(url, headers, secret)
        except CheckError as exc:
            raise CheckError(f"GitHub API: {exc}") from exc
        if not isinstance(repos, list):
            raise CheckError("GitHub API: expected a list of repositories")
        for repo in repos:
            if (
                not isinstance(repo, dict)
                or not isinstance(repo.get("name"), str)
                or not isinstance(repo.get("archived"), bool)
            ):
                raise CheckError("GitHub API: malformed repository")
            if repo.get("archived") is True:
                names.add(repo["name"].lower())
        if len(repos) < PER_PAGE:
            return names
    raise CheckError(f"GitHub API: more than {MAX_PAGES} pages of repositories")


def find_mentions(files: Iterable[Path], archived: set[str]) -> list[Mention]:
    """Finds the unmarked links to archived repositories.

    Args:
        files: The files to read.
        archived: The names of the archived repositories, in lower case.

    Returns:
        The links, in order of file and line.
    """
    mentions = []
    for path in files:
        previous = ""
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not MARKER.search(line) and not ONLY_MARKER.match(previous):
                for match in REPO_LINK.finditer(line):
                    if match["repo"].lower() in archived:
                        mentions.append(Mention(match["repo"], f"{path}:{number}"))
            previous = line
    return mentions


def report(mentions: list[Mention], archived: set[str]) -> str:
    """Renders the result as Markdown.

    Args:
        mentions: The unmarked links to archived repositories.
        archived: The names of the archived repositories.

    Returns:
        The report.
    """
    summary = f"The organization has {len(archived)} archived repositories."
    if not mentions:
        return f"{summary} No page links to them without a `historical` marker.\n"
    lines = [
        (
            f"{summary} Unmarked links to them: {len(mentions)}. Remove "
            "each link, point it to the successor, or mark it with "
            "`<!-- historical -->`:"
        ),
        "",
    ]
    lines += [f"- {code(m.location)}: `{ORG}/{m.repo}`" for m in mentions]
    return "\n".join(lines) + "\n"


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parses the command line.

    Args:
        args: The arguments, without the program name.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Report links to archived repositories in the docs."
    )
    parser.add_argument("paths", nargs="*", help="files and directories")
    parser.add_argument("--api-url", default=API_URL, help="GitHub REST API")
    parser.add_argument("--output", type=Path, help="also write the report here")
    return parser.parse_args(args)


def main(args: list[str]) -> int:
    """Runs the check.

    Args:
        args: The command line arguments, without the program name.

    Returns:
        The exit status: 0 without unmarked links, 2 with some, 1 if the
        check could not run.
    """
    options = parse_args(args)
    try:
        files = find_files(options.paths or DEFAULT_PATHS, SUFFIXES)
        api_url = options.api_url.rstrip("/")
        # The token goes to GitHub's own API only, never to another --api-url
        token = os.environ.get("GITHUB_TOKEN") if api_url == API_URL else None
        archived = archived_repos(api_url, token)
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    mentions = find_mentions(files, archived)
    text = report(mentions, archived)
    print(text, end="")
    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(text, encoding="utf-8")
    return 2 if mentions else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
