"""Checks the GA4GH service URLs in the docs against the Cloud Registry.

The script collects the URLs of GA4GH services (`<base>/ga4gh/<api>/v<n>`,
with any path after it) from the docs and reports each service that

- is not in the Cloud Registry (unless `service-check.toml` lists it under
  `unregistered`, with a reason), or
- does not answer `GET <url>/service-info` with a JSON object.

It also reports entries of `unregistered` that are no longer needed: the
service is registered now, or no page names it any more. Placeholders
(`example.org`, `<HOST>`, `localhost`, `127.0.0.1`, names without a dot) and
the hosts in `skip_hosts` of `service-check.toml` (public third-party
services) are skipped.

Usage:
    python scripts/check_services.py [--config FILE] [--registry URL]
        [--output FILE] [PATH ...]

Without paths, the script checks `README.md`, `docs` and `includes`. The
registry defaults to `extra.registry_url` of `mkdocs.yml`. The report, in
Markdown, goes to standard output and, with `--output`, to a file.

Exit status: 0 if all services are fine, 2 if the report lists problems,
1 if the check could not run (e.g. the registry can't be reached or the
configuration is invalid).
"""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PATHS = ["README.md", "docs", "includes"]
DEFAULT_CONFIG = "service-check.toml"
MKDOCS_CONFIG = "mkdocs.yml"
SUFFIXES = {".md"}
TIMEOUT = 15
ATTEMPTS = 2
RETRY_DELAY = 2.0
MAX_BYTES = 5 * 1024 * 1024
CHUNK_BYTES = 64 * 1024

# Characters that end a URL in Markdown, HTML and shell examples. A `}`
# right after the host is allowed for defaults such as `${TES:-https://h}`
STOP = r"\s/<>\"'`()\[\]{}|\\"
SERVICE_URL = re.compile(
    rf"(?P<scheme>https?)://(?P<host>[^{STOP}]+)\}}?"
    rf"(?P<prefix>(?:/[^{STOP}]+?)*?)"
    r"/ga4gh/(?P<api>[a-z][a-z0-9-]*)/v(?P<version>[0-9]+)(?![\w-]|\.\w)",
    re.IGNORECASE,
)
# `registry_url: <url>` in `mkdocs.yml`, the URL plain or quoted, with an
# optional comment
REGISTRY_URL = re.compile(
    r"^[ \t]+registry_url:[ \t]*(?P<quote>[\"']?)(?P<url>[^\s\"'#]+)(?P=quote)"
    r"[ \t]*(?:#.*)?$",
    re.MULTILINE,
)
# Domains reserved for documentation and testing (RFC 2606, RFC 6761), and
# local and in-cluster names
PLACEHOLDER_TLDS = {"example", "internal", "invalid", "local", "localhost", "test"}
IN_CLUSTER_SUFFIXES = (".svc", ".svc.cluster.local")
DEFAULT_PORTS = {"http": "80", "https": "443"}
PLACEHOLDER_DOMAINS = {"example.com", "example.net", "example.org"}


class CheckError(Exception):
    """The check could not run, e.g. the registry can't be reached."""


@dataclass(frozen=True)
class Config:
    """Configuration of the check (`service-check.toml`).

    Attributes:
        skip_hosts: Hosts (and their subdomains) that are not checked.
        unregistered: Service URLs that need not be in the registry, each
            with the reason.
    """

    skip_hosts: frozenset[str] = frozenset()
    unregistered: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    """A problem with a service URL.

    Attributes:
        url: The base URL of the service.
        problem: What is wrong.
        locations: Where the docs name the URL (`file:line`).
    """

    url: str
    problem: str
    locations: tuple[str, ...] = ()


def normalize(url: str) -> str | None:
    """Returns the base URL of a GA4GH service, without the path after it.

    Args:
        url: A URL, e.g. `https://h/ga4gh/tes/v1/tasks`.

    Returns:
        The base URL, e.g. `https://h/ga4gh/tes/v1`, with scheme and host in
        lower case; None if the URL is not one of a GA4GH service.
    """
    match = SERVICE_URL.search(url)
    if match is None:
        return None
    return base_url(match)


