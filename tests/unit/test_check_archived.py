"""Tests of the archived-repository check in `scripts/check_archived.py`.

The GitHub API is a local HTTP server, so the tests need no network access.
"""

from __future__ import annotations

import http.server
import json
import runpy
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

import check_archived
import pytest
from check_archived import Mention
from check_services import CheckError

ROOT = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "scripts" / "check_archived.py"
REPOS = "/orgs/elixir-cloud-aai/repos?type=public&per_page=100&page="


class Api(http.server.BaseHTTPRequestHandler):
    """Answers with the response set for each path in `routes`.

    A route maps a path to a status and a JSON-encodable body. Unknown paths
    get a 404. `headers` records the request headers of the last request.
    """

    routes: ClassVar[dict[str, tuple[int, Any]]] = {}
    headers_seen: ClassVar[list[dict[str, str]]] = []

    def do_GET(self) -> None:
        """Answers a GET request from `routes`."""
        self.headers_seen.append(dict(self.headers))
        status, body = self.routes.get(self.path, (404, {}))
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        """Keeps the test output quiet.

        Args:
            format: The format of the message.
            *args: The arguments of the message.
        """


@pytest.fixture
def api() -> Iterator[str]:
    """Runs the local API.

    Yields:
        Its base URL.
    """
    Api.routes = {}
    Api.headers_seen = []
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Api)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(autouse=True)
def no_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skips the delay between retries.

    Args:
        monkeypatch: The pytest fixture.
    """
    monkeypatch.setattr("check_services.RETRY_DELAY", 0)


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


def repos(*names: str, archived: bool = False) -> list[dict[str, Any]]:
    """Builds a page of repositories as the GitHub API returns it.

    Args:
        *names: Names of the repositories.
        archived: Whether they are archived.

    Returns:
        The page.
    """
    return [{"name": name, "archived": archived} for name in names]


def test_archived_repos(api: str) -> None:
    """Collects archived repositories over pages, in lower case."""
    first = repos("Old", archived=True) + repos(*(f"r{i}" for i in range(99)))
    Api.routes = {
        f"{REPOS}1": (200, first),
        f"{REPOS}2": (200, repos("gone", archived=True) + repos("new")),
    }
    assert check_archived.archived_repos(api, None) == {"old", "gone"}
    assert all("Authorization" not in headers for headers in Api.headers_seen)


def test_archived_repos_sends_token(api: str) -> None:
    """Sends the token if there is one."""
    Api.routes = {f"{REPOS}1": (200, [])}
    assert check_archived.archived_repos(api, "t0k") == set()
    assert Api.headers_seen[0]["Authorization"] == "Bearer t0k"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"message": "x"}, "expected a list"),
        (["x"], "malformed repository"),
        ([{"archived": True}], "malformed repository"),
    ],
)
def test_archived_repos_malformed(api: str, body: Any, message: str) -> None:
    """Fails for answers that aren't lists of repositories."""
    Api.routes = {f"{REPOS}1": (200, body)}
    with pytest.raises(CheckError, match=message):
        check_archived.archived_repos(api, None)


def test_archived_repos_unreachable(api: str) -> None:
    """Names the API if it can't be reached."""
    with pytest.raises(CheckError, match="GitHub API: HTTP 404"):
        check_archived.archived_repos(api, None)


