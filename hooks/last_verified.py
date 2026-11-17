"""MkDocs hook that checks the `last_verified` dates of the fact pages.

Pages with operational facts carry `last_verified` in their front matter: the
date when someone last verified those facts against their sources
(`YYYY-MM-DD`, which YAML reads as a date), or `null` until someone has. The
page shows it at its end (`overrides/partials/content.html`). Any other value
fails the build, so that no page shows a malformed date as verified.

An impossible date, such as `2026-13-01`, makes YAML fail, and MkDocs then
drops the whole front matter of the page without a warning and leaves it in
the Markdown. The hook catches that case too.
"""

from __future__ import annotations

import datetime
import re
from typing import Any

from mkdocs.exceptions import PluginError
from mkdocs.structure.pages import Page
from mkdocs.utils.meta import YAML_RE

KEY_RE = re.compile(r"^last_verified\s*:", re.MULTILINE)


def on_page_markdown(markdown: str, *, page: Page, **kwargs: Any) -> str:
    """Fails the build if `last_verified` is neither a date nor `null`.

    Args:
        markdown: The Markdown of the page, returned unchanged. It still
            starts with the front matter if MkDocs couldn't read it.
        page: The page, with its front matter in `meta`.
        **kwargs: The other arguments of the event, unused.

    Returns:
        The Markdown of the page.

    Raises:
        PluginError: If `last_verified` is set to anything but a date
            (without time) or `null`, or the front matter that sets it can't
            be read.
    """
    where = f"last_verified hook: {page.file.src_uri}"
    if "last_verified" not in page.meta:
        front_matter = YAML_RE.match(markdown)
        if front_matter and KEY_RE.search(front_matter.group(1)):
            raise PluginError(
                f"{where}: the front matter can't be read, e.g., because of an "
                "impossible date in `last_verified`"
            )
        return markdown
    value = page.meta["last_verified"]
    if value is None or (
        isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)
    ):
        return markdown
    raise PluginError(
        f"{where}: `last_verified` must be a date (YYYY-MM-DD, unquoted) or "
        f"null, not {value!r}"
    )
