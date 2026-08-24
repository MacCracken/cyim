# cyim — Roadmap

A phased plan for building cyim from scaffold to a daily-driver
modal text editor. **Current state lives in
[`state.md`](state.md);** this file is the sequencing — what
ships next, what's deferred, and what's refused.

---

## Guiding Principles

- **Modal grammar is fixed; everything else is up for grabs.** Vim's
  modal grammar (normal/insert/command/visual) is a 50-year proven
  interface — we inherit it. Implementation, configuration surface,
  rendering, and extensibility are designed today, not transliterated.
- **No embedded scripting language. Ever.** Vimscript, Lua, Python —
  the editor's surface is its binary. Configuration is data
  (`.cyimrc`, CYML). Refusal §0.
- **Reference, don't mimic.** Vim is the reference. cyim is what a
  modal editor looks like designed today, in a sovereign language,
  without the carried legacy of `:set compatible` and 30-year `.vimrc`
  shapes.
- **Two consumer classes, designed in parallel.** Humans drive cyim
  at a TTY. AI agents (daimon-orchestrated, Claude-style assistants
  included) drive cyim programmatically. The modal grammar is the
  same; the I/O harness differs. Don't retrofit headless drive — the
  keymap dispatch is the API surface for both.
- **Every milestone is dogfoodable.** From M1 onward, the user should
  be able to open this very file in cyim and edit it.
- **Defer what you can.** Clipboard, terminal embed, macros, anything
  that doesn't earn its keep — gated on real demand.

---

## Status

cyim is at **1.9.2** (see [`state.md`](state.md)). The 1.6.x
catch-up cycle closed at 1.6.8; 1.7.0 opened the post-catch-up
era with the darshana TUI dep pickup, and **1.8.0 is the one
feature cut since** — cyim runs on AGNOS, full-screen on the
framebuffer console (`src/agnos_kbd.cyr` reverse-maps raw Set-1
scancodes from `kbscan#42` into the byte stream `editor_feed`
already expects) or as an ed/ex line editor via `cyim --line`
(`src/agnos_line.cyr`). Everything else in the 1.7.x–1.8.x span
is toolchain, dependency and vendored-stdlib maintenance:
1.7.1–1.7.5, 1.8.1 (restoring the `--agnos` *build*) and 1.8.2
(the current catch-up — cyrius 6.5.35, darshana 1.0.0's API
freeze, vyakarana 2.4.0 with `grammars/` re-synced 45 → 46).
1.8.2 also closed a highlighting regression that had been live
since 1.6.2: 34 of the 45 routed languages had no grammar
loaded, so they rendered uncolored. Syntax highlighting now
covers everything `src/lang.cyr` routes, guarded both ways by
`tests/lang.tcyr`.

**1.8.3–1.8.6 are the hardening line and its follow-through.**
1.8.3 is the P(-1) cut — see
[`docs/audit/2026-08-23-1.8x-hardening.md`](../audit/2026-08-23-1.8x-hardening.md).
Its HIGH finding is worth knowing even if you read nothing else:
every write path in cyim treated a short `write(2)` as a
completed one, so `:w` and all six agent verbs could destroy
most of a file and report success. Fixed at 1.8.3 (the failure is reported)
and **closed at 1.8.4** (the failure is harmless): saving is now
atomic by default per [ADR 0006](../adr/0006-atomic-save.md),
with an enumerated in-place fallback for the file shapes where
renaming would break something the user relies on more.
**1.8.5** swept dead code and cleanliness — the finding was that
there was nothing to delete, and the whole tree came out
lint-clean. **1.8.6** closed the last documentation gap: every
public function is documented, and every remaining deferral is
in one table below. **1.8.7 is the closeout** — all 11 CLAUDE.md
steps, 2 code-review findings fixed, and the 94%-duplicated
`render_build_line` / `_naked` pair collapsed to a wrapper with
byte-identical output. **The 1.8.x cycle is closed.**

**1.9.0 opens the 1.9.x line with `o` / `O`** — open a line
below / above and enter INSERT on it. The roadmap had marked it
*"Ready to implement"* since the agnos bring-up at 1.8.0
surfaced the gap, and it queue-jumped as promised. Implementing
it uncovered a bug in `A` that had shipped since `A` landed:
`A` on a **one-character line** appended *before* the character,
because `buf_line_end(pos) == line_start` was used as the
"empty line" test and cannot tell an empty line from a one-char
one. Both now share `_insert_eol_pos`, which asks the buffer
rather than inferring.

The full LSP user-visible surface — diagnostics, `gd` goto-def
same-file + cross-file, `gr` references quickfix, `:lsp-*`
ex-commands, URL-decoded `file://` paths, open-in-split — is
wired and compiles clean, but **is not currently functional on
Linux**: see BUG-002 below, root-caused at 1.8.2 to a
slot-vs-byte buffer in the cyim-lsp bundle and waiting on an
upstream cut.

The 1.x plugin ABI freeze (1.3.6 / [ADR 0004](../adr/0004-plugin-abi-freeze.md))
holds across all 1.4.x and 1.5.x extensions. Three additive
extensions (`plugin_register_normal_prefix_key`, `plugin_buf_load_file`
in 1.4.2; `plugin_list_display` in 1.5.0) all landed under the
"additions allowed" envelope.

---

## Closed Milestones

Through-the-fingers list. CHANGELOG.md is the canonical record;
this is a sequencing index.

