"""Tests of the service check in `scripts/check_services.py`.

The registry and the services are a local HTTP server, so the tests need no
network access.
"""

from __future__ import annotations

import http.client
import http.server
import json
import runpy
import sys
import threading
import urllib.error
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

import check_services
import pytest
from check_services import CheckError, Config, Finding

ROOT = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "scripts" / "check_services.py"
# The recorded registry response of the hook tests, shared on purpose:
# both must handle the real response
DATA = ROOT / "tests" / "data" / "registry" / "services.json"

# The real function, which the fixture `site` replaces
PLACEHOLDER = check_services.placeholder


class Server(http.server.BaseHTTPRequestHandler):
    """Answers with the response set for each path in `routes`.

    A route maps a path to a status and a body (bytes, or a JSON-encodable
    value). Unknown paths get a 404. `calls` counts the requests per path.
    """

    routes: ClassVar[dict[str, tuple[int, Any]]] = {}
    calls: ClassVar[dict[str, int]] = {}

    def do_GET(self) -> None:
        """Answers a GET request from `routes`."""
        self.calls[self.path] = self.calls.get(self.path, 0) + 1
        status, body = self.routes.get(self.path, (404, b""))
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keeps the test output quiet.

        Args:
            format: The format of the message.
            *args: The arguments of the message.
        """


@pytest.fixture
def server() -> Iterator[str]:
    """Runs the local server.

    Yields:
        Its base URL, e.g. `http://127.0.0.1:12345`.
    """
    Server.routes = {}
    Server.calls = {}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Server)
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
    monkeypatch.setattr(check_services, "RETRY_DELAY", 0)


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
    ("url", "base"),
    [
        ("https://h.org/ga4gh/tes/v1", "https://h.org/ga4gh/tes/v1"),
        ("https://H.org/ga4gh/TES/v1/tasks?x=1", "https://h.org/ga4gh/tes/v1"),
        ("HTTP://h.org:8443/p/q/ga4gh/wes/v1/", "http://h.org:8443/p/q/ga4gh/wes/v1"),
        ("${TES:-https://h.org}/ga4gh/tes/v1", "https://h.org/ga4gh/tes/v1"),
        ("See https://h.org/ga4gh/tes/v1.", "https://h.org/ga4gh/tes/v1"),
        ("https://u:p@h.org:443/ga4gh/tes/v1", "https://h.org/ga4gh/tes/v1"),
        ("http://h.org:80/ga4gh/tes/v1", "http://h.org/ga4gh/tes/v1"),
        ("http://h.org:443/ga4gh/tes/v1", "http://h.org:443/ga4gh/tes/v1"),
        ("https://h.org/ga4gh/drs/v1.2", None),
        ("https://h.org/ga4gh/tes/v1beta", None),
        ("https://h.org/ga4gh/tes/", None),
        ("https://<HOST>/ga4gh/tes/v1", None),
        ("https://h.org/tes/v1", None),
    ],
)
def test_normalize(url: str, base: str | None) -> None:
    """Strips the path after the version and lowers scheme and host."""
    assert check_services.normalize(url) == base


@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("https://h.org/x", "h.org"),
        ("https://u:p@H.org:8080/x", "h.org"),
        ("http://[::1]:8080/x", "::1"),
        ("h.org", "h.org"),
    ],
)
def test_hostname(url: str, host: str) -> None:
    """Drops user info and port."""
    assert check_services.hostname(url) == host


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("example.org", True),
        ("tes.example.com", True),
        ("gateway.example.net", True),
        ("my.service.test", True),
        ("x.invalid", True),
        ("x.localhost", True),
        ("x.example", True),
        ("localhost", True),
        ("cloud-registry", True),
        ("127.0.0.1", True),
        ("0.0.0.0", True),
        ("::1", True),
        ("10.0.0.5", True),
        ("192.168.1.2", True),
        ("169.254.169.254", True),
        ("host.docker.internal", True),
        ("printer.local", True),
        ("tesk-api.tesk.svc", True),
        ("tesk-api.tesk.svc.cluster.local", True),
        ("%3chost%3e.org", True),
        ("$host.org", True),
        ("*.rahtiapp.fi", True),
        ("protes.rahtiapp.fi", False),
        ("example.org.evil.fi", False),
        ("8.8.8.8", False),
    ],
)
def test_placeholder(host: str, expected: bool) -> None:
    """Recognizes placeholder, local and template hosts."""
    assert check_services.placeholder(host) is expected


def test_skipped() -> None:
    """Skips placeholders and the configured hosts with their subdomains."""
    skip = {"workflowhub.eu"}
    assert check_services.skipped("https://workflowhub.eu/ga4gh/trs/v2", skip)
    assert check_services.skipped("https://x.workflowhub.eu/ga4gh/trs/v2", skip)
    assert check_services.skipped("http://localhost:8080/ga4gh/tes/v1", skip)
    assert not check_services.skipped("https://notworkflowhub.eu/ga4gh/trs/v2", skip)


def test_collect(tmp_path: Path) -> None:
    """Collects base URLs with file and line of each mention."""
    page = write(
        tmp_path / "page.md",
        "Use `https://h.org/ga4gh/tes/v1/tasks`.\n\n"
        "[TES](https://h.org/ga4gh/tes/v1) and https://w.org/ga4gh/wes/v1|x\n",
    )
    other = write(tmp_path / "other.md", "No services here.\n")
    assert check_services.collect([page, other]) == {
        "https://h.org/ga4gh/tes/v1": [f"{page}:1", f"{page}:3"],
        "https://w.org/ga4gh/wes/v1": [f"{page}:3"],
    }


def test_find_files(tmp_path: Path) -> None:
    """Expands directories to their Markdown files, in order."""
    b = write(tmp_path / "docs" / "b.md", "")
    a = write(tmp_path / "docs" / "sub" / "a.md", "")
    write(tmp_path / "docs" / "c.yml", "")
    readme = write(tmp_path / "README.md", "")
    assert check_services.find_files([str(readme), str(tmp_path / "docs")]) == [
        readme,
        b,
        a,
    ]


def test_find_files_missing(tmp_path: Path) -> None:
    """Fails for a path that does not exist."""
    with pytest.raises(CheckError, match="no such file or directory"):
        check_services.find_files([str(tmp_path / "missing")])


def test_load_config(tmp_path: Path) -> None:
    """Reads skipped hosts and unregistered services."""
    path = write(
        tmp_path / "c.toml",
        'skip_hosts = ["WorkflowHub.eu"]\n'
        "[unregistered]\n"
        '"https://h.org/ga4gh/tes/v1" = "reason"\n',
    )
    assert check_services.load_config(path) == Config(
        skip_hosts=frozenset({"workflowhub.eu"}),
        unregistered={"https://h.org/ga4gh/tes/v1": "reason"},
    )


def test_load_config_empty(tmp_path: Path) -> None:
    """Accepts an empty configuration."""
    assert check_services.load_config(write(tmp_path / "c.toml", "")) == Config()


def test_load_config_of_repository() -> None:
    """Accepts the configuration of the repository."""
    config = check_services.load_config(ROOT / "service-check.toml")
    assert "workflowhub.eu" in config.skip_hosts


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("x = ", "c.toml"),
        ("other = 1", "unknown keys other"),
        ('skip_hosts = "h.org"', "skip_hosts must be a list"),
        ('skip_hosts = [""]', "skip_hosts must be a list"),
        ("skip_hosts = [1]", "skip_hosts must be a list"),
        ('unregistered = ["x"]', "unregistered must be a table"),
        ('[unregistered]\n"https://h.org/ga4gh/tes/v1" = ""', "needs a reason"),
        ('[unregistered]\n"https://h.org/ga4gh/tes/v1" = 1', "needs a reason"),
        (
            '[unregistered]\n"https://h.org/ga4gh/tes/v1/tasks" = "r"',
            "not the base URL",
        ),
        ('[unregistered]\n"https://h.org/" = "r"', "not the base URL"),
    ],
)
def test_load_config_invalid(tmp_path: Path, text: str, message: str) -> None:
    """Rejects invalid configurations."""
    with pytest.raises(CheckError, match=message):
        check_services.load_config(write(tmp_path / "c.toml", text))


def test_load_config_missing(tmp_path: Path) -> None:
    """Fails for a missing configuration file."""
    with pytest.raises(CheckError, match=r"missing\.toml"):
        check_services.load_config(tmp_path / "missing.toml")


def test_default_registry(tmp_path: Path) -> None:
    """Reads `extra.registry_url` of the MkDocs configuration."""
    path = write(
        tmp_path / "mkdocs.yml", "extra:\n  registry_url: https://r.org/v1/ \n"
    )
    assert check_services.default_registry(path) == "https://r.org/v1"


def test_default_registry_of_repository() -> None:
    """Finds the registry of the site in `mkdocs.yml`."""
    url = check_services.default_registry(ROOT / "mkdocs.yml")
    assert url.endswith("/ga4gh/registry/v1")


def test_default_registry_missing(tmp_path: Path) -> None:
    """Fails without the file or the setting."""
    with pytest.raises(CheckError, match="mkdocs.yml"):
        check_services.default_registry(tmp_path / "mkdocs.yml")
    path = write(tmp_path / "mkdocs.yml", "site_name: x\n")
    with pytest.raises(CheckError, match="no registry_url"):
        check_services.default_registry(path)


def test_fetch_json(server: str) -> None:
    """Returns the decoded document."""
    Server.routes = {"/x": (200, {"a": 1})}
    assert check_services.fetch_json(f"{server}/x") == {"a": 1}


def test_fetch_json_retries_transient_errors(server: str) -> None:
    """Retries a 5xx response once, then fails."""
    Server.routes = {"/x": (503, b"")}
    with pytest.raises(CheckError, match="HTTP 503"):
        check_services.fetch_json(f"{server}/x")
    assert Server.calls["/x"] == 2


def test_fetch_json_retry_succeeds(
    server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Returns the document of a successful retry."""
    Server.routes = {"/x": (429, b"")}
    sleep_calls: list[float] = []

    def sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        Server.routes = {"/x": (200, [1])}

    monkeypatch.setattr("check_services.time.sleep", sleep)
    assert check_services.fetch_json(f"{server}/x") == [1]
    assert sleep_calls == [0]


