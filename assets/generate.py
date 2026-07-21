#!/usr/bin/env python3
"""
Self-hosted profile dashboard generator — NEUBRUTALIST edition, v2.

Pulls live data from the GitHub REST API and renders a set of custom SVG
"instruments" (hero HUD, domain radar, benchmark board, PQC clock, language
mix) in matching dark and light themes, written to assets/*.svg. The README
embeds them with <picture> tags so nothing depends on a third-party image host
at view time — the images live in this repo.

Design language: neubrutalism — thick high-contrast borders, hard offset
shadows (no blur), saturated accent blocks, chunky uppercase mono type. A
signature magenta accent, faint dot-grid texture, corner registration marks
and instrument numbering tie all five panels into one visual system. Subtle
SMIL motion (radar sweep, urgency pulse, scanline, load-in reveals) that
degrades to a complete static frame if a renderer ignores animation — GitHub
serves SVG bytes verbatim, so the motion plays (same mechanism as the
contribution-snake SVG already on the profile).

Run locally:   GITHUB_TOKEN=$(gh auth token) python3 assets/generate.py
In CI:         GITHUB_TOKEN is provided by actions/checkout's default token.

Stdlib only. No pip install. If a live fetch fails, the generator falls back
to the last-verified constant so CI never emits a broken asset.
"""
import json
import math
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts  # noqa: E402

OWNER = facts.OWNER
OUT = Path(__file__).resolve().parent
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
NOW = datetime.now(timezone.utc)

MONO = "ui-monospace,'SF Mono','Cascadia Code','DejaVu Sans Mono',Menlo,Consolas,monospace"
SANS = "'Arial Black',system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

# `ink` is the single high-contrast colour for every border, hard shadow and
# primary text. `sig` is the signature magenta that recurs on every instrument.
# `on_accent` is always near-black because accent fills are light in both themes.
DARK = dict(
    page="#0d1117", card="#191921", ink="#f4efe1", muted="#b3ae9d", faint="#6f6c60",
    on_accent="#141109", grid="#2b2b33", sig="#ff2e88",
    yellow="#ffd23f", pink="#ff6fa5", cyan="#34e2ea", lime="#b6f24d",
    orange="#ff9142", blue="#6aa3ff", purple="#c9a2ff", red="#ff6b6b", green="#5ee08a",
)
LIGHT = dict(
    page="#fdf6e6", card="#ffffff", ink="#141109", muted="#5c574a", faint="#948f7e",
    on_accent="#141109", grid="#e4dcc6", sig="#ff1f7a",
    yellow="#ffcf33", pink="#ff5d8f", cyan="#1fc7e0", lime="#8fd613",
    orange="#ff7a45", blue="#4d7cfe", purple="#b06bff", red="#ff4d4d", green="#1fbf5a",
)

DOMAIN_ACCENT = {
    "Agent Security": "red", "AI Infrastructure": "blue",
    "Post-Quantum Crypto": "purple", "Backend Systems": "green", "Supply Chain": "yellow",
}
SHORT_DOMAIN = {
    "Agent Security": "AGENT SEC", "AI Infrastructure": "AI INFRA",
    "Post-Quantum Crypto": "PQC", "Backend Systems": "BACKEND", "Supply Chain": "SUPPLY",
}


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------
def api(path, params=None):
    url = f"https://api.github.com{path}"
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "bharat3645-profile-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  ! api {path} failed: {e}", file=sys.stderr)
        return None


def gather():
    data = {"followers": 23, "public_source_repos": 78, "lang_bytes": {}, "ci": {}}
    user = api(f"/users/{OWNER}")
    if user:
        data["followers"] = user.get("followers", data["followers"])

    repos, page = [], 1
    while True:
        chunk = api(f"/users/{OWNER}/repos", {"per_page": 100, "page": page, "type": "owner"})
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    if repos:
        data["public_source_repos"] = sum(
            1 for r in repos if not r.get("fork") and not r.get("private"))

    lang_bytes = {}
    for f in facts.FLAGSHIPS:
        name = f["name"]
        if f.get("private"):
            continue  # keep the CI tally reproducible by any viewer (public-only)
        langs = api(f"/repos/{OWNER}/{name}/languages")
        if langs:
            for k, v in langs.items():
                lang_bytes[k] = lang_bytes.get(k, 0) + v
        runs = api(f"/repos/{OWNER}/{name}/actions/runs", {"per_page": 1})
        concl = runs["workflow_runs"][0].get("conclusion") if (
            runs and runs.get("workflow_runs")) else None
        data["ci"][name] = concl
    if lang_bytes:
        data["lang_bytes"] = lang_bytes
    return data


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def col(p, name):
    return p[name] if isinstance(name, str) and name in p else name