| Phase | Status |
|---|---|
| **M0** — scaffold | Done |
| **M1** — modal core (gap-buffer, raw-mode TTY, modal dispatch) | Done |
| **M2** — syntax highlighting via vyakarana | Done |
| **M3** — multi-buffer + splits + window navigation | Done |
| **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc` | Done |
| **M5** — polish: docs, perf benchmarks, fuzz, receipts | Done |
| **M6** — P(-1) hardening (cleanliness, refactor, dead-code) | Done |
| **M7** — Security audit + 0-day corpus survey | Done (0 CRITICAL / 0 HIGH / 0 MEDIUM at v1.0) |
| **v1.0** | Shipped 2026-04-25 |
| **v1.0.x / v1.1.x** — agent-drive CLI surface | Shipped 2026-04-26+ (--write/--replace/--grep/--batch/--replace-files/--context/--regex flavors) |
| **v1.2.x** — `--regex=ere` Pike NFA via cyrius stdlib | Shipped 2026-04-28 |
| **v1.3.x** — niyama fold + 6 regex flavors + plugin ABI scaffold + freeze | Shipped 2026-05-06 (1.3.0 → 1.3.7 closeout) |
| **v1.4.0** — first non-trivial external plugin folded in (cyim-lsp 1.0.2) | Shipped 2026-05-07 |
| **v1.4.1** — cyim-lsp 1.0.3 env-passthrough fix + first `cyrius smoke` harness | Shipped 2026-05-07 |
| **v1.4.2** — additive plugin ABIs (`plugin_register_normal_prefix_key`, `plugin_buf_load_file`) + `gg` motion wired | Shipped 2026-05-07 |
| **v1.4.3** — cyim-lsp 1.1.0 pickup (gd/gr keymap + cross-file goto-def) | Shipped 2026-05-07 |
| **v1.5.0** — `plugin_list_display` ABI (popup picker subsystem) | Shipped 2026-05-07 |
| **v1.5.1** — cyim-lsp 1.2.0 pickup (refs quickfix activates) | Shipped 2026-05-07 |
| **v1.5.2** — closeout audit (pre-1.6.0; all 11 steps PASS, 4 LOW findings tracked) | Shipped 2026-05-07 |
| **v1.5.3** — closes 3 of 4 LOW closeout findings (F-CO-1 multi-iter bench, F-CO-3 prefix-clear, F-CO-4 URL-decode via cyim-lsp 1.2.1) | Shipped 2026-05-07 |
| **v1.6.0** — VIM-style marks (`m<letter>` / `'<letter>`; per-buffer a-z + global A-Z) | Shipped 2026-05-07 |
| **v1.6.1** — Toolchain + vyakarana catch-up (cyrius 5.9.16 → 5.10.10; vyakarana 1.0.2 → 2.2.1; `tokenize_source` → streaming primitive migration in `src/highlight.cyr`; cyim-lsp pin moved in lockstep with no tag bump) | Shipped 2026-05-09 |
| **v1.6.2** — Grammar-routing catch-up (`LANG_COUNT` 11 → 45; 34 new grammar `.cyml` files in `grammars/`; `.cyml` migrates from "toml" to dedicated "cyml" grammar; `tests/lang.tcyr` 37 → 77 assertions) | Shipped 2026-05-09 |
| **v1.6.3** — cyim-lsp 1.3.0 pickup (`[deps.cyim-lsp].tag` 1.2.1 → 1.3.0; banner-only delta, distfile byte-identical, no cyim source changes; binary byte-identical to 1.6.2) | Shipped 2026-05-09 |
| **v1.6.4** — Basename-driven language detection (`lang_basenames(i)` table; `Dockerfile`/`Makefile`/`GNUmakefile`/`Containerfile` + `.bashrc`/`.zshrc`/`.profile` family; case-sensitive with directory-boundary check; `tests/lang.tcyr` 77 → 103 assertions) | Shipped 2026-05-09 |
| **v1.6.5** — cyim-lsp 1.4.0 pickup; reference previews in `:lsp-find-refs` (`_cyim_lsp_label_for_ref` calls `lsp_ref_preview(uri, line, 80)` and appends snippet after coordinates; falls through cleanly when preview unavailable) | Shipped 2026-05-09 |
| **v1.6.6** — Plugin ABI: `plugin_buf_load_file_split(s, path, direction)` (additive per ADR 0004; `SPLIT_HORIZONTAL`/`SPLIT_VERTICAL` constants; cyim side of the open-in-split carry-over from 1.5.x; cyim-lsp 1.5.0 will consume) | Shipped 2026-05-09 |
| **v1.6.7** — cyim-lsp 1.5.0 pickup (open-in-split for `:lsp-find-refs`) + arrow keys in list mode (CSI Up/Down → `_plugin_list_prev`/`_plugin_list_next` when picker active; Left/Right swallowed); both 1.5.x carry-over items in one pre-tag bundle | Shipped 2026-05-09 |
| **v1.6.8** — Closeout cut for the 1.6.x cycle (all 11 CLAUDE.md audit steps PASS; 0 new findings; byte-identical to 1.6.7 modulo `_VERSION_STR_CYIM` regen); audit doc `docs/audit/2026-05-09-1.6x-closeout.md` | Shipped 2026-05-09 |
| **v1.7.0** — Toolchain refresh (cyrius 5.10.10 → 5.10.20) + darshana 0.2.0 TUI dep pickup. cyim's `src/tty.cyr` strips down to `tty_probe()` only; donor surface (termios + ANSI + cursor) now resolves through darshana's `[lib]`. cyim-lsp pin moves in lockstep (no tag). Binary byte-identical to 1.6.8 — donor bodies were byte-equivalent | Shipped 2026-05-09 |
| **v1.7.1** — darshana 0.4.0 + cyrius 6.0.1 dep refresh. Forward-compat only; no cyim callsite landed on darshana's expanded surface (`tty_winsize`, `tty_open_signalfd`, `tty_sgr`) | Shipped 2026-05-20 |
| **v1.7.2** — cyrius 6.2.7 pin + darshana 0.7.0 (**first darshana cut to break symbols cyim calls**: `tty_itoa`→`tty_dec_buf`, `tty_cooked(0)`→`tty_cooked()`, `tty_apply_raw_flags`→`_tty_apply_raw_flags`; callsites ported in `src/{render,main,tty}.cyr` + `tests/tty.tcyr`) + vyakarana 2.2.3 + `lib/` re-synced to an exact 6.2.7 mirror (11 dropped stdlib modules pruned) | Shipped 2026-06-15 |
| **v1.7.3** — cyrius 6.2.11 pin + `lib/` re-sync. Pure pin move; editor source byte-for-byte unchanged, DCE binary byte-identical to 1.7.2 | Shipped 2026-06-15 |
| **v1.7.4** — darshana 0.8.0 (agnos `tty_winsize` branch via `winsize#60`). Additive; symbol vendored, not yet called | Shipped 2026-06-22 |
| **v1.7.5** — cyrius 6.2.36 pin. No source change | Shipped 2026-06-22 |
| **v1.8.0** — **cyim runs on AGNOS.** Full-screen on the framebuffer console via new `src/agnos_kbd.cyr` (polls `kbscan#42`, tracks shift/ctrl/caps from make/break codes, reverse-maps Set-1 scancodes to the raw-terminal byte stream `editor_feed` already consumes); `src/agnos_line.cyr` ships an ed/ex line editor behind `cyim --line`. Entry point switched to the bare-call `_agnos_entry()` pattern (the module-scope `var exit_code = main();` double-ran on agnos, and literal `syscall(60, …)` is `winsize` there, not exit). LSP gated Linux-only. darshana 0.8.0 → 0.8.2. Verified on the real kernel under QEMU and under mirshi ≥ 1.11.0; Linux/macOS builds byte-unchanged | Shipped 2026-07-08 |
| **v1.8.1** — the agnos *build* restored. `cyrius build --agnos` was failing inside the vendored cyim-lsp bundle on a Linux-shaped 3-arg `sys_waitpid`; fixed upstream and picked up as cyim-lsp 1.5.0 → 1.5.2 (per-target `sys_waitpid`, spawn half compiled out behind matched `#ifdef`/`#ifndef` arms, `LSP_HAVE_SUBPROC` exposed). Toolchain pin 6.2.36 → 6.5.18 + `lib sync --full`; 10 test files repaired for missing includes. No cyim source change for the fix | Shipped 2026-08-11 |
| **v1.8.2** — dependency + toolchain catch-up, **plus the highlighting regression it uncovered**. cyrius 6.5.18 → 6.5.35; darshana 0.8.2 → **1.0.0** (the API freeze; carries 0.9.2's aarch64 `SYS_IOCTL` fix and two pre-freeze breaks cyim does not trip); vyakarana 2.2.3 → 2.4.0 with all 45 `grammars/*.cyml` re-synced and `openqasm` added as the 46th (`LANG_COUNT` 45 → 46, `.qasm` routing); `lib/` full re-sync to the 6.5.35 snapshot and `lib/agnosys.cyr` pruned (stdlib-retired at cyrius 6.2.37; `lib sync` copies without pruning). **Fixed: 34 of 45 routed languages rendered uncolored** — `highlight_init()`'s grammar load list stayed at its original 11 through 1.6.2's 11 → 45 routing growth, and it suppresses vyakarana's cwd-relative fallback, so a missing entry means no grammar rather than a slower path. Load list is now the `hl_grammar_name(i)` table with a two-way, mutation-tested drift guard in `tests/lang.tcyr`. Three files reformatted for 6.5.28's parenthesis-tracking `cyrfmt`. **CI repaired**: both workflows hand-unpacked the release tarball into the flat, pre-`versions/` `~/.cyrius/{bin,lib}`, so every run died at `cyrius deps` — they now delegate to the upstream `install.sh` (patra's shape), pinned to the tag, with a layout-assertion step; a format gate, a CLI-smoke gate and `src/plugins/` linting were added alongside. **BUG-002 root-caused** — see Open Bugs | Shipped 2026-08-23 |
| **v1.8.3** — **P(-1) audit / refactor / hardening / security pass.** 1 HIGH, 1 MEDIUM, 3 LOW, 3 informational; all five code findings fixed with mutation-tested regressions. HIGH: `buf_save_file` treated a short `write(2)` as success, so `:w` cleared the modified flag and all six agent verbs exited 0 on a truncated file (measured 475 of 575 bytes lost) — and made `--batch`'s documented atomicity false. MEDIUM: an unvalidated `.cyimrc` palette value reached a backward-filled buffer index and overran `render_build_line`'s 12-byte escape reservation. LOW ×3: render scratch buffers bounded by terminal geometry rather than their own size (latent until resize support lands), an i64-undersized itoa scratch, and an integer parser that wrapped instead of rejecting. Docs: ADR 0005 filed (Proposed), the missing `docs/adr/{README,template}.md` and `docs/architecture/README.md` written, architecture notes 002 and 003 added, and two doc claims that contradicted the code corrected. Suite 1136 → 1161; CLI smoke 118 → 122; benchmarks unmoved | Shipped 2026-08-23 |
| **v1.8.4** — **Atomic save** ([ADR 0006](../adr/0006-atomic-save.md)), closing audit residual R-1. A save writes a sibling temp, `fchmod`s it to the target's mode, writes, `fsync`s, `rename`s over the target, then `fsync`s the parent directory — so a write that dies part way leaves the original bit-for-bit intact. Atomic by DEFAULT, not unconditionally: six enumerated conditions (symlink, `nlink > 1`, non-regular file, foreign uid, non-writable directory, agnos) take the in-place path, because rename changes the inode and for those shapes that breaks something the user relies on more. Return contract unchanged; no call site touched. `buf_save_was_atomic()` added so a silent fallback cannot rot unobserved. Suite 1161 → 1174; CLI smoke 122 → 128; both the conditions and the fall-through logic mutation-tested | Shipped 2026-08-23 |
| **v1.8.5** — **Dead-code + cleanliness cut**, closing audit residual R-2 — with the honest answer that there was nothing to delete: all 24 cyim-side unreachable functions are frozen ABI, test-only introspection, or documented-deferred config, and the one symbol with no caller anywhere (`diag_msg`) was a coverage hole closed with a test. Real dead code sat one level down: **five named constants the code was not using** (`BUFFER_REC_SIZE`, `RENDER_LINE_BUF`, `KEY_CTRL_R`, the `REPLACE_*` pair, `_CYIMRC_PALETTE_SLOTS`) — the same size-expressed-twice shape the last two audits kept finding. Four wired up, one deleted as unusable by construction. **Five stale comments** corrected, describing states that had stopped being true up to five minors earlier. **20 untracked lint deferrals → 0**: 8 cross-referenced to a new roadmap § Deferred in-source notes, 5 stale ones corrected, 7 false positives given `#skip-lint` with a reason. Ten over-length test lines wrapped. Suite 1174 → 1177; whole tree now lint-clean | Shipped 2026-08-23 |
| **v1.8.6** — **Documentation sweep.** `cyrius audit`'s "101 undocumented public fns" advisory → **0**: every public function in `src/` and `src/plugins/` now carries a docstring saying what it *means* rather than what it loads — the 40-accessor editor-state block in `mode.cyr` and the 20-accessor window record are the bulk, and both now read as self-describing tables instead of requiring a scroll to the layout comment. Doc-tree sweep alongside: README's status was four minors stale (still "1.7.5 — released", old pins, "3 fuzz harnesses"), SECURITY.md's most recent state was "v1.6.0: 0 CRITICAL / 0 HIGH" when the 1.8.3 audit had since found a HIGH, and BENCHMARKS.md had not been re-run since v1.6.0. All three current. Roadmap gains a single **Everything Still Deferred** table — the 1.8.x line had left open items in four separate places | Shipped 2026-08-23 |
| **v1.8.7** — **Closeout cut for the 1.8.x cycle**, all 11 CLAUDE.md steps ([audit](../audit/2026-08-23-1.8x-closeout.md)). 2 code-review findings, both fixed: `sys_fchmod`'s return was discarded in the atomic save path, so a failure would have let the rename proceed at 0644 — a mode-600 file coming back world-readable with no error (now a pre-write fallback to in-place, which is what "cannot preserve the mode" means, plus a duplicate `stat` dropped); and `_hl_load_one` wrote into a 1024-byte scratch whose bound was distributed across three functions with nowhere stating it. **Refactor:** `render_build_line` and `render_build_line_naked` were **94.4% identical** — and the 1.8.3 audit had to apply the same bounds fixes to both copies — collapsed to a wrapper, verified byte-identical across 46 cases, `render.cyr` 723 → 663 lines, binary −4,080 B. Dead-code floor 24 with every symbol having a caller; 0 unused globals; security re-scan clean; downstream `agnoshi` / `aethersafha` confirmed not yet integrated | Shipped 2026-08-23 |
| **v1.9.0** — **`o` / `O`: open a line below / above and enter INSERT.** New action ids `ACT_OPEN_BELOW` (16) / `ACT_OPEN_ABOVE` (17), additive under ADR 0004. Undoable as one unit and dot-repeatable with no special-casing — `_dot_begin` and `undo_record_pre_op` already key off "enters INSERT", so adding the two actions to those lists is the whole integration. **Fixed alongside: `A` appended BEFORE the character on a one-character line** — `buf_line_end(pos) == line_start` cannot distinguish an empty line from a one-char line, and `A` had shipped that way since it landed. Surfaced only when `o` copied the idiom and an end-to-end pty run disagreed with the unit suite; both call sites now share `_insert_eol_pos`. `tests/insert.tcyr` 37 → 62 assertions, mutation-tested in three directions | Shipped 2026-08-23 |
| **v1.9.1** — **BUG-002 closed; LSP works.** `[deps.cyim-lsp]` `1.5.2 → 1.5.3` with **no cyim source change** — the defect was upstream (`var argv[4]`, four bytes for four 64-bit pointers, so every spawn with an argument overran and `execve` failed silently). `cyrius smoke` 4 passed / 9 failed → **13 / 0**. Everything the LSP surface shipped since 1.4.0 was correct code that never got to run. **`cyrius smoke` is now a CI gate** — the structural half, held back at 1.8.2 because a gate that fails on day one gets ignored, landed here green | Shipped 2026-08-23 |
| **v1.9.2** — **[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md) decided and implemented.** Config lives in `$XDG_CONFIG_HOME/cyim/cyimrc` (else `$HOME/.config/cyim/cyimrc`); `./.cyimrc` overrides it **key by key**. Before this, cyim read config from only the cwd, so nothing followed a user between projects. Local override accepted with no gate — the trade is sized by what `.cyimrc` can express, and the worst a hostile directory achieves is a wrong colour. Held honest by a rule rather than machinery: every new key gets classified local-overridable or home-only. Backward compatible; `tests/cyimrc.tcyr` 50 → 59 assertions including a reversed-order control | Shipped 2026-08-23 |

