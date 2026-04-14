"""
Regression tests for interactive-block CSS layout.

Background
----------
All three interactive chapters (2-SQL, 3-Python, 6-CS) create
.interactive-python-block elements via JavaScript.

Two bugs were fixed:

1. Viewport-breakout positioning (position:relative + left:50% +
   margin-left based on 100vw) shifted blocks off-screen whenever the
   gitbook sidebar changed the parent/viewport width ratio.  Fix: remove
   that positioning from the CSS class entirely.

2. The editor textarea used width:80ch while the wrapper used width:84ch,
   but these resolve via *different* font-size contexts (wrapper inherits
   section's 1.6rem; editor uses its own explicit 0.95rem monospace font).
   Because html{font-size:62.5%} makes 1rem=10px, the monospace ch is much
   smaller than the section ch, leaving the editor narrow in its container.
   Fix: CSS class sets width:84ch on the wrapper (so it doesn't collapse to
   full column width when JS inline style is absent), and editor uses
   width:100% to always fill the wrapper regardless of ch unit context.

Run
---
    python3 tests/test_interactive_layout.py
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS_CSS = REPO / "docs" / "style.css"
SRC_CSS = REPO / "style.css"

CHAPTER_HTMLS = {
    "python-r-analyses": REPO / "docs" / "python-r-analyses.html",
    "computer-science-data-scructures-and-algorithms": (
        REPO / "docs" / "computer-science-data-scructures-and-algorithms.html"
    ),
    "sql-questions": REPO / "docs" / "sql-questions.html",
}

REQUIRED_WIDTH_OVERRIDES = {
    "python-r-analyses": [
        r"wrapper\.style\.width\s*=\s*['\"]84ch['\"]",
    ],
    "computer-science-data-scructures-and-algorithms": [
        r"block\.style\.width\s*=\s*['\"]84ch['\"]",
    ],
    "sql-questions": [
        r"wrapper\.style\.width\s*=\s*['\"]84ch['\"]",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_first_rule(css_text: str, selector: str) -> str:
    pattern = re.escape(selector) + r"\s*\{([^}]*)\}"
    m = re.search(pattern, css_text)
    return m.group(1) if m else ""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInteractiveBlockCSSRule(unittest.TestCase):
    """The .interactive-python-block CSS class must not use viewport-relative
    positioning and must set a safe width that doesn't depend on JS alone."""

    def _rule(self, path: Path) -> str:
        rule = _extract_first_rule(path.read_text(), ".interactive-python-block")
        self.assertTrue(rule, f"Could not find .interactive-python-block rule in {path}")
        return rule

    def test_no_left_50_percent(self):
        """`left: 50%` must not appear (parent-width offset causes off-screen shift)."""
        for path in (DOCS_CSS, SRC_CSS):
            with self.subTest(file=path.name):
                self.assertNotIn("left: 50%", self._rule(path),
                    f"{path.name}: `left: 50%` re-introduced — shifts blocks left "
                    "when parent container is narrower than viewport (sidebar open).")

    def test_no_100vw_in_rule(self):
        """`100vw` must not appear (viewport units break layout when sidebar open)."""
        for path in (DOCS_CSS, SRC_CSS):
            with self.subTest(file=path.name):
                self.assertNotIn("100vw", self._rule(path),
                    f"{path.name}: `100vw` re-introduced.")

    def test_no_negative_margin_left_calc(self):
        """`margin-left: calc(-1 *` must not appear (the specific broken pattern)."""
        for path in (DOCS_CSS, SRC_CSS):
            with self.subTest(file=path.name):
                self.assertNotIn("margin-left: calc(-1 *", self._rule(path),
                    f"{path.name}: negative-calc margin-left re-introduced.")

    def test_css_class_sets_width(self):
        """CSS class must set an explicit width so blocks don't default to full
        column width when the JS inline style is absent or overridden.

        The width must be 84ch (uses section font context, not tiny monospace ch)
        and max-width must be 100% so it stays responsive.
        """
        for path in (DOCS_CSS, SRC_CSS):
            with self.subTest(file=path.name):
                rule = self._rule(path)
                self.assertIn("width: 84ch", rule,
                    f"{path.name}: .interactive-python-block missing `width: 84ch` — "
                    "without this, blocks default to full column width when JS inline "
                    "style doesn't apply.")
                self.assertIn("max-width: 100%", rule,
                    f"{path.name}: .interactive-python-block missing `max-width: 100%` — "
                    "needed to keep the block responsive on narrow viewports.")


