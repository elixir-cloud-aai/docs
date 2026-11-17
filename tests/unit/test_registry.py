"""Unit tests of the Cloud Registry hook in `hooks/registry.py`."""

from __future__ import annotations

import copy
import http.client
import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

import pytest
import registry
from mkdocs.exceptions import PluginError

DATA = Path(__file__).parent.parent / "data" / "registry" / "services.json"
URL = "https://registry.example.org/ga4gh/registry/v1"

# The hook ignores the configuration and the files in `on_page_markdown`
NO_CONFIG: Any = None
NO_FILES: Any = None


@pytest.fixture
def services() -> list[dict[str, Any]]:
    """Returns the recorded response of `GET /services`.

    Returns:
        The services.
    """
    return json.loads(DATA.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configures the hook with a registry URL and no offline mode.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
    """
    monkeypatch.delenv(registry.OFFLINE_VARIABLE, raising=False)
    monkeypatch.setattr(registry.time, "sleep", lambda _: None)
    registry.on_config(config({"registry_url": URL}))


def config(extra: dict[str, Any]) -> Any:
    """Builds a stand-in for the MkDocs configuration.

    Args:
        extra: The `extra` section.

    Returns:
        An object with an `extra` attribute.
    """
    return SimpleNamespace(extra=extra)


def page(src_uri: str = "operators/services/index.md") -> Any:
    """Builds a stand-in for a MkDocs page.

    Args:
        src_uri: The source path of the page.

    Returns:
        An object with `file.src_uri`.
    """
    return SimpleNamespace(file=SimpleNamespace(src_uri=src_uri))


class FakeResponse(io.BytesIO):
    """A response of `urllib.request.urlopen` with a fixed body."""

    def __enter__(self) -> Self:
        """Enters the context.

        Returns:
            The response.
        """
        return self

    def __exit__(self, *args: object) -> None:
        """Leaves the context.

        Args:
            *args: The exception details, ignored.
        """


def fake_urlopen(
    monkeypatch: pytest.MonkeyPatch, *results: bytes | Exception
) -> list[Any]:
    """Replaces `urlopen` with one that returns or raises the given results.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        *results: Bodies to return or exceptions to raise, one per call.

    Returns:
        The list of requests made, filled as the hook calls `urlopen`.
    """
    requests: list[Any] = []
    pending = list(results)

    def urlopen(request: Any, timeout: float) -> FakeResponse:
        requests.append((request, timeout))
        result = pending.pop(0)
        if isinstance(result, Exception):
            raise result
        return FakeResponse(result)

    monkeypatch.setattr(registry.urllib.request, "urlopen", urlopen)
    return requests


def test_on_config_strips_url_and_resets_services() -> None:
    """Strips trailing slashes and forgets the services of a previous build."""
    registry.state.services = []
    registry.on_config(config({"registry_url": f" {URL}/ "}))
    assert registry.state.url == URL
    assert registry.state.services is None


@pytest.mark.parametrize("extra", [{}, {"registry_url": " "}, {"registry_url": 1}])
def test_on_config_requires_url(extra: dict[str, Any]) -> None:
    """Fails without a registry URL."""
    with pytest.raises(PluginError, match="registry_url"):
        registry.on_config(config(extra))


def test_page_without_marker_is_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leaves pages without markers alone and fetches nothing."""
    requests = fake_urlopen(monkeypatch)
    markdown = "# Title\n\n<!-- a comment -->\n"
    assert registry.on_page_markdown(markdown, page(), NO_CONFIG, NO_FILES) == markdown
    assert requests == []


def test_marker_renders_table(
    monkeypatch: pytest.MonkeyPatch, services: list[dict[str, Any]]
) -> None:
    """Replaces markers with tables and fetches once per build."""
    requests = fake_urlopen(monkeypatch, json.dumps(services).encode())
    markdown = (
        "Before\n\n<!-- registry:services type=tes -->\n\n"
        "  <!--registry:services environment=all-->\n\nAfter\n"
    )
    result = registry.on_page_markdown(markdown, page(), NO_CONFIG, NO_FILES)
    assert "registry:services" not in result
    assert result.startswith("Before\n\n\n| Service |")
    assert result.endswith("\nAfter\n")
    assert result.count("BIH Funnel") == 2
    assert result.count("JAN DIGITRUST temporary TESK lab") == 1
    assert len(requests) == 1
    request, timeout = requests[0]
    assert request.full_url == f"{URL}/services"
    assert request.get_header("Accept") == "application/json"
    assert timeout == registry.TIMEOUT
    # A second page of the same build uses the services fetched before
    registry.on_page_markdown("<!-- registry:services -->", page(), NO_CONFIG, NO_FILES)
    assert len(requests) == 1


def test_markers_in_code_blocks_are_examples(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leaves markers in fenced code blocks alone."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    examples = (
        "````markdown\n"
        "```\n"
        "<!-- registry:services -->\n"
        "```\n"
        "````\n"
        "~~~\n"
        "<!-- registry:services unknown=1 -->\n"
        "~~~\n"
    )
    result = registry.on_page_markdown(
        f"{examples}<!-- registry:services -->\n", page(), NO_CONFIG, NO_FILES
    )
    assert result == f"{examples}\n{registry.offline_notice()}\n"


def test_inline_code_is_no_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Doesn't take inline code at the start of a line for a fence."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    result = registry.on_page_markdown(
        "```x``` is code.\n\n<!-- registry:services -->\n", page(), NO_CONFIG, NO_FILES
    )
    assert "!!! warning" in result