def test_fetch_json_does_not_retry_client_errors(server: str) -> None:
    """Fails at once on a 404."""
    with pytest.raises(CheckError, match="HTTP 404"):
        check_services.fetch_json(f"{server}/x")
    assert Server.calls["/x"] == 1


def test_fetch_json_not_json(server: str) -> None:
    """Fails for a body that is not JSON."""
    Server.routes = {"/x": (200, b"<html>")}
    with pytest.raises(CheckError, match="not JSON"):
        check_services.fetch_json(f"{server}/x")


def test_fetch_json_too_large(server: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails for a body larger than the limit."""
    monkeypatch.setattr(check_services, "MAX_BYTES", 4)
    Server.routes = {"/x": (200, b"[1, 2, 3]")}
    with pytest.raises(CheckError, match="larger than 4 bytes"):
        check_services.fetch_json(f"{server}/x")


def test_fetch_json_unreachable() -> None:
    """Describes network errors by their reason."""
    with pytest.raises(CheckError) as info:
        check_services.fetch_json("http://127.0.0.1:1/x")
    assert "refused" in str(info.value).lower()


def test_fetch_json_invalid_url() -> None:
    """Fails at once for an invalid URL."""
    with pytest.raises(CheckError, match="unknown url type"):
        check_services.fetch_json("nope://x")


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (urllib.error.HTTPError("u", 500, "m", None, None), True),  # type: ignore[arg-type]
        (urllib.error.HTTPError("u", 429, "m", None, None), True),  # type: ignore[arg-type]
        (urllib.error.HTTPError("u", 404, "m", None, None), False),  # type: ignore[arg-type]
        (urllib.error.URLError("refused"), True),
        (TimeoutError(), True),
        (http.client.RemoteDisconnected("closed"), True),
        (ValueError("bad URL"), False),
    ],
)
def test_transient(error: Exception, expected: bool) -> None:
    """Retries network errors, timeouts, 429 and 5xx only."""
    assert check_services.transient(error) is expected


@pytest.mark.parametrize(
    ("error", "text"),
    [
        (urllib.error.HTTPError("u", 404, "m", None, None), "HTTP 404"),  # type: ignore[arg-type]
        (urllib.error.URLError("refused"), "refused"),
        (TimeoutError("timed out"), "timed out"),
        (TimeoutError(), "TimeoutError"),
    ],
)
def test_describe(error: Exception, text: str) -> None:
    """Describes errors briefly."""
    assert check_services.describe(error) == text


def test_registered_urls(server: str) -> None:
    """Normalizes the URLs of the recorded registry response."""
    Server.routes = {"/r/services": (200, json.loads(DATA.read_bytes()))}
    urls = check_services.registered_urls(f"{server}/r")
    assert "https://elixir-on.cloud/ga4gh/registry/v1" in urls
    assert "https://spe4hd.tes.bihealth.org/ga4gh/tes/v1" in urls


def test_registered_urls_skips_odd_entries(server: str) -> None:
    """Ignores entries without a service URL."""
    services = [
        {"url": "https://h.org/ga4gh/wes/v1/service-info"},
        {"url": "https://h.org/no-ga4gh"},
        {"url": 1},
        {},
        "x",
    ]
    Server.routes = {"/r/services": (200, services)}
    assert check_services.registered_urls(f"{server}/r") == {
        "https://h.org/ga4gh/wes/v1"
    }


def test_registered_urls_not_a_list(server: str) -> None:
    """Fails if the registry does not answer with a list."""
    Server.routes = {"/r/services": (200, {"services": []})}
    with pytest.raises(CheckError, match="expected a list"):
        check_services.registered_urls(f"{server}/r")


def test_registered_urls_unreachable(server: str) -> None:
    """Names the registry if it can't be reached."""
    with pytest.raises(CheckError, match=r"registry .*/r: HTTP 404"):
        check_services.registered_urls(f"{server}/r")


def test_probe_service_info(server: str) -> None:
    """Accepts a JSON object and reports anything else."""
    Server.routes = {
        "/ok/service-info": (200, {"id": "x"}),
        "/list/service-info": (200, []),
    }
    probe = check_services.probe_service_info
    assert probe(f"{server}/ok") is None
    assert probe(f"{server}/list") == "`service-info` is not a JSON object"
    assert probe(f"{server}/gone") == "`service-info` failed: HTTP 404"


TES = "https://tes.org/ga4gh/tes/v1"


def run_check(
    mentions: dict[str, list[str]],
    registered: set[str] | None = None,
    config: Config | None = None,
    problems: dict[str, str] | None = None,
) -> tuple[list[Finding], int, list[str]]:
    """Runs `check` with a fake probe of `service-info`.

    Args:
        mentions: Where each base URL is named.
        registered: The base URLs in the registry; none if not given.
        config: The configuration; the default if not given.
        problems: The problem of `service-info` per URL; others are fine.

    Returns:
        The findings, the number of services checked and the probed URLs.
    """
    probed: list[str] = []

    def probe(url: str) -> str | None:
        probed.append(url)
        return (problems or {}).get(url)

    findings, checked = check_services.check(
        mentions, registered or set(), config or Config(), probe
    )
    return findings, checked, probed


def test_check_registered_service() -> None:
    """Finds nothing for a registered service that answers."""
    assert run_check({TES: ["a.md:1"]}, {TES}) == ([], 1, [TES])


def test_check_unregistered_service() -> None:
    """Reports a service that is not in the registry, with its locations."""
    findings, _, _ = run_check({TES: ["a.md:1", "b.md:2"]})
    assert findings == [Finding(TES, "not in the Cloud Registry", ("a.md:1", "b.md:2"))]


def test_check_service_down() -> None:
    """Reports a registered service whose `service-info` fails."""
    findings, _, _ = run_check({TES: ["a.md:1"]}, {TES}, problems={TES: "down"})
    assert findings == [Finding(TES, "down", ("a.md:1",))]


def test_check_unregistered_and_down() -> None:
    """Reports both problems of a service."""
    findings, _, _ = run_check({TES: ["a.md:1"]}, problems={TES: "down"})
    assert [f.problem for f in findings] == ["not in the Cloud Registry", "down"]


def test_check_allowed_unregistered_service() -> None:
    """Accepts a listed unregistered service but still probes it."""
    config = Config(unregistered={TES: "later"})
    assert run_check({TES: ["a.md:1"]}, config=config) == ([], 1, [TES])


@pytest.mark.parametrize(
    "url",
    ["https://tes.example.org/ga4gh/tes/v1", "https://workflowhub.eu/ga4gh/trs/v2"],
)
def test_check_skips(url: str) -> None:
    """Neither checks nor probes placeholders and skipped hosts."""
    config = Config(skip_hosts=frozenset({"workflowhub.eu"}))
    assert run_check({url: ["a.md:1"]}, config=config) == ([], 0, [])


def test_check_stale_entries() -> None:
    """Reports listed services that are registered now or no longer named."""
    now = "https://now.org/ga4gh/tes/v1"
    gone = "https://gone.org/ga4gh/tes/v1"
    config = Config(unregistered={now: "r", gone: "r"})
    findings, _, _ = run_check({now: ["a.md:1"]}, {now}, config)
    assert findings == [
        Finding(gone, "no page names it; remove it from `unregistered`"),
        Finding(now, "registered now; remove it from `unregistered`"),
    ]


def test_check_order() -> None:
    """Lists findings of named services by URL, then stale entries."""
    gone = "https://gone.org/ga4gh/tes/v1"
    mentions = {
        "https://b.org/ga4gh/tes/v1": ["a.md:1"],
        "https://a.org/ga4gh/tes/v1": ["a.md:2"],
    }
    config = Config(unregistered={gone: "r"})
    findings, checked, _ = run_check(mentions, config=config)
    assert checked == 2
    assert [f.url for f in findings] == [
        "https://a.org/ga4gh/tes/v1",
        "https://b.org/ga4gh/tes/v1",
        gone,
    ]


def test_report_without_findings() -> None:
    """Says that all is fine."""
    assert check_services.report([], 3) == (
        "Checked 3 service URLs named in the docs. No problems found.\n"
    )


def test_report_with_findings() -> None:
    """Lists each finding with where it is named."""
    findings = [
        Finding("https://a.org/ga4gh/tes/v1", "not in the Cloud Registry", ("x:1",)),
        Finding("https://b.org/ga4gh/tes/v1", "registered now"),
    ]
    assert check_services.report(findings, 2) == (
        "Checked 2 service URLs named in the docs. Found 2 problems "
        "(configuration: `service-check.toml`):\n"
        "\n"
        "- `https://a.org/ga4gh/tes/v1`: not in the Cloud Registry\n"
        "  - `x:1`\n"
        "- `https://b.org/ga4gh/tes/v1`: registered now\n"
    )


@pytest.fixture
def site(tmp_path: Path, server: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a small repository whose services are on the local server.

    Args:
        tmp_path: The pytest fixture.
        server: The base URL of the local server.
        monkeypatch: The pytest fixture.

    Returns:
        The repository, which is also the working directory.
    """
    write(
        tmp_path / "mkdocs.yml",
        f"site_name: x\nextra:\n  registry_url: {server}/ga4gh/registry/v1\n",
    )
    write(tmp_path / "service-check.toml", "")
    write(tmp_path / "README.md", f"Registry: {server}/ga4gh/registry/v1\n")
    write(tmp_path / "docs" / "index.md", "See https://tes.example.org/ga4gh/tes/v1\n")
    write(tmp_path / "includes" / "x.md", "")
    Server.routes = {
        "/ga4gh/registry/v1/services": (
            200,
            [{"url": f"{server}/ga4gh/registry/v1"}],
        ),
    }
    monkeypatch.chdir(tmp_path)
    # The local server's address is a loopback address, which the check
    # skips as a placeholder in real docs
    monkeypatch.setattr(check_services, "placeholder", lambda host: host != "127.0.0.1")
    return tmp_path


def test_main_without_problems(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exits with 0 and says so."""
    Server.routes["/ga4gh/registry/v1/service-info"] = (200, {"id": "r"})
    assert check_services.main([]) == 0
    assert "Checked 1 service URLs" in capsys.readouterr().out


def test_main_skips_placeholders(
    site: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Skips the loopback and example services of the docs in a real run."""
    monkeypatch.setattr(check_services, "placeholder", PLACEHOLDER)
    assert check_services.main([]) == 0
    assert "Checked 0 service URLs" in capsys.readouterr().out


def test_main_with_problems(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exits with 2 and writes the report."""
    output = site / "out" / "services.md"
    assert check_services.main(["--output", str(output)]) == 2
    out = capsys.readouterr().out
    assert "`service-info` failed: HTTP 404" in out
    assert output.read_text(encoding="utf-8") == out


def test_main_with_registry_option(
    site: Path, server: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Uses the registry given on the command line."""
    Server.routes["/other/services"] = (200, [])
    assert check_services.main(["--registry", f"{server}/other/", "README.md"]) == 2
    assert "not in the Cloud Registry" in capsys.readouterr().out


def test_main_errors(site: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exits with 1 if the check can't run."""
    assert check_services.main(["missing.md"]) == 1
    assert "no such file" in capsys.readouterr().err
    Server.routes = {}
    assert check_services.main([]) == 1
    assert "HTTP 404" in capsys.readouterr().err


def test_script(site: Path, server: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Runs as a script and exits with the status of `main`."""
    monkeypatch.setattr(sys, "argv", ["check_services.py", "missing.md"])
    with pytest.raises(SystemExit) as info:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert info.value.code == 1
