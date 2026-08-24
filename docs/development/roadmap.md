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

cyim is at **1.8.2** (see [`state.md`](state.md)). The 1.6.x
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

**1.8.3 is the P(-1) hardening cut** — see
[`docs/audit/2026-08-23-1.8x-hardening.md`](../audit/2026-08-23-1.8x-hardening.md).
Its HIGH finding is worth knowing even if you read nothing else:
every write path in cyim treated a short `write(2)` as a
completed one, so `:w` and all six agent verbs could destroy
most of a file and report success. Fixed, with the residual
that the save is still not *atomic* — recorded as R-1 rather
than changed, because temp-file-plus-rename contradicts
[ADR 0001](../adr/0001-trust-model.md) § 3 and is an ADR-level
call.

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
| **`o` / `O` — open line below/above** (open a fresh line and enter INSERT) | **Ready to implement** — surfaced 2026-07-08 during agnos full-screen bring-up (`i` works; `o`/`O` have no handler — no `ACT_OPEN_*`). A core vim command, so it jumps the queue when normal-mode editing next earns a bite (unlike the deliberately-deferred rows below). | `src/mode.cyr`: map `o` → `ACT_OPEN_BELOW`, `O` → `ACT_OPEN_ABOVE`; handler (near the `i`/`a`/`A` insert-entry paths in `insert.cyr`) inserts a `\n` below/above the cursor's line, moves the cursor onto the new blank line, and switches to INSERT mode. Add coverage to `tests/`. |
| **System clipboard** | Wayland integration via `aethersafha` | Belongs in compositor layer, not editor. cyim's yank/paste single-register stays the in-editor primitive. |
| **Terminal emulator embed** | Third user asks for `:term` | Until then, `Ctrl-z` + shell is fine. |
| **Macros** (`q<reg>` recording) | Recurring user need surfaces | Vim's macro DSL is a sequence-replay primitive, not a scripting language — fits the no-embedded-scripting refusal. |
| **Folding** (`zM` / `zR` / `:foldenable`) | User asks while editing > 1 KLOC source | Range-marked spans + render skip; structural folds (function / block) require a vyakarana-style structural marker pass. |
| **`:make` / `:cnext` quickfix flow** | User asks | Native compiler-driven flow is what `gr` already prototypes. `:make` runs an external compiler, captures stderr, parses error format, populates the same `plugin_list_display` machinery. Consumer-side patch (no cyim ABI change). |
| **Plugin system beyond sandhi** | Probably never | Refusal §0 — the sandhi pattern (vendored bundle + cyim-side glue) is already "the plugin system". Nothing beyond it earns its keep. |

---

## Open from the 1.8.3 hardening audit

Findings were fixed in-cut; these are the items deliberately left open,
each with the reason. Full context in
[`docs/audit/2026-08-23-1.8x-hardening.md`](../audit/2026-08-23-1.8x-hardening.md).

| ID | Item | Why it is open |
|---|---|---|
| **R-1** | The save path is not atomic — `O_TRUNC` in place, so a failed write leaves a truncated file | The fix exists in the stdlib (`file_write_atomic`), but temp-file-plus-rename changes the inode on every save: breaks hardlinks, discards the target's permissions, and fails where the user can write the file but not create a sibling. It also contradicts [ADR 0001](../adr/0001-trust-model.md) § 3, which *accepts* write-in-place semantics because vim's default does. ADR-level, not a patch-cut change. The shape worth costing is vim's: a `backupcopy`-style choice rather than one fixed behaviour |
| **R-2** | Dead-code floor of 20 cyim-side functions | Mostly not dead: frozen plugin ABI ([ADR 0004](../adr/0004-plugin-abi-freeze.md) forbids removal), test/fuzz introspection reachable from harnesses but not `main`, and two documented-deferred config getters. A DCE report is not a dead-code list for a project with a frozen ABI and an out-of-line harness |
| **ADR 0005** | Should `.cyimrc` be loaded from the current directory at all? | [Filed as Proposed](../adr/0005-cyimrc-cwd-trust-boundary.md) with four costed options. Not urgent — the whole surface is ten colour indexes, and the worst a hostile config achieves is the wrong colour. Not to be left open either: `cyimrc.md` names keymaps as an M4 candidate, and a keymap accepted from a directory you just cloned is a different proposition from a colour. Decide while the answer is cheap |
| **F-7** | The renderer is byte-oriented; C1 bytes pass through, no double-width or combining-character handling | Accepted and documented as [architecture note 003](../architecture/003-render-is-byte-oriented.md), not filed as a defect — these are one decision, and the obvious "fix" (substituting `0x80`–`0x9F`) breaks every non-ASCII file, because that range overlaps UTF-8 continuation bytes. The trigger that would change the calculus is a consumer editing CJK or RTL text in earnest — `aethersafha` is the likeliest |