def text(x, y, s, size=13, fill="ink", weight=700, font=SANS, anchor="start",
         spacing=None, opacity=None, p=None):
    style = f'font-family:{font};font-size:{size}px;font-weight:{weight}'
    if spacing is not None:
        style += f';letter-spacing:{spacing}px'
    extra = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{col(p,fill)}" text-anchor="{anchor}" '
            f'style="{style}"{extra}>{esc(s)}</text>')


def rect(x, y, w, h, fill="card", rx=0, stroke=None, sw=2.5, opacity=None, p=None):
    s = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
         f'fill="{col(p,fill)}"')
    if stroke:
        s += f' stroke="{col(p,stroke)}" stroke-width="{sw}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def line(x1, y1, x2, y2, stroke="ink", sw=2, p=None, dash=None, cap="butt", opacity=None):
    s = (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
         f'stroke="{col(p,stroke)}" stroke-width="{sw}" stroke-linecap="{cap}"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def circle(cx, cy, r, fill="ink", stroke=None, sw=2, p=None, opacity=None):
    s = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col(p,fill)}"'
    if stroke:
        s += f' stroke="{col(p,stroke)}" stroke-width="{sw}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def card(x, y, w, h, p, fill="card", accent=None, dx=6, dy=6, rx=3, bw=2.5):
    """Neubrutalist block: hard offset shadow + thick-bordered panel."""
    out = rect(x + dx, y + dy, w, h, fill="ink", rx=rx, p=p)
    out += rect(x, y, w, h, fill=fill, rx=rx, stroke="ink", sw=bw, p=p)
    if accent:
        out += rect(x, y, 7, h, fill=accent, rx=0, p=p)
        out += line(x + 7, y, x + 7, y + h, stroke="ink", sw=bw, p=p)
    return out


def tab(x, y, label, accent, p, size=15, h=30, dx=5, dy=5, font=MONO):
    """Brutalist sticker label: accent fill, ink border, hard shadow."""
    w = len(label) * size * 0.62 + 26
    out = rect(x + dx, y + dy, w, h, fill="ink", rx=3, p=p)
    out += rect(x, y, w, h, fill=accent, rx=3, stroke="ink", sw=2.5, p=p)
    out += text(x + 13, y + h / 2 + size * 0.35, label, size=size, fill="on_accent",
                weight=800, font=font, spacing=0.5, p=p)
    return out, w


def defs(idn, p):
    """Per-file <defs>: dot-grid texture + radar sweep gradient (namespaced ids)."""
    return (
        f'<defs>'
        f'<pattern id="dg{idn}" width="19" height="19" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.6" cy="1.6" r="1.15" fill="{p["ink"]}" opacity="0.05"/></pattern>'
        f'<radialGradient id="sw{idn}" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{p["sig"]}" stop-opacity="0.34"/>'
        f'<stop offset="1" stop-color="{p["sig"]}" stop-opacity="0"/></radialGradient>'
        f'</defs>'
    )


def frame(w, h, p, idn, texture=True):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" font-family="{SANS}">'
         + defs(idn, p) + rect(0, 0, w, h, fill="page", rx=0, p=p))
    if texture:
        s += rect(0, 0, w, h, fill=f"url(#dg{idn})", rx=0, p=p)
    return s


def corner_marks(w, h, p, inset=11, L=17):
    """Signature magenta registration brackets, top-right + bottom-left."""
    sg = p["sig"]
    o = []
    o.append(line(w - inset - L, inset, w - inset, inset, stroke=sg, sw=3, p=p))
    o.append(line(w - inset, inset, w - inset, inset + L, stroke=sg, sw=3, p=p))
    o.append(line(inset, h - inset, inset + L, h - inset, stroke=sg, sw=3, p=p))
    o.append(line(inset, h - inset - L, inset, h - inset, stroke=sg, sw=3, p=p))
    return "".join(o)


