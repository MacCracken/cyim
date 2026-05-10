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

cyim is at **1.6.7** (see [`state.md`](state.md)). VIM-style
marks (`m<letter>` / `'<letter>`) shipped at 1.6.0 as the first
feature minor of the post-1.5.x cycle; 1.6.1 and 1.6.2 are the
opening bites of the **1.6.x catch-up channel** — toolchain pin
5.9.16 → 5.10.10, vyakarana 1.0.2 → 2.2.1 (across the breaking
2.0.0 streaming-API replacement), and grammar-routing wiring
from 11 → 45 languages. The full LSP user-visible surface
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
| **v1.6.1** — Toolchain + vyakarana catch-up (cyrius 5.9.16 → 5.10.10; vyakarana 1.0.2 → 2.2.1; `tokenize_source` → streaming primitive migration in `src/highlight.cyr`; cyim-lsp pin moved in lockstep with no tag bump) | Shipped 2026-05-09 |
| **v1.6.2** — Grammar-routing catch-up (`LANG_COUNT` 11 → 45; 34 new grammar `.cyml` files in `grammars/`; `.cyml` migrates from "toml" to dedicated "cyml" grammar; `tests/lang.tcyr` 37 → 77 assertions) | Shipped 2026-05-09 |
| **v1.6.3** — cyim-lsp 1.3.0 pickup (`[deps.cyim-lsp].tag` 1.2.1 → 1.3.0; banner-only delta, distfile byte-identical, no cyim source changes; binary byte-identical to 1.6.2) | Shipped 2026-05-09 |
| **v1.6.4** — Basename-driven language detection (`lang_basenames(i)` table; `Dockerfile`/`Makefile`/`GNUmakefile`/`Containerfile` + `.bashrc`/`.zshrc`/`.profile` family; case-sensitive with directory-boundary check; `tests/lang.tcyr` 77 → 103 assertions) | Shipped 2026-05-09 |
| **v1.6.5** — cyim-lsp 1.4.0 pickup; reference previews in `:lsp-find-refs` (`_cyim_lsp_label_for_ref` calls `lsp_ref_preview(uri, line, 80)` and appends snippet after coordinates; falls through cleanly when preview unavailable) | Shipped 2026-05-09 |
| **v1.6.6** — Plugin ABI: `plugin_buf_load_file_split(s, path, direction)` (additive per ADR 0004; `SPLIT_HORIZONTAL`/`SPLIT_VERTICAL` constants; cyim side of the open-in-split carry-over from 1.5.x; cyim-lsp 1.5.0 will consume) | Shipped 2026-05-09 |
| **v1.6.7** — cyim-lsp 1.5.0 pickup; open-in-split for `:lsp-find-refs` (`:lsp-find-refs-split` / `:lsp-find-refs-vsplit` ex-commands; `_cyim_lsp_on_ref_select` branches on mode flag; default in-place behaviour preserved byte-for-byte) | Shipped 2026-05-09 |

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
| **v1.6.7** | cyim-lsp 1.5.0 pickup. Tag bump 1.4.0 → 1.5.0; cyim-lsp's `[lib]` source unchanged (banner-only distfile delta), but example glue refactored to add `_cyim_lsp_ref_split_mode` state, `_cyim_lsp_ex_find_refs_with_mode(s, mode)` helper, and three ex-commands (`:lsp-find-refs` / `-split` / `-vsplit`). cyim's `src/plugins/lsp_glue.cyr` mirrors the refactor; on_select branches on mode 0/1/2 to in-place / horizontal / vertical loads. Default behaviour byte-equivalent to pre-1.6.7. | ✅ Shipped 2026-05-09 |

### Planned (next bites)