---

## Open Bugs

### BUG-002 — LSP fold smoke: `lsp_client_start_default()` handshake never completes (**P2**, opened 2026-08-11, **root-caused 2026-08-23**)

`cyrius smoke` (`tests/smcyr/lsp_fold.smcyr`) reports **4 passed, 9 failed**.
`lsp_client_start_default()` answers -1 and `lsp_client_describe()` reports
`"(not attached)"`. The 8 trailing failures are all downstream of that one.

**Root cause (found at 1.8.2):** `cyim-lsp/src/subprocess.cyr:180` declares
`var argv[4]` — four **bytes** — and `_lsp_proc_exec` then stores up to four
64-bit pointers into it. `lsp_client_start_default()` passes
`("/usr/bin/env", "cyrius-lsp", 0)`, so the write range is `[0, 24)`: a 6×
overrun of a 4-byte stack slot. `execve` receives a clobbered `argv`, fails, and
the child falls through to its own `sys_exit(127)`. `var fallback[1]` eleven
lines down is the same defect. Proven by construction — the identical spawn with
`argv[32]` / `fallback[8]`, linked against the same unmodified 1.5.2 bundle,
completes the handshake and gets a 397-byte `initialize` response.

Same bug class the 1.5.2 audit already fixed once *in this file*
(`var status_buf[1]` in `lsp_proc_close`) and missed twice. Deterministic since
cyrius **6.3.13** moved function-local `var X[N]` onto a guard-paged stack —
which cyim's pin crossed at 1.8.1 (`6.2.36 → 6.5.18`), which is why the smoke
started failing exactly then. The 1.5.0 control run reproduced the same 4/9
because it varied the *bundle*, not the *toolchain*.

**Owner: `cyim-lsp`.** The fix is `argv[4]` → `argv[32]` and `fallback[1]` →
`fallback[8]` plus a `cyrius distlib` regen; cyim picks it up with a `tag` bump
under `[deps.cyim-lsp]` and **no cyim source change**, exactly as at 1.8.1.
Blocked on that cut, not on investigation. cyim's own tree was swept for the
same class at 1.8.2 — every `var NAME[N]` later read or written via
`load64`/`store64`, checked against its maximum written offset — with **0
findings**.

**P2 rationale (unchanged):** nothing ships broken (all 1.8.2 gates green,
editor unaffected on every target) and LSP is opt-in, so it is below BUG-001's
P1 bar of a silent wrong answer on a scriptable surface — this failure is loud
and self-announcing. But it is the whole LSP feature being non-functional on its
only supported platform, across seven cuts of consumer-side glue built against
an end-to-end path that was unproven until now.

**Structural half is still open, and is the durable fix:** put `cyrius smoke`
behind a CI gate. It is absent from `.github/workflows/ci.yml`, which is exactly
how this rotted while `state.md` still claimed "13 PASS" (corrected at 1.8.1).
Fixing `argv` makes the harness pass; it does not make anyone watch it. The gate
needs `cyrius-lsp` on the runner — a packaging problem, not a reason to leave
the harness unwatched.

1.8.2 repaired CI and added three gates (format, CLI smoke, `src/plugins/`
linting) but **deliberately left this one out**: a gate that fails on day one
gets ignored or reverted. **Add it in the same cut that picks up the fixed
`cyim-lsp` tag** — that is when it can land green.

Full issue doc:
[`issues/2026-08-11-lsp-fold-smoke-handshake.md`](issues/2026-08-11-lsp-fold-smoke-handshake.md).

---

## Closed Bugs

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