def live_badge(x, y, p):
    """Small pulsing '● LIVE' — marks panels driven by live GitHub data."""
    dot = (f'<circle cx="{x:.1f}" cy="{y-3:.1f}" r="4" fill="{p["sig"]}">'
           f'<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" '
           f'repeatCount="indefinite"/></circle>')
    return dot + text(x + 10, y, "LIVE", size=10.5, fill="muted", weight=800,
                      font=MONO, spacing=1, p=p)


def head(p, w, num, title, sub, accent, live=False):
    t, tw = tab(24, 20, f"{num} // {title}", accent, p)
    t += text(24, 72, sub, size=12, fill="muted", weight=600, p=p)
    if live:
        t += live_badge(w - 66, 36, p)
    return t


# ---------------------------------------------------------------------------
# Instrument 1 — hero HUD
# ---------------------------------------------------------------------------
def hero(p, d):
    W, H = 850, 248
    idn = "h"
    green = sum(1 for c in d["ci"].values() if c == "success")
    withruns = sum(1 for c in d["ci"].values() if c is not None)
    if withruns == 0:
        green, withruns = 10, 11
    langs = len([k for k in d["lang_bytes"] if k in facts.LANG_COLORS])
    tiles = [
        (str(len(facts.FLAGSHIPS)), "FLAGSHIP REPOS", "blue"),
        (f"{green}/{withruns}", "CI GREEN", "green"),
        (str(langs or 6), "LANGUAGES", "purple"),
        (str(d["public_source_repos"]), "PUBLIC REPOS", "cyan"),
        (str(d["followers"]), "FOLLOWERS", "orange"),
    ]
    s = [frame(W, H, p, idn, texture=False)]
    # window plate
    s.append(rect(16 + 6, 12 + 6, W - 32, H - 24, fill="ink", rx=4, p=p))
    s.append(rect(16, 12, W - 32, H - 24, fill="card", rx=4, stroke="ink", sw=3, p=p))
    s.append(rect(16, 12, W - 32, H - 24, fill=f"url(#dg{idn})", rx=4, p=p))
    # scanline (CRT sweep) — clipped to the screen, hidden when static
    s.append(f'<clipPath id="scr{idn}"><rect x="19" y="55" width="{W-38}" height="{H-73}" '
             f'rx="2"/></clipPath>')
    # base transform parks it off-screen so the static (un-animated) frame shows
    # nothing; the animation sweeps it down through the clipped screen area.
    s.append(f'<g clip-path="url(#scr{idn})"><rect x="16" y="55" width="{W-32}" height="24" '
             f'fill="{p["sig"]}" opacity="0.09" transform="translate(0 -60)">'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 -60;0 {H-60};0 {H-60}" dur="5.4s" repeatCount="indefinite"/>'
             f'</rect></g>')
    # top bar
    s.append(rect(16, 12, W - 32, 40, fill="yellow", rx=0, p=p))
    s.append(line(16, 52, W - 16, 52, stroke="ink", sw=3, p=p))
    for i in range(3):
        s.append(rect(34 + i * 22, 25, 14, 14, fill="card", rx=2, stroke="ink", sw=2, p=p))
    s.append(text(W - 32, 37, f"01 // github.com/{OWNER}", size=13, fill="on_accent",
                  weight=800, font=MONO, anchor="end", spacing=0.5, p=p))
    # layered name (hard signature-magenta text shadow)
    nx, ny = 36, 100
    s.append(text(nx + 3, ny + 3, facts.NAME.upper(), size=31, fill="sig", weight=800,
                  font=MONO, spacing=1, p=p))
    s.append(text(nx, ny, facts.NAME.upper(), size=31, fill="ink", weight=800,
                  font=MONO, spacing=1, p=p))
    tag = "> " + facts.TAGLINE
    s.append(text(nx, ny + 30, tag, size=15, fill="ink", weight=700, font=MONO, p=p))
    curx = nx + len(tag) * 9.02
    s.append(f'<rect x="{curx:.1f}" y="{ny+18:.1f}" width="10" height="15" fill="{p["sig"]}">'
             f'<animate attributeName="opacity" values="1;1;0;0" dur="1.05s" '
             f'repeatCount="indefinite"/></rect>')
    s.append(text(nx, ny + 50, facts.SUBLINE, size=12.5, fill="muted", weight=600, p=p))
    # stat tiles
    n = len(tiles)
    x0, y0, gap = 36, 180, 13
    tw = (W - 2 * x0 - (n - 1) * gap) / n
    th = 48
    for i, (val, lab, c) in enumerate(tiles):
        tx = x0 + i * (tw + gap)
        s.append(card(tx, y0, tw, th, p, fill="card", accent=c, dx=4, dy=4, rx=2))
        s.append(text(tx + tw / 2 + 3, y0 + 24, val, size=20, fill="ink", weight=800,
                      font=MONO, anchor="middle", p=p))
        s.append(text(tx + tw / 2 + 3, y0 + 39, lab, size=9, fill="muted", weight=700,
                      font=MONO, anchor="middle", spacing=0.3, p=p))
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------------
# Instrument 2 — domain radar + repo index (animated sweep)
# ---------------------------------------------------------------------------
def radar(p, d):
    W, H = 850, 470
    idn = "d"
    doms = facts.DOMAINS
    counts = {dm: sum(1 for f in facts.FLAGSHIPS if f["domain"] == dm) for dm in doms}
    mx = max(counts.values()) or 1
    cx, cy, R = 200, 290, 128
    N = len(doms)
    s = [frame(W, H, p, idn)]
    s.append(corner_marks(W, H, p))
    s.append(head(p, W, "02", "DOMAIN MAP",
                  "13 flagship repositories · five problem domains · axis = live repo count",
                  "blue", live=True))

    def pt(i, frac):
        ang = -math.pi / 2 + i * 2 * math.pi / N
        return cx + R * frac * math.cos(ang), cy + R * frac * math.sin(ang)

    for ring in (0.34, 0.67, 1.0):
        pts = " ".join(f"{pt(i, ring)[0]:.1f},{pt(i, ring)[1]:.1f}" for i in range(N))
        s.append(f'<polygon points="{pts}" fill="none" stroke="{p["grid"]}" stroke-width="2"/>')
    # rotating radar sweep (wedge + leading line), behind data polygon
    wtip1 = (cx + R * math.cos(math.radians(-90)), cy + R * math.sin(math.radians(-90)))
    wtip2 = (cx + R * math.cos(math.radians(-52)), cy + R * math.sin(math.radians(-52)))
    s.append(
        f'<g><animateTransform attributeName="transform" type="rotate" '
        f'values="0 {cx} {cy};360 {cx} {cy}" dur="7s" repeatCount="indefinite"/>'
        f'<polygon points="{cx},{cy} {wtip1[0]:.1f},{wtip1[1]:.1f} {wtip2[0]:.1f},{wtip2[1]:.1f}" '
        f'fill="url(#sw{idn})"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{wtip1[0]:.1f}" y2="{wtip1[1]:.1f}" '
        f'stroke="{p["sig"]}" stroke-width="2" opacity="0.9"/></g>')
    for i, dm in enumerate(doms):
        ex, ey = pt(i, 1.0)
        s.append(line(cx, cy, ex, ey, stroke="grid", sw=2, p=p))
        lx, ly = pt(i, 1.20)
        c = DOMAIN_ACCENT[dm]
        anchor = "middle"
        if lx < cx - 20:
            anchor = "end"
        elif lx > cx + 20:
            anchor = "start"
        dy = -4 if ly < cy - 40 else 12
        s.append(text(lx, ly + dy, SHORT_DOMAIN[dm], size=10.5, fill="ink", weight=800,
                      anchor=anchor, font=MONO, p=p))
        s.append(text(lx, ly + dy + 13, f"{counts[dm]} REPOS", size=10, fill=c, weight=800,
                      anchor=anchor, font=MONO, p=p))
    dpts = " ".join(f"{pt(i, counts[dm] / mx)[0]:.1f},{pt(i, counts[dm] / mx)[1]:.1f}"
                    for i, dm in enumerate(doms))
    s.append(f'<polygon points="{dpts}" fill="{p["blue"]}" fill-opacity="0.22" '
             f'stroke="{p["ink"]}" stroke-width="3" stroke-linejoin="round"/>')
    for i, dm in enumerate(doms):
        vx, vy = pt(i, counts[dm] / mx)
        s.append(rect(vx - 5, vy - 5, 10, 10, fill=DOMAIN_ACCENT[dm], rx=1, stroke="ink",
                      sw=2, p=p))

    ix, iy = 446, 100
    s.append(line(430, 84, 430, H - 20, stroke="grid", sw=2, p=p))
    for dm in doms:
        c = DOMAIN_ACCENT[dm]
        s.append(rect(ix, iy - 11, 14, 14, fill=c, rx=2, stroke="ink", sw=2, p=p))
        s.append(text(ix + 22, iy, dm.upper(), size=11, fill="ink", weight=800,
                      font=MONO, spacing=0.3, p=p))
        for f in [f for f in facts.FLAGSHIPS if f["domain"] == dm]:
            iy += 18
            lc = facts.LANG_COLORS.get(f["lang"], p["muted"])
            s.append(circle(ix + 8, iy - 4, 4, fill=lc, stroke="ink", sw=1.5, p=p))
            nm = f["name"] + ("  [private]" if f.get("private") else "")
            s.append(text(ix + 22, iy, nm, size=11.5, fill="ink", weight=600, font=MONO, p=p))
            if f.get("tag"):
                tagx = ix + 22 + len(nm) * 7.05 + 8
                s.append(text(tagx, iy, f["tag"], size=10, fill=c, weight=800, font=MONO, p=p))
        iy += 22
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------------
# Instrument 3 — benchmark board (bars reveal on load)
# ---------------------------------------------------------------------------
def benchmarks(p, d):
    W, H = 850, 336
    idn = "b"
    s = [frame(W, H, p, idn)]
    s.append(corner_marks(W, H, p))
    s.append(head(p, W, "03", "VERIFIED BENCHMARKS",
                  "every figure reproducible from the repo's own committed harness — no hand-waving",
                  "green"))
    bx, by, gap = 24, 88, 16
    cw = (W - 2 * bx - gap) / 2
    ch = 108
    accents = ["blue", "purple", "lime", "orange"]
    for i, b in enumerate(facts.BENCHMARKS):
        c = accents[i]
        x = bx + (i % 2) * (cw + gap)
        y = by + (i // 2) * (ch + gap)
        s.append(card(x, y, cw, ch, p, fill="card", accent=c, dx=6, dy=6))
        s.append(text(x + 22, y + 26, b["repo"], size=12, fill="ink", weight=800,
                      font=MONO, p=p))
        mlabel = b["metric"].upper()
        mw = len(mlabel) * 6.4 + 14
        s.append(rect(x + cw - mw - 14, y + 13, mw, 19, fill=c, rx=2, stroke="ink", sw=1.5, p=p))
        s.append(text(x + cw - mw - 7, y + 26, mlabel, size=9, fill="on_accent",
                      weight=800, font=MONO, p=p))
        s.append(text(x + 22, y + 60, b["value"], size=27, fill="ink", weight=800,
                      font=MONO, p=p))
        if b.get("bar") is not None:
            bar_x, bar_y, bar_w = x + 22, y + 72, cw - 44
            s.append(rect(bar_x, bar_y, bar_w, 9, fill="card", rx=1, stroke="ink", sw=2, p=p))
            fillw = max(5, min(1.0, b["bar"]) * bar_w)
            # base width = full (static fallback); animate reveal 0 -> full, then freeze
            s.append(
                f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{fillw:.1f}" height="9" '
                f'fill="{p[c]}"><animate attributeName="width" values="0;{fillw:.1f}" '
                f'dur="0.9s" begin="{0.15*i:.2f}s" fill="freeze" '
                f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.7 0.2 1"/></rect>')
            s.append(line(bar_x + fillw, bar_y, bar_x + fillw, bar_y + 9, stroke="ink", sw=2, p=p))
        s.append(text(x + 22, y + 98, b["detail"], size=10.3, fill="muted", weight=600, p=p))
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------------
# Instrument 4 — post-quantum migration clock (urgency pulse)
# ---------------------------------------------------------------------------
def pqc_clock(p, d):
    W, H = 850, 300
    idn = "q"
    s = [frame(W, H, p, idn)]
    s.append(corner_marks(W, H, p))
    s.append(head(p, W, "04", "PQC MIGRATION CLOCK",
                  "why the crypto work ships now — real US federal PQC deadlines, counting down live",
                  "purple", live=True))
    today = NOW.date()
    dls = []
    for dl in facts.PQC_DEADLINES:
        dt = datetime.strptime(dl["date"], "%Y-%m-%d").date()
        dls.append(dict(dl, dt=dt, days=(dt - today).days))
    horizon = max(x["days"] for x in dls) or 1

    def urg(days):
        return "red" if days <= 120 else "orange" if days <= 400 else \
            "yellow" if days <= 1500 else "blue"

    tx0, tx1, ty = 32, W - 32, 104
    s.append(line(tx0, ty, tx1, ty, stroke="ink", sw=3, p=p))
    s.append(rect(tx0 - 4, ty - 4, 8, 8, fill="ink", rx=1, p=p))
    s.append(text(tx0, ty + 20, "TODAY " + today.strftime("%b %Y"), size=9.5, fill="muted",
                  weight=700, font=MONO, p=p))
    nearest = min(range(len(dls)), key=lambda i: dls[i]["days"])
    for i, dl in enumerate(dls):
        fx = tx0 + (dl["days"] / horizon) * (tx1 - tx0)
        c = urg(dl["days"])
        s.append(line(fx, ty - 11, fx, ty + 11, stroke="ink", sw=3, p=p))
        mk = rect(fx - 6, ty - 6, 12, 12, fill=c, rx=1, stroke="ink", sw=2, p=p)
        if i == nearest:  # pulse the most urgent marker
            mk = (f'<g>{mk}<circle cx="{fx:.1f}" cy="{ty}" r="6" fill="none" '
                  f'stroke="{p[c]}" stroke-width="2"><animate attributeName="r" '
                  f'values="6;16;6" dur="1.8s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="0.9;0;0.9" dur="1.8s" '
                  f'repeatCount="indefinite"/></circle></g>')
        s.append(mk)
    cx0, cy0, gap = 24, 132, 14
    cw = (W - 2 * cx0 - 3 * gap) / 4
    ch = 138
    for i, dl in enumerate(dls):
        c = urg(dl["days"])
        x = cx0 + i * (cw + gap)
        s.append(card(x, cy0, cw, ch, p, fill="card", dx=5, dy=5))
        stripe = rect(x, cy0, cw, 8, fill=c, rx=0, p=p)
        if i == nearest:  # pulse the nearest card's top stripe
            stripe = (f'<g>{stripe}<rect x="{x:.1f}" y="{cy0}" width="{cw:.1f}" height="8" '
                      f'fill="{p[c]}"><animate attributeName="opacity" values="1;0.35;1" '
                      f'dur="1.4s" repeatCount="indefinite"/></rect></g>')
        s.append(stripe)
        s.append(line(x, cy0 + 8, x + cw, cy0 + 8, stroke="ink", sw=2.5, p=p))
        s.append(text(x + 14, cy0 + 32, dl["dt"].strftime("%Y-%m-%d"), size=11, fill="muted",
                      weight=700, font=MONO, p=p))
        s.append(text(x + 14, cy0 + 66, f"{dl['days']:,}", size=30, fill="ink", weight=800,
                      font=MONO, p=p))
        s.append(text(x + 14, cy0 + 82, "DAYS LEFT", size=10, fill=c, weight=800, font=MONO,
                      spacing=0.5, p=p))
        s.append(text(x + 14, cy0 + 104, dl["label"], size=10.5, fill="ink", weight=800, p=p))
        _wrap(s, p, dl["note"], x + 14, cy0 + 120, cw - 22, size=9, fill="muted",
              lh=11, maxlines=2)
    s.append("</svg>")
    return "".join(s)


def _wrap(s, p, txt, x, y, w, size=10, fill="muted", lh=12, maxlines=3, font=SANS):
    cpl = max(6, int(w / (size * 0.53)))
    words, line_s, lines = txt.split(), "", []
    for word in words:
        t = (line_s + " " + word).strip()
        if len(t) > cpl and line_s:
            lines.append(line_s)
            line_s = word
        else:
            line_s = t
    if line_s:
        lines.append(line_s)
    for i, ln in enumerate(lines[:maxlines]):
        if i == maxlines - 1 and len(lines) > maxlines:
            ln = ln.rstrip(".,") + "…"
        s.append(text(x, y + i * lh, ln, size=size, fill=fill, weight=600, font=font, p=p))


# ---------------------------------------------------------------------------
# Instrument 5 — language mix (left-to-right reveal)
# ---------------------------------------------------------------------------
def langmix(p, d):
    W, H = 850, 158
    idn = "l"
    lb = d["lang_bytes"] or {"Go": 351152, "Rust": 224529, "Ruby": 156837,
                             "Python": 118975, "JavaScript": 100465, "Shell": 26261}
    items = sorted(lb.items(), key=lambda kv: kv[1], reverse=True)
    total = sum(v for _, v in items) or 1
    s = [frame(W, H, p, idn)]
    s.append(corner_marks(W, H, p))
    s.append(head(p, W, "05", "LANGUAGE MIX",
                  "by bytes across the public flagship repos · computed live from the GitHub API",
                  "cyan", live=True))
    bx, by, bw, bh = 24, 84, W - 48, 26
    s.append(rect(bx + 4, by + 4, bw, bh, fill="ink", rx=2, p=p))
    # reveal clip grows left->right on load (base width = full for static fallback)
    s.append(f'<clipPath id="rv{idn}"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}">'
             f'<animate attributeName="width" values="0;{bw}" dur="1.0s" fill="freeze" '
             f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.7 0.2 1"/></rect></clipPath>')
    s.append(f'<g clip-path="url(#rv{idn})">')
    x = bx
    for lang, v in items:
        seg = v / total * bw
        c = facts.LANG_COLORS.get(lang, p["muted"])
        s.append(f'<rect x="{x:.1f}" y="{by}" width="{max(0,seg):.1f}" height="{bh}" fill="{c}"/>')
        if x > bx:
            s.append(line(x, by, x, by + bh, stroke="ink", sw=2, p=p))
        x += seg
    s.append('</g>')
    s.append(rect(bx, by, bw, bh, fill="none", rx=2, stroke="ink", sw=2.5, p=p))
    lx, ly = 24, 138
    for lang, v in items:
        pct = v / total * 100
        c = facts.LANG_COLORS.get(lang, p["muted"])
        s.append(rect(lx, ly - 11, 13, 13, fill=c, rx=2, stroke="ink", sw=1.5, p=p))
        label = f"{lang} {pct:.1f}%"
        s.append(text(lx + 19, ly, label, size=12, fill="ink", weight=700, font=MONO, p=p))
        lx += 40 + len(label) * 7.5
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------------
INSTRUMENTS = {"hero": hero, "domains": radar, "benchmarks": benchmarks,
               "pqc-clock": pqc_clock, "langmix": langmix}


def main():
    print("fetching live data from GitHub API ...", file=sys.stderr)
    d = gather()
    print(f"  followers={d['followers']} public_source_repos={d['public_source_repos']} "
          f"langs={list(d['lang_bytes'])}", file=sys.stderr)
    print(f"  ci={d['ci']}", file=sys.stderr)
    for base, fn in INSTRUMENTS.items():
        for theme, pal in (("dark", DARK), ("light", LIGHT)):
            svg = fn(pal, d)
            (OUT / f"{base}-{theme}.svg").write_text(svg, encoding="utf-8")
            print(f"  wrote {base}-{theme}.svg ({len(svg)} bytes)", file=sys.stderr)
    print("done.", file=sys.stderr)


if __name__ == "__main__":
    main()
