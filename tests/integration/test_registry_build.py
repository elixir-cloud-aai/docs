"""Builds a small site with the Cloud Registry hook against a local registry.

The registry is a local HTTP server that serves the recorded response of
`GET /services` (or an error), so the tests need no network access.
"""

from __future__ import annotations

import http.server
import json
import re
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort

ROOT = Path(__file__).parent.parent.parent
HOOK = ROOT / "hooks" / "registry.py"
DATA = ROOT / "tests" / "data" / "registry" / "services.json"


# The Markdown extensions of the site (`mkdocs.yml`) that could turn text
# from the registry into markup
EXTENSIONS = [
    "abbr",
    "admonition",
    "attr_list",
    "def_list",
    "md_in_html",
    "pymdownx.details",
    "pymdownx.emoji",
    "pymdownx.inlinehilite",
    "pymdownx.snippets",
    "pymdownx.superfences",
    "pymdownx.tabbed",
    "pymdownx.tasklist",
    "tables",
    "toc",
]

# A registry entry that tries to inject markup through each field
HOSTILE = {
    "id": "X",
    "name": '<img src=x onerror="alert(1)"> *[TES]: injected',
    "url": 'https://example.org/a)"onmouseover="alert(1)',
    "version": "--8<-- 'README.md'",
    "environment": "prod",
    "documentationUrl": "javascript:alert(1)",
    "organization": {"name": ":smile: {: onclick=alert(1) } [x](y)", "url": "x"},
    "type": {"artifact": "tes", "group": "org.ga4gh", "version": "1.1.0"},
}


class Registry(http.server.BaseHTTPRequestHandler):
    """Serves `body` as the services, or a 503 error if `failing` is set."""

    failing = False
    body = DATA.read_bytes()

    def do_GET(self) -> None:
        """Answers `GET /ga4gh/registry/v1/services`."""
        if self.failing or self.path != "/ga4gh/registry/v1/services":
            self.send_error(503 if self.failing else 404)
            return
        body = self.body
        self.send_response(200)
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
def registry_url() -> Iterator[str]:
    """Runs a local registry.

    Yields:
        The base URL of its API.
    """
    Registry.failing = False
    Registry.body = DATA.read_bytes()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Registry)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/ga4gh/registry/v1"
    server.shutdown()
    server.server_close()


def make_site(tmp_path: Path, registry_url: str) -> Path:
    """Writes a site with one page that has a marker.

    Args:
        tmp_path: Directory to write to.
        registry_url: The registry to read.

    Returns:
        The path of `mkdocs.yml`.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "# Services\n\n<!-- registry:services type=tes,wes -->\n",
        encoding="utf-8",
    )
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: Test\n"
        f"markdown_extensions: [{', '.join(EXTENSIONS)}]\n"
        f"hooks: ['{HOOK}']\n"
        f"extra: {{registry_url: '{registry_url}'}}\n",
        encoding="utf-8",
    )
    return config


def run_build(config: Path) -> str:
    """Builds a site strictly and returns its index page.

    Args:
        config: The path of `mkdocs.yml`.

    Returns:
        The HTML of the index page.
    """
    cfg = load_config(str(config), strict=True)
    build(cfg)
    return (Path(cfg.site_dir) / "index.html").read_text(encoding="utf-8")


def test_build_renders_table(
    tmp_path: Path, registry_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renders the production TES and WES services as an HTML table."""
    monkeypatch.delenv("DOCS_REGISTRY_OFFLINE", raising=False)
    html = run_build(make_site(tmp_path, registry_url))
    assert "<table>" in html
    assert "<td>BIH Funnel</td>" in html
    assert "<td>BIH weskit</td>" in html
    assert "JAN DIGITRUST" not in html  # test environment
    assert "Service Registry" not in html  # other type
    assert 'href="https://spe4hd.tes.bihealth.org/ga4gh/tes/v1"' in html


def test_build_fails_without_registry(
    tmp_path: Path,
    registry_url: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Fails the build if the registry answers with errors."""
    monkeypatch.delenv("DOCS_REGISTRY_OFFLINE", raising=False)
    monkeypatch.setattr("time.sleep", lambda _: None)
    Registry.failing = True
    with pytest.raises(Abort):
        run_build(make_site(tmp_path, registry_url))
    assert "could not fetch" in caplog.text
    assert "503" in caplog.text


def test_build_offline_renders_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Builds strictly without a registry in offline mode."""
    monkeypatch.setenv("DOCS_REGISTRY_OFFLINE", "1")
    html = run_build(make_site(tmp_path, "http://127.0.0.1:9/unreachable"))
    assert "admonition warning" in html
    assert "<table>" not in html


def test_build_escapes_registry_data(
    tmp_path: Path, registry_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renders hostile registry data as text, with the site's extensions."""
    monkeypatch.delenv("DOCS_REGISTRY_OFFLINE", raising=False)
    Registry.body = json.dumps([HOSTILE]).encode()
    html = run_build(make_site(tmp_path, registry_url))
    table = html[html.index("<table>") : html.index("</table>")]
    tags = re.findall(r"<[^>]*>", table)
    assert {re.match(r"</?(\w+)", tag).group(1) for tag in tags} == {  # type: ignore[union-attr]
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "a",
    }
    # No attributes but the href of links, and only http(s) targets
    for tag in tags:
        assert re.fullmatch(r'</?\w+>|<a href="https?://[^"\s]*">', tag), tag
    assert "ELIXIR On-Cloud docs" not in table  # README.md not included
    assert "&lt;img src=x onerror=" in table
    assert "--8&lt;-- 'README.md'" in table
    # The URL is a link with its quotes and parentheses encoded; the
    # organization's URL and the docs URL are not http(s), so no links
    assert table.count("<a ") == 1
    assert 'href="https://example.org/a%29%22onmouseover=%22alert%281%29"' in table
