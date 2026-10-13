# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-10-12 (v1.11.0 — **toolchain 6.6.2 → 6.7.9, darshana 1.0.0 → 1.3.0, BUG-003 … BUG-006 closed.** The pin move surfaced an aarch64 raw-`lseek` that had broken `:e` there; darshana 1.3.0's `TTY_SIGMASK_PIPE` closed a SIGPIPE crash that killed the editor when its language server died; `tty_sanitize_buf` closed escape injection through paths, messages and the LSP picker. Full CSI decoding with split-read carry; C1 controls shown as `<xx>`; the agnos decoder's AG1 / AG2 fixes; the teardown order darshana 1.1.4 recommends.)*

---

## Version

- **VERSION**: `1.11.0`
- **Cyrius toolchain pin**: `6.7.9`
- **Last release**: `1.11.0` — **Minor; toolchain + darshana move, four survey bugs, three defects the move surfaced.** 2026-10-12. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,098,280 B**
  - Last delta: **+35,736 B** vs 1.10.1 rebuilt at its own 6.6.2 pin (1,062,544 B). Not attributed further — a toolchain minor, a regenerated `lib/`, darshana 1.3.0 and this cut's code moved together. (1.10.0's recorded 1,201,776 B was at 6.5.35; 1.10.1 never recorded a size.)
  - **`build/cyim_agnos`**: 1,074,016 B — static x86-64 ELF64 (1.10.1: 1,038,064 B). Runs full-screen on the real agnos kernel under QEMU (`scripts/agnos-fullscreen-test.py` PASS at 1.11.0).
  - **`build/cyim_aarch64`**: 1,487,280 B — ARM aarch64 ELF64 (1.10.1: 1,615,440 B). **The whole suite runs under qemu-aarch64 now** (`cyrius test --aarch64`, 1329 / 0) — the run that exposed the raw-`lseek` `:e` failure.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: **23 suites, 1329 assertions** PASS, 0 failures, **0 warnings** *(measured at 1.11.0. +103: `tests/feed.tcyr` 52 and `tests/agnos_kbd.tcyr` 23 are new; `render.tcyr` 60 → 84; `cyimrc.tcyr` 66 → 70. The run also counts `src/test.cyr` — the `[build] test` entry, which cyrius ≥ 6.6.17 executes — as a 24th unit; it asserts nothing. The 40 "undefined function" warnings four suites and the bench harness printed on every run through 1.10.1 are gone: their include chains were completed)*