| Cut | Theme | Notes |
|---|---|---|
| **v1.6.x** | **Arrow keys in list mode** (carry-over from 1.5.x deferred polish). Wire arrow handling in `editor_feed`'s CSI parser to route to `_plugin_list_next` / `_plugin_list_prev` when `_plugin_list_active`. Pure driver-side change. Smallest carry-over remaining. **Slot is your call**: was originally 1.6.7 in the original sequence; that slot was consumed by the cyim-lsp 1.5.0 pickup. Either lands as 1.6.7.x patch or shifts the closeout from 1.6.8 → 1.6.9. | Triggered by user finding j/k off in list mode. |
| **v1.6.8** *(or 1.6.9 if arrow keys lands as 1.6.8 first)* | **Closeout pass for the 1.6.x cycle.** Follows CLAUDE.md's 11-step Closeout Pass policy (same shape as 1.5.2's). Specific 1.6.x agenda: re-baseline benchmarks under cyrius 5.10.10 + vyakarana 2.2.1 + cyim-lsp 1.5.0 + full grammar surface (1.6.1's numbers are the new baseline; 1.6.x cumulative regression vs 1.5.3 worth a chart). Confirm `agnoshi` / `aethersafha` integration paths still embed cyim cleanly under the catch-up sequence. Architecture review: `lang.cyr` if-chain at 45 entries + parallel `lang_basenames` table from 1.6.4 — assess whether the third forcing function for refactor has arrived. `_cyim_lsp_label_for_ref` shape duplicated in cyim-lsp's example glue and cyim's `src/plugins/lsp_glue.cyr`; `_cyim_lsp_ex_find_refs_with_mode` similarly duplicated as of 1.6.7 — both cases are wait-for-third-instance. Audit doc lands at `docs/audit/2026-MM-DD-1.6x-closeout.md`. | The 1.6.x cycle gate. |

### v1.7.0 — Mechanical refresh + darshana TUI dep pickup (planned)

User-confirmed shape (FYI 2026-05-09):

- **`cyrius` toolchain pin 5.10.10 → 5.10.20.** 10 patches of
  drift to absorb; expect stdlib drift similar to 5.9.16 → 5.10.10
  but bounded to the 5.10.x series. Lockstep cyim-lsp own-pin
  bump (likely a 1.5.0 cut on cyim-lsp's side per the
  vyakarana 2.2.0 toolchain-bump-as-minor convention).
- **New `[deps.darshana]` block.** darshana is a sibling TUI
  library (currently `0.1.0` against cyrius 5.10.20) being
  worked on as a primary-donor extraction from cyim's own TTY
  / render code. cyim becomes the consumer side of the
  extraction once the lib is published. cyim's `src/tty.cyr` +
  `src/render.cyr` paths are the integration target — exact
  shape of consumption depends on what darshana 0.1.x exposes.
- vyakarana — bumped if a newer tag is available at 1.7.0 cut
  time; otherwise stays at 2.2.1.

**Cut as a minor** (1.6.x → 1.7.0) per the toolchain-bump-as-
minor convention vyakarana 2.2.0 set: consumers pinning cyim
need to know the toolchain expectation moved + a new external
dep entered the manifest.

After 1.7.0 the 1.6.x → 1.7.x → 1.8.x cycles open the next
demand-gated work window (macros, folding, system clipboard
via aethersafha, etc.) — the catch-up channel work converges
here.

### Watch list (architectural debt; not yet earning a bite)

| Item | Forcing function |
|---|---|
| `lang.cyr` if-chain refactor | At 45 entries today. CLAUDE.md "wait for the third instance" applies. 1.6.2 (extension catch-up) was instance 1; 1.6.4 (basename probe added a parallel data table) is instance 2 — but it added a *new* table, not a third growth of the existing one. The refactor trigger is the next forcing function that grows `lang_name`/`lang_exts`/`lang_basenames` again. 1.6.8 closeout will reassess. |
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

*Last updated: 2026-05-09 (v1.6.7 — cyim-lsp 1.5.0 pickup
shipped. Open-in-split ABI now end-to-end usable through three
new ex-commands. Catch-up cycle seven cuts deep: 1.6.1 toolchain
/ 1.6.2 grammars / 1.6.3 cyim-lsp toolchain publish / 1.6.4
basename detection / 1.6.5 reference previews / 1.6.6
open-in-split ABI / 1.6.7 open-in-split consumer activation.
The original 1.6.7 slot (arrow keys in list mode) has slipped —
it's the only 1.5.x carry-over still pending. Slot for arrow
keys + sequencing of the 1.6.8 closeout is the next sequencing
question. Then 1.7.0 (cyrius 5.10.20 + darshana TUI).)*
