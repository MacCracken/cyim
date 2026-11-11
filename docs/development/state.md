# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-11-11 (v1.13.1 — **the screen scrolls.** Through 1.13.0 every frame drew from line 0, so nothing past the first screen of a file could be seen. Each window now has a view that follows the cursor; the vim scroll keys and PgUp / PgDn are added; BUG-007 (SS3 keys) and BUG-008 (rxvt `$` keys) are fixed.)*

---

## Version

- **VERSION**: `1.13.1`
- **Cyrius toolchain pin**: `6.7.18`
- **Last release**: `1.13.1` — **Patch; a scrolling view, the scroll keys, BUG-007 and BUG-008.** 2026-11-11. Full entry in CHANGELOG; audit at [`docs/audit/2026-11-11-1.13.1-audit.md`](../audit/2026-11-11-1.13.1-audit.md).

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,092,720 B**
  - Last delta: **+4,224 B** vs 1.13.0 (1,088,496 B).
  - **`build/cyim_agnos`**: 1,072,720 B — static x86-64 ELF64 (1.13.0: 1,064,400 B). Runs full-screen on the real agnos kernel under QEMU (`scripts/agnos-fullscreen-test.py` PASS at 1.13.1, re-run because the render change reaches agnos too). The `--agnos` build is a CI gate since 1.11.2.
  - **`build/cyim_aarch64`**: 1,551,360 B — ARM aarch64 ELF64 (1.13.0: 1,551,240 B). The whole suite runs under qemu-aarch64 (`cyrius test --aarch64`, 1521 / 0), a CI gate since 1.11.2.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: **25 suites, 1521 assertions** PASS, 0 failures, **0 warnings** *(measured at 1.13.1: +97 `tests/scroll.tcyr` (new), +34 `tests/feed.tcyr`, +3 `tests/render.tcyr`. The run also counts `src/test.cyr`, the `[build] test` entry, as a 26th unit; it asserts nothing)*
