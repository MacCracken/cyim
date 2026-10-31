# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-10-31 (v1.11.1 — **toolchain 6.7.9 → 6.7.18; vyakarana 2.4.0 → 2.10.0, darshana 1.3.0 → 1.7.0, cyim-lsp 1.5.3 → 1.5.4; `cyrius.cyml` cut back to a manifest.** No dependency changed an API cyim calls. The new lint's write-length rule found 25 off-by-one literal writes (24 CLI messages wrote a NUL to stderr) — fixed. Lean / MDX / NASM highlighting routed; `grammars/` re-synced.)*

---

## Version

- **VERSION**: `1.11.1`
- **Cyrius toolchain pin**: `6.7.18`
- **Last release**: `1.11.1` — **Patch; toolchain + dependency move, manifest cleanup, write-length fixes the new lint found.** 2026-10-31. Full entry in CHANGELOG.

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,057,560 B**
  - Last delta: **−40,720 B** vs 1.11.0 (1,098,280 B): −4,112 B from the pin alone, −36,608 B from the dependency move (not attributed further).
  - **`build/cyim_agnos`**: 1,033,480 B — static x86-64 ELF64 (1.11.0: 1,074,016 B). Runs full-screen on the real agnos kernel under QEMU (`scripts/agnos-fullscreen-test.py` PASS at 1.11.0; not re-run at 1.11.1).
  - **`build/cyim_aarch64`**: 1,483,440 B — ARM aarch64 ELF64 (1.11.0: 1,487,280 B). The whole suite runs under qemu-aarch64 (`cyrius test --aarch64`, 1338 / 0).
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: **23 suites, 1338 assertions** PASS, 0 failures, **0 warnings** *(measured at 1.11.1. +9, all `tests/lang.tcyr` 110 → 119: the lean / mdx / nasm routes, and every `grammars/` file must load from disk — the editor's path, which `cyrius test` otherwise never reaches because vyakarana serves its embedded copies. The run also counts `src/test.cyr` — the `[build] test` entry — as a 24th unit; it asserts nothing)*
- **`cyrius test --aarch64`** (qemu-aarch64): the same 23 suites / 1338 / 0. Not a CI step.
- **`cyrius fuzz`**: **5 harnesses**, all PASS — `fuzz/{buffer,driver,tokenizer,feed}.fcyr` + `tests/cyim.fcyr`. New at 1.11.0: `fuzz/feed.fcyr`, the key-sequence decoder's **split-independence** property (300 random 64-byte streams; random 1–9-byte chunks must decode exactly as the whole stream does). The 1.10.1 decoder fails it.
- **CLI smoke** (`tests/cli_smoke.sh`): **128 PASS** (unchanged at 1.11.1; exit codes are the contract, and the 1.11.1 write-length fixes changed only stderr bytes).
- **Integration smoke** (`tests/integration_smoke.py`): all PASS, **58 PASS lines** (+9 at 1.11.0: file-name escape, C1 in content, Delete in INSERT, ESC timeout ×2, language server dying mid-session, stdout to a dead pipe, two `--headless` split-read inputs). ⚠ Its new cases reset SIGPIPE to SIG_DFL in the child — Python starts with SIGPIPE ignored and an exec'd child inherits that, which hides exactly the SIGPIPE deaths those cases look for. The older `drive()` cases still run with it ignored. DCE parity build re-runs it green.
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **13 passed, 0 failed**. A CI gate since 1.9.1.
- **agnos full-screen** (`scripts/agnos-fullscreen-test.py`, out-of-band, needs agnos / gnoboot / agnshi builds): PASS at 1.11.0. A variant typing `i ZED ← ← Delete Esc :wq` saved `ZDalpha line one` (1.10.1 saved `EDalpha line one` — Delete was Backspace there).
- **`cyrius audit`**: fmt / lint / tests / bench stages clean; exits 1 on its docs stage — **48 undocumented public fns, all in `tests/` and `fuzz/`** (test helpers and `main`s), the same 48 as 1.11.0. Since cyrius 6.7.12 its fmt stage takes `cyrfmt --check`'s verdict, so the two no longer disagree.
- **Performance benches** (`tests/perf.bcyr`): run clean; **not re-baselined at 1.11.1** — the host was shared (load average ≈ 12 on 16 cores). Three interleaved 1.11.0 / 1.11.1 rounds put every workload within noise; `highlight_buf_1MB_cyrius` 530–553 → 481–532 ms (vyakarana 2.10.0). See CHANGELOG 1.11.1 § Benchmarks. Last clean baseline remains the 1.8.6 table in [`BENCHMARKS.md`](../../BENCHMARKS.md).
- **Documentation**: `cyrius doc --check` reports **0 undocumented public fns** across `src/` + `src/plugins/`.
- **Cleanliness**: `cyrius lint` 0 warnings and **0 untracked deferrals** across `src/`, `src/plugins/`, `tests/` and `fuzz/` at 6.7.18 (whose new write-length rule flagged 25 literal writes — fixed in 1.11.1). `cyrfmt --check` clean.
- **Security**: most recent pass is the [1.11.1 release audit](../audit/2026-10-31-1.11.1-audit.md) — one LOW (B-1, the over-length literal writes) found by the new lint and fixed; the dependency and toolchain deltas add nothing reachable. Residuals carried from the [1.11.0 release audit](../audit/2026-10-12-1.11.0-audit.md): the LSP child inherits blocked SIGWINCH / SIGPIPE (upstream fix), and the [1.8.x hardening](../audit/2026-08-23-1.8x-hardening.md)'s R-1a (xattrs / ACLs across the atomic save). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version), and assert `~/.cyrius/versions/<pin>/lib` exists right after.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature.
- **CI gates** (`build-and-test` job): install → verify layout → deps → fmt → build → ELF → lint (`src/` + `src/plugins/`) → test → fuzz → bench → CLI smoke → LSP smoke → PTY integration smoke → DCE parity. Plus independent `security` and `docs` jobs. New suites and harnesses are auto-discovered (`tests/*.tcyr`, `fuzz/*.fcyr`), so 1.11.0 added no CI step.
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest.
- **Not gated**: `cyrius audit` (its docs step counts test helpers); the `--agnos` / `--aarch64` cross-builds and `cyrius test --aarch64` (they need nothing but the toolchain and qemu-user, and the aarch64 run is what would have caught the 1.10.x `:e` breakage — a candidate gate).

## Cycle in flight

**Current cycle: 1.11.x — open.** 1.11.0 opened it with the toolchain and darshana move and the four bugs darshana's consumer survey filed; 1.11.1 is the toolchain / dependency patch. No next feature is claimed; cuts open as triggers surface (per [`roadmap.md`](roadmap.md)'s Post-1.5.x — Demand-Gated table).

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
  - `vyakarana` **2.10.0** — token-level grammar/tokenizer; **49** bundled grammars, all routed by `src/lang.cyr` (extension + basename probes) except `asm_aarch64`. `grammars/*.cyml` is a copy of the tag's `grammars/`, re-synced at every bump: the editor loads grammars from disk by absolute path, never from the bundle's embedded copies, so a stale file ships silently (`tests/lang.tcyr` loads each through that path, but cannot tell a stale file from a current one). ⚠ Routing a language is only half of it: `src/highlight.cyr`'s `hl_grammar_name` table must also name the grammar, because `highlight_init()` suppresses vyakarana's own `bootstrap_grammars()`; `tests/lang.tcyr` asserts both directions. `.asm` stays on `asm_x86_64` although vyakarana's `nasm` also claims it.
  - `cyim-lsp` **1.5.4** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin 6.6.2; 1.5.4 is a toolchain-pin release. Under `--agnos` the spawn half is compiled out and cyim registers no LSP hooks. ⚠ Two upstream asks recorded in [`roadmap.md` § Dependency notes](roadmap.md): its spawn (`lsp_proc_spawn`) does raw `fork` / `execve` without resetting the child's signal mask, so the server inherits cyim's blocked SIGWINCH and SIGPIPE; and `lsp_doc_lazy_start` retries the spawn on EVERY edit while the server is missing or dying (10 edits → 10 spawns, measured).
  - `darshana` **1.7.0** — TTY / raw-mode primitives extracted from cyim's `src/tty.cyr` donor source; cyim is primary donor and first consumer. API frozen since 1.0.0 (darshana ADR 0003), additive since; its Linux floor is cyrius ≥ 6.7.2, its AGNOS arm's ≥ 6.7.11. cyim uses: termios (`tty_raw`, `tty_cooked`), screen (`tty_alt_enter` / `_leave`, `tty_clear`, `tty_cursor_home`, `tty_move`), `tty_winsize`, the signalfd pair plus `tty_read_signal` (resize watch) and `TTY_SIGMASK_PIPE` (SIGPIPE guard), `tty_sanitize_buf` (untrusted text outside the buffer), and the SGR composers `tty_fg_256_buf` / `tty_sgr_buf` / `tty_sgr_reset_buf` / `tty_sgr` / `tty_sgr_reset`, plus `tty_dec_buf`. Teardown follows darshana ADR 0002 as amended at 1.1.4 (cooked first, signalfds last). What cyim deliberately does not adopt, and why, is in [`roadmap.md` § Dependency notes](roadmap.md).

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux** — out-of-band; not blocking. The full suite runs under qemu-aarch64 (`cyrius test --aarch64`, 1338 / 0 at 1.11.1). Not run on real hardware (Pi) this cut.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.7.18` → `lib/`, **generated** by `rm -rf lib/ && cyrius deps` from `[deps].stdlib` plus the three `[deps.*]` bundles and their sidecars (46 files; `cyrius deps --locked` verifies it against `cyrius.lock`). `lib/niyama.cyr` is not vendored — `src/main.cyr`'s explicit `include "lib/niyama.cyr"` resolves to the pinned snapshot (`~/.cyrius/versions/6.7.18/lib`) → `src/main.cyr` → `build/cyim`.
