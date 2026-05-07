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

cyim is at **1.6.0** (see [`state.md`](state.md)). VIM-style
marks (`m<letter>` / `'<letter>`) shipped as the first feature
minor of the post-1.5.x cycle. The full LSP user-visible surface
remains active via cyim-lsp 1.2.1 (diagnostics, `gd` goto-def
same-file + cross-file, `gr` references quickfix, `:lsp-*`
ex-commands, URL-decoded `file://` paths).

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

### Deferred LSP polish — carry-over to 1.5.x or 1.6.0

Bigger than LOW; not closeout findings. Each lands independently
when the trigger surfaces.

| Item | Trigger | Scope |
|---|---|---|
| **Reference previews** | User asks for "what's at this reference" without jumping | Append a source-line snippet to each `_cyim_lsp_label_for_ref` cstring. Requires fetching the line from disk (or buf if open) and truncating to popup width. Cyim-lsp patch (no cyim ABI change). |
| **Open-in-split** | User wants to keep current buffer visible while jumping | New plugin ABI `plugin_buf_load_file_split(s, path, direction)` (additive); consumer passes a "split" hint to on_select. Cyim 1.5.x patch (additive ABI) + cyim-lsp follow-up. |
| **Arrow keys in list mode** | A user complains j/k feels off | Wire up arrow handling in `editor_feed`'s CSI parser to route to `_plugin_list_next` / `_plugin_list_prev` when `_plugin_list_active`. Driver-side change in cyim. Cyim 1.5.x patch. |

### Closeout Pass — ✅ shipped 2026-05-07 as v1.5.2

[Audit doc](../audit/2026-05-07-1.5x-closeout.md). Pure
verification cut; no runtime code changes (binary byte-identical
to 1.5.1 modulo the regenerated `_VERSION_STR_CYIM`). All 11
CLAUDE.md closeout steps PASS. 0 CRITICAL / 0 HIGH / 0 MEDIUM /
4 LOW. Of the 4 LOW: F-CO-1 / F-CO-3 / F-CO-4 closed at 1.5.3;
F-CO-2 informational.

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

*Last updated: 2026-05-07 (v1.6.0 — VIM-style marks shipped.
Marks row removed from demand-gated table; remaining 1.5.x
deferred polish items are carry-over candidates for 1.6.x
patches. Next minor's theme is open — macros, folding, or
something else demand-gated.)*
