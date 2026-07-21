<!--
  Profile README — self-hosted dashboard.
  Every visual below is a custom SVG generated from live GitHub API data by
  assets/generate.py and committed to this repo (assets/*.svg), refreshed daily
  by .github/workflows/profile-assets.yml. Nothing here depends on a third-party
  image host at view time. Every number is real and reproducible from the named
  repo's own committed harness. Dark/light variants are served via <picture>.
-->

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/hero-light.svg">
  <img alt="Bharat Singh Parihar — agent-security & AI-infrastructure engineer" src="./assets/hero-dark.svg" width="850">
</picture>

</div>

## ▌ WHOAMI

I build **small, verifiable tools for the parts of the AI stack that fail quietly** — agent sandboxes, MCP gateways, model-fit predictors, and post-quantum crypto. Each of the 13 flagship repos below ships with a real test suite, CI, and — where it makes a claim about speed or correctness — a committed benchmark you can re-run yourself.

- 🔭 **Now:** hardening the flagship portfolio for launch · `pqc-scan` in private beta ahead of the **Sept 2026** FIPS 140-2 sunset
- 🧭 **Focus:** agent security · AI infrastructure · post-quantum readiness · backend systems
- 🧪 **How I work:** reference-validated implementations, adversarial tests, reproducible benchmarks — no unverified claims
- 💬 **Ask me about:** MCP security & sandboxing · LLM gateways · PQC migration · idempotent backends
- 📫 **Reach me:** [LinkedIn](https://linkedin.com/in/bharat-singh-parihar) · [Portfolio](https://bharat3645.vercel.app) · [Email](mailto:404ghost.2@gmail.com)

---

## ▌ PORTFOLIO MAP

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/domains-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/domains-light.svg">
  <img alt="Domain map — 13 flagship repositories across five problem domains" src="./assets/domains-dark.svg" width="850">
</picture>

</div>

### 🛡️ Agent Security

| Repo | Stack | Release | What it does |
|------|-------|:-------:|--------------|
| **[agent-rules-audit](https://github.com/bharat3645/agent-rules-audit)** | JavaScript | — | Static linter for AI-agent rule files (Cursor / Claude / Copilot) — flags over-broad tool grants and injection-prone instructions. |
| **[mcp-sentinel](https://github.com/bharat3645/mcp-sentinel)** | Rust | — | Offline risk scanner for MCP client configs — grades each server **A–F** on inline secrets, `@latest` pins, shell indirection, typosquats. |
| **[toolcage](https://github.com/bharat3645/toolcage)** | Rust | `v0.1.0` | WASM sandbox for MCP tool calls — a fresh `wasmtime` Store per call, deny-by-default caps, HMAC-signed `tools/list` pagination. |
| **[agent-flightbox](https://github.com/bharat3645/agent-flightbox)** | Go | `v0.1.0` | Flight recorder for agent processes — captures the syscall / exec / network surface of a run to tamper-evident JSONL, with a session `diff`. |

### 🧠 AI Infrastructure

| Repo | Stack | Release | What it does |
|------|-------|:-------:|--------------|
| **[mcp-gateway-lite](https://github.com/bharat3645/mcp-gateway-lite)** | Go | `v0.4.0` | Single-binary reverse proxy for MCP — allowlist filtering, rate limiting, tamper-evident audit log, `tools_lock` against rug-pulls. |
| **[modelgate](https://github.com/bharat3645/modelgate)** | Go | — | Multi-provider LLM gateway — routing, automatic fallback, token/cost accounting, metadata-only audit trail. stdlib-only. |
| **[localmodel-fit](https://github.com/bharat3645/localmodel-fit)** | Go | `v0.1.0` | Predicts whether a GGUF model fits and how fast it decodes on given hardware — MoE-aware, validated against real `ollama` runs. |
| **[trace2eval](https://github.com/bharat3645/trace2eval)** | JavaScript | — | Turns raw agent traces into scrubbed, deduplicated eval datasets — PII scrub *before* dedupe, deterministic, offline. |

### 🔐 Post-Quantum Crypto

| Repo | Stack | Release | What it does |
|------|-------|:-------:|--------------|
| **[ml-kem-rb](https://github.com/bharat3645/ml-kem-rb)** | Ruby | — | Reference **ML-KEM (FIPS 203)** in pure Ruby, plus a real **hybrid X25519 + ML-KEM-768** KEM implementing the TLS 1.3 draft wire format. |
| **pqc-scan** `🔒 private` | Rust | — | Crypto inventory → CycloneDX **CBOM** → A–F post-quantum readiness grade, with live TLS 1.3 handshake checks. Launches **Sept 2026**. |

### 🗄️ Backend Systems & Supply Chain

| Repo | Stack | Release | What it does |
|------|-------|:-------:|--------------|
| **[idempotent-rack](https://github.com/bharat3645/idempotent-rack)** | Ruby | `v0.1.0` | Idempotency-Key middleware for Rack/Rails — dedupes retried POST/PUT against a pluggable store. *(0.3.0 Redis/ActiveRecord backends in progress.)* |
| **[acts-as-mcp](https://github.com/bharat3645/acts-as-mcp)** | Ruby | — | Expose ActiveRecord models as MCP tools from a Rails app with one class macro — scoped, read-only-by-default agent access. |
| **[gemfile-lock-audit](https://github.com/bharat3645/gemfile-lock-audit)** | Ruby | — | Audits a `Gemfile.lock` for yanked gems, git-sourced deps, and pins that drift from the lockfile — zero network, CI-friendly. |

---

## ▌ VERIFIED BENCHMARKS

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/benchmarks-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/benchmarks-light.svg">
  <img alt="Verified benchmarks — reproducible from each repo's committed harness" src="./assets/benchmarks-dark.svg" width="850">
</picture>

</div>

<details>
<summary><b>Reproduce these numbers yourself ▸</b></summary>

```sh
# mcp-gateway-lite — reverse-proxy overhead (Apple M4, go1.26.5)
go test -run '^$' -bench . -benchtime=2s ./gateway/...      # 29.3µs direct vs 69.9µs through gateway

# toolcage — per-call WASM sandbox overhead (ubuntu-latest CI, 200 echo calls)
python3 ci/bench.py WORK ./target/release/toolcage x.wasm 200   # 0.415ms median vs 0.089ms unsandboxed floor

# localmodel-fit — prefill 1/params scaling (Apple M4, real ollama)
go run ./bench -model qwen2.5:0.5b -hw m4 -params 494032768     # measured 0.5b/1.5b ratio 3.06–3.18 vs exact 3.125

# ml-kem-rb — hybrid X25519+ML-KEM-768, TLS draft wire format (FIPS 203)
ruby -rml_kem/hybrid -e 'p MLKem::Hybrid.client_init[0].bytesize'  # => 1216 (server share 1120, shared secret 64 B)
```
</details>

---

## ▌ POST-QUANTUM MIGRATION CLOCK

Two of my repos (`ml-kem-rb`, `pqc-scan`) exist because the crypto deadlines below are real and close. The clock counts down live against these US federal dates (NIST / NSA primary sources).

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/pqc-clock-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/pqc-clock-light.svg">
  <img alt="Post-quantum migration clock — real US federal PQC deadlines counting down" src="./assets/pqc-clock-dark.svg" width="850">
</picture>

</div>

---

## ▌ LANGUAGE MIX

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/langmix-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/langmix-light.svg">
  <img alt="Language mix by bytes across the public flagship repos" src="./assets/langmix-dark.svg" width="850">
</picture>

</div>

---

## ▌ TOOLBOX

| | |
|---|---|
| **Languages** | `Go` · `Rust` · `Ruby` · `Python` · `TypeScript` · `JavaScript` · `C` |
| **AI / Agents** | `MCP` · `Claude / Anthropic API` · `LangGraph` · `Ollama` · `GGUF / llama.cpp` · `wasmtime` |
| **Security** | `WASM sandboxing` · `SBOM / CBOM (CycloneDX)` · `SARIF` · `ML-KEM (FIPS 203)` · `TLS 1.3 hybrid KEX` |
| **Backend / Infra** | `Rack / Rails` · `net/http` · `Redis` · `PostgreSQL` · `Docker` · `GitHub Actions` |
| **Practices** | reference-validated impls · adversarial testing · reproducible benchmarks · tamper-evident audit logs |

---

## ▌ CONTRIBUTION GRAPH

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="https://raw.githubusercontent.com/bharat3645/bharat3645/output/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/bharat3645/bharat3645/output/github-contribution-grid-snake.svg">
  <img alt="Contribution snake" src="https://raw.githubusercontent.com/bharat3645/bharat3645/output/github-contribution-grid-snake-dark.svg">
</picture>

</div>

---

<div align="center">

**Every panel above is a self-hosted SVG built from live GitHub data — no third-party widget services, no unverified stats.**
<br>
Generated by [`assets/generate.py`](./assets/generate.py) · refreshed daily via [GitHub Actions](./.github/workflows/profile-assets.yml)

</div>
