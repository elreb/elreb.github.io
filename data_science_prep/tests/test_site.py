"""
Generic site-integrity tests for the data_science_prep book.

Covers three areas:
  1. Required files  — expected HTML pages and assets exist in docs/
  2. Local assets    — every <script src> / <link href> that is not a CDN
                       URL resolves to an actual file on disk
  3. Internal links  — every <a href="page.html[#anchor]"> whose file
                       portion is a relative .html path resolves to an
                       existing HTML file

Run
---
    python3 tests/test_site.py
"""

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

DOCS = Path(__file__).resolve().parent.parent / "docs"

EXPECTED_PAGES = [
    "index.html",
    "introduction.html",
    "sql-questions.html",
    "python-r-analyses.html",
    "computer-science-data-scructures-and-algorithms.html",
    "statistics-and-machine-learning.html",
    "case-studies.html",
    "style.css",
]


# ---------------------------------------------------------------------------
# Tiny HTML parser that collects hrefs, script srcs, and link hrefs
# ---------------------------------------------------------------------------

class _AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []       # <a href>
        self.scripts: list[str] = []     # <script src>
        self.stylesheets: list[str] = [] # <link rel=stylesheet href>

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
        elif tag == "script" and "src" in d:
            self.scripts.append(d["src"])
        elif tag == "link" and d.get("rel") == "stylesheet" and "href" in d:
            self.stylesheets.append(d["href"])


def _parse(html_path: Path) -> _AssetParser:
    p = _AssetParser()
    p.feed(html_path.read_text(encoding="utf-8", errors="replace"))
    return p


def _is_external(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


def _is_anchor_only(url: str) -> bool:
    return url.startswith("#")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRequiredFiles(unittest.TestCase):
    """docs/ must contain all expected chapter pages and the stylesheet."""

    def test_expected_pages_exist(self):
        for name in EXPECTED_PAGES:
            with self.subTest(file=name):
                self.assertTrue(
                    (DOCS / name).exists(),
                    f"docs/{name} is missing — chapter page or stylesheet was deleted or renamed.",
                )

    def test_libs_directory_exists(self):
        self.assertTrue(
            (DOCS / "libs").is_dir(),
            "docs/libs/ is missing — gitbook JS/CSS assets will 404.",
        )


class TestLocalAssets(unittest.TestCase):
    """Every locally-referenced script and stylesheet must exist on disk.

    CDN URLs (http/https) are skipped; only relative paths are checked.
    A missing local asset causes a silent 404 that is easy to miss.
    """

    def _check_assets(self, html_path: Path, urls: list[str], kind: str):
        for url in urls:
            if _is_external(url) or _is_anchor_only(url):
                continue
            resolved = (html_path.parent / url).resolve()
            with self.subTest(file=html_path.name, asset=url):
                self.assertTrue(
                    resolved.exists(),
                    f"{html_path.name}: {kind} '{url}' does not exist at {resolved}.",
                )

    def test_scripts_resolve(self):
        for html_path in sorted(DOCS.glob("*.html")):
            parsed = _parse(html_path)
            self._check_assets(html_path, parsed.scripts, "script src")

    def test_stylesheets_resolve(self):
        for html_path in sorted(DOCS.glob("*.html")):
            parsed = _parse(html_path)
            self._check_assets(html_path, parsed.stylesheets, "stylesheet href")


class TestInternalLinks(unittest.TestCase):
    """Every relative <a href> that points to an .html file must resolve to a
    file that actually exists.  Anchor fragments (#section) are ignored —
    only the file portion is checked.

    This catches renames like renaming a chapter file without updating all
    navigation links to it.
    """

    def test_cross_page_links_resolve(self):
        for html_path in sorted(DOCS.glob("*.html")):
            parsed = _parse(html_path)
            for href in parsed.links:
                if _is_external(href) or _is_anchor_only(href):
                    continue
                # Strip fragment and query string; keep only the file path
                file_part = href.split("#")[0].split("?")[0]
                if not file_part.endswith(".html"):
                    continue
                resolved = (html_path.parent / file_part).resolve()
                with self.subTest(source=html_path.name, href=href):
                    self.assertTrue(
                        resolved.exists(),
                        f"{html_path.name}: link '{href}' → {resolved} does not exist.",
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