- **`cyrius test --aarch64`** (qemu-aarch64): the same 25 suites / 1521 / 0. A CI step (`cross-targets`) since 1.11.2.
- **`cyrius fuzz`**: **6 harnesses**, all PASS — `fuzz/{buffer,driver,tokenizer,feed,diff}.fcyr` + `tests/cyim.fcyr`. New at 1.12.2: `fuzz/diff.fcyr`, the diff's **round-trip** property (400 pairs, 40 of them past the Myers cap; a strict applier must turn every diff back into its new text). At 1.11.0: `fuzz/feed.fcyr`, the key decoder's split-independence.
- **CLI smoke** (`tests/cli_smoke.sh`): **272 PASS** (unchanged at 1.13.1; +17 at 1.13.0, +54 at 1.12.3, +29 at 1.12.2, +20 at 1.12.1, +24 at 1.12.0).
- **Integration smoke** (`tests/integration_smoke.py`): all PASS, **75 PASS lines**. New at 1.13.1: 11 view checks on a real 24 × 80 PTY (lines on screen and the cursor row after `G`, PgDn, `40 j`, arrows, `Ctrl-d` / `Ctrl-u` / `Ctrl-f`; 8 fail against 1.13.0), and the BUG-007 / BUG-008 key cases, including a `--headless` read of exactly `ESC O P`. Since 1.12.3 it includes `line_verbs_model`, 300 random `--replace-lines` / `--batch-lines` cases against an independent Python model (invalid ones must be refused with the file byte-identical). ⚠ Its PTY cases since 1.11.0 reset SIGPIPE to SIG_DFL in the child — Python starts with SIGPIPE ignored and an exec'd child inherits that, which hides exactly the SIGPIPE deaths those cases look for. DCE parity build re-runs it green.
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **13 passed, 0 failed**. A CI gate since 1.9.1.
- **agnos full-screen** (`scripts/agnos-fullscreen-test.py`, out-of-band, needs agnos / gnoboot / agnoshi builds): PASS at 1.13.1 — `ZED` typed through kbscan#42 and saved.
- **`cyrius audit`**: fmt / lint / tests / bench stages clean; exits 1 on its docs stage — **48 undocumented public fns, all in `tests/` and `fuzz/`** (test helpers and `main`s), the same 48 as 1.11.0. Since cyrius 6.7.12 its fmt stage takes `cyrfmt --check`'s verdict, so the two no longer disagree.
- **Performance benches** (`tests/perf.bcyr`): **re-baselined at 1.12.3 on a quiet host** (load 0.7–0.9) — the current table in [`BENCHMARKS.md`](../../BENCHMARKS.md). Against 1.8.6: highlighting −7 %, `render_build_line` +16 % (all of it at 1.11.0, ~20 ns per line), everything else within 2.5 %. New at 1.13.1, under load (not a re-baseline): a 22-row view frame on the 1 MB fixture is 5.6–6.0 ms at the top and 9.4–10.3 ms at the end; `render_build_line` by number is one call deeper, +3–9 % in an A/B.
- **Documentation**: `cyrius doc --check` reports **0 undocumented public fns** across `src/` + `src/plugins/`.
- **Cleanliness**: `cyrius lint` 0 warnings and **0 untracked deferrals** across `src/`, `src/plugins/`, `tests/` and `fuzz/` (true again at 1.13.1: two `tests/feed.tcyr` false positives carried since 1.11.2 are now `#skip-lint`). `cyrfmt --check` clean. Dead-code floor **29** (+2 at 1.13.1: `render_build_line` and `render_build_line_naked`, whose only callers are now tests), every symbol with a caller; 0 unused globals.
- **Security**: most recent pass is the [1.13.1 release audit](../audit/2026-11-11-1.13.1-audit.md) — nothing found; one latent line buffer bounded by a bare literal now uses `RENDER_LINE_BUF`. Residuals carried from the [1.11.0 release audit](../audit/2026-10-12-1.11.0-audit.md): the LSP child inherits blocked SIGWINCH / SIGPIPE (upstream fix), and the [1.8.x hardening](../audit/2026-08-23-1.8x-hardening.md)'s R-1a (xattrs / ACLs across the atomic save). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version), and assert `~/.cyrius/versions/<pin>/lib` exists right after.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature.
- **CI gates** (`build-and-test` job): install → verify layout → deps → fmt → build → ELF → lint (`src/` + `src/plugins/`) → test → fuzz → bench → CLI smoke → LSP smoke → PTY integration smoke → DCE parity. Plus independent `cross-targets` (new at 1.11.2: `--agnos` and `--aarch64` DCE builds, then `cyrius test --aarch64` under qemu-user — about 15 s locally), `security` and `docs` jobs. New suites and harnesses are auto-discovered (`tests/*.tcyr`, `fuzz/*.fcyr`).
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest.
- **Not gated**: `cyrius audit` (its docs step counts test helpers) and the agnos full-screen run (it needs agnos, gnoboot and agnoshi builds).

## Cycle in flight

**Current cycle: 1.13.x — open.** 1.13.0 opened it on the output side (exit 7); 1.13.1 added the scrolling view and closed BUG-007 / BUG-008. Next in the line, per [`roadmap.md`](roadmap.md): bracketed paste (a design decision first).

**Open bugs: one.** BUG-009 (filed at 1.13.1, planned for 1.14.x with `:set tabstop`): text past the window's width cannot be seen — no sideways scroll or wrap, and `$` on a long line takes the cursor off the right edge.

**Issues:** `docs/development/issues/` holds only `archive/` since 1.13.1 (both remaining issues were closed long before and re-verified).

⚠ ADR 0005's **live obligation** stands: every new `.cyimrc` key must be classified local-overridable or home-only when it is added. Every open or deferred item is in [`roadmap.md`](roadmap.md), organized by version line.

**Save semantics** are [ADR 0006](../adr/0006-atomic-save.md): atomic by default, in-place for six enumerated file shapes. `buf_save_was_atomic()` reports which path the last save took.

## Consumers