- **`cyrius test --aarch64`** (qemu-aarch64): the same 23 suites / 1329 / 0. Not a CI step.
- **`cyrius fuzz`**: **5 harnesses**, all PASS — `fuzz/{buffer,driver,tokenizer,feed}.fcyr` + `tests/cyim.fcyr`. New at 1.11.0: `fuzz/feed.fcyr`, the key-sequence decoder's **split-independence** property (300 random 64-byte streams; random 1–9-byte chunks must decode exactly as the whole stream does). The 1.10.1 decoder fails it.
- **CLI smoke** (`tests/cli_smoke.sh`): **128 PASS** (unchanged at 1.11.0).
- **Integration smoke** (`tests/integration_smoke.py`): all PASS, **58 PASS lines** (+9 at 1.11.0: file-name escape, C1 in content, Delete in INSERT, ESC timeout ×2, language server dying mid-session, stdout to a dead pipe, two `--headless` split-read inputs). ⚠ Its new cases reset SIGPIPE to SIG_DFL in the child — Python starts with SIGPIPE ignored and an exec'd child inherits that, which hides exactly the SIGPIPE deaths those cases look for. The older `drive()` cases still run with it ignored. DCE parity build re-runs it green.
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **13 passed, 0 failed**. A CI gate since 1.9.1.
- **agnos full-screen** (`scripts/agnos-fullscreen-test.py`, out-of-band, needs agnos / gnoboot / agnshi builds): PASS at 1.11.0. A variant typing `i ZED ← ← Delete Esc :wq` saved `ZDalpha line one` (1.10.1 saved `EDalpha line one` — Delete was Backspace there).
- **`cyrius audit`**: fmt / lint / tests / bench stages clean; exits 1 on its docs stage — **48 undocumented public fns, all in `tests/` and `fuzz/`** (test helpers and `main`s), the same 48 as 1.10.1. ⚠ `cyrfmt --check` (the CI gate) passes continuation indents that `cyrfmt` itself would rewrite and that `cyrius audit`'s fmt stage flags; one such line in a new test was re-indented to the formatter's output.
- **Performance benches** (`tests/perf.bcyr`): run clean; **not re-baselined at 1.11.0** — the host was shared (load average 8–18 on 16 cores). Interleaved 1.10.1 / 1.11.0 runs: `render_build_line_80c_x1000` 275–309 → 307–377 µs, ≈ 3 % of it the BUG-005 decode check and the rest the toolchain; see CHANGELOG 1.11.0 § Benchmarks. Last clean baseline remains the 1.8.6 table in [`BENCHMARKS.md`](../../BENCHMARKS.md).
- **Documentation**: `cyrius doc --check` reports **0 undocumented public fns** across `src/` + `src/plugins/`.
- **Cleanliness**: `cyrius lint` 0 warnings and **0 untracked deferrals** across `src/`, `src/plugins/`, `tests/` and `fuzz/` at 6.7.9 (whose lint flagged two comments the 6.6.2 lint passed — re-wrapped). `cyrfmt --check` clean.
- **Security**: most recent pass is the [1.11.0 release audit](../audit/2026-10-12-1.11.0-audit.md) — 3 defects found and fixed in the cut (SIGPIPE death, escape injection outside the buffer, aarch64 `:e`), plus the four survey bugs; one residual (the LSP child inherits blocked SIGWINCH / SIGPIPE — upstream fix). Prior: [1.9.x closeout](../audit/2026-08-23-1.9x-closeout.md); [1.8.x hardening](../audit/2026-08-23-1.8x-hardening.md), whose R-1a (xattrs / ACLs across the atomic save) is still open. 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version), and assert `~/.cyrius/versions/<pin>/lib` exists right after.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature.
- **CI gates** (`build-and-test` job): install → verify layout → deps → fmt → build → ELF → lint (`src/` + `src/plugins/`) → test → fuzz → bench → CLI smoke → LSP smoke → PTY integration smoke → DCE parity. Plus independent `security` and `docs` jobs. New suites and harnesses are auto-discovered (`tests/*.tcyr`, `fuzz/*.fcyr`), so 1.11.0 added no CI step.
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest.
- **Not gated**: `cyrius audit` (its docs step counts test helpers); the `--agnos` / `--aarch64` cross-builds and `cyrius test --aarch64` (they need nothing but the toolchain and qemu-user, and the aarch64 run is what would have caught the 1.10.x `:e` breakage — a candidate gate).

## Cycle in flight

**Current cycle: 1.11.x — open.** 1.11.0 opens it with the toolchain and darshana move and the four bugs darshana's consumer survey filed. No next feature is claimed; cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table).

**Open bugs: one** — BUG-007, SS3 keys (`ESC O P`..: F1–F4 on xterm-style terminals) are not decoded, so they arrive as Esc, `O` (open line above) and a letter. Deliberately not decoded at 1.11.0 — `<Esc>O` typed quickly lands in one read — so it needs a decision, not just code.

⚠ **No closeout shipped for 1.10.x.** CLAUDE.md asks for one as the last patch before a minor; 1.11.0 was cut straight from 1.10.1 at the owner's instruction, with the closeout's mechanical gates run inside it (see the [release audit](../audit/2026-10-12-1.11.0-audit.md)). A closeout is owed as the last patch of 1.11.x.

⚠ ADR 0005's **live obligation** stands: every new `.cyimrc` key must be classified local-overridable or home-only when it is added. Everything genuinely deferred is in one table: [`roadmap.md` § Everything Still Deferred](roadmap.md).

**Save semantics** are [ADR 0006](../adr/0006-atomic-save.md): atomic by default, in-place for six enumerated file shapes. `buf_save_was_atomic()` reports which path the last save took.

## Consumers

| Consumer | Status | Notes |
|---|---|---|
| `agnoshi` | Planned | Wires when the AI shell embeds cyim |
| `aethersafha` | Planned | Wires when the Wayland compositor hosts cyim |
| `daimon`-orchestrated agents | Surface ready (since v1.2.0) | Drive cyim via `--headless` (full keymap) or one-shot CLI verbs (`--write`, `--replace[-all]`, `--replace-files[-all]`, `--grep[files]`, `--batch`) with composable modifiers (`--expect[/-not/-N/-1]`, `--all`, `--context=`, `--regex=`, `--wc[=l]`, `--fuzzy-edits=`). `daimon` integrates when ready. |

## Dependencies

