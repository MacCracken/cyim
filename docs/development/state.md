# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-05-09 (v1.7.0 — toolchain refresh: cyrius 5.10.10 → 5.10.20, new `[deps.darshana]` at tag 0.2.0; `src/tty.cyr` strips to `tty_probe()` as donor surface moves to darshana; cyim-lsp pin moves in lockstep, no tag bump. Binary byte-identical to 1.6.8 — donor extraction was clean. See [CHANGELOG](../../CHANGELOG.md#170--2026-05-09) for full entry.)*

---

## Version

- **VERSION**: `1.7.0`
- **Cyrius toolchain pin**: `5.10.20`
- **Last release**: `1.7.0` — Minor; first cut of the post-1.6.x cycle. Toolchain 5.10.10 → 5.10.20 + darshana 0.2.0 dep pickup. 2026-05-09. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,214,656 B**
  - Last delta: byte-identical to 1.6.8 modulo `_VERSION_STR_CYIM` regen — darshana extraction is byte-equivalent at DCE.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: 22 suites, **1150 assertions** PASS, 0 failures
- **`cyrius fuzz`**: 3 harnesses, all PASS
- **CLI smoke** (`tests/cli_smoke.sh`): 118 PASS
- **Integration smoke** (`tests/integration_smoke.py`): all PASS (PTY-driven + headless-subprocess sections covering `--headless`, `--write`, `--replace[-all]`, `--grep[files]`, `--batch`, `--replace-files[-all]`, `--regex=`, `--expect[/-not/-N/-1]`, multi-window cascade)
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): 1 PASS
- **Performance benches** (`tests/perf.bcyr`): 9 benches; current numbers in [1.6.x closeout audit](../audit/2026-05-09-1.6x-closeout.md) §2 (= the v1.7.0 baseline since 1.7.0 is byte-identical to 1.6.8). Numbers in CHANGELOG per release.
- **Cleanliness**: `cyrius lint` 0 warnings (24 src files, per-file iteration); `cyrfmt --check` clean.
- **Security**: most recent audit at [`docs/audit/2026-05-09-1.6x-closeout.md`](../audit/2026-05-09-1.6x-closeout.md) — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW new findings. Carry-over: F-CO-2 from 1.5.2 stays informational. Earlier audits: [M5](../audit/2026-04-25-security-audit.md), [M7](../audit/2026-04-25-m7-audit.md), [1.5.x closeout](../audit/2026-05-07-1.5x-closeout.md). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## Cycle in flight

**Current cycle: 1.7.x — demand-gated.** The 1.6.x catch-up cycle closed at 1.6.8 (audit doc above); 1.7.0 is the user-FYI'd toolchain + darshana refresh. No specific bite is in flight; the next cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table). Closed milestones (M0–M7, all 1.x cuts through 1.7.0) are tracked in roadmap.md's Closed Milestones table.

## Consumers

| Consumer | Status | Notes |
|---|---|---|
| `agnoshi` | Planned | Wires when the AI shell embeds cyim |
| `aethersafha` | Planned | Wires when the Wayland compositor hosts cyim |
| `daimon`-orchestrated agents | Surface ready (since v1.2.0) | Drive cyim via `--headless` (full keymap) or one-shot CLI verbs (`--write`, `--replace[-all]`, `--replace-files[-all]`, `--grep[files]`, `--batch`) with composable modifiers (`--expect[/-not/-N/-1]`, `--all`, `--context=`, `--regex=`, `--wc[=l]`, `--fuzzy-edits=`). `daimon` integrates when ready. |

## Dependencies

- **stdlib (auto-prepended)**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex`, `unicode/{_decode,categories,_categories_data,casefold,_casefold_data,normalize,_normalize_data}`.
- **stdlib (sandhi-pattern, explicit-include)**: `lib/niyama.cyr` (folded at cyrius 5.9.0 per the opt-in pattern; provides `niyama_{bre,re2,pcre,fuzzy,vim}_*`).
- **External Cyrius deps**:
  - `vyakarana` **2.2.1** — token-level grammar/tokenizer; 45 bundled grammars routed by `src/lang.cyr` (extension + basename probes).
  - `cyim-lsp` **1.5.0** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. cyim-lsp's own `[package].cyrius` is at 5.10.20 in-tree but no tag yet publishes that pin.
  - `darshana` **0.2.0** — TUI/raw-mode primitives extracted from cyim's `src/tty.cyr` donor source. cyim is primary donor + first consumer. Three `[lib]` modules: termios, ansi, cursor.

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux (Pi)** — out-of-band; not blocking.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 5.10.20` → vendored stdlib in `lib/` (refreshed by `cyrius deps`) → external deps `lib/{vyakarana,cyim-lsp,darshana}.cyr` (sandhi-pattern symlinks) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` for the folded regex engines) → `build/cyim`.