Verbose milestone descriptions for M0–M7 lived here in the v1.x
era; trimmed at v1.5.x cycle cleanup. The full record is in
CHANGELOG.md and the per-version state.md narrative.

---

## v1.5.x Cycle — Deferred Polish (before 1.6.0)

The 1.4.x → 1.5.x arc lit up the full LSP user-visible surface.
**Closeout audit shipped at 1.5.2; 3 of 4 LOW findings closed
at 1.5.3.** Remaining 1.5.x deferred-polish items are
carry-over candidates — bigger than LOW; not blocking 1.6.0.

### Closeout findings (from v1.5.2 audit) — status

| ID | Class | Status |
|---|---|---|
| ~~**F-CO-1**~~ | perf | ✅ **Closed in v1.5.3.** Multi-iter bench (`tests/perf.bcyr` 10× outer for short-runtime, 3× outer for medium-runtime). Verdict: the +18% render_build_line "regression" was 1-iter sampling noise; multi-iter shows 250 μs avg ± 4 μs across 10 iters. See [`BENCHMARKS.md`](../../BENCHMARKS.md) v1.5.3 row. |
| **F-CO-2** | refactor | **Informational — defer.** "Load uri + jump to lc" pattern at 2 instances. Per "wait for the third instance" rule, no action until cyim-lsp grows `:lsp-implementation` or `:lsp-type-definition`. Then extract `_cyim_lsp_jump_to_uri_lc(s, uri, line, char, err_msg)`. |
| ~~**F-CO-3**~~ | defense-in-depth | ✅ **Closed in v1.5.3.** `plugin_list_display` clears latched prefix at entry (`editor_set_prefix(s, 0)`). Unreachable today, but the corner case is closed once. +3 assertions in `tests/plugin.tcyr`. |
| ~~**F-CO-4**~~ | UX | ✅ **Closed in v1.5.3.** cyim-lsp 1.2.1 added public `lsp_uri_decode(uri)` to the bundle (real source change, +77 lines). cyim's `src/plugins/lsp_glue.cyr` cross-file branches use it. Files with spaces / non-ASCII / `%XX` escapes in `file://` URIs now load correctly. Closes the deferred-LSP-polish URL-decode row simultaneously. |

