#!/usr/bin/env python3
"""
Unit tests for the profile-dashboard generator.

Covers the two parts of assets/generate.py + assets/facts.py that are
actually deterministic and testable offline: the hand-curated data in
facts.py (structural/consistency checks — e.g. every flagship's domain
is a real axis on the radar chart) and the squarified-treemap layout
math in generate.py (pure geometry — no network, no GitHub API).

Everything that depends on live GitHub data (gather(), the api() calls)
is intentionally out of scope here: it isn't reachable without a token
and a network connection, and generate.py already degrades gracefully
(falls back to last-verified constants) if that data is unavailable.

Stdlib only, matching the rest of this repo. Run with:
    python3 -m unittest assets/test_dashboard.py -v
or, from inside assets/:
    python3 -m unittest test_dashboard -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts    # noqa: E402
import generate  # noqa: E402


class TestFactsIntegrity(unittest.TestCase):
    """facts.py is hand-curated and feeds several SVG panels directly off
    its shape (radar axes, domain colors, network clusters). If it drifts
    out of internal consistency the dashboard renders silently wrong
    (e.g. a flagship plotted on a radar axis that doesn't exist) rather
    than erroring, so it's worth pinning down with real assertions."""

    def test_every_flagship_domain_is_a_known_axis(self):
        known = set(facts.DOMAINS)
        for f in facts.FLAGSHIPS:
            self.assertIn(
                f["domain"], known,
                f"{f['name']!r} has domain {f['domain']!r}, "
                f"which isn't in facts.DOMAINS {sorted(known)}",
            )

    def test_every_domain_has_at_least_one_flagship(self):
        # An axis with zero repos would render a degenerate (zero-area)
        # spoke on the radar chart.
        used = {f["domain"] for f in facts.FLAGSHIPS}
        for domain in facts.DOMAINS:
            self.assertIn(domain, used, f"domain {domain!r} has no flagship repos")

    def test_flagship_names_are_unique(self):
        names = [f["name"] for f in facts.FLAGSHIPS]
        dupes = {n for n in names if names.count(n) > 1}
        self.assertEqual(dupes, set(), f"duplicate flagship names: {dupes}")

    def test_flagship_required_fields_are_well_typed(self):
        for f in facts.FLAGSHIPS:
            with self.subTest(repo=f.get("name")):
                self.assertIsInstance(f.get("name"), str)
                self.assertTrue(f["name"], "name must be non-empty")
                self.assertIsInstance(f.get("domain"), str)
                self.assertIsInstance(f.get("lang"), str)
                self.assertIsInstance(f.get("blurb"), str)
                self.assertTrue(f["blurb"], "blurb must be non-empty")
                # tag is either a real git tag string or explicitly None —
                # never missing, since generate.py reads it unconditionally.
                self.assertIn("tag", f)

    def test_domain_accent_and_short_labels_cover_every_domain(self):
        # generate.py's DOMAIN_ACCENT / SHORT_DOMAIN maps are keyed by the
        # domain strings in facts.py; a typo in either place means a
        # KeyError deep inside SVG rendering instead of a clear failure.
        for domain in facts.DOMAINS:
            self.assertIn(domain, generate.DOMAIN_ACCENT)
            self.assertIn(domain, generate.SHORT_DOMAIN)


class TestSquarifyLayout(unittest.TestCase):
    """generate.squarify() is the squarified-treemap algorithm behind the
    language-mix panel. It's pure geometry (sizes in, rects out) with no
    GitHub dependency, so it's exercised directly against known inputs.

    Its one calling convention (see langmix()) is that the input sizes are
    pre-scaled *areas* whose sum already equals dx*dy — squarify() doesn't
    renormalize, it just tiles. Every test below scales its raw "shares"
    into areas the same way langmix() does before calling squarify()."""

    @staticmethod
    def _areas(shares, dx, dy):
        total = sum(shares)
        box_area = dx * dy
        return [s / total * box_area for s in shares]

    def test_empty_input_returns_no_rects(self):
        self.assertEqual(generate.squarify([], 0, 0, 100, 50), [])

    def test_single_item_fills_the_whole_box(self):
        dx, dy = 100.0, 50.0
        rects = generate.squarify(self._areas([42], dx, dy), 10, 20, dx, dy)
        self.assertEqual(len(rects), 1)
        x, y, w, h = rects[0]
        self.assertAlmostEqual(x, 10)
        self.assertAlmostEqual(y, 20)
        self.assertAlmostEqual(w, dx)
        self.assertAlmostEqual(h, dy)

    def test_rect_areas_sum_to_box_area(self):
        # langmix() always feeds squarify() shares pre-scaled so they sum
        # to the panel's pixel area; the returned rects should tile it
        # exactly, with no gap or overlap slack lost off the total.
        shares = [500.0, 300.0, 120.0, 80.0]
        x0, y0, dx, dy = 5.0, 5.0, 90.0, 40.0
        rects = generate.squarify(self._areas(shares, dx, dy), x0, y0, dx, dy)
        self.assertEqual(len(rects), len(shares))
        total_area = sum(w * h for (_, _, w, h) in rects)
        self.assertAlmostEqual(total_area, dx * dy, places=6)

    def test_rects_stay_within_bounds(self):
        shares = [640.0, 210.0, 90.0, 45.0, 15.0]
        x0, y0, dx, dy = 0.0, 0.0, 80.0, 25.0
        rects = generate.squarify(self._areas(shares, dx, dy), x0, y0, dx, dy)
        for (x, y, w, h) in rects:
            self.assertGreaterEqual(round(x, 6), x0)
            self.assertGreaterEqual(round(y, 6), y0)
            self.assertLessEqual(round(x + w, 6), round(x0 + dx, 6))
            self.assertLessEqual(round(y + h, 6), round(y0 + dy, 6))
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)

    def test_larger_share_gets_larger_area(self):
        # Not a tiling-correctness proof, just a sanity check that the
        # biggest input share really does end up as the biggest rect —
        # the property the whole "area-proportional" panel claims to have.
        shares = [900.0, 60.0, 40.0]
        dx, dy = 100.0, 30.0
        rects = generate.squarify(self._areas(shares, dx, dy), 0.0, 0.0, dx, dy)
        areas = [w * h for (_, _, w, h) in rects]
        self.assertEqual(areas.index(max(areas)), 0)


if __name__ == "__main__":
    unittest.main()