def test_unclosed_fence_hiding_marker_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails the build if a code block that is never closed hides a marker."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    with pytest.raises(PluginError, match="never closed hides 1 registry marker"):
        registry.on_page_markdown(
            "```\nCode\n\n<!-- registry:services -->\n", page(), NO_CONFIG, NO_FILES
        )


def test_unclosed_fence_after_marker_is_fine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepts a code block that is never closed if it hides no marker."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    result = registry.on_page_markdown(
        "~~~\n<!-- registry:services -->\n~~~\n<!-- registry:services -->\n```\nx\n",
        page(),
        NO_CONFIG,
        NO_FILES,
    )
    assert result.endswith("```\nx\n")


def test_marker_without_blank_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    """Separates the table from text right above and below the marker."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    result = registry.on_page_markdown(
        "Intro\n<!-- registry:services -->\nOutro\n", page(), NO_CONFIG, NO_FILES
    )
    assert result == f"Intro\n\n{registry.offline_notice()}\nOutro\n"


def test_marker_keeps_indentation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Indents the replacement like the marker, e.g. inside an admonition."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    markdown = '!!! note "Services"\n\n    <!-- registry:services -->\n\nAfter\n'
    result = registry.on_page_markdown(markdown, page(), NO_CONFIG, NO_FILES)
    expected = registry.indent(registry.offline_notice(), "    ")
    assert result == f'!!! note "Services"\n\n\n{expected}\n\n\nAfter\n'
    assert expected.startswith('    !!! warning "Services not loaded"\n\n        This')


def test_marker_offline_renders_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Renders a warning and fetches nothing in offline mode."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    requests = fake_urlopen(monkeypatch)
    with caplog.at_level("INFO"):
        result = registry.on_page_markdown(
            "<!-- registry:services -->\n", page(), NO_CONFIG, NO_FILES
        )
    assert result.startswith('\n!!! warning "Services not loaded"')
    assert requests == []
    assert "not rendered" in caplog.text


@pytest.mark.parametrize("value", ["", "0", "true", "yes"])
def test_offline_needs_exactly_one(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Treats only `1` as offline mode."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, value)
    assert not registry.offline()


def test_marker_with_bad_options_fails_even_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Checks the options of markers in offline builds too."""
    monkeypatch.setenv(registry.OFFLINE_VARIABLE, "1")
    with pytest.raises(PluginError, match="unknown marker option 'kind'"):
        registry.on_page_markdown(
            "<!-- registry:services kind=tes -->", page(), NO_CONFIG, NO_FILES
        )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", {"environment": "prod"}),
        (" type=tes", {"type": "tes", "environment": "prod"}),
        (
            " type=tes,wes  environment=test",
            {"type": "tes,wes", "environment": "test"},
        ),
    ],
)
def test_parse_options(text: str, expected: dict[str, str]) -> None:
    """Parses known options and sets the default environment."""
    assert registry.parse_options(text, "page.md") == expected


@pytest.mark.parametrize("text", [" type", " type=tes extra", " type==tes", "x"])
def test_parse_options_rejects_malformed(text: str) -> None:
    """Fails on text that isn't a `key=value` option."""
    with pytest.raises(PluginError, match="page.md: malformed marker options"):
        registry.parse_options(text, "page.md")


