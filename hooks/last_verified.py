"""MkDocs hook that checks the `last_verified` dates of the fact pages.

Pages with operational facts carry `last_verified` in their front matter: the
date when someone last verified those facts against their sources
(`YYYY-MM-DD`, which YAML reads as a date), or `null` until someone has. The
page shows it at its end (`overrides/partials/content.html`). Any other value
fails the build, so that no page shows a malformed date as verified.
"""

from __future__ import annotations

import datetime
from typing import Any

from mkdocs.exceptions import PluginError
from mkdocs.structure.pages import Page


def on_page_markdown(markdown: str, *, page: Page, **kwargs: Any) -> str:
    """Fails the build if `last_verified` is neither a date nor `null`.

    Args:
        markdown: The Markdown of the page, returned unchanged.
        page: The page, with its front matter in `meta`.
        **kwargs: The other arguments of the event, unused.

    Returns:
        The Markdown of the page.

    Raises:
        PluginError: If `last_verified` is set to anything but a date
            (without time) or `null`.
    """
    if "last_verified" not in page.meta:
        return markdown
    value = page.meta["last_verified"]
    if value is None or (
        isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)
    ):
        return markdown
    raise PluginError(
        f"last_verified hook: {page.file.src_uri}: `last_verified` must be a "
        f"date (YYYY-MM-DD, unquoted) or null, not {value!r}"
    )