def base_url(match: re.Match[str]) -> str:
    """Builds the base URL of a service from a match of `SERVICE_URL`.

    Args:
        match: The match.

    Returns:
        The base URL, with scheme and host in lower case, without user info
        and default port.
    """
    scheme = match["scheme"].lower()
    host = match["host"].lower().rsplit("@", 1)[-1]
    host = host.removesuffix(f":{DEFAULT_PORTS[scheme]}")
    # Fully qualified names may end with a dot, before the port if any
    name, colon, port = host.partition(":")
    host = f"{name.rstrip('.')}{colon}{port}"
    return (
        f"{scheme}://{host}{match['prefix']}"
        f"/ga4gh/{match['api'].lower()}/v{match['version']}"
    )


def hostname(url: str) -> str:
    """Returns the host of a URL, without user info and port.

    Args:
        url: The URL.

    Returns:
        The host in lower case.
    """
    netloc = url.split("://", 1)[-1].split("/", 1)[0].rsplit("@", 1)[-1]
    if netloc.startswith("["):
        return netloc[1:].split("]", 1)[0].lower()
    return netloc.split(":", 1)[0].lower()


def placeholder(host: str) -> bool:
    """Tells whether a host is a placeholder or local.

    Args:
        host: The host, in lower case and without port.

    Returns:
        True for reserved example and test domains, `localhost`, local and
        in-cluster names (`.local`, `.internal`, `.svc`, names without a
        dot, which also covers shell variables), loopback, private,
        link-local and unspecified addresses (also in numeric shorthand
        such as `127.1`), and hosts with template characters.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Shorthands such as `127.1`, which resolvers accept
        if re.fullmatch(r"[0-9.]+", host):
            return True
    else:
        return (
            address.is_loopback
            or address.is_private
            or address.is_link_local
            or address.is_unspecified
        )
    if "." not in host or any(char in host for char in "%$*"):
        return True
    if host.rstrip(".").endswith(IN_CLUSTER_SUFFIXES):
        return True
    labels = host.rstrip(".").split(".")
    return labels[-1] in PLACEHOLDER_TLDS or ".".join(labels[-2:]) in (
        PLACEHOLDER_DOMAINS
    )


def skipped(url: str, skip_hosts: Iterable[str]) -> bool:
    """Tells whether a service URL is left out of the check.

    Args:
        url: The base URL of the service.
        skip_hosts: Hosts that are skipped with their subdomains.

    Returns:
        True for placeholders and skipped hosts.
    """
    host = hostname(url)
    return placeholder(host) or any(
        host == skip or host.endswith(f".{skip}") for skip in skip_hosts
    )


def collect(files: Iterable[Path]) -> dict[str, list[str]]:
    """Collects the service URLs named in files.

    Args:
        files: The files to read.

    Returns:
        For each base URL, where it is named (`file:line`), in order.
    """
    mentions: dict[str, list[str]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in SERVICE_URL.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            mentions.setdefault(base_url(match), []).append(f"{path}:{line}")
    return mentions


def find_files(args: Iterable[str], suffixes: Iterable[str] = SUFFIXES) -> list[Path]:
    """Lists the files of the given paths, e.g. the Markdown files.

    Args:
        args: Files and directories.
        suffixes: Suffixes of the files to list in directories.

    Returns:
        The files, directories expanded in sorted order.

    Raises:
        CheckError: If a path does not exist.
    """
    files: list[Path] = []
    for arg in args:
        path = Path(arg)
        if path.is_dir():
            files += sorted(p for p in path.rglob("*") if p.suffix in suffixes)
        elif path.is_file():
            files.append(path)
        else:
            raise CheckError(f"{arg}: no such file or directory")
    return files


def load_config(path: Path) -> Config:
    """Reads and validates the configuration.

    Args:
        path: The configuration file (TOML).

    Returns:
        The configuration.

    Raises:
        CheckError: If the file can't be read or is invalid.
    """
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CheckError(f"{path}: {exc}") from exc
    unknown = set(data) - {"skip_hosts", "unregistered"}
    if unknown:
        raise CheckError(f"{path}: unknown keys {', '.join(sorted(unknown))}")
    skip_hosts = data.get("skip_hosts", [])
    if not isinstance(skip_hosts, list) or not all(
        isinstance(host, str) and host for host in skip_hosts
    ):
        raise CheckError(f"{path}: skip_hosts must be a list of host names")
    unregistered = data.get("unregistered", {})
    if not isinstance(unregistered, dict):
        raise CheckError(f"{path}: unregistered must be a table")
    for url, reason in unregistered.items():
        if not isinstance(reason, str) or not reason:
            raise CheckError(f"{path}: unregistered: {url} needs a reason")
        if normalize(url) != url:
            raise CheckError(
                f"{path}: unregistered: {url} is not the base URL of a "
                f"service, e.g. https://host/ga4gh/tes/v1"
            )
    return Config(
        skip_hosts=frozenset(host.lower() for host in skip_hosts),
        unregistered=dict(unregistered),
    )


def default_registry(path: Path) -> str:
    """Reads the registry URL from `extra.registry_url` of `mkdocs.yml`.

    Args:
        path: The MkDocs configuration.

    Returns:
        The registry URL, without a trailing slash.

    Raises:
        CheckError: If the file or the setting is missing.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckError(f"{path}: {exc}") from exc
    match = REGISTRY_URL.search(text)
    if match is None:
        raise CheckError(f"{path}: no registry_url; pass --registry")
    return match["url"].rstrip("/")