### Deferred LSP polish — carry-over to 1.6.x

Bigger than LOW; not closeout findings. As of 1.6.2 these are
formally placed in the **v1.6.x Cycle** section below as
**v1.6.5** (reference previews), **v1.6.6** (open-in-split ABI),
and **v1.6.7** (arrow keys in list mode). They lost their
"trigger-gated only" status when the 1.6.x cycle absorbed them
as catch-up bites.

### Closeout Pass — ✅ shipped 2026-05-07 as v1.5.2

[Audit doc](../audit/2026-05-07-1.5x-closeout.md). Pure
verification cut; no runtime code changes (binary byte-identical
to 1.5.1 modulo the regenerated `_VERSION_STR_CYIM`). All 11
CLAUDE.md closeout steps PASS. 0 CRITICAL / 0 HIGH / 0 MEDIUM /
4 LOW. Of the 4 LOW: F-CO-1 / F-CO-3 / F-CO-4 closed at 1.5.3;
F-CO-2 informational.

---

## v1.6.x Cycle — Catch-Up Channel

The 1.6.x line is split: 1.6.0 was a feature minor (marks);
1.6.1+ is a **catch-up channel** to absorb infrastructure
drift accumulated across the 1.4.x–1.5.x feature push. Toolchain
+ vyakarana already moved through; the rest finishes deferred
LSP polish carried over from 1.5.x and republishes cyim-lsp
under the new toolchain.

### Shipped

