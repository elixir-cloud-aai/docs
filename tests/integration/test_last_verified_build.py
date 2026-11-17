"""Builds a small site with the theme overrides and checks the "last verified" note.

Pages with operational facts carry `last_verified` in their front matter: a
date, or `null` until someone has verified them. The override of the
`content` partial in `overrides/partials/` shows it at the end of the page;
the hook `hooks/last_verified.py` fails the build on any other value.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort

ROOT = Path(__file__).parent.parent.parent
OVERRIDES = ROOT / "overrides"
HOOK = ROOT / "hooks" / "last_verified.py"

PAGES = {
    "verified.md": "---\nlast_verified: 2026-11-17\n---\n\n# Verified\n",
    "unverified.md": "---\nlast_verified: null\n---\n\n# Unverified\n",
    "other.md": "# Other\n",
}


def build_site(tmp_path: Path, pages: dict[str, str]) -> Path:
    """Builds a site with the overrides and the hook, strictly.

    Args:
        tmp_path: Directory to write to.
        pages: The Markdown of each page, by file name.

    Returns:
        The directory of the built site.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, text in pages.items():
        (docs / name).write_text(text, encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: Test\n"
        f"theme: {{name: material, custom_dir: '{OVERRIDES}'}}\n"
        f"hooks: ['{HOOK}']\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config), strict=True)
    build(cfg)
    return Path(cfg.site_dir)


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Builds a site with one page of each kind.

    Args:
        tmp_path_factory: Factory of temporary directories.

    Returns:
        The directory of the built site.
    """
    return build_site(tmp_path_factory.mktemp("site"), PAGES)


def read_page(site: Path, name: str) -> str:
    """Reads a built page.

    Args:
        site: The directory of the built site.
        name: The name of the page, without `.md`.

    Returns:
        The HTML of the page.
    """
    return (site / name / "index.html").read_text(encoding="utf-8")


def test_shows_date(site: Path) -> None:
    """Shows the date of a verified page, as a machine-readable `time`."""
    html = read_page(site, "verified")
    assert 'class="md-source-file last-verified"' in html
    assert '<time datetime="2026-11-17">2026-11-17</time>' in html
    assert "not verified yet" not in html


def test_shows_not_verified(site: Path) -> None:
    """Says so on a page whose facts haven't been verified yet."""
    html = read_page(site, "unverified")
    assert 'class="md-source-file last-verified"' in html
    assert "Facts not verified yet" in html
    assert "<time" not in html


def test_leaves_other_pages_alone(site: Path) -> None:
    """Adds nothing to pages without `last_verified`."""
    html = read_page(site, "other")
    assert "last-verified" not in html


@pytest.mark.parametrize(
    "value",
    [
        "'2026-11-17'",
        "17.11.2026",
        "never",
        "2026-13-01",
        "2026-11-17T10:00:00Z",
        "2026-11-17 10:00",
        "2026-1-5",
    ],
)
def test_fails_on_malformed_date(
    tmp_path: Path, value: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Fails the build for a value that isn't a date or `null`, as YAML reads it."""
    with pytest.raises(Abort):
        build_site(tmp_path, {"bad.md": f"---\nlast_verified: {value}\n---\n\n# Bad\n"})
    assert "last_verified hook: bad.md" in caplog.text
