"""Tests of the hook `hooks/last_verified.py`."""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from last_verified import on_page_markdown
from mkdocs.exceptions import PluginError


def make_page(meta: dict[str, Any]) -> MagicMock:
    """Builds a page with the given front matter.

    Args:
        meta: The front matter of the page.

    Returns:
        A stand-in for an MkDocs page.
    """
    page = MagicMock()
    page.meta = meta
    page.file.src_uri = "operators/page.md"
    return page


@pytest.mark.parametrize(
    "meta",
    [
        {},
        {"title": "Other"},
        {"last_verified": None},
        {"last_verified": datetime.date(2026, 11, 17)},
    ],
)
def test_accepts_valid_values(meta: dict[str, Any]) -> None:
    """Leaves the Markdown of pages without the key or with valid values."""
    assert on_page_markdown("# Page\n", page=make_page(meta)) == "# Page\n"


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-17",
        "17.11.2026",
        "never",
        "",
        False,
        20261117,
        datetime.datetime(2026, 11, 17, 12, 0),
    ],
)
def test_refuses_malformed_values(value: object) -> None:
    """Fails the build for anything but a date or `null`, naming the page."""
    with pytest.raises(PluginError, match="operators/page.md"):
        on_page_markdown("# Page\n", page=make_page({"last_verified": value}))


def test_refuses_unreadable_front_matter() -> None:
    """Fails the build if MkDocs dropped front matter that sets the key."""
    markdown = "---\nlast_verified: 2026-13-01\n---\n\n# Page\n"
    with pytest.raises(PluginError, match="can't be read"):
        on_page_markdown(markdown, page=make_page({}))


@pytest.mark.parametrize(
    "markdown",
    [
        "---\ntitle: x: y\n---\n\n# Page\n",
        "# Page\n\nlast_verified: 2026-13-01\n",
    ],
)
def test_ignores_other_unread_text(markdown: str) -> None:
    """Leaves pages alone whose unread front matter or text has no key."""
    assert on_page_markdown(markdown, page=make_page({})) == markdown
