# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-08-23 (v1.9.0 — **`o` / `O`: open a line below / above and enter INSERT on it.** First feature of the 1.9.x line; the roadmap had it marked "Ready to implement" since the agnos bring-up at 1.8.0 found `i` working and `o`/`O` with no handler. Undoable as one unit and dot-repeatable, both falling out of the existing insert-entry machinery. **Fixed alongside: `A` on a ONE-CHARACTER line appended BEFORE the character** — `buf_line_end(pos) == line_start` cannot tell an empty line from a one-char line, and `A` had shipped that way since it landed. Surfaced only because `o` copied the idiom and an end-to-end pty run disagreed with the unit suite.)*

---

## Version

- **VERSION**: `1.9.0`
- **Cyrius toolchain pin**: `6.5.35`
- **Last release**: `1.9.0` — **Minor; `o` / `O` open line below / above.** New action ids `ACT_OPEN_BELOW` (16) / `ACT_OPEN_ABOVE` (17), additive under ADR 0004. Undoable as one unit, dot-repeatable. Fixed alongside: `A` appended before the character on a one-character line, a bug present since `A` landed. `tests/insert.tcyr` 37 → 62 assertions. 2026-08-23. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,201,664 B**
  - Last delta: **+4,112 B** at 1.9.0 (`o` / `O` handlers + dispatch). Prior: −4,080 B at 1.8.7 (the render deduplication). Prior: 0 B at 1.8.6 (documentation only — comments do not survive compilation). Prior: +4,096 B at 1.8.5 (comment volume shifting DCE alignment; the constants-wiring itself is size-neutral). Prior: +32 B at 1.8.4 (the atomic-save path largely replaces code DCE was already keeping). Prior: +4,120 B at 1.8.3, +17,528 B at 1.8.2 (cyrius `6.5.18→6.5.35` codegen + `vyakarana 2.2.3→2.4.0` scanner additions + a wholly replaced stdlib snapshot). Not attributed further — three independent movers in one cut.
  - **`build/cyim_agnos`**: 1,209,880 B — static x86-64 ELF64, passes `stage_one`'s file-type gate in agnos's `scripts/burn/stage-tools.sh`.
  - **`build/cyim_aarch64`**: 1,615,296 B — ARM aarch64 ELF64. Re-verified at 1.8.2 because darshana 0.9.2 fixed an aarch64-only ioctl misdirection on the five termios callsites cyim uses.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius tests`**: 21 suites, **1200 assertions** PASS, 0 failures *(measured at 1.9.0; +23 for `o` / `O` plus the `A` one-character-line regression, mutation-tested in three directions. At 1.8.5: +3 closing the `diag_msg` coverage hole. At 1.8.4: +13 for ADR 0006's save-path selection tests, which assert WHICH path ran rather than only the outcome. At 1.8.3: +25 from the hardening audit's regressions, every one mutation-tested against the pre-fix source. At 1.8.2: +4 openqasm routing, +3 the routing↔loading drift guard. The pre-1.8.1 "22 suites / 1150" counted `src/test.cyr`, an empty stub returning 0 — it asserts nothing)*
- **`cyrius fuzz`**: 4 harnesses, all PASS — `fuzz/{buffer,driver,tokenizer}.fcyr` + `tests/cyim.fcyr` (10K random buffer ops, 5K keystrokes, 100×1KB tokenizer buffers). **This is the gate that matters after a toolchain bump**: cyrius 6.3.13 moved function-local `var X[N]` onto a guard-paged stack, so latent undersized buffers that were benign before now segfault.
- **CLI smoke** (`tests/cli_smoke.sh`): **128 PASS** — +6 at 1.8.4 (ADR 0006: a failed write leaves the original byte-identical and no `.cyimtmp.` behind; symlink survives; hardlink stays linked; mode 600 stays 600; a writable file in a 0555 directory still saves). +4 at 1.8.3 (audit F-1).
- **Integration smoke** (`tests/integration_smoke.py`): all PASS (PTY-driven + headless-subprocess sections covering `--headless`, `--write`, `--replace[-all]`, `--grep[files]`, `--batch`, `--replace-files[-all]`, `--regex=`, `--expect[/-not/-N/-1]`, multi-window cascade). DCE parity build re-runs it green.
- ⚠ **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **4 passed, 9 failed** — unchanged at 1.8.2, but **root-caused**. `cyim-lsp`'s `_lsp_proc_exec` declares `var argv[4]` — four **bytes**, into which it stores up to four 64-bit pointers, so `lsp_client_start_default()` writes `[0, 24)` into a 4-byte stack slot, `execve` gets a clobbered `argv` and the child exits 127. (`var fallback[1]` alongside it is the same bug.) Proven by construction: the identical spawn with `argv[32]` / `fallback[8]` completes the handshake against the same unmodified bundle. Same bug class the 1.5.2 audit fixed once in this file (`var status_buf[1]`) and missed twice; deterministic since cyrius 6.3.13's guard-paged stack, which cyim's pin crossed at 1.8.1 — hence the timing. **Fix is a `cyim-lsp` cut**; cyim picks it up with a `tag` bump and no source change. cyim's own tree swept for the class at 1.8.2: 0 findings. Not a CI gate (`cyrius smoke` is absent from `.github/workflows/ci.yml`) — that half of the issue stands. **BUG-002 (P2)** — [`roadmap.md` § Open Bugs](roadmap.md#open-bugs), full issue doc at [`issues/2026-08-11-lsp-fold-smoke-handshake.md`](issues/2026-08-11-lsp-fold-smoke-handshake.md).
- **`cyrius audit`**: clean (fmt / lint / docs / tests / bench) as of 1.8.2. It had been failing on `tests/cyim.bcyr`, a scaffold stub from the initial commit calling a `bench()` helper that exists in no cyrius `lib/bench.cyr` — removed at 1.8.2. Advisory "100 undocumented public fns" is unchanged and not a gate.
- **Performance benches** (`tests/perf.bcyr`): 9 benches, re-run and tabulated against the 1.6.8 baseline in [`BENCHMARKS.md`](../../BENCHMARKS.md) at 1.8.6 — the first re-bench since v1.6.0. ⚠ Two caveats there: cyrius 6.5.19 changed the measurement (timer floor now subtracted) and most of the improvement is the toolchain, not cyim. latest numbers + the 1.6.8 comparison table in [CHANGELOG 1.8.2 § Benchmarks](../../CHANGELOG.md#182--2026-08-23). Cold tokenize `highlight_buf_1MB_cyrius` 307 ms → **281 ms** at vyakarana 2.4.0, giving back about half of the +21% the 2.0.0 streaming-API migration cost at 1.6.1. Not a `perf.bcyr` bench but measured at 1.8.2: `highlight_init()` start-up cost 0.42 ms → **1.95 ms** (11 → 46 grammars), the price of the highlighting fix. Note cyrius 6.5.19 made the bench framework subtract a measured timer floor, so cross-era deltas are approximate.
- **Documentation**: `cyrius doc --check` reports **0 undocumented public fns** across `src/` + `src/plugins/` as of 1.8.6 (was 103). `cyrius audit`'s docs step is silent.
- **Cleanliness**: **whole tree lint-clean as of 1.8.5** — `cyrius lint` reports 0 warnings AND **0 untracked deferrals** across `src/`, `src/plugins/`, `tests/` and `fuzz/` (was 20 untracked deferrals + 10 long-line warnings). Genuine deferrals are cross-referenced to [`roadmap.md` § Deferred in-source notes](roadmap.md); false positives carry `#skip-lint` with a reason — the rule matches "follow-up" and "not yet", which in those lines are a prefix-sequence noun and assertion text. `cyrfmt --check` clean. ⚠ cyrius 6.5.28 made bare `cyrius fmt <file>` **rewrite in place**; `--dry` is the report-only mode.
- **Security**: most recent pass is the [1.8.x closeout](../audit/2026-08-23-1.8x-closeout.md) (2026-08-23) — security re-scan clean, 2 code-review findings fixed. The defect-hunting audit behind it is [`2026-08-23-1.8x-hardening.md`](../audit/2026-08-23-1.8x-hardening.md) — **1 HIGH / 1 MEDIUM / 3 LOW / 3 informational, all five code findings fixed**. **R-1 closed at 1.8.4** by [ADR 0006](../adr/0006-atomic-save.md); **R-2 closed at 1.8.5** (nothing to delete — see [architecture note 004](../architecture/004-reading-the-dce-report.md)). Still open from it: residual **R-1a** (xattrs/ACLs are not carried across the atomic path, and cyim cannot detect a non-trivial ACL without an xattr surface the stdlib lacks), and the **[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)** policy question on cwd-relative `.cyimrc`. Carry-over: F-CO-2 from 1.5.2 stays informational. Earlier audits: [M5](../audit/2026-04-25-security-audit.md), [M7](../audit/2026-04-25-m7-audit.md), [1.5.x closeout](../audit/2026-05-07-1.5x-closeout.md). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version). Repaired at 1.8.2 — they previously unpacked the release tarball by hand into a flat `~/.cyrius/{bin,lib}`, the layout the toolchain used before it grew `versions/`. `cyrius deps` resolves a dep bundle's sidecar stdlib leaves out of `~/.cyrius/versions/<pin>/lib`, so **every CI run failed at the deps step**. A `Verify toolchain layout` step now asserts the snapshot exists right after install, so the next packaging regression fails where it happens.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature, and fails closed when no SHA-256 tool is present.
- **CI gates** (`build-and-test` job): install → verify layout → deps → **fmt** → build → ELF → **lint (`src/` + `src/plugins/`)** → test → fuzz → bench → **CLI smoke** → PTY integration smoke → DCE parity. Plus independent `security` and `docs` jobs. The bolded three were added or widened at 1.8.2; cyim had no format gate at all until then, and `tests/cli_smoke.sh`'s 118 assertions — the `daimon` consumer contract — had never run in CI.
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest, so `cyrfmt --check src/*.cyr` checks one file and exits 0.
- **Still not a CI gate**: `cyrius smoke` (would fail today — BUG-002) and `cyrius audit`. Gating `cyrius smoke` is the structural half of BUG-002 and needs `cyrius-lsp` on the runner.