def test_get_services_requires_config() -> None:
    """Fails if the hook wasn't configured."""
    registry.state.url = None
    with pytest.raises(PluginError, match="not configured"):
        registry.get_services()


def test_fetch_retries_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retries a failed request once."""
    sleeps: list[float] = []
    monkeypatch.setattr(registry.time, "sleep", sleeps.append)
    requests = fake_urlopen(monkeypatch, TimeoutError("timed out"), b"[]")
    assert registry.fetch(f"{URL}/services") == []
    assert len(requests) == 2
    assert sleeps == [registry.RETRY_DELAY]


def http_error(code: int) -> urllib.error.HTTPError:
    """Builds an HTTP error.

    Args:
        code: The HTTP status code.

    Returns:
        The error.
    """
    return urllib.error.HTTPError(f"{URL}/services", code, "Error", Message(), None)


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.URLError("no route"),
        TimeoutError("timed out"),
        http.client.IncompleteRead(b""),
        http_error(503),
        http_error(429),
    ],
)
def test_fetch_fails_after_retry(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    """Fails the build if both attempts fail, naming the offline variable."""
    requests = fake_urlopen(monkeypatch, error, error)
    with pytest.raises(PluginError, match=registry.OFFLINE_VARIABLE):
        registry.fetch(f"{URL}/services")
    assert len(requests) == registry.ATTEMPTS


@pytest.mark.parametrize(
    "error", [http_error(404), http_error(401), ValueError("unknown url type")]
)
def test_fetch_fails_at_once_on_permanent_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    """Doesn't retry errors that a retry can't fix."""
    requests = fake_urlopen(monkeypatch, error)
    with pytest.raises(PluginError, match="could not fetch"):
        registry.fetch(f"{URL}/services")
    assert len(requests) == 1


@pytest.mark.parametrize("body", [b"<html>Bad gateway</html>", b"[" * 100_000])
def test_fetch_fails_on_invalid_json(
    monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    """Fails the build if the response isn't JSON (or nested too deeply)."""
    fake_urlopen(monkeypatch, body)
    with pytest.raises(PluginError, match="did not return JSON"):
        registry.fetch(f"{URL}/services")


def test_fetch_fails_on_large_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails the build if the response is too large."""
    monkeypatch.setattr(registry, "MAX_BYTES", 10)
    fake_urlopen(monkeypatch, b"[" + b" " * 20 + b"]")
    with pytest.raises(PluginError, match="more than 10 bytes"):
        registry.fetch(f"{URL}/services")


def test_validate_accepts_recorded_response(services: list[dict[str, Any]]) -> None:
    """Accepts the recorded response of the live registry."""
    assert registry.validate(services) is services


@pytest.mark.parametrize("data", [{}, None, "[]"])
def test_validate_rejects_non_list(data: Any) -> None:
    """Fails if the response isn't a list."""
    with pytest.raises(PluginError, match="expected a list"):
        registry.validate(data)


@pytest.mark.parametrize(
    ("path", "value", "problem"),
    [
        (("name",), None, "name"),
        (("url",), 42, "url"),
        (("type",), "tes", "type.artifact, type.version"),
        (("organization", "name"), None, "organization.name"),
        (("environment",), ["prod"], "environment"),
        (("documentationUrl",), 1, "documentationUrl"),
        (("organization", "url"), {}, "organization.url"),
    ],
)
def test_validate_rejects_bad_service(
    services: list[dict[str, Any]],
    path: tuple[str, ...],
    value: Any,
    problem: str,
) -> None:
    """Fails on services with missing or invalid fields."""
    bad = copy.deepcopy(services)
    target = bad[1]
    for key in path[:-1]:
        target = target[key]
    if value is None:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    with pytest.raises(PluginError, match=f"index 1: missing or invalid {problem}$"):
        registry.validate(bad)


def test_validate_rejects_non_dict_service() -> None:
    """Fails on entries that aren't objects."""
    with pytest.raises(PluginError, match="index 0"):
        registry.validate(["tes"])


def test_validate_accepts_null_optional_fields(
    services: list[dict[str, Any]],
) -> None:
    """Accepts optional fields that are null."""
    services[0]["environment"] = None
    services[0]["documentationUrl"] = None
    assert registry.validate(services) is services