| Cut | Theme | Status |
|---|---|---|
| **v1.6.1** | cyrius 5.9.16 → 5.10.10 + vyakarana 1.0.2 → 2.2.1 (single breaking surface: `tokenize_source` → streaming primitive in `src/highlight.cyr`); cyim-lsp's own pin moves in lockstep, no tag bump. | ✅ Shipped 2026-05-09 |
| **v1.6.2** | Wire vyakarana 2.2.1's 35 new grammars into `src/lang.cyr` extension routing + ship the matching grammar `.cyml` files in `grammars/`. `LANG_COUNT` 11 → 45. `.cyml` extension migrates from "toml" to dedicated "cyml" grammar. | ✅ Shipped 2026-05-09 |
| **v1.6.3** | cyim-lsp 1.3.0 cut + pickup. cyim-lsp's `[package].cyrius` had moved to 5.10.10 in 1.6.1; 1.3.0 publishes that as a tag (banner-only distfile delta), and cyim 1.6.3 bumps `[deps.cyim-lsp].tag` to 1.3.0. Pure infrastructure on both sides; binary byte-identical to 1.6.2. | ✅ Shipped 2026-05-09 |
| **v1.6.4** | Basename-driven language detection. New `lang_basenames(i)` table in `src/lang.cyr` populated for shell (`.bashrc` family), dockerfile (`Dockerfile`/`Containerfile`), and makefile (`Makefile`/`GNUmakefile`). Case-sensitive equality with `/` directory-boundary check; basename probe runs before extension probe in `detect_language_from_path`. `tests/lang.tcyr` 77 → 103 assertions. | ✅ Shipped 2026-05-09 |
| **v1.6.5** | cyim-lsp 1.4.0 pickup. Tag bump 1.3.0 → 1.4.0 plus `src/plugins/lsp_glue.cyr` mirror of cyim-lsp's `_cyim_lsp_label_for_ref` change — calls `lsp_ref_preview(uri, line, 80)` and appends snippet after coordinates separated by two spaces. Closes the long-standing "reference previews" carry-over from 1.5.x deferred polish. No new cyim ABI surface. | ✅ Shipped 2026-05-09 |
| **v1.6.6** | Open-in-split ABI: `plugin_buf_load_file_split(s, path, direction)` added to `src/plugin.cyr`. Additive per ADR 0004's freeze envelope — `plugin_buf_load_file` unchanged. New public constants `SPLIT_HORIZONTAL = 0` / `SPLIT_VERTICAL = 1`. Implementation reuses dedup + load helpers, then `window_split_active` + focus move to new sibling. `tests/plugin.tcyr` 88 → 109 assertions. cyim-lsp 1.5.0 (next) consumes for ref-jumping UX; ABI dormant until then. | ✅ Shipped 2026-05-09 |
| **v1.6.7** | cyim-lsp 1.5.0 pickup (open-in-split) **+ arrow keys in list mode** — both 1.5.x carry-over polish items in a single pre-tag cut. Tag bump 1.4.0 → 1.5.0; cyim-lsp's `[lib]` source unchanged (banner-only distfile delta); example glue refactored. cyim's `src/plugins/lsp_glue.cyr` mirrors: `_cyim_lsp_ref_split_mode` global, `_cyim_lsp_ex_find_refs_with_mode(s, mode)` helper, three ex-commands (`:lsp-find-refs` / `-split` / `-vsplit`); on_select branches mode 0/1/2 → `plugin_buf_load_file` / `plugin_buf_load_file_split`. Arrow keys: `src/driver.cyr` `editor_feed` CSI dispatch routes `ESC [ A` / `ESC [ B` to `_plugin_list_prev` / `_plugin_list_next` when picker active; Left/Right swallowed; outside list mode the existing `motion_apply` routing is unchanged. `tests/plugin.tcyr` 88 → 125 assertions (+37 net). All 1.5.x deferred-polish carry-overs now closed. | ✅ Shipped 2026-05-09 |
| **v1.6.8** | **Closeout cut for the 1.6.x cycle.** Pure verification per CLAUDE.md "Closeout Pass" policy. All 11 audit steps PASS; 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW new findings. Binary byte-identical to 1.6.7 modulo `_VERSION_STR_CYIM` regen. Carry-over F-CO-2 (informational since 1.5.2) stays at instance 2. Cyim-side dead-code floor 24 → 22 (net -2). Cumulative 1.6.x test growth: 973 → 1150 assertions (+177). Bench: cold-tokenize 253ms → 307ms (+21% — documented vyakarana 2.0.0 alloc-overhead trade); cache-hit hot path within sampling noise. Audit doc: [`docs/audit/2026-05-09-1.6x-closeout.md`](../audit/2026-05-09-1.6x-closeout.md). | ✅ Shipped 2026-05-09 |

### v1.7.0 — Toolchain refresh + darshana TUI dep pickup ✅ shipped 2026-05-09

What landed:

- **`cyrius` toolchain pin 5.10.10 → 5.10.20.** 10 patches of
  stdlib drift absorbed via `cyrius deps`; bench numbers within
  sampling noise.
- **New `[deps.darshana]` block** at tag `0.2.0`. Three
  bundled modules (`termios`, `ansi`, `cursor`) — extracted
  byte-for-byte from cyim's `src/tty.cyr` donor source. cyim
  is the primary donor and first consumer.
