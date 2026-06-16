# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-06-15 (v1.7.3 — cyrius 6.2.7 → 6.2.11 pin, vendored `lib/` stdlib re-synced to the 6.2.11 snapshot via `cyrius lib sync` (8 unlinked modules updated; binary byte-identical). No cyim-side source or dep changes. See [CHANGELOG](../../CHANGELOG.md#173--2026-06-15) for full entry.)*

---

## Version

- **VERSION**: `1.7.3`
- **Cyrius toolchain pin**: `6.2.11`
- **Last release**: `1.7.3` — Patch; cyrius 6.2.7 → 6.2.11 pin + vendored-stdlib re-sync to the 6.2.11 snapshot. No cyim-side source/dep changes; binary byte-identical. 2026-06-15. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,226,704 B**
  - Last delta: 0 B at 1.7.3 (6.2.11 pin re-synced only unlinked stdlib modules; codegen byte-identical to 1.7.2).
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: 22 suites, **1150 assertions** PASS, 0 failures
- **`cyrius fuzz`**: 3 harnesses, all PASS
- **CLI smoke** (`tests/cli_smoke.sh`): 118 PASS
- **Integration smoke** (`tests/integration_smoke.py`): all PASS (PTY-driven + headless-subprocess sections covering `--headless`, `--write`, `--replace[-all]`, `--grep[files]`, `--batch`, `--replace-files[-all]`, `--regex=`, `--expect[/-not/-N/-1]`, multi-window cascade)
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): 13 PASS (vestigial `lib/json.cyr` include dropped at 1.7.2 — bundle is self-contained)
- **Performance benches** (`tests/perf.bcyr`): 9 benches; current numbers in [1.6.x closeout audit](../audit/2026-05-09-1.6x-closeout.md) §2. Numbers in CHANGELOG per release.
- **Cleanliness**: `cyrius lint` 0 warnings (per-file iteration over `src/`); `cyrfmt --check` clean (`src/cli.cyr` + `src/window.cyr` reformatted to 6.2.7's revised continuation-indent rule at 1.7.2).
- **Security**: most recent audit at [`docs/audit/2026-05-09-1.6x-closeout.md`](../audit/2026-05-09-1.6x-closeout.md) — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW new findings. Carry-over: F-CO-2 from 1.5.2 stays informational. Earlier audits: [M5](../audit/2026-04-25-security-audit.md), [M7](../audit/2026-04-25-m7-audit.md), [1.5.x closeout](../audit/2026-05-07-1.5x-closeout.md). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## Cycle in flight

**Current cycle: 1.7.x — demand-gated.** The 1.6.x catch-up cycle closed at 1.6.8; 1.7.0–1.7.2 are toolchain/dep-refresh cuts (1.7.2 = cyrius 6.2.7 + darshana 0.7.0 + vendored-stdlib re-sync). No specific feature bite is in flight; the next cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table). Closed milestones (M0–M7, all 1.x cuts through 1.7.2) are tracked in roadmap.md's Closed Milestones table.

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
  - `vyakarana` **2.2.3** — token-level grammar/tokenizer; 45 bundled grammars routed by `src/lang.cyr` (extension + basename probes).
  - `cyim-lsp` **1.5.0** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle; rebuilds clean against 6.2.7. No tag yet publishes a 6.2.7 in-tree pin.
  - `darshana` **0.7.0** — TUI/raw-mode primitives extracted from cyim's `src/tty.cyr` donor source. cyim is primary donor + first consumer. 0.7.0 broke the API for symbols cyim calls (`tty_itoa`→`tty_dec_buf`, `tty_cooked(0)`→`tty_cooked()`, `tty_apply_raw_flags`→`_tty_apply_raw_flags`); callsites ported at 1.7.2.

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux (Pi)** — out-of-band; not blocking.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.2.7` → vendored stdlib in `lib/` (synced to the version-pinned snapshot via `cyrius lib sync`; exact 6.2.7 mirror) → external deps `lib/{vyakarana,cyim-lsp,darshana}.cyr` (resolved by `cyrius deps`) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` for the folded regex engines) → `build/cyim`.