def names(services: list[dict[str, Any]]) -> list[str]:
    """Returns the names of services.

    Args:
        services: The services.

    Returns:
        Their names, in order.
    """
    return [service["name"] for service in services]


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (
            {"environment": "prod"},
            ["ELIXIR On-Cloud Service Registry", "BIH Funnel", "BIH weskit"],
        ),
        ({"type": "TES", "environment": "prod"}, ["BIH Funnel"]),
        (
            {"type": "tes, wes,", "environment": "PROD"},
            ["BIH Funnel", "BIH weskit"],
        ),
        (
            {"type": "tes", "environment": "all"},
            ["BIH Funnel", "JAN DIGITRUST temporary TESK lab"],
        ),
        ({"type": "drs", "environment": "all"}, []),
    ],
)
def test_filter_services(
    services: list[dict[str, Any]], options: dict[str, str], expected: list[str]
) -> None:
    """Filters by type and environment and sorts by type and name."""
    assert names(registry.filter_services(services, options)) == expected


def test_filter_services_without_environment(
    services: list[dict[str, Any]],
) -> None:
    """Lists services without an environment only for `environment=all`."""
    del services[0]["environment"]
    assert "BIH Funnel" not in names(
        registry.filter_services(services, {"environment": "prod"})
    )
    assert "BIH Funnel" in names(
        registry.filter_services(services, {"environment": "all"})
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("BIH Funnel", "BIH Funnel"),
        ("a|b", r"a\|b"),
        ("<script>&", "&lt;script&gt;&amp;"),
        ("[x](y) *z* _w_ `v` #1 !", r"\[x\]\(y\) \*z\* \_w\_ \`v\` \#1 \!"),
        ("two\n  lines", "two lines"),
        ("back\\slash", "back\\\\slash"),
        (":smile:", "&#58;smile&#58;"),
    ],
)
def test_escape(text: str, expected: str) -> None:
    """Escapes HTML and Markdown and joins lines."""
    assert registry.escape(text) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.org/a", "[Docs](https://example.org/a)"),
        ("HTTP://example.org/", "[Docs](HTTP://example.org/)"),
        (
            'https://example.org/a|b(c)<d>"e',
            "[Docs](https://example.org/a%7Cb%28c%29%3Cd%3E%22e)",
        ),
        ("javascript:alert(1)", "Docs"),
        ("mailto:a@example.org", "Docs"),
        ("https://", "Docs"),
        ("https://example.org/a b", "Docs"),
        (None, "Docs"),
        ("", "Docs"),
    ],
)
def test_link(url: str | None, expected: str) -> None:
    """Links only http(s) URLs and encodes characters that end links."""
    assert registry.link("Docs", url) == expected


@pytest.mark.parametrize(
    ("artifact", "expected"),
    [("tes", "TES"), ("wes", "WES"), ("service-registry", "service-registry")],
)
def test_artifact_name(artifact: str, expected: str) -> None:
    """Capitalises acronyms only."""
    assert registry.artifact_name(artifact) == expected


def test_render_row(services: list[dict[str, Any]]) -> None:
    """Renders all columns of a service."""
    assert registry.render_row(services[0]) == (
        "| BIH Funnel "
        "| [Berlin Institute of Health at Charité \\(BIH\\)](https://www.bihealth.org/) "
        "| TES unknown | unknown | prod "
        "| [https&#58;//spe4hd.tes.bihealth.org/ga4gh/tes/v1]"
        "(https://spe4hd.tes.bihealth.org/ga4gh/tes/v1) "
        "| [Docs](https://docs.elixir-on.cloud/) |"
    )


def test_render_row_without_optional_fields(
    services: list[dict[str, Any]],
) -> None:
    """Renders dashes for missing environments and docs."""
    service = services[3]
    del service["environment"]
    del service["organization"]["url"]
    assert registry.render_row(service) == (
        "| BIH weskit | BIH Germany | WES 1.1.0 | 1.1.0 | – "
        "| [https&#58;//spe4hd.weskit.bihealth.org/ga4gh/wes/v1/service-info]"
        "(https://spe4hd.weskit.bihealth.org/ga4gh/wes/v1/service-info) | – |"
    )


def test_render_table(services: list[dict[str, Any]]) -> None:
    """Renders a header and one row per service."""
    lines = registry.render_table(services[:2]).splitlines()
    assert lines[:2] == registry.HEADER.splitlines()
    assert len(lines) == 4


def test_render_table_empty() -> None:
    """Renders a sentence if no service matches."""
    assert registry.render_table([]).startswith("_No matching services")