class TestEditorFillsWrapper(unittest.TestCase):
    """The editor textarea must use width:100% (not a fixed ch value).

    The wrapper uses the section font (1.6rem) for ch units; the editor
    has its own explicit monospace font (0.95rem).  With html{font-size:62.5%}
    making 1rem=10px, the monospace ch is much smaller than the section ch,
    so a fixed '80ch' editor ends up narrower than an '84ch' wrapper.
    Using 100% on the editor ensures it always fills the wrapper.
    """

    def test_legacy_editor_css_uses_100_percent(self):
        """.legacy-analysis-block .interactive-python-editor must use width:100%."""
        for path in (DOCS_CSS, SRC_CSS):
            with self.subTest(file=path.name):
                rule = _extract_first_rule(
                    path.read_text(), ".legacy-analysis-block .interactive-python-editor"
                )
                self.assertTrue(rule,
                    f"{path.name}: no .legacy-analysis-block .interactive-python-editor rule")
                self.assertNotIn("80ch", rule,
                    f"{path.name}: editor still uses 80ch — mismatches wrapper's 84ch "
                    "because section-font ch != monospace-font ch.")
                self.assertIn("width: 100%", rule,
                    f"{path.name}: editor must use width:100% to fill wrapper.")

    def test_js_editor_width_is_100_percent(self):
        """JS block-creators must set editor width to 100%, not a fixed ch value."""
        for stem, html_path in CHAPTER_HTMLS.items():
            self.assertTrue(html_path.exists(), f"HTML file not found: {html_path}")
            html_text = html_path.read_text()
            with self.subTest(file=stem):
                self.assertNotIn(
                    '"80ch"', html_text,
                    f"{html_path.name}: JS still sets editor width to '80ch'. "
                    "Change to '100%' so editor fills its wrapper regardless of font context."
                )
                self.assertNotIn(
                    "'80ch'", html_text,
                    f"{html_path.name}: JS still sets editor width to '80ch'. "
                    "Change to '100%' so editor fills its wrapper regardless of font context."
                )


class TestCSSSourceDocSync(unittest.TestCase):
    """style.css and docs/style.css must stay in sync for the key rules."""

    def _check_rule_sync(self, selector: str):
        src = _normalise(_extract_first_rule(SRC_CSS.read_text(), selector))
        docs = _normalise(_extract_first_rule(DOCS_CSS.read_text(), selector))
        self.assertTrue(src, f"No '{selector}' rule in style.css")
        self.assertTrue(docs, f"No '{selector}' rule in docs/style.css")
        self.assertEqual(src, docs,
            f"style.css and docs/style.css have diverged for '{selector}'.\n"
            f"  style.css:      {src}\n"
            f"  docs/style.css: {docs}")

    def test_interactive_block_rule_matches(self):
        self._check_rule_sync(".interactive-python-block")

    def test_legacy_editor_rule_matches(self):
        self._check_rule_sync(".legacy-analysis-block .interactive-python-editor")


class TestJSBlockCreatorsSetExplicitWidth(unittest.TestCase):
    """JS block-creation functions must set explicit wrapper width inline.

    Even though the CSS class now sets width:84ch, the inline style acts as
    a second guarantee and documents the intended size at the call site.
    """

    def test_all_chapters_set_width_inline(self):
        for stem, patterns in REQUIRED_WIDTH_OVERRIDES.items():
            html_path = CHAPTER_HTMLS[stem]
            self.assertTrue(html_path.exists(), f"HTML file not found: {html_path}")
            html_text = html_path.read_text()
            for pattern in patterns:
                with self.subTest(file=stem, pattern=pattern):
                    self.assertTrue(
                        re.search(pattern, html_text),
                        f"{html_path.name}: JS block creator no longer sets inline "
                        f"width matching `{pattern}`."
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