| Consumer | Status | Notes |
|---|---|---|
| `agnoshi` | Planned | Wires when the AI shell embeds cyim |
| `aethersafha` | Planned | Wires when the Wayland compositor hosts cyim |
| `daimon`-orchestrated agents | Surface ready (since v1.2.0) | Drive cyim via `--headless` (full keymap) or one-shot CLI verbs (`--write`, `--replace[-all]`, `--replace-files[-all]`, `--replace-lines`, `--grep[files]`, `--batch`, `--batch-lines`) with composable modifiers (`--expect[/-not/-N/-1/-first]`, `--all`, `--context=`, `--regex=`, `--wc[=l]`, `--fuzzy-edits=`, `--dry-run`). `daimon` integrates when ready. |

## Dependencies

- **stdlib (auto-prepended)**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex`, `unicode/{_decode,categories,_categories_data,casefold,_casefold_data,normalize,_normalize_data}`.
- **stdlib (sandhi-pattern, explicit-include)**: `lib/niyama.cyr` (folded at cyrius 5.9.0 per the opt-in pattern; provides `niyama_{bre,re2,pcre,fuzzy,vim}_*`). Since 1.11.0 not vendored — resolved from the pinned snapshot, so it is always the pin's own.
- **External Cyrius deps**:
  - `vyakarana` **2.10.0** — token-level grammar/tokenizer; **49** bundled grammars, all routed by `src/lang.cyr` (extension + basename probes) except `asm_aarch64`. `grammars/*.cyml` is a copy of the tag's `grammars/`, re-synced at every bump: the editor loads grammars from disk by absolute path, never from the bundle's embedded copies, so a stale file ships silently (`tests/lang.tcyr` loads each through that path, but cannot tell a stale file from a current one). ⚠ Routing a language is only half of it: `src/highlight.cyr`'s `hl_grammar_name` table must also name the grammar, because `highlight_init()` suppresses vyakarana's own `bootstrap_grammars()`; `tests/lang.tcyr` asserts both directions. `.asm` stays on `asm_x86_64` although vyakarana's `nasm` also claims it.
  - `cyim-lsp` **1.5.4** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin 6.6.2; 1.5.4 is a toolchain-pin release. Under `--agnos` the spawn half is compiled out and cyim registers no LSP hooks. ⚠ Two upstream asks recorded in [`roadmap.md` § Dependency notes](roadmap.md): its spawn (`lsp_proc_spawn`) does raw `fork` / `execve` without resetting the child's signal mask, so the server inherits cyim's blocked SIGWINCH and SIGPIPE; and `lsp_doc_lazy_start` retries the spawn on EVERY edit while the server is missing or dying (10 edits → 10 spawns, measured).
  - `darshana` **1.7.0** — TTY / raw-mode primitives extracted from cyim's `src/tty.cyr` donor source; cyim is primary donor and first consumer. API frozen since 1.0.0 (darshana ADR 0003), additive since; its Linux floor is cyrius ≥ 6.7.2, its AGNOS arm's ≥ 6.7.11. cyim uses: termios (`tty_raw`, `tty_cooked`), screen (`tty_alt_enter` / `_leave`, `tty_clear`, `tty_cursor_home`, `tty_move`), `tty_winsize`, the signalfd pair plus `tty_read_signal` (resize watch) and `TTY_SIGMASK_PIPE` (SIGPIPE guard), `tty_sanitize_buf` (untrusted text outside the buffer), and the SGR composers `tty_fg_256_buf` / `tty_sgr_buf` / `tty_sgr_reset_buf` / `tty_sgr` / `tty_sgr_reset`, plus `tty_dec_buf`. Teardown follows darshana ADR 0002 as amended at 1.1.4 (cooked first, signalfds last). What cyim deliberately does not adopt, and why, is in [`roadmap.md` § Dependency notes](roadmap.md).

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux** — the full suite runs under qemu-aarch64 in CI since 1.11.2 (`cyrius test --aarch64`, 1521 / 0 at 1.13.1). Not run on real hardware (Pi) this cut.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.7.18` → `lib/`, **generated** by `rm -rf lib/ && cyrius deps` from `[deps].stdlib` plus the three `[deps.*]` bundles and their sidecars (46 files; `cyrius deps --locked` verifies it against `cyrius.lock`). `lib/niyama.cyr` is not vendored — `src/main.cyr`'s explicit `include "lib/niyama.cyr"` resolves to the pinned snapshot (`~/.cyrius/versions/6.7.18/lib`) → `src/main.cyr` → `build/cyim`.