def test_archived_repos_too_many_pages(
    api: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stops after `MAX_PAGES` full pages."""
    monkeypatch.setattr(check_archived, "MAX_PAGES", 1)
    monkeypatch.setattr(check_archived, "PER_PAGE", 1)
    path = REPOS.replace("per_page=100", "per_page=1")
    Api.routes = {f"{path}1": (200, repos("a"))}
    with pytest.raises(CheckError, match="more than 1 pages"):
        check_archived.archived_repos(api, None)


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("See https://github.com/elixir-cloud-aai/old.", ["old"]),
        ("[x](https://github.com/elixir-cloud-aai/Old/pull/3)", ["Old"]),
        ("git clone https://github.com/elixir-cloud-aai/old.git", ["old"]),
        ("git clone git@github.com:elixir-cloud-aai/old.git", ["old"]),
        ("https://raw.githubusercontent.com/elixir-cloud-aai/old/main/x", ["old"]),
        ("https://github.com/elixir-cloud-aai/old-but-new", []),
        ("https://github.com/elixir-cloud-aai/older", []),
        ("https://github.com/elixir-cloud-aai/new", []),
        ("https://github.com/other/old", []),
        ("https://github.com/elixir-cloud-aai/old.github.io", []),
        ("https://github.com/elixir-cloud-aai/old.github.io.", []),
        ("Clone https://github.com/elixir-cloud-aai/old.git.", ["old"]),
        ("https://github.com/orgs/elixir-cloud-aai/discussions", []),
        ("[old](https://github.com/elixir-cloud-aai/old) <!-- historical -->", []),
        ("<!--historical-->\n[old]: <https://github.com/elixir-cloud-aai/old>", []),
        ("  # <!-- historical -->\n  url: https://github.com/elixir-cloud-aai/old", []),
        (
            "<!-- historical -->\ntext\nhttps://github.com/elixir-cloud-aai/old",
            ["old"],
        ),
        (
            "x <!-- historical -->\nhttps://github.com/elixir-cloud-aai/old",
            ["old"],
        ),
    ],
)
def test_find_mentions(tmp_path: Path, text: str, found: list[str]) -> None:
    """Finds unmarked links to archived repositories."""
    page = write(tmp_path / "page.md", text)
    mentions = check_archived.find_mentions([page], {"old"})
    assert [m.repo for m in mentions] == found


def test_find_mentions_locations(tmp_path: Path) -> None:
    """Reports file and line of each link."""
    a = write(tmp_path / "a.md", "x\nhttps://github.com/elixir-cloud-aai/old\n")
    b = write(
        tmp_path / "b.md",
        "github.com/elixir-cloud-aai/old and github.com/elixir-cloud-aai/gone\n",
    )
    assert check_archived.find_mentions([a, b], {"old", "gone"}) == [
        Mention("old", f"{a}:2"),
        Mention("old", f"{b}:1"),
        Mention("gone", f"{b}:1"),
    ]


def test_report_without_mentions() -> None:
    """Says that all is fine."""
    assert check_archived.report([], {"a", "b"}) == (
        "The organization has 2 archived repositories. No page links to them "
        "without a `historical` marker.\n"
    )


def test_report_with_mentions() -> None:
    """Lists each link with its location."""
    text = check_archived.report([Mention("old", "a.md:2")], {"old"})
    assert "Unmarked links to them: 1." in text
    assert text.endswith("\n\n- `a.md:2`: `elixir-cloud-aai/old`\n")


@pytest.fixture
def site(tmp_path: Path, api: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a small repository and an API with one archived repository.

    Args:
        tmp_path: The pytest fixture.
        api: The base URL of the local API.
        monkeypatch: The pytest fixture.

    Returns:
        The repository, which is also the working directory.
    """
    write(tmp_path / "README.md", "https://github.com/elixir-cloud-aai/new\n")
    write(tmp_path / "mkdocs.yml", "site_name: x\n")
    write(tmp_path / "docs" / "index.md", "")
    write(tmp_path / "includes" / "x.md", "")
    Api.routes = {f"{REPOS}1": (200, repos("old", archived=True) + repos("new"))}
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return tmp_path


def test_main_without_mentions(
    site: Path, api: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exits with 0 and says so."""
    assert check_archived.main(["--api-url", f"{api}/"]) == 0
    assert "No page links to them" in capsys.readouterr().out


def test_main_with_mentions(
    site: Path, api: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exits with 2 and writes the report."""
    write(site / "docs" / "old.md", "https://github.com/elixir-cloud-aai/old\n")
    output = site / "out" / "archived.md"
    assert check_archived.main(["--api-url", api, "--output", str(output)]) == 2
    out = capsys.readouterr().out
    assert "`docs/old.md:1`" in out
    assert output.read_text(encoding="utf-8") == out


def test_main_missing_path(
    site: Path, api: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exits with 1 for a path that does not exist."""
    assert check_archived.main(["--api-url", api, "missing.md"]) == 1
    assert "no such file" in capsys.readouterr().err


def test_main_api_down(
    site: Path, api: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exits with 1 if the GitHub API fails."""
    Api.routes = {}
    assert check_archived.main(["--api-url", api]) == 1
    assert "error: GitHub API: HTTP 404" in capsys.readouterr().err


def test_script(site: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Runs as a script and exits with the status of `main`."""
    monkeypatch.setattr(sys, "argv", ["check_archived.py", "missing.md"])
    with pytest.raises(SystemExit) as info:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert info.value.code == 1
