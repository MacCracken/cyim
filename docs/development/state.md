# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-08-23 (v1.8.2 — catch-up cut: every pin in the tree pulled to current, plus two things found underneath it. Toolchain `6.5.18→6.5.35`, `darshana 0.8.2→1.0.0` (the API freeze), `vyakarana 2.2.3→2.4.0` with all 45 bundled `grammars/*.cyml` re-synced and `openqasm` added as the 46th, `lib/` re-synced full to the 6.5.35 snapshot and the stdlib-retired `lib/agnosys.cyr` pruned. **Fixed: 34 of 45 routed languages had no syntax highlighting** — regression since 1.6.2, invisible because the failure mode is "uncolored" and the one test on that path deliberately skips `highlight_init()`. **BUG-002 root-caused**: `var argv[4]` in cyim-lsp's `_lsp_proc_exec` is sized in pointer slots, not bytes; fix is upstream. **CI repaired**: both workflows unpacked the release tarball into the flat, pre-`versions/` `~/.cyrius/{bin,lib}`, so every run died at `cyrius deps`; they now use the upstream `install.sh`. See [CHANGELOG](../../CHANGELOG.md#182--2026-08-23) for full entry.)*

---

## Version

- **VERSION**: `1.8.2`
- **Cyrius toolchain pin**: `6.5.35`
- **Last release**: `1.8.2` — Patch; dependency + toolchain catch-up. Pin `6.5.18→6.5.35`, `darshana 0.8.2→1.0.0`, `vyakarana 2.2.3→2.4.0` (+ `grammars/` re-sync, 45→46), `lib/` full re-sync to the 6.5.35 snapshot, `lib/agnosys.cyr` pruned (stdlib-retired at cyrius 6.2.37). `cyim-lsp` holds at `1.5.2` (latest tag). `openqasm` routing added, `LANG_COUNT` 45→46. **Behaviour fix**: `highlight_init()`'s grammar load list had been stuck at its original 11 since 1.6.2 while routing grew to 45, and it suppresses vyakarana's cwd-relative fallback — so 34 routed languages rendered uncolored. List is now a `hl_grammar_name(i)` table with a mutation-tested two-way drift guard in `tests/lang.tcyr`. Three files reformatted for 6.5.28's parenthesis-tracking `cyrfmt`. **CI repaired** — see CI/Release below. 2026-08-23. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,193,384 B**
  - Last delta: **+17,528 B** at 1.8.2 (cyrius `6.5.18→6.5.35` codegen + `vyakarana 2.2.3→2.4.0` scanner additions + a wholly replaced stdlib snapshot). Not attributed further — three independent movers in one cut.
  - **`build/cyim_agnos`**: 1,205,696 B — static x86-64 ELF64, passes `stage_one`'s file-type gate in agnos's `scripts/burn/stage-tools.sh`.
  - **`build/cyim_aarch64`**: 1,615,208 B — ARM aarch64 ELF64. Re-verified at 1.8.2 because darshana 0.9.2 fixed an aarch64-only ioctl misdirection on the five termios callsites cyim uses.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius tests`**: 21 suites, **1136 assertions** PASS, 0 failures *(measured at 1.8.2; +4 openqasm routing, +3 the routing↔loading drift guard. The pre-1.8.1 "22 suites / 1150" counted `src/test.cyr`, an empty stub returning 0 — it asserts nothing)*
- **`cyrius fuzz`**: 4 harnesses, all PASS — `fuzz/{buffer,driver,tokenizer}.fcyr` + `tests/cyim.fcyr` (10K random buffer ops, 5K keystrokes, 100×1KB tokenizer buffers). **This is the gate that matters after a toolchain bump**: cyrius 6.3.13 moved function-local `var X[N]` onto a guard-paged stack, so latent undersized buffers that were benign before now segfault.
- **CLI smoke** (`tests/cli_smoke.sh`): 118 PASS
- **Integration smoke** (`tests/integration_smoke.py`): all PASS (PTY-driven + headless-subprocess sections covering `--headless`, `--write`, `--replace[-all]`, `--grep[files]`, `--batch`, `--replace-files[-all]`, `--regex=`, `--expect[/-not/-N/-1]`, multi-window cascade). DCE parity build re-runs it green.
- ⚠ **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **4 passed, 9 failed** — unchanged at 1.8.2, but **root-caused**. `cyim-lsp`'s `_lsp_proc_exec` declares `var argv[4]` — four **bytes**, into which it stores up to four 64-bit pointers, so `lsp_client_start_default()` writes `[0, 24)` into a 4-byte stack slot, `execve` gets a clobbered `argv` and the child exits 127. (`var fallback[1]` alongside it is the same bug.) Proven by construction: the identical spawn with `argv[32]` / `fallback[8]` completes the handshake against the same unmodified bundle. Same bug class the 1.5.2 audit fixed once in this file (`var status_buf[1]`) and missed twice; deterministic since cyrius 6.3.13's guard-paged stack, which cyim's pin crossed at 1.8.1 — hence the timing. **Fix is a `cyim-lsp` cut**; cyim picks it up with a `tag` bump and no source change. cyim's own tree swept for the class at 1.8.2: 0 findings. Not a CI gate (`cyrius smoke` is absent from `.github/workflows/ci.yml`) — that half of the issue stands. **BUG-002 (P2)** — [`roadmap.md` § Open Bugs](roadmap.md#open-bugs), full issue doc at [`issues/2026-08-11-lsp-fold-smoke-handshake.md`](issues/2026-08-11-lsp-fold-smoke-handshake.md).
- **`cyrius audit`**: clean (fmt / lint / docs / tests / bench) as of 1.8.2. It had been failing on `tests/cyim.bcyr`, a scaffold stub from the initial commit calling a `bench()` helper that exists in no cyrius `lib/bench.cyr` — removed at 1.8.2. Advisory "100 undocumented public fns" is unchanged and not a gate.
- **Performance benches** (`tests/perf.bcyr`): 9 benches; latest numbers + the 1.6.8 comparison table in [CHANGELOG 1.8.2 § Benchmarks](../../CHANGELOG.md#182--2026-08-23). Cold tokenize `highlight_buf_1MB_cyrius` 307 ms → **281 ms** at vyakarana 2.4.0, giving back about half of the +21% the 2.0.0 streaming-API migration cost at 1.6.1. Not a `perf.bcyr` bench but measured at 1.8.2: `highlight_init()` start-up cost 0.42 ms → **1.95 ms** (11 → 46 grammars), the price of the highlighting fix. Note cyrius 6.5.19 made the bench framework subtract a measured timer floor, so cross-era deltas are approximate.
- **Cleanliness**: `cyrius lint` 0 warnings (per-file iteration over `src/` + `src/plugins/`); `cyrfmt --check` clean (`src/cli.cyr`, `src/plugins/lsp_glue.cyr` and `tests/plugin.tcyr` reformatted at 1.8.2 — cyrius 6.5.28 gave `cyrfmt` the parenthesis tracking it never had, so align-under-open-paren continuations stopped passing). ⚠ 6.5.28 also made bare `cyrius fmt <file>` **rewrite in place**; `--dry` is the report-only mode now.
- **Security**: most recent audit at [`docs/audit/2026-05-09-1.6x-closeout.md`](../audit/2026-05-09-1.6x-closeout.md) — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW new findings. Carry-over: F-CO-2 from 1.5.2 stays informational. Earlier audits: [M5](../audit/2026-04-25-security-audit.md), [M7](../audit/2026-04-25-m7-audit.md), [1.5.x closeout](../audit/2026-05-07-1.5x-closeout.md). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version). Repaired at 1.8.2 — they previously unpacked the release tarball by hand into a flat `~/.cyrius/{bin,lib}`, the layout the toolchain used before it grew `versions/`. `cyrius deps` resolves a dep bundle's sidecar stdlib leaves out of `~/.cyrius/versions/<pin>/lib`, so **every CI run failed at the deps step**. A `Verify toolchain layout` step now asserts the snapshot exists right after install, so the next packaging regression fails where it happens.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature, and fails closed when no SHA-256 tool is present.
- **CI gates** (`build-and-test` job): install → verify layout → deps → **fmt** → build → ELF → **lint (`src/` + `src/plugins/`)** → test → fuzz → bench → **CLI smoke** → PTY integration smoke → DCE parity. Plus independent `security` and `docs` jobs. The bolded three were added or widened at 1.8.2; cyim had no format gate at all until then, and `tests/cli_smoke.sh`'s 118 assertions — the `daimon` consumer contract — had never run in CI.
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest, so `cyrfmt --check src/*.cyr` checks one file and exits 0.
- **Still not a CI gate**: `cyrius smoke` (would fail today — BUG-002) and `cyrius audit`. Gating `cyrius smoke` is the structural half of BUG-002 and needs `cyrius-lsp` on the runner.

## Cycle in flight

**Current cycle: 1.8.x — demand-gated.** The 1.6.x catch-up cycle closed at 1.6.8. 1.7.1–1.7.5 were toolchain/dep-refresh cuts; **1.8.0 is the one feature cut of the era** (cyim runs on AGNOS — full-screen on the framebuffer console via `src/agnos_kbd.cyr`, or the `--line` ed/ex editor via `src/agnos_line.cyr`); 1.8.1 restored the `--agnos` *build*; 1.8.2 is this catch-up. No feature bite is in flight. **One item is now owned and waiting on an upstream cut**: BUG-002's fix is a `cyim-lsp` release, which cyim picks up with a `tag` bump and no source change. Otherwise the next cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table). Closed milestones (M0–M7, all 1.x cuts through 1.8.2) are tracked in roadmap.md's Closed Milestones table.

**Nearest closeout gate:** `1.9.0` will be the next minor, so a closeout pass is owed as the last patch before it (CLAUDE.md § Closeout Pass). 1.8.2 covers several of its steps already — full test + fuzz suite, bench baseline, security-class sweep, doc sync, clean cross-target builds — but not the dead-code audit, refactor pass, or full-diff code review.

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
  - `vyakarana` **2.4.0** — token-level grammar/tokenizer; **46** bundled grammars routed by `src/lang.cyr` (extension + basename probes). `grammars/*.cyml` re-synced from the tag at 1.8.2 — all 45 prior files had drifted; `openqasm` is the 46th (2.3.5) and got `LANG_COUNT` 45→46 + `.qasm` routing. ⚠ Routing a language is only half of it: `src/highlight.cyr`'s `hl_grammar_name` table must also name the grammar, because `highlight_init()` suppresses vyakarana's cwd-relative `bootstrap_grammars()`. `tests/lang.tcyr` asserts both directions. 2.4.0's five chunk-boundary fixes are latent for cyim (whole-buffer tokenization) and land only if incremental re-tokenization does.
  - `cyim-lsp` **1.5.2** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin 6.5.18. **Latest tag, and the one dep that needs an upstream cut**: `src/subprocess.cyr`'s `var argv[4]` / `var fallback[1]` are sized in pointer slots rather than bytes, which is BUG-002 (see Tests above). 1.5.2 remains the correct pin until a fix ships.

    What 1.5.2 itself carries is the agnos capability gate: `sys_waitpid` branched per target (agnos takes 1 arg), the spawn half (`sys_fork`/`sys_execve`/`sys_dup2`) compiled out behind matched `#ifdef`/`#ifndef CYRIUS_TARGET_AGNOS` definitions rather than left unreachable, and `LSP_HAVE_SUBPROC` / `lsp_have_subproc()` exposed. Also drops `json` from its stdlib leaves (folded into `bayan` upstream; never called) and adds `args` (agnos-only — `io.cyr`'s `getenv()` delegates to `args_agnos.cyr`); both arrive via the `dist/cyim-lsp.deps` sidecar and cyim already declares `args`.
  - `darshana` **1.0.0** — TUI/raw-mode primitives extracted from cyim's `src/tty.cyr` donor source. cyim is primary donor + first consumer. **1.0.0 is the API freeze**: 29 public fns + 37 public constants enumerated in darshana's ADR 0003 and machine-checked against the bundle upstream; byte-identical to 0.9.4. cyim names 27 of those symbols, all still frozen public surface. Code-shaped content picked up at 1.8.2 is 0.9.0–0.9.3 — darshana's own pin to 6.5.35 (0.9.1), the aarch64 `SYS_IOCTL` shadowing fix that had all five termios callsites issuing `fremovexattr` on ARM (0.9.2), and two pre-freeze breaks cyim does not trip (`tty_dec_buf`/`tty_sgr_reset_buf` gain a `-1` for negative `pos`; `AGNOS_*` → `_AGNOS_*`) (0.9.3). Earlier: 0.7.0 broke `tty_itoa`→`tty_dec_buf`, `tty_cooked(0)`→`tty_cooked()`, `tty_apply_raw_flags`→`_tty_apply_raw_flags`; callsites ported at 1.7.2.

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux (Pi)** — out-of-band; not blocking. Cross-build re-verified at 1.8.2 (`build/cyim_aarch64`, 1,615,208 B) because darshana 0.9.2 fixed an aarch64-only ioctl misdirection cyim was exposed to on all five termios callsites. Not run on real hardware this cut — the build is proof the symbol resolves, not that the Pi works.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.5.35` → vendored stdlib in `lib/` (synced to the version-pinned snapshot via `cyrius lib sync --full`; exact 6.5.35 mirror, 108 modules — `async_macos` added at 6.5.27, `agnosys` pruned by hand at 1.8.2 because it was retired from the stdlib at 6.2.37 and `lib sync` copies without pruning) → external deps `lib/{vyakarana,cyim-lsp,darshana}.cyr` (re-materialized by `cyrius build`, **not** by `lib sync` — the two are independent operations) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` for the folded regex engines) → `build/cyim`.
