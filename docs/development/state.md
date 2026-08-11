# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-08-11 (v1.8.1 — the agnos build works again: `cyrius build --agnos` was failing inside the vendored `cyim-lsp` bundle on a Linux-shaped 3-arg `sys_waitpid`, so `stage-tools.sh --build` could not regenerate `/bin/cyim`. Fixed upstream and picked up as `cyim-lsp` `1.5.0→1.5.2` (agnos capability gate + `LSP_HAVE_SUBPROC`); toolchain pin `6.2.36→6.5.18` + `lib sync --full`; 10 test files repaired for missing includes. Fix-only — no editor behaviour change. See [CHANGELOG](../../CHANGELOG.md#181--2026-08-11) for full entry.)*

---

## Version

- **VERSION**: `1.8.1`
- **Cyrius toolchain pin**: `6.5.18`
- **Last release**: `1.8.1` — Patch; agnos build restored. `cyim-lsp` `1.5.0→1.5.2` carries the agnos capability gate (per-target `sys_waitpid`; `sys_fork`/`sys_execve`/`sys_dup2` compiled out behind matched `#ifdef`/`#ifndef` arms; `LSP_HAVE_SUBPROC`). Toolchain pin `6.2.36→6.5.18` + `cyrius lib sync --full`. No cyim source change for the fix — `cyim_lsp_init()` already registered nothing under `--agnos`. 2026-08-11. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,175,856 B**
  - Last delta: **−50,848 B** at 1.8.1 (cyrius `6.2.36→6.5.18` codegen + `cyim-lsp` `1.5.0→1.5.2`). Not attributed further — the pin moved across three minors, so the delta is the sum of everything 6.3/6.4/6.5 changed in codegen, not one identifiable win.
  - **`build/cyim_agnos`**: 1,184,016 B — static x86-64 ELF64, passes `stage_one`'s file-type gate in agnos's `scripts/burn/stage-tools.sh`.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: 21 suites, **1129 assertions** PASS, 0 failures *(measured at 1.8.1; the prior "22 suites / 1150" counted `src/test.cyr`, which is an empty stub returning 0 — it asserts nothing)*
- **`cyrius fuzz`**: 4 harnesses, all PASS — `fuzz/{buffer,driver,tokenizer}.fcyr` + `tests/cyim.fcyr` (10K random buffer ops, 5K keystrokes, 100×1KB tokenizer buffers). **This is the gate that matters after a toolchain bump**: cyrius 6.3.13 moved function-local `var X[N]` onto a guard-paged stack, so latent undersized buffers that were benign before now segfault.
- **CLI smoke** (`tests/cli_smoke.sh`): 118 PASS
- **Integration smoke** (`tests/integration_smoke.py`): all PASS (PTY-driven + headless-subprocess sections covering `--headless`, `--write`, `--replace[-all]`, `--grep[files]`, `--batch`, `--replace-files[-all]`, `--regex=`, `--expect[/-not/-N/-1]`, multi-window cascade). DCE parity build re-runs it green.
- ⚠ **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **4 passed, 9 failed** — `lsp_client_start_default()` answers -1 and `lsp_client_describe()` reports "(not attached)", so the spawn-plus-`initialize` handshake against a real `cyrius-lsp` is not completing. **Pre-existing and NOT from the 1.5.2 dep bump**: pinning `[deps.cyim-lsp]` back to 1.5.0 reproduces the identical 4/9 split, so both bundles fail the same way. Not an agnos issue either — this is the host/Linux path. Ruled out so far: the server itself is fine (`cyrius-lsp` is on PATH, responds to a hand-fed `initialize` with a well-formed 374-byte frame) and its startup banner goes to **stderr**, so it is not corrupting the stdout protocol stream. Not a CI gate (`cyrius smoke` is not in `.github/workflows/ci.yml`), which is how it drifted to failing while this file still claimed "13 PASS". Unowned — needs its own investigation.
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
  - `cyim-lsp` **1.5.2** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin now 6.5.18. 1.5.2 is the agnos capability gate: `sys_waitpid` branched per target (agnos takes 1 arg), the spawn half (`sys_fork`/`sys_execve`/`sys_dup2`) compiled out behind matched `#ifdef`/`#ifndef CYRIUS_TARGET_AGNOS` definitions rather than left unreachable, and `LSP_HAVE_SUBPROC` / `lsp_have_subproc()` exposed. Also drops `json` from its stdlib leaves (folded into `bayan` upstream; never called) and adds `args` (agnos-only — `io.cyr`'s `getenv()` delegates to `args_agnos.cyr`); both arrive via the `dist/cyim-lsp.deps` sidecar and cyim already declares `args`.
  - `darshana` **0.8.2** — TUI/raw-mode primitives extracted from cyim's `src/tty.cyr` donor source. cyim is primary donor + first consumer. 0.7.0 broke the API for symbols cyim calls (`tty_itoa`→`tty_dec_buf`, `tty_cooked(0)`→`tty_cooked()`, `tty_apply_raw_flags`→`_tty_apply_raw_flags`); callsites ported at 1.7.2. Advanced to 0.8.2 at 1.8.0.

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux (Pi)** — out-of-band; not blocking.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.5.18` → vendored stdlib in `lib/` (synced to the version-pinned snapshot via `cyrius lib sync --full`; exact 6.5.18 mirror, 107 modules) → external deps `lib/{vyakarana,cyim-lsp,darshana}.cyr` (re-materialized by `cyrius build`, **not** by `lib sync` — the two are independent operations) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` for the folded regex engines) → `build/cyim`.