- **stdlib (auto-prepended)**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex`, `unicode/{_decode,categories,_categories_data,casefold,_casefold_data,normalize,_normalize_data}`.
- **stdlib (sandhi-pattern, explicit-include)**: `lib/niyama.cyr` (folded at cyrius 5.9.0 per the opt-in pattern; provides `niyama_{bre,re2,pcre,fuzzy,vim}_*`). Since 1.11.0 not vendored — resolved from the pinned snapshot, so it is always the pin's own.
- **External Cyrius deps**:
  - `vyakarana` **2.4.0** — token-level grammar/tokenizer; **46** bundled grammars routed by `src/lang.cyr` (extension + basename probes). `grammars/*.cyml` re-synced from the tag at 1.8.2 — all 45 prior files had drifted; `openqasm` is the 46th (2.3.5) and got `LANG_COUNT` 45→46 + `.qasm` routing. ⚠ Routing a language is only half of it: `src/highlight.cyr`'s `hl_grammar_name` table must also name the grammar, because `highlight_init()` suppresses vyakarana's cwd-relative `bootstrap_grammars()`. `tests/lang.tcyr` asserts both directions. 2.4.0's five chunk-boundary fixes are latent for cyim (whole-buffer tokenization) and land only if incremental re-tokenization does.
  - `cyim-lsp` **1.5.3** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin 6.5.18. 1.5.3 fixes BUG-002: `src/subprocess.cyr`'s `var argv[4]` / `var fallback[1]` were sized in pointer slots rather than bytes, so every spawn with an argument overran and `execve` failed silently. Picked up at cyim 1.9.1 with no cyim source change. Builds clean at 6.7.9; no bump needed at 1.11.0. ⚠ Two upstream asks recorded in [`roadmap.md` § Dependency notes](roadmap.md): its spawn (`lsp_proc_spawn`) does raw `fork` / `execve` without resetting the child's signal mask, so the server inherits cyim's blocked SIGWINCH and SIGPIPE; and `lsp_doc_lazy_start` retries the spawn on EVERY edit while the server is missing or dying (10 edits → 10 spawns, measured).

    What 1.5.2 itself carries is the agnos capability gate: `sys_waitpid` branched per target (agnos takes 1 arg), the spawn half (`sys_fork`/`sys_execve`/`sys_dup2`) compiled out behind matched `#ifdef`/`#ifndef CYRIUS_TARGET_AGNOS` definitions rather than left unreachable, and `LSP_HAVE_SUBPROC` / `lsp_have_subproc()` exposed. Also drops `json` from its stdlib leaves (folded into `bayan` upstream; never called) and adds `args` (agnos-only — `io.cyr`'s `getenv()` delegates to `args_agnos.cyr`); both arrive via the `dist/cyim-lsp.deps` sidecar and cyim already declares `args`.
  - `darshana` **1.3.0** — TTY / raw-mode primitives extracted from cyim's `src/tty.cyr` donor source; cyim is primary donor and first consumer. API frozen since 1.0.0 (darshana ADR 0003), additive since; **1.3.0 needs cyrius ≥ 6.7.2** (its bundle declares `const`s). Picked up at 1.11.0 with the 6.7.9 pin. cyim uses: termios (`tty_raw`, `tty_cooked`), screen (`tty_alt_enter` / `_leave`, `tty_clear`, `tty_cursor_home`, `tty_move`), `tty_winsize`, the signalfd pair plus `tty_read_signal` (resize watch) and `TTY_SIGMASK_PIPE` (SIGPIPE guard), `tty_sanitize_buf` (untrusted text outside the buffer), and the SGR composers `tty_fg_256_buf` / `tty_sgr_buf` / `tty_sgr_reset_buf` / `tty_sgr` / `tty_sgr_reset`, plus `tty_dec_buf`. Teardown follows darshana ADR 0002 as amended at 1.1.4 (cooked first, signalfds last). Not adopted, with reasons in `cyrius.cyml`: `tty_winsize_or`, `tty_raw_nonblock`, bracketed paste, the frame composers.

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux** — out-of-band; not blocking. At 1.11.0 the full suite runs under qemu-aarch64 (`cyrius test --aarch64`, 1329 / 0), which is how the raw-`lseek` `:e` breakage was found. Not run on real hardware (Pi) this cut.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.7.9` → `lib/`, **generated** by `rm -rf lib/ && cyrius deps` from `[deps].stdlib` plus the three `[deps.*]` bundles and their sidecars (46 files; `cyrius deps --locked` verifies it against `cyrius.lock`). Through 1.10.1 `lib/` was a `cyrius lib sync --full` mirror of the whole snapshot (112 files), which had gone stale: twelve folded libs in it were older than the 6.6.2 snapshot and shadowed it. `lib/niyama.cyr` is not vendored — `src/main.cyr`'s explicit `include "lib/niyama.cyr"` resolves to the pinned snapshot (`~/.cyrius/versions/6.7.9/lib`) → `src/main.cyr` → `build/cyim`.
