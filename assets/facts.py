"""
Verified, hand-curated facts for the profile dashboard.

Everything here was pulled from the repositories' own committed files or the
GitHub API on the date noted and cross-checked before being written down.
Numbers the GitHub API cannot give us (benchmark results, regulatory dates)
live here as constants with their source; everything the API *can* give us
(repo languages, CI status, follower/repo counts) is fetched live by
generate.py and is never hard-coded.

Last verified: 2026-07-21.
"""

OWNER = "bharat3645"
NAME = "Bharat Singh Parihar"
TAGLINE = "Agent-security & AI-infrastructure engineer"
SUBLINE = "I build small, verifiable tools for the parts of the AI stack that fail quietly."

# ---------------------------------------------------------------------------
# The flagship portfolio. `private` repos are described but never hard-linked
# (a link to a private repo 404s for visitors). `domain` drives the radar map.
# `tag` is the real git tag if one exists; verified via `gh api .../tags`.
# ---------------------------------------------------------------------------
FLAGSHIPS = [
    # Agent Security
    dict(name="agent-rules-audit", domain="Agent Security", lang="JavaScript", tag=None,
         blurb="Static linter for AI-agent rule files (Cursor / Claude / Copilot) — flags "
               "over-broad tool grants and prompt-injection-prone instructions."),
    dict(name="mcp-sentinel", domain="Agent Security", lang="Rust", tag=None,
         blurb="Offline risk scanner for MCP client configs — grades each server A–F on inline "
               "secrets, @latest pins, shell indirection and typosquat-like names."),
    dict(name="toolcage", domain="Agent Security", lang="Rust", tag="v0.1.0",
         blurb="WASM sandbox for MCP tool calls — a fresh wasmtime Store per call, deny-by-default "
               "capabilities, stateless HMAC-signed tools/list pagination."),
    dict(name="agent-flightbox", domain="Agent Security", lang="Go", tag="v0.1.0",
         blurb="Flight recorder for agent processes — captures the syscall/exec/network surface "
               "of a run to tamper-evident JSONL, with a session `diff`."),
    # AI Infrastructure
    dict(name="mcp-gateway-lite", domain="AI Infrastructure", lang="Go", tag="v0.4.0",
         blurb="Single-binary reverse proxy for MCP — tool-allowlist filtering, rate limiting, "
               "tamper-evident audit log and a tools_lock against rug-pulls."),
    dict(name="modelgate", domain="AI Infrastructure", lang="Go", tag=None,
         blurb="Multi-provider LLM gateway — routing, automatic fallback, token/cost accounting "
               "and a metadata-only audit trail. stdlib-only."),
    dict(name="localmodel-fit", domain="AI Infrastructure", lang="Go", tag="v0.1.0",
         blurb="Predicts whether a GGUF model fits and how fast it decodes on given hardware — "
               "MoE-aware, with a benchmark harness validated against real ollama runs."),
    dict(name="trace2eval", domain="AI Infrastructure", lang="JavaScript", tag=None,
         blurb="Turns raw agent traces into scrubbed, deduplicated evaluation datasets — "
               "PII scrub before dedupe, deterministic and offline."),
    # Post-Quantum Crypto
    dict(name="ml-kem-rb", domain="Post-Quantum Crypto", lang="Ruby", tag=None,
         blurb="Reference ML-KEM (FIPS 203) in pure Ruby, plus a real hybrid X25519+ML-KEM-768 "
               "KEM implementing the TLS 1.3 draft wire format."),
    dict(name="pqc-scan", domain="Post-Quantum Crypto", lang="Rust", tag=None, private=True,
         blurb="Crypto inventory → CycloneDX CBOM → A–F post-quantum readiness grade, with live "
               "TLS 1.3 handshake checks. Private until the Sept 2026 launch."),
    # Backend & Rails
    dict(name="idempotent-rack", domain="Backend Systems", lang="Ruby", tag="v0.1.0",
         blurb="Idempotency-Key middleware for Rack/Rails — dedupes retried POST/PUT against a "
               "pluggable store (memory / file / Redis / ActiveRecord)."),
    dict(name="acts-as-mcp", domain="Backend Systems", lang="Ruby", tag=None,
         blurb="Expose ActiveRecord models as MCP tools from a Rails app with one class macro — "
               "scoped, read-only-by-default agent access to your data layer."),
    # Supply-Chain / Dev Tooling
    dict(name="gemfile-lock-audit", domain="Supply Chain", lang="Ruby", tag=None,
         blurb="Audits a Gemfile.lock for yanked gems, git-sourced deps and version pins that "
               "drift from the lockfile — zero network, CI-friendly."),
]

# Domains in radar order. Value on each axis is the live repo count (computed
# in generate.py from FLAGSHIPS), so the shape is honest, not eyeballed.
DOMAINS = [
    "Agent Security",
    "AI Infrastructure",
    "Post-Quantum Crypto",
    "Backend Systems",
    "Supply Chain",
]

# ---------------------------------------------------------------------------
# Verified benchmark numbers. Each is reproducible from the named repo's own
# committed harness; `source` is the file, `date`/`env` the capture context.
# ---------------------------------------------------------------------------
BENCHMARKS = [
    dict(repo="mcp-gateway-lite", metric="reverse-proxy overhead",
         value="+40 µs", detail="29.3µs direct → 69.9µs through gateway, per tools/call",
         env="Apple M4 · go1.26.5 · 2026-07-20", source="gateway/bench_test.go",
         # bar: fraction of a 100µs reference budget consumed by the added overhead
         bar=0.40),
    dict(repo="toolcage", metric="per-call WASM sandbox",
         value="+0.33 ms", detail="0.415ms median sandboxed vs 0.089ms unsandboxed floor",
         env="ubuntu-latest CI · 200 echo calls · 2026-07-20", source="ci/bench.py",
         bar=0.33),
    dict(repo="localmodel-fit", metric="prefill 1/params scaling",
         value="~2% err", detail="measured 0.5b/1.5b ratio 3.06–3.18 vs exact 3.125",
         env="Apple M4 · qwen2.5 0.5b+1.5b · real ollama", source="bench/RESULTS.md",
         bar=0.02),
    dict(repo="ml-kem-rb", metric="hybrid KEM (TLS draft)",
         value="1216 / 1120 B", detail="X25519+ML-KEM-768 client/server shares, 64B shared secret",
         env="draft-ietf-tls-ecdhe-mlkem-05 · FIPS 203", source="README.md",
         bar=None),  # not a latency bar — shown as spec
]

# ---------------------------------------------------------------------------
# Post-quantum regulatory calendar. Dates from NIST/NSA primary sources,
# also emitted verbatim by pqc-scan's own `regulatory calendar` command
# (captured 2026-07-20). days-remaining is computed live against run date.
# ---------------------------------------------------------------------------
PQC_DEADLINES = [
    dict(date="2026-09-21", label="FIPS 140-2 → Historical",
         note="FIPS 140-2 certs no longer valid for new federal procurement"),
    dict(date="2027-01-01", label="NSA CNSA 2.0",
         note="new National Security Systems must support ML-KEM-1024 + ML-DSA-87"),
    dict(date="2030-01-01", label="NIST IR 8547: deprecate",
         note="RSA / ECDSA / ECDH / DH deprecated for new federal deployments"),
    dict(date="2035-01-01", label="NIST IR 8547: disallow",
         note="classical asymmetric crypto disallowed — treated as forgeable"),
]

# GitHub linguist colors for the languages we actually ship.
LANG_COLORS = {
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "Python": "#3572A5",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Shell": "#89e051",
    "C": "#555555", "HTML": "#e34c26",
}
