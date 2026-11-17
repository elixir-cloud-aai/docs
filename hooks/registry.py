"""MkDocs hook that renders tables of services from the Cloud Registry.

A page asks for a table with a marker, an HTML comment on a line of its own:

    <!-- registry:services -->
    <!-- registry:services type=tes -->
    <!-- registry:services type=tes,wes environment=all -->

Options:
    type: Comma-separated service type artifacts (e.g. `tes`, `wes`) to
        list; all types if not given.
    environment: Environment of the services to list (`prod`, `test`, ...),
        or `all` for every environment. Defaults to `prod`.

The hook fetches `<registry_url>/services` once per build, the first time a
page has a marker. The registry URL is `extra.registry_url` in `mkdocs.yml`.
A failed fetch or a malformed response fails the build, so the site never
shows stale data. For local builds without network access, set
`DOCS_REGISTRY_OFFLINE=1`: markers then render as a warning instead (never
set it in CI or on Read the Docs).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

log = logging.getLogger(f"mkdocs.hooks.{__name__}")

OFFLINE_VARIABLE = "DOCS_REGISTRY_OFFLINE"
TIMEOUT = 10
ATTEMPTS = 2
RETRY_DELAY = 1.0
DEFAULT_ENVIRONMENT = "prod"
ALL_ENVIRONMENTS = "all"
OPTIONS = {"type", "environment"}

MARKER = re.compile(
    r"^[ \t]*<!--[ \t]*registry:services(?P<options>[^\n]*?)[ \t]*-->[ \t]*$",
    re.MULTILINE,
)
OPTION = re.compile(r"(?P<key>[\w-]+)=(?P<value>[^\s=]+)")
SAFE_URL = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

# Characters with a meaning in Markdown tables, links or emphasis
MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|])")

HEADER = (
    "| Service | Organization | Type | Version | Environment | URL | Docs |\n"
    "|---|---|---|---|---|---|---|"
)


class _State:
    """State of one build: the registry URL and the fetched services."""

    url: str | None = None
    services: list[dict[str, Any]] | None = None


state = _State()


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    """Reads the registry URL and resets the services of a previous build.

    Args:
        config: The MkDocs configuration.

    Returns:
        The unchanged configuration.

    Raises:
        PluginError: If `extra.registry_url` is not set.
    """
    url = config.extra.get("registry_url")
    if not isinstance(url, str) or not url.strip():
        raise PluginError("registry hook: set `extra.registry_url` in mkdocs.yml")
    state.url = url.strip().rstrip("/")
    state.services = None
    return config


def on_page_markdown(
    markdown: str, page: Page, config: MkDocsConfig, files: Files
) -> str:
    """Replaces the registry markers of a page with tables of services.

    Args:
        markdown: The Markdown source of the page.
        page: The page.
        config: The MkDocs configuration.
        files: The files of the site.

    Returns:
        The Markdown with the markers replaced.
    """
    if not MARKER.search(markdown):
        return markdown
    where = page.file.src_uri

    def replace(match: re.Match[str]) -> str:
        options = parse_options(match.group("options"), where)
        if offline():
            log.info("%s: %s=1, registry table not rendered", where, OFFLINE_VARIABLE)
            return offline_notice()
        return render_table(filter_services(get_services(), options))

    return MARKER.sub(replace, markdown)


def offline() -> bool:
    """Tells whether the build runs without the registry.

    Returns:
        True if `DOCS_REGISTRY_OFFLINE` is set to `1`.
    """
    return os.environ.get(OFFLINE_VARIABLE, "").strip() == "1"


def offline_notice() -> str:
    """Renders the warning shown instead of a table in offline builds.

    Returns:
        A Markdown admonition.
    """
    return (
        '!!! warning "Services not loaded"\n\n'
        f"    This build ran with `{OFFLINE_VARIABLE}=1`, so the list of services\n"
        "    was not fetched from the Cloud Registry. Published builds always\n"
        "    show it.\n"
    )


def parse_options(text: str, where: str) -> dict[str, str]:
    """Parses the options of a marker.

    Args:
        text: The text of the marker after `registry:services`.
        where: The page of the marker, for error messages.

    Returns:
        The options, with `environment` set to its default if not given.

    Raises:
        PluginError: If the text has anything but known `key=value` options.
    """
    options: dict[str, str] = {}
    rest = OPTION.sub("", text)
    if rest.strip():
        raise PluginError(f"registry hook: {where}: malformed marker options {text!r}")
    for match in OPTION.finditer(text):
        key = match.group("key")
        if key not in OPTIONS:
            raise PluginError(
                f"registry hook: {where}: unknown marker option {key!r}; "
                f"use {', '.join(sorted(OPTIONS))}"
            )
        options[key] = match.group("value")
    options.setdefault("environment", DEFAULT_ENVIRONMENT)
    return options


def get_services() -> list[dict[str, Any]]:
    """Returns the services of the registry, fetching them once per build.

    Returns:
        The services.

    Raises:
        PluginError: If the hook was not configured.
    """
    if state.url is None:
        raise PluginError("registry hook: not configured (on_config did not run)")
    if state.services is None:
        state.services = validate(fetch(f"{state.url}/services"))
    return state.services


def fetch(url: str) -> Any:
    """Fetches and decodes a JSON document, with one retry.

    Args:
        url: The URL to fetch.

    Returns:
        The decoded JSON document.

    Raises:
        PluginError: If both attempts fail or the response is not JSON.
    """
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    error: Exception | None = None
    for attempt in range(ATTEMPTS):
        if attempt:
            time.sleep(RETRY_DELAY)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = response.read()
            break
        except (OSError, ValueError) as exc:  # URLError, HTTPError, timeouts
            error = exc
            log.debug(
                "registry hook: attempt %d for %s failed: %s", attempt + 1, url, exc
            )
    else:
        raise PluginError(
            f"registry hook: could not fetch {url}: {error}. Set "
            f"{OFFLINE_VARIABLE}=1 for local builds without network access"
        )
    try:
        return json.loads(body)
    except ValueError as exc:
        raise PluginError(f"registry hook: {url} did not return JSON: {exc}") from exc


def validate(data: Any) -> list[dict[str, Any]]:
    """Checks that a response is a list of services with the fields we show.

    Args:
        data: The decoded response of `GET /services`.

    Returns:
        The services.

    Raises:
        PluginError: If the response is malformed.
    """
    if not isinstance(data, list):
        raise PluginError("registry hook: malformed response, expected a list")
    for index, service in enumerate(data):
        problems = [
            path
            for path in (
                "id",
                "name",
                "url",
                "version",
                "type.artifact",
                "type.version",
                "organization.name",
            )
            if not isinstance(lookup(service, path), str)
        ]
        problems += [
            path
            for path in ("environment", "documentationUrl", "organization.url")
            if lookup(service, path) is not None
            and not isinstance(lookup(service, path), str)
        ]
        if problems:
            raise PluginError(
                f"registry hook: malformed service at index {index}: "
                f"missing or invalid {', '.join(problems)}"
            )
    return data


def lookup(data: Any, path: str) -> Any:
    """Looks up a dotted path in nested dictionaries.

    Args:
        data: The data to look in.
        path: The path, e.g. `type.artifact`.

    Returns:
        The value, or None if any part of the path is missing.
    """
    for key in path.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def filter_services(
    services: list[dict[str, Any]], options: dict[str, str]
) -> list[dict[str, Any]]:
    """Selects and sorts the services that a marker asks for.

    Args:
        services: The services of the registry.
        options: The options of the marker.

    Returns:
        The matching services, sorted by type and name.
    """
    types = {
        value.strip().lower()
        for value in options.get("type", "").split(",")
        if value.strip()
    }
    environment = options["environment"].lower()
    selected = [
        service
        for service in services
        if (not types or service["type"]["artifact"].lower() in types)
        and (
            environment == ALL_ENVIRONMENTS
            or str(service.get("environment") or "").lower() == environment
        )
    ]
    return sorted(
        selected,
        key=lambda s: (s["type"]["artifact"].lower(), s["name"].lower(), s["id"]),
    )


def escape(text: str) -> str:
    """Escapes text for a cell of a Markdown table.

    Args:
        text: The text.

    Returns:
        The text with HTML and Markdown characters escaped and line breaks
        replaced by spaces.
    """
    text = " ".join(text.split())
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return MARKDOWN_SPECIAL.sub(r"\\\1", text)


def link(text: str, url: str | None) -> str:
    """Renders a link, or only the text if the URL is not http(s).

    Args:
        text: The text of the link.
        url: The target of the link.

    Returns:
        The Markdown of the link.
    """
    if not url or not SAFE_URL.match(url):
        return escape(text)
    # Encodes what would end the link or the table cell: spaces, `<>`, `()`,
    # `|`, quotes and backslashes
    target = urllib.parse.quote(url, safe=":/?#@!$&'*+,;=%~-._")
    return f"[{escape(text)}]({target})"


def artifact_name(artifact: str) -> str:
    """Spells a type artifact the way the docs do.

    Args:
        artifact: The artifact, e.g. `tes` or `service-registry`.

    Returns:
        Acronyms such as `tes` in capitals (`TES`), other names unchanged.
    """
    return artifact.upper() if artifact.isalnum() else artifact


def render_row(service: dict[str, Any]) -> str:
    """Renders one service as a row of the table.

    Args:
        service: The service.

    Returns:
        The Markdown row.
    """
    kind = service["type"]
    cells = [
        escape(service["name"]),
        link(service["organization"]["name"], service["organization"].get("url")),
        escape(f"{artifact_name(kind['artifact'])} {kind['version']}"),
        escape(service["version"]),
        escape(service.get("environment") or "–"),
        link(service["url"], service["url"]),
        link("Docs", service.get("documentationUrl"))
        if service.get("documentationUrl")
        else "–",
    ]
    return f"| {' | '.join(cells)} |"


def render_table(services: list[dict[str, Any]]) -> str:
    """Renders services as a Markdown table.

    Args:
        services: The services.

    Returns:
        The Markdown table, or a sentence if there are no services.
    """
    if not services:
        return "_No matching services are registered in the Cloud Registry._\n"
    rows = "\n".join(render_row(service) for service in services)
    return f"{HEADER}\n{rows}\n"