class Redirects(urllib.request.HTTPRedirectHandler):
    """Follows redirects, except to placeholder and local hosts."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Refuses a redirect to a placeholder or local host.

        Args:
            req: The request that was redirected.
            fp: The response.
            code: The HTTP status of the redirect.
            msg: The reason of the status.
            headers: The headers of the response.
            newurl: The target of the redirect.

        Returns:
            The request to the target, or None to refuse it, which fails
            the fetch with the status of the redirect.
        """
        if placeholder(hostname(newurl)):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(Redirects)


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    secret_headers: dict[str, str] | None = None,
) -> Any:
    """Fetches and decodes a JSON document, with one retry.

    Network errors, timeouts, HTTP 429 and 5xx responses are retried once.

    Args:
        url: The URL to fetch.
        headers: Request headers in addition to the defaults (`Accept:
            application/json`, a `User-Agent`), which they may replace.
        secret_headers: Request headers that are not sent again when the
            server redirects, e.g. `Authorization`.

    Returns:
        The decoded document.

    Raises:
        CheckError: If the fetch fails or the response is not JSON.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "elixir-on-cloud-docs-checks",
                    **(headers or {}),
                },
            )
            for name, value in (secret_headers or {}).items():
                request.add_unredirected_header(name, value)
            with OPENER.open(request, timeout=TIMEOUT) as response:
                body = read(response, time.monotonic() + TIMEOUT)
            break
        except (OSError, ValueError, http.client.HTTPException) as exc:
            # OSError includes URLError, HTTPError and timeouts
            if attempt == ATTEMPTS or not transient(exc):
                raise CheckError(describe(exc)) from exc
            time.sleep(RETRY_DELAY)
    if len(body) > MAX_BYTES:
        raise CheckError(f"response larger than {MAX_BYTES} bytes")
    try:
        return json.loads(body)
    except (ValueError, RecursionError) as exc:
        raise CheckError("response is not JSON") from exc


def read(response: Any, deadline: float) -> bytes:
    """Reads a response body in chunks, within a deadline and a size limit.

    The timeout of `open` applies to each socket operation only, so a server
    that sends a trickle of data could stall the check without the deadline.

    Args:
        response: The response to read.
        deadline: The `time.monotonic()` value by which the body must be
            read.

    Returns:
        The body, or its first `MAX_BYTES + 1` bytes if it is larger.

    Raises:
        TimeoutError: If the deadline passes before the body is read.
    """
    chunks: list[bytes] = []
    size = 0
    while size <= MAX_BYTES:
        if time.monotonic() > deadline:
            raise TimeoutError(f"response not read within {TIMEOUT} s")
        chunk = response.read(min(CHUNK_BYTES, MAX_BYTES + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks)


def transient(error: Exception) -> bool:
    """Tells whether a failed fetch is worth a retry.

    Args:
        error: The error of the fetch.

    Returns:
        True for network errors, timeouts and HTTP 429 and 5xx responses.
    """
    if isinstance(error, urllib.error.HTTPError):
        return error.code == 429 or error.code >= 500
    return not isinstance(error, ValueError)


def describe(error: Exception) -> str:
    """Describes a failed fetch in a few words.

    Args:
        error: The error of the fetch.

    Returns:
        E.g. `HTTP 404` or the reason of a network error.
    """
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    if isinstance(error, urllib.error.URLError):
        return str(error.reason)
    return str(error) or type(error).__name__


def registered_urls(registry: str) -> set[str]:
    """Fetches the base URLs of the services in the registry.

    Args:
        registry: The base URL of the registry.

    Returns:
        The base URLs of all services, in every environment.

    Raises:
        CheckError: If the registry can't be reached or its answer is not a
            list of services.
    """
    try:
        services = fetch_json(f"{registry}/services")
    except CheckError as exc:
        raise CheckError(f"registry {registry}: {exc}") from exc
    if not isinstance(services, list):
        raise CheckError(f"registry {registry}: expected a list of services")
    urls = set()
    for service in services:
        url = service.get("url") if isinstance(service, dict) else None
        base = normalize(url) if isinstance(url, str) else None
        if base is not None:
            urls.add(base)
    return urls


def probe_service_info(url: str) -> str | None:
    """Checks that a service answers `GET <url>/service-info`.

    Args:
        url: The base URL of the service.

    Returns:
        None if the service answers with a JSON object, otherwise the
        problem.
    """
    try:
        info = fetch_json(f"{url}/service-info")
    except CheckError as exc:
        return f"`service-info` failed: {exc}"
    if not isinstance(info, dict):
        return "`service-info` is not a JSON object"
    return None


def check(
    mentions: dict[str, list[str]],
    registered: set[str],
    config: Config,
    probe: Callable[[str], str | None] = probe_service_info,
) -> tuple[list[Finding], int]:
    """Checks the service URLs named in the docs.

    Args:
        mentions: Where each base URL is named, from `collect`.
        registered: The base URLs in the registry.
        config: The configuration.
        probe: Checks the `service-info` of a service.

    Returns:
        The findings, and the number of services checked.
    """
    findings = []
    checked = 0
    for url, locations in sorted(mentions.items()):
        if skipped(url, config.skip_hosts):
            continue
        checked += 1
        where = tuple(locations)
        if url not in registered and url not in config.unregistered:
            findings.append(Finding(url, "not in the Cloud Registry", where))
        problem = probe(url)
        if problem is not None:
            findings.append(Finding(url, problem, where))
    for url in sorted(config.unregistered):
        if url in registered:
            findings.append(
                Finding(url, "registered now; remove it from `unregistered`")
            )
        elif url not in mentions:
            findings.append(
                Finding(url, "no page names it; remove it from `unregistered`")
            )
    return findings, checked


def report(findings: list[Finding], checked: int) -> str:
    """Renders the findings as Markdown.

    Args:
        findings: The findings.
        checked: The number of services checked.

    Returns:
        The report.
    """
    summary = f"Checked {checked} service URLs named in the docs."
    if not findings:
        return f"{summary} No problems found.\n"
    lines = [
        (
            f"{summary} Found {len(findings)} problems (configuration: "
            "`service-check.toml`):"
        ),
        "",
    ]
    for finding in findings:
        lines.append(f"- `{finding.url}`: {finding.problem}")
        lines += [f"  - `{location}`" for location in finding.locations]
    return "\n".join(lines) + "\n"


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parses the command line.

    Args:
        args: The arguments, without the program name.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Check the GA4GH service URLs in the docs."
    )
    parser.add_argument("paths", nargs="*", help="files and directories")
    parser.add_argument("--config", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--registry", help="base URL of the Cloud Registry")
    parser.add_argument("--output", type=Path, help="also write the report here")
    return parser.parse_args(args)


def main(args: list[str]) -> int:
    """Runs the check.

    Args:
        args: The command line arguments, without the program name.

    Returns:
        The exit status: 0 without problems, 2 with problems, 1 if the
        check could not run.
    """
    options = parse_args(args)
    try:
        config = load_config(options.config)
        files = find_files(options.paths or DEFAULT_PATHS)
        registry = options.registry or default_registry(Path(MKDOCS_CONFIG))
        registered = registered_urls(registry.rstrip("/"))
        mentions = collect(files)
    except (CheckError, OSError, UnicodeDecodeError) as exc:
        # OSError and UnicodeDecodeError: a file of the docs can't be read
        print(f"error: {exc}", file=sys.stderr)
        return 1
    findings, checked = check(mentions, registered, config)
    text = report(findings, checked)
    print(text, end="")
    if options.output is not None:
        try:
            options.output.parent.mkdir(parents=True, exist_ok=True)
            options.output.write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"error: {options.output}: {exc}", file=sys.stderr)
            return 1
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