## Cycle in flight

**Current cycle: 1.9.x — open.** The 1.8.x cycle closed cleanly at 1.8.7 ([closeout audit](../audit/2026-08-23-1.8x-closeout.md)); **1.9.0 opens the new line with `o` / `O`**, the roadmap's "Ready to implement" item since 1.8.0.

No next feature is claimed — subsequent cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table). The two items worth settling early are unchanged: **BUG-002** (LSP dead on Linux; the fix is a `cyim-lsp` release, and the `cyrius smoke` CI gate lands green in the same cut) and **[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)** (should `.cyimrc` load from the cwd at all — cheap now, expensive once the config surface widens to keymaps). Everything deferred is in one table: [`roadmap.md` § Everything Still Deferred](roadmap.md).

⚠ A closeout pass is owed as the last patch of the 1.9.x line, before 1.10.0.

**1.9.0 opens next, and nothing deferred blocks it.** No feature bite is claimed; the next cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table). The two items worth knowing before starting: **BUG-002** (LSP dead on Linux; the fix is a `cyim-lsp` release, and the `cyrius smoke` CI gate lands green in the same cut) and **[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)** (should `.cyimrc` load from the cwd at all — cheap to settle now, expensive once the config surface widens to keymaps). Everything deferred is in one table: [`roadmap.md` § Everything Still Deferred](roadmap.md).