- **cyim-lsp lockstep**: `cyim-lsp/cyrius.cyml [package].cyrius`
  → 5.10.20; no tag bump (mirrors 1.6.1's in-tree edit pattern).
  `[deps.cyim-lsp].tag` stays at 1.5.0; a future cyim-lsp tag
  publishes the pin (cyim picks up later, similar to how 1.6.3
  picked up cyim-lsp 1.3.0 after 1.6.1's lockstep edit).
- **`src/tty.cyr` shrank 207 → ~37 lines** (~82% reduction).
  `tty_probe()` and the Linux ifdef guard are the only cyim-
  internal pieces that stayed; everything else now resolves
  through darshana's bundle.
- vyakarana stayed at 2.2.1 (no newer tag).

**Binary byte-identical to 1.6.8** modulo `_VERSION_STR_CYIM`
regen — the donor extraction was clean: bodies were
byte-identical, DCE coalesces to the same image.

The 1.7.x cycle now opens demand-gated. Next major work
windows (macros, folding, system clipboard via aethersafha,
terminal emulator embed) all require user demand or a real
trigger.

### Watch list (architectural debt; not yet earning a bite)

| Item | Forcing function |
|---|---|
| `lang.cyr` if-chain refactor | **Trigger fired at 1.8.2, and the shape of the refactor is now clearer.** 46 entries, and as of 1.8.2 there is a *second* if-chain that must stay in lockstep with it — `hl_grammar_name(i)` in `src/highlight.cyr`. Their silent divergence is precisely what cost 34 languages their highlighting for six minor versions. 1.6.2 (extension catch-up) was instance 1; 1.6.4 added a new parallel table rather than growing the existing one; 1.8.2's `openqasm` append is the third growth, satisfying CLAUDE.md's "wait for the third instance". `tests/lang.tcyr`'s drift guard makes divergence loud, which downgrades this from correctness risk to maintenance debt — but the right end state is one table, not three chains plus a guard. Owed: an ADR choosing between parallel global string arrays and a vyakarana metadata query (`grammar_count()` / `grammar_name_at(i)` would let the load list be derived rather than restated), then the refactor. |
| `_cyim_lsp_*` shape duplication (cyim-lsp example glue ↔ cyim's `src/plugins/lsp_glue.cyr`) | The mirror pattern is instance-counting per CLAUDE.md "wait for the third": (1) `_cyim_lsp_label_for_ref` (1.6.5 — preview format), (2) `_cyim_lsp_ex_find_refs_with_mode` + `_cyim_lsp_on_ref_select` mode-branch + `_cyim_lsp_ref_split_mode` global (1.6.7 — open-in-split). The mirror itself is by design (cyim-lsp's bundle is self-contained; consumer copies the glue), but if a third example-glue refactor lands and the glue divergence becomes a maintenance burden, generalize the mirror into a documented copy-from-upstream procedure or a more aggressive bundle inclusion. |
| F-CO-2 (extract `_cyim_lsp_jump_to_uri_lc`) | Informational since 1.5.2. Still 2 instances; cyim-lsp `:lsp-implementation` or `:lsp-type-definition` would be the third. |

---

## Post-1.5.x — Demand-Gated

Truly-future work. Each is gated on a real trigger; deliberately
not slated.

| Feature | Trigger | Notes |
|---|---|---|
| **System clipboard** | Wayland integration via `aethersafha` | Belongs in compositor layer, not editor. cyim's yank/paste single-register stays the in-editor primitive. |
| **Terminal emulator embed** | Third user asks for `:term` | Until then, `Ctrl-z` + shell is fine. |
| **Macros** (`q<reg>` recording) | Recurring user need surfaces | Vim's macro DSL is a sequence-replay primitive, not a scripting language — fits the no-embedded-scripting refusal. |
| **Folding** (`zM` / `zR` / `:foldenable`) | User asks while editing > 1 KLOC source | Range-marked spans + render skip; structural folds (function / block) require a vyakarana-style structural marker pass. |
| **`:make` / `:cnext` quickfix flow** | User asks | Native compiler-driven flow is what `gr` already prototypes. `:make` runs an external compiler, captures stderr, parses error format, populates the same `plugin_list_display` machinery. Consumer-side patch (no cyim ABI change). |
| **Plugin system beyond sandhi** | Probably never | Refusal §0 — the sandhi pattern (vendored bundle + cyim-side glue) is already "the plugin system". Nothing beyond it earns its keep. |

---

## Everything Still Deferred

**One table, every open item.** Consolidated at 1.8.6 because the 1.8.x line
left deferrals in four places — the hardening audit's residuals, an ADR filed
Proposed, an architecture note recording an accepted limitation, and a
refactor whose trigger had fired — and no single page listed them. Anything
deferred from here on belongs in this table or it does not exist.

Ordered by what it would cost a user, not by when it was filed.

| ID | Item | Why it is still open | What would move it |
|---|---|---|---|
| ~~**ADR 0005**~~ | ~~Should `.cyimrc` be loaded from the current directory at all?~~ | ✅ **Decided and implemented at v1.9.2.** Config lives in `$XDG_CONFIG_HOME/cyim/cyimrc`; `./.cyimrc` overrides it key by key, accepted with no gate because the whole surface is ten colour indexes. **The live obligation it leaves**: every new `.cyimrc` key must be classified local-overridable or home-only when added, per [ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)'s table. Keymaps are the first serious candidate for home-only |
| **R-1a** | Extended attributes and ACLs are not carried across the atomic save path | `fchmod` preserves permission bits; xattrs, POSIX ACLs and SELinux labels are not copied, and cyim cannot *detect* a non-trivial ACL without an `xattr` surface the stdlib does not expose. Narrow: needs an ACL'd file, owned by the invoking user, not a symlink, not hardlinked | A stdlib `listxattr`/`getxattr` surface — then the detection becomes a sixth in-place condition in [ADR 0006](../adr/0006-atomic-save.md) |
| **`lang.cyr` refactor** | Two if-chains (`lang_name` / `hl_grammar_name`) that must stay in lockstep | Trigger fired at 1.8.2 (third growth). Their silent divergence is what cost 34 languages their highlighting for six minor versions. The drift guard makes divergence loud, which downgrades this from correctness risk to maintenance debt | An ADR choosing between parallel global string arrays and a **vyakarana metadata query** — `grammar_count()` / `grammar_name_at(i)` would let the load list be *derived* rather than restated, which is the real end state |
| **F-7 / arch 003** | The renderer is byte-oriented: C1 pass-through, no double-width or combining-character handling | [Accepted and documented](../architecture/003-render-is-byte-oriented.md), not a defect queue. The obvious "fix" breaks every non-ASCII file, because `0x80`–`0x9F` overlaps UTF-8 continuation bytes | A consumer editing CJK or RTL text in earnest — `aethersafha` hosting cyim is the likeliest. It needs a codepoint coordinate system threaded through cursor / undo / marks / search, not a render patch |
| **Resize-aware rendering** | `scr_cols` is a hardcoded 80 on Linux/macOS; `tty_winsize` is consulted only under agnos | Named since 1.7.4. darshana has shipped the primitives (`tty_winsize`, `tty_open_signalfd`, `TTY_SIGMASK_WINCH`) since 0.4.0 — cyim simply does not call them | Whoever wants a resizable editor. ⚠ The render scratch buffers were bounded by terminal geometry until 1.8.3 fixed them precisely *because* this feature would have made that live — the guards are already in place |
| **F-CO-2** | Extract `_cyim_lsp_jump_to_uri_lc` | Informational since 1.5.2. Still 2 instances; CLAUDE.md's "wait for the third" applies | `:lsp-implementation` or `:lsp-type-definition` would be the third |

Closed from this list recently: **ADR 0005** at 1.9.2 (decided *and* implemented — see the live obligation it leaves above); **BUG-002** and the **`cyrius smoke` CI gate**
at 1.9.1 (cyim-lsp 1.5.3's `argv` fix — a tag bump with no cyim source
change); **R-1** (non-atomic save) at 1.8.4 via
[ADR 0006](../adr/0006-atomic-save.md); **R-2** (dead-code floor) at 1.8.5 —
there was nothing to delete, see
[architecture note 004](../architecture/004-reading-the-dce-report.md); the
**101 undocumented public fns** advisory at 1.8.6, now zero.

---

## Deferred in-source notes

Comments in `src/` that defer work. Tracked here so `cyrius lint`'s
untracked-deferral rule has something to point at, and — more usefully — so
the deferrals are visible in one place instead of only to whoever happens to
read that file. Added at **1.8.5**, when the lint sweep found 20 untracked
deferrals and five of them turned out to be **stale**: describing a state that
had stopped being true, in some cases years of cuts ago.

| Where | Deferred | Status |
|---|---|---|
| `src/cli.cyr` (regex caveats), `src/main.cyr` (`--help`) | Backreferences (`\1`) in regex flavors | Engine-side, not cyim's: deferred per niyama's own v1 plan. Reassess when niyama ships them |
| `src/command.cyr` | Multi-byte ex ranges (`:1,5d`), `:%s/x/y/`, tab-completion, `:!cmd` | Out of scope since M1. `:!cmd` is additionally constrained by Refusal §0 — see Non-Goals |
| `src/driver.cyr` | Dot-repeat captures insert sessions only; `x` / paste / visual are not replayable | The hook structure accepts them; needs a bite |
| `src/driver.cyr` | A split CSI escape (ESC and `[`+final arriving in separate reads) dispatches a spurious mode-exit | Needs a 1-iteration look-ahead buffer. Not observed on modern terminals; plausible on slow serial |
| `src/marks.cyr` | `viminfo`-style mark persistence across sessions | Post-1.6 and still unclaimed — gated on persistence earning its keep. *(The note said "post-1.6"; corrected at 1.8.5 from a stale "1.6.x" window that had closed.)* |
| `src/marks.cyr` | A `:marks` command | `marks_count` exists for it. *(Was "deferred to 1.6.x" — stale, corrected at 1.8.5.)* |
| `src/mode.cyr` | `cfg_line_numbers` / `cfg_tabstop` are stored but not rendered | Documented in [`cyimrc.md`](../guides/cyimrc.md) as storage-only. *(The note said "deferred to M5 perf pass"; M5 closed long ago — corrected at 1.8.5.)* |
| `tests/perf.bcyr` | Bench coverage follows the "deferred until perf surfaces" notes M2–M4 left | Live; the bench suite is the answer to those notes |

**Stale notes corrected at 1.8.5**, rather than cross-referenced — they were
describing things that had already happened:

- `src/plugin.cyr` claimed only 2 of the 6 hooks were wired and that the rest
  "land at v1.3.5+". All six wired at **1.3.5**.
- `src/mode.cyr` claimed multi-byte sequences were "NOT handled here yet" and
  deferred. `Ctrl-W`, `gg` (1.4.2), `m<letter>` and `'<letter>` (1.6.0) are all
  multi-byte and all dispatch in that file.

**False positives** (`src/mode.cyr`, `src/plugin.cyr`, `tests/{marks,plugin,window}.tcyr`)
carry `#skip-lint` with a reason: the rule matches the words "follow-up" and
"not yet", which in those lines mean *the follow-up byte of a prefix sequence*
and appear inside assertion messages — not deferrals.

---

## Open Bugs

**None.** BUG-001 closed at v1.3.3, BUG-002 at v1.9.1.

That is a statement about what is *tracked*, not a claim that cyim is
bug-free — the 1.8.x line found seven defects nobody had filed, and 1.9.0
found an eighth in `A` that had shipped since `A` landed. What it does mean is
that every known defect has been fixed rather than parked.

---

## Closed Bugs

### BUG-002 — LSP fold smoke: handshake never completed (CLOSED cyim v1.9.1, 2026-08-23)

`lsp_client_start_default()` answered -1 and the whole LSP feature was dead on
its only supported platform. **Root cause: `cyim-lsp`'s `_lsp_proc_exec`
declared `var argv[4]`** — four *bytes* for four 64-bit pointers, so
`("/usr/bin/env", "cyrius-lsp", 0)` wrote 24 bytes into 4, `execve` got a
clobbered vector, and the child died on its own `sys_exit(127)`. Silent,
because execve never took and so `env` was never there to complain it could
not find `cyrius-lsp`.

Root-caused from this repo at **1.8.2**, fixed upstream in **cyim-lsp 1.5.3**,
picked up at **cyim 1.9.1** as a `tag` bump with **no cyim source change**.
`cyrius smoke`: 4 passed / 9 failed → **13 passed / 0 failed**.

**The structural half closed with it**: `cyrius smoke` is now a CI step. Its
absence is why a dead feature sat unobserved for seven cuts. Deliberately held
back at 1.8.2 when CI was repaired — a gate that fails on day one gets ignored
or reverted — and landed here, green.

Full issue doc:
[`issues/2026-08-11-lsp-fold-smoke-handshake.md`](issues/2026-08-11-lsp-fold-smoke-handshake.md).

### BUG-001 — `cyim --replace` 4 KB `<new>` arg cap (CLOSED v1.3.3, 2026-05-06)

cyrius `args_init`'s 4 KB stack-buffer truncated `<new>`
arguments at the 4063 / 4064 byte boundary, breaking
agent-driven `--replace` pipelines that spliced large blocks.
Worked around in v1.0.2 with `_cli_args_reload_big()` (2 MB
heap re-read of `/proc/self/cmdline`). **Upstream fix landed in
cyrius 5.9.5** (heap-backed 2 MB args buffer matching Linux
`ARG_MAX`); v1.3.3 retired the workaround. Issue archive:
[`issues/archive/2026-05-06-cyrius-args-init-4kb-cap.md`](issues/archive/2026-05-06-cyrius-args-init-4kb-cap.md).
Regression guard: `tests/integration_smoke.py` retains the
BUG-001 row.

---

## Non-Goals

- **No Vimscript / Lua / Python / any embedded scripting.** Load-
  bearing constraint. If a feature requires a language to express,
  the feature gets data syntax or doesn't ship.
- **No `:set compatible`.** This is not a vim clone. It is a modal
  editor in the lineage.
- **No GUI.** cyim is a TTY editor. The compositor (`aethersafha`)
  hosts a terminal; the editor is in the terminal.
- **No "IDE" features.** Project drawer, fuzzy file finder,
  integrated debugger — those compose externally via the AGNOS
  library, not internally via plugin sprawl.

---

## Naming

`cy` (Cyrius) + `im` (the lineage `vi → vim → nvim → cyim`). A
name in the tradition, written in the language of the library.

---

*Last updated: 2026-08-23 (v1.9.2 — **ADR 0005 decided and
implemented**. Config lives in `$XDG_CONFIG_HOME/cyim/cyimrc`;
`./.cyimrc` overrides it key by key. Until now cyim read config
from only the current directory, so a user had no settings that
followed them between projects. Local override accepted without
a gate: the trade is sized by what `.cyimrc` can express, and the
worst a hostile directory achieves is a wrong colour. Held honest
by a rule rather than machinery — **every new key must be
classified local-overridable or home-only when it is added**, and
keymaps are the first serious candidate for the latter. Backward
compatible. Preceded by v1.9.1, which closed BUG-002 via a
cyim-lsp tag bump and put `cyrius smoke` behind a CI gate — Open
Bugs is now empty.)*

*Last updated: 2026-08-23 (v1.9.0 — **`o` / `O` open line
below / above**, the first feature of the 1.9.x line and the
roadmap's "Ready to implement" item since 1.8.0. Undoable as one
unit and dot-repeatable, both falling out of the existing
insert-entry machinery rather than needing special cases.
**Fixed alongside: `A` on a ONE-CHARACTER line appended before
the character**, not after — a bug that shipped from the day `A`
landed and survived three audits, because two-character lines
always worked. Found when `o` copied the same idiom and an
end-to-end pty run disagreed with the unit suite; the fixture
that caught it was one byte shorter than the ones that did not.
Suite 1177 → 1200 assertions.)*

*Last updated: 2026-08-23 (v1.8.7 — **closeout cut for the
1.8.x cycle**; all 11 CLAUDE.md steps green. 2 code-review
findings fixed: a discarded `sys_fchmod` return that would have
let the atomic save's rename proceed at 0644, and a grammar-path
bound spanning three functions with nowhere stating it. One
refactor: `render_build_line` and `render_build_line_naked` were
94.4% identical, and the 1.8.3 audit had to fix the same bounds
logic in BOTH — collapsed to a wrapper, byte-identical across 46
verification cases. Cycle totals: 1129 → 1177 assertions, 118 →
128 CLI smoke, 103 → 0 undocumented fns, 20 → 0 untracked
deferrals, 10 → 0 lint warnings. **1.8.x is closed. 1.9.0 opens
clean** — nothing in § Everything Still Deferred blocks it; the
two worth settling early are BUG-002 and ADR 0005.)*

*Last updated: 2026-08-23 (v1.8.6 — **documentation sweep**.
`cyrius audit`'s "101 undocumented public fns" advisory is now
**0**; the two big accessor blocks (`mode.cyr`'s 40 editor-state
fields, `window.cyr`'s 20 window-record fields) were documented
as what each field MEANS to a caller rather than what it loads,
which is the part you cannot read off `load64(s + 152)`.
Doc-tree sweep alongside: README four minors stale, SECURITY.md
still reporting "v1.6.0: 0 CRITICAL / 0 HIGH" after the 1.8.3
audit found a HIGH, BENCHMARKS.md not re-run since v1.6.0 — all
current. **All remaining deferred work is now in one table**
(§ Everything Still Deferred): BUG-002 and its CI gate, ADR 0005,
R-1a, the lang.cyr two-table refactor, F-7, resize-aware
rendering, F-CO-2. Nothing new deferred in this cut.)*

*Last updated: 2026-08-23 (v1.8.5 — **dead-code + cleanliness
cut**, closing audit residual R-2. The finding is that there was
no dead code to delete: all 24 cyim-side unreachable functions
are frozen plugin ABI, test/fuzz introspection, or
documented-deferred config, and `diag_msg` — the only symbol
with no caller anywhere — was a coverage hole wearing a
dead-code costume, closed with a test. Real dead code was one
level down: five named constants the code was not using, the
same size-expressed-twice shape the last two audits kept
finding. Four wired up, one deleted. Five stale comments
corrected (one five minors out of date). 20 untracked lint
deferrals → 0. Whole tree lint-clean: 0 warnings, 0 untracked
deferrals across src/, tests/, fuzz/. Architecture note 004
records how to read a DCE report so R-2 is not re-derived next
closeout. Suite 1174 → 1177. Still deferred: ADR 0005, F-7,
R-1a, the lang.cyr two-table refactor, and the 101-undocumented-fns
advisory.)*

*Last updated: 2026-08-23 (v1.8.4 — **atomic save**, closing
audit residual R-1 per [ADR 0006](../adr/0006-atomic-save.md).
A save writes a sibling temp and renames it over the target, so
a write that dies part way leaves the original bit-for-bit
intact — measured across all three write verbs under
`RLIMIT_FSIZE`, with no temp left behind. Atomic by DEFAULT,
not unconditionally: six enumerated conditions take the in-place
path, because rename changes the inode and would otherwise
replace symlinks, break hardlink sets, discard modes and
ownership, and make a writable file in a non-writable directory
unsaveable. ADR 0001 § 3 amended. Return contract unchanged; no
call site touched. The other 1.8.3 items — R-2, ADR 0005, F-7 —
stay deferred as filed, and R-1a (xattrs/ACLs) is new. Suite
1161 → 1174, CLI smoke 122 → 128, binary 1,197,504 →
1,197,536 B, benchmarks unmoved.)*

*Last updated: 2026-08-23 (v1.8.3 — **P(-1) audit / refactor /
hardening / security pass.** 1 HIGH, 1 MEDIUM, 3 LOW, 3
informational; all five code findings fixed, every regression
mutation-tested against the pre-fix source. The HIGH is the one
to remember: `buf_save_file` treated a short `write(2)` as a
completed one, so `:w` cleared the modified flag and all six
agent verbs exited 0 on a truncated file — measured at 475 of
575 bytes lost — and `--batch`'s documented atomicity was false.
Left open on purpose: R-1 (the save is still not atomic —
ADR-level), R-2 (dead-code floor is mostly frozen ABI), ADR 0005
(cwd-relative `.cyimrc` policy), F-7 (byte-oriented renderer).
Docs: ADR 0005 filed, the missing adr/architecture READMEs and
ADR template written, notes 002 and 003 added, two doc claims
that contradicted the code corrected. Suite 1136 → 1161, CLI
smoke 118 → 122, binary 1,193,384 → 1,197,504 B, benchmarks
unmoved.)*

*Last updated: 2026-08-23 (v1.8.2 — **dependency + toolchain
catch-up.** Every pin in the tree pulled to current: cyrius
6.5.18 → 6.5.35, darshana 0.8.2 → 1.0.0 (the API freeze;
carries 0.9.2's aarch64 `SYS_IOCTL` fix and two pre-freeze
breaks cyim does not trip), vyakarana 2.2.3 → 2.4.0 with all 45
bundled `grammars/*.cyml` re-synced and `openqasm` added as the
46th, `lib/` full re-sync to the 6.5.35 snapshot with the
stdlib-retired `lib/agnosys.cyr` pruned. cyim-lsp holds at 1.5.2
(latest tag). `LANG_COUNT` 45 → 46 with `.qasm` routing.
**Behaviour fix**: `highlight_init()`'s grammar load list had
been stuck at 11 since 1.6.2 while routing grew to 45, and it
suppresses vyakarana's cwd-relative fallback, so 34 routed
languages rendered uncolored — verified A/B against a 1.8.1
binary under a pty. Load list is now a `hl_grammar_name(i)`
table with a two-way mutation-tested guard in `tests/lang.tcyr`.
**BUG-002 root-caused** to a slot-vs-byte `var argv[4]` in the
cyim-lsp bundle — owner is upstream; cyim picks the fix up with
a tag bump and no source change. `lang.cyr` refactor trigger has
fired (third growth, and now a second chain to keep in step).
**CI repaired** — both workflows built the flat,
pre-`versions/` toolchain layout by hand, so every run failed at
`cyrius deps`; they now use the upstream `install.sh` pinned to
the tag, and gained a layout assertion, a format gate, a
CLI-smoke gate and `src/plugins/` linting. Binary 1,175,856 →
1,193,384 B; 21 suites / 1136 assertions, fuzz 4/4, 118 CLI
smoke, PTY integration smoke green, lint 0, fmt clean, all three
cross-targets build, full pipeline replayed green in a sandboxed
HOME.)*

*Prior update: 2026-05-09 (v1.7.0 — Toolchain refresh +
darshana TUI dep pickup shipped. First minor of the
post-catch-up era. cyrius 5.10.10 → 5.10.20; new
`[deps.darshana]` at tag 0.2.0. `src/tty.cyr` strips to ~37
lines (`tty_probe()` only). Binary byte-identical to 1.6.8 —
donor extraction was clean. Darshana joins vyakarana + cyim-lsp
as cyim's third external sandhi-pattern dep.)*

*Prior update: 2026-05-09 (v1.6.8 — **Closeout cut for the 1.6.x
cycle shipped. Cycle is closed.** All 11 CLAUDE.md audit steps
PASS; 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW new findings.
Binary byte-identical to 1.6.7 modulo `_VERSION_STR_CYIM` regen.
Audit doc at `docs/audit/2026-05-09-1.6x-closeout.md`. The 1.6.x
catch-up trajectory: 1.6.1 toolchain (cyrius 5.10.10 + vyakarana
2.2.1) → 1.6.2 grammars → 1.6.3 cyim-lsp 1.3.0 publish →
1.6.4 basename detection → 1.6.5 cyim-lsp 1.4.0 pickup
(reference previews) → 1.6.6 open-in-split ABI → 1.6.7
cyim-lsp 1.5.0 pickup (split consumer + arrow keys) → 1.6.8
closeout. All 1.5.x deferred-polish items closed; cumulative
test growth 973 → 1150 assertions; binary 957,720 B → 1,214,656 B
(absorbing vyakarana's 45 grammars + grammar routing + cyim-lsp
2x bundle changes); plugin ABI freeze (1.3.6 / ADR 0004) holds.
**v1.7.0 opens next** — anticipated mechanical: cyrius 5.10.10
→ 5.10.20 + new `[deps.darshana]` block (TUI lib being extracted
from cyim's `src/tty.cyr` + `src/render.cyr`; cyim is primary
donor + first consumer).)*