**Save semantics** are now [ADR 0006](../adr/0006-atomic-save.md): atomic by default, in-place for six enumerated file shapes. `buf_save_was_atomic()` reports which path the last save took — the two are otherwise indistinguishable from outside, which is how a silent fallback would rot unobserved.

**Closeout gate: satisfied.** The 1.8.x closeout shipped as 1.8.7, per CLAUDE.md § Closeout Pass. The next one is owed as the last patch of the 1.9.x line.

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
- **aarch64 Linux (Pi)** — out-of-band; not blocking. Cross-build re-verified at 1.8.2 (`build/cyim_aarch64`, 1,615,296 B) because darshana 0.9.2 fixed an aarch64-only ioctl misdirection cyim was exposed to on all five termios callsites. Not run on real hardware this cut — the build is proof the symbol resolves, not that the Pi works.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.5.35` → vendored stdlib in `lib/` (synced to the version-pinned snapshot via `cyrius lib sync --full`; exact 6.5.35 mirror, 108 modules — `async_macos` added at 6.5.27, `agnosys` pruned by hand at 1.8.2 because it was retired from the stdlib at 6.2.37 and `lib sync` copies without pruning) → external deps `lib/{vyakarana,cyim-lsp,darshana}.cyr` (re-materialized by `cyrius build`, **not** by `lib sync` — the two are independent operations) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` for the folded regex engines) → `build/cyim`.
