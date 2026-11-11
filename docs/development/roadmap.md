# cyim — Roadmap

What ships next, what waits on a trigger, and what is refused. **This file
holds open work only.** Shipped work is recorded in
[`CHANGELOG.md`](../../CHANGELOG.md), and current state lives in
[`state.md`](state.md). When an item ships, delete it here rather than marking
it done.

Every deferral is recorded here.

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
- **Every milestone is dogfoodable.** The user should be able to open
  this very file in cyim and edit it.
- **Defer what you can.** Clipboard, terminal embed, macros, anything
  that doesn't earn its keep — gated on real demand.

---

## Standing rules

These rules apply to every cut in every version line below.

- **Each minor line ends in a closeout patch.** Ship it as the last patch
  before the next `X.Y.0`, per CLAUDE.md § Closeout Pass.
- **The plugin ABI only grows through 1.x**
  ([ADR 0004](../adr/0004-plugin-abi-freeze.md)). Anything that needs a
  break waits for 2.0.0 and is listed there.
- **Classify every new `.cyimrc` key** as local-overridable or home-only
  when it is added, using
  [ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)'s table.
- **Every vyakarana tag bump re-syncs `grammars/`** from that tag's
  checkout. The editor reads grammars from disk, and `tests/lang.tcyr`
  load-tests every file there. This stops being needed once the language
  table below lands.
- **Agent-verb exit codes are a contract** (CLAUDE.md § Consumers), and
  `cyim-edit` matches them. A 1.x cut may add a verb, a modifier or a
  message. It may not change what an existing exit code means.

---

## Next: 1.13.x — Input and output

The line opened on the output side: 1.13.0 makes the agent verbs report a
failed write to stdout (exit 7). 1.13.1 decoded the keys outside CSI's
grammar (BUG-007, BUG-008). What is left is the input decoder's last item
(`editor_feed`, `src/driver.cyr`), which needs a decision before any code.

| Cut | Item | Notes |
|---|---|---|
| 1.13.x | **Bracketed paste** | darshana ships `tty_paste_enable` / `_disable`, and since 1.11.0 the decoder already swallows the paste markers, so turning them on changes nothing by itself. The work is deciding what a paste *does*. In INSERT and on the command line it inserts literally, so a pasted ESC cannot run commands (the pastejacking case). It also needs a NORMAL-mode behaviour, one undo unit per paste, and a dot-repeat rule. Design first, and write an ADR if the NORMAL-mode answer is not obvious |

---

## 1.14.x — Commands that do less than they say

Vim's modal grammar is the inheritance, so a gap in it is a defect rather
than a missing feature. cyim accepts everything listed here today, but each
does nothing or only part of the job. They are ordered by how often a vim
user will hit them.

| Item | Today | Where |
|---|---|---|
| **`:set number`** (`.cyimrc` `line_numbers`) | Stored but never rendered: `:set number` succeeds and the screen does not change | `src/mode.cyr`; [`cyimrc.md`](../guides/cyimrc.md) documents it as storage-only |
| **`:set tabstop`** (`.cyimrc` `tabstop`) | Stored but never rendered: Tab goes to the terminal as a raw byte | same |
| **Long lines** (BUG-009) | Cut at the window's width, with no sideways scroll or wrap: `$` takes the cursor off the right edge. Shares the column model with `tabstop` | `src/render.cyr`; § Open Bugs |
| **Dot-repeat** | `.` repeats insert sessions only. `x`, paste and visual-mode operations do not repeat, and neither does a Delete typed during an insert session | `src/driver.cyr` |
| **`:marks`** | No command lists the marks. `marks_count` already exists for it | `src/marks.cyr` |
| **Ex ranges and `:s`** | `:1,5d` and `:%s/x/y/` are not parsed. `:s` can reuse the niyama regex engine that the CLI's `--regex` flavors already link | `src/command.cyr` |

---

## Maintenance — any 1.x patch

These are not features. Each lands as a patch in whichever 1.x line is
open.

| Item | Why | What closes it |
|---|---|---|
| **One language table** — next in this track | Two if-chains have to stay in step: `src/lang.cyr` (`lang_name`, `lang_exts`, `lang_basenames`) and `src/highlight.cyr` (`hl_grammar_name`). When they drifted, 34 languages lost highlighting from 1.6.2 to 1.8.2. The CLAUDE.md "third instance" trigger fired at 1.8.2, and 1.11.1 grew both chains again. `tests/lang.tcyr` makes drift loud, so this is debt rather than risk, but every vyakarana bump pays for it with a `grammars/` re-sync | An ADR picks one of three options, then the refactor follows. (1) Parallel global string arrays. (2) Derive the load list from vyakarana (`grammar_count()` / `grammar_name_at(i)`). (3) Drop cyim's on-disk `grammars/` for vyakarana's embedded set and `detect_language_registered` (2.9.8). Option 3 loses cyim's routing overrides: `.asm` → `asm_x86_64`, the `.tcyr` / `.bcyr` / `.fcyr` extensions, and the shell rc basenames. See [architecture note 002](../architecture/002-routing-and-loading-are-two-tables.md) |
| **Plugin-ABI snapshot in CI** | ADR 0004's freeze is written down but not enforced. With a snapshot, 2.0.0's list of breaks is a diff instead of a recollection | A test or CI step that fails when a frozen symbol changes, as ADR 0004 § Neutral suggests |

---

## 2.0.0 — the contract cut

Only a contract change opens a major version, and nothing below forces
one. If every decision here goes the compatible way, 2.0.0 has no content
and 1.x continues. If any goes the breaking way, the rest land in the
same cut so consumers migrate once.

### Agent CLI

The argv parser is hand-rolled: one modifier loop per verb in
`src/main.cyr` and `src/cli.cyr`. Since 1.12.3 the eight writing verbs share
`_cli_parse_mods` for `--wc`, `--dry-run`, `--expect` and `--expect-not`.
cmdit could replace most of it, but not with identical behaviour. It was surveyed on 2026-10-14 and re-checked
against cmdit 1.5.0 on 2026-10-31. The migration waits on demand, and
these decisions are cyim's to make:

1. **Dash-led OLD / NEW.** Today every token that is not a modifier is a
   positional, so an OLD of `-x` or `--foo` works as-is. cmdit's getopt
   rules reject those unless the caller writes `--` first. Requiring `--`
   would break every agent that passes such text.
2. **Duplicate flags.** Today a repeated modifier exits 2
   (`tests/cli_smoke.sh` cases 26–31, 41, 66 and 87d). cmdit keeps the
   last value and has no way to refuse a repeat.
3. **`--wc[=l|=long]` takes an optional value.** That is still on cmdit's
   v2 backlog. A `cmdit_bool` refuses `=l` (since cmdit 1.3.1). A
   `cmdit_str` swallows the file in a bare `--wc FILE`, and case 4
   asserts that form works.
4. **An unrecognised first argument.** Today any first argument that is
   not a verb is the file the editor opens, including `-h` and `--typo`,
   and later arguments are ignored. Keeping that means calling
   `cmdit_help_short(h, 0)` / `cmdit_version_short(h, 0)`. Changing it
   is a break.
5. **An exit code for "already applied".** The message half shipped in
   1.12.0. A separate code
   ([issue](issues/archive/2026-08-29-batch-and-expect-diagnostics.md) § 3) would
   change what scripts see where they get exit 4 today.

**Once unblocked:**

- Verbs stay a `streq` on the first argument, because cmdit verbs are
  bare words.
- `print_help` and `print_version` stay, because they write to stdout
  and cmdit renders on stderr.
- Each verb's modifier loop becomes a cmdit handle over the arguments
  after the verb.
- The positional checks become `cmdit_require_positionals[_exact]`.
- Pin cmdit at its current tag. stiva's `src/main.cyr` is a worked
  migration of a verb tool. Source plan:
  [agnosticos `planning/cmdit.md`](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/cmdit.md).

**Bar for identical behaviour:**

- Every exit code and stdout capture in `tests/cli_smoke.sh` is
  unchanged.
- The agent rows in `tests/integration_smoke.py` still pass, including
  BUG-001's 64 KB NEW.

### Plugin ABI

ADR 0004 reserves these breaks for 2.x:

- renaming or removing a frozen symbol;
- the 24-byte diagnostic record layout;
- the `DIAG_*` values;
- the rule that built-ins win over plugins;
- how long the per-frame diagnostics vector lives.

Spend them only on candidates collected during 1.x. None has been filed
yet. The shape to watch for is the one ADR 0004 § Negative predicts: a
second API added because the original could not change. For example,
`plugin_buf_load_file_split` (1.6.6) now sits beside
`plugin_buf_load_file`.

---

## 2.x — after the contract cut

None of these breaks a contract, but each is large, so they wait until
after 2.0.0. Any of them can move earlier if its trigger fires first.

| Item | Trigger | Notes |
|---|---|---|
| **Unicode cell model** (F-7, [architecture note 003](../architecture/003-render-is-byte-oriented.md)) | Someone editing non-ASCII text in earnest. `aethersafha` hosting cyim is the likeliest | The renderer counts each byte as one column. A multi-byte character takes several columns, double-width characters are not accounted for, and each combining character takes a column. Even an em-dash line cuts off early. Plugins can keep seeing byte offsets. The work is a character-width table plus codepoint-aware motion, cursor column, search and marks — not a fix inside the renderer |
| **Multi-file transactions** | Proposal § 5 | A `--batch` over `file\0OLD\0NEW` triples that is all-or-nothing across the files. `rename(2)` is atomic for one file only, and renaming staged temps one by one can still stop part way, so this needs an ADR before any code |
| **Consumer integration** | `agnoshi` starts embedding cyim, or `aethersafha` starts hosting it | Neither had started at the 1.8.7 closeout. The surface either one needs is designed when it starts. Any break waits for a major version |

---

## Demand-gated — no version until the trigger fires

| Feature | Trigger | Notes |
|---|---|---|
| **Mouse reporting** (click to place the cursor, wheel scrolls the view) | A user asks for clicks, or uses a terminal that does not send the wheel as arrow keys | Since 1.13.1 the wheel scrolls wherever the terminal sends it as Up / Down on the alternate screen, which most do. Turning reporting on (`?1000h` / `?1006h`) takes text selection away from the terminal unless Shift is held, so it would be a `.cyimrc` key, off by default like vim's `mouse=`, and classified under ADR 0005. The decoder already swallows SGR mouse reports |
| **`zt` / `zz` / `zb`, counts, `scrolloff`** | A user asks | The 1.13.1 scroll keys take no count, because nothing in cyim's grammar does yet. `z` is unbound in NORMAL. `scrolloff` would be a `.cyimrc` key and a margin in `view_follow` (`src/window.cyr`) |
| **System clipboard** | Wayland integration through `aethersafha` | Belongs in the compositor, not the editor. The single yank register stays the in-editor primitive |
| **Terminal embed** (`:term`) | A third user asks | `Ctrl-z` and a shell work until then |
| **Macros** (`q<reg>`) | A recurring need | Replaying a recorded key sequence is not a scripting language, so it fits the refusal. Would need named registers |
| **Named registers** (`"a`–`"z`) | A user asks | One shared yank register today ([usage guide](../guides/usage.md)) |
| **Folding** (`zM` / `zR`) | A user asks while editing a source file over 1,000 lines | Folding marked ranges only needs the renderer to skip them. Folding functions and blocks needs structural markers from a vyakarana-style pass |
| **`:make` / `:cnext`** | A user asks | Run the compiler, parse its stderr, and fill the same `plugin_list_display` picker `gr` uses. No ABI change |
| **Diagnostics in the buffer view** (gutter or inline marks) | A user asks which line an LSP diagnostic is on | Diagnostics have been collected every frame since 1.3.5. Users see them only as status-line counts (`E:1 W:2`, `TWS:N`). How they look is not frozen ([ADR 0004](../adr/0004-plugin-abi-freeze.md)). Cheapest once the 1.14.x line-number gutter exists |
| **Ex tab completion** | A user asks | `src/command.cyr` |
| **Mark persistence** (`viminfo`-style) | Persistence earns its keep | `src/marks.cyr` |
| **Frame batching** | A repaint-cost measurement says the writes matter | Render writes once per line. darshana's `_buf` composers would let a frame be one write, but today the per-frame cost is retokenizing, not writing |
| **Cyrius-aware edit warnings** | A scope decision | Proposal § 4: warn at edit time on literal lengths, duplicate `var`s and array sizing. cyrlint already checks write lengths (since cyrius 6.7.11), so the editor would be a second checker unless it calls the linter. Decide against Refusal §0 first |

---

## Blocked upstream

| Item | Waiting on | Then |
|---|---|---|
| **R-1a** — the atomic save drops extended attributes, POSIX ACLs and SELinux labels | A stdlib `listxattr` / `getxattr` surface | Detecting an ACL becomes a seventh in-place condition in [ADR 0006](../adr/0006-atomic-save.md). Narrow case: the file must have an ACL, be owned by the invoking user, and be neither a symlink nor hardlinked |
| **Regex backreferences** (`\1`) | niyama | Reassess when niyama ships them (`src/cli.cyr`, `--help`) |
| **The language server starts with cyim's signals blocked** | cyim-lsp | § Dependency notes |
| **cyim-lsp re-spawns its server on every edit while the server will not start** | cyim-lsp | § Dependency notes |

---

## Watch list — refactors waiting for a third instance

| Item | Count | Trigger |
|---|---|---|
| **LSP glue copied from cyim-lsp's example** into `src/plugins/lsp_glue.cyr` | 2: the reference label (1.6.5), the split mode (1.6.7) | A third refactor of the example glue. Then document how to copy from upstream, or include more of the bundle |
| **F-CO-2** — extract `_cyim_lsp_jump_to_uri_lc` | 2 | `:lsp-implementation` or `:lsp-type-definition` |
| **Window-navigation geometry** — `window_navigate` lays out at `WIN_NAV_DEFAULT_ROWS` × `WIN_NAV_DEFAULT_COLS` (23 × 80) while render uses the live size | 2: Ctrl-W's neighbour (1.11.2); the scroll keys' height (1.13.1) | Proportional layout keeps the two in agreement in every case tried at the 1.11.2 closeout. Since 1.13.1 the scroll keys read a view's height from the same rects, so a scroll in the same read as a Ctrl-W move uses the 23 × 80 layout until the next frame. Revisit if Ctrl-W picks the wrong neighbour on a small terminal, or a third reader of the rects appears |
| **Decimal-to-ASCII** — `_buf_append_dec`, `_cmd_ls_put_int`, agnos `_al_put_uint` | 3 | Deliberately not merged. One writes raw, one goes through a bounds-checked putter, and one writes via `syscall` under `#ifdef`. A shared version would be used three different ways. Revisit on a new instance or a bounds bug in any of them |

---

## Deferred in-source notes

Comments in `src/` and `tests/` that defer work point here, so `cyrius lint`'s
untracked-deferral rule has a target. Each row says where that work is now
planned.

| Where | Deferred | Planned |
|---|---|---|
| `src/cli.cyr`, `src/main.cyr` (`--help`) | Regex backreferences | Blocked upstream (niyama) |
| `src/command.cyr` | Ex ranges, `:%s`, tab completion, `:!cmd` | Ranges and `:s` in 1.14.x. Tab completion is demand-gated. `:!cmd` is not planned; if it ever ships, it runs an explicit argv through `exec_vec()` (CLAUDE.md § Security Hardening) |
| `src/driver.cyr`, `tests/dot.tcyr` | Dot-repeat beyond insert sessions | 1.14.x |
| `src/marks.cyr` | `viminfo`-style persistence | Demand-gated |
| `src/marks.cyr` | `:marks` | 1.14.x |
| `src/mode.cyr` | `cfg_line_numbers` / `cfg_tabstop` are stored but not rendered | 1.14.x |
| `tests/perf.bcyr` | Benchmarks for the "deferred until perf surfaces" notes that M2–M4 left | Ongoing: the benchmark suite is the answer to those notes |

Some lines in `src/mode.cyr`, `src/plugin.cyr` and
`tests/{marks,plugin,window}.tcyr` carry `#skip-lint` because the rule
misfires there. The words "follow-up" and "not yet" refer to the second
byte of a prefix key, or appear inside assertion messages. They are not
deferrals.

---

## Dependency notes

- **darshana: what cyim does not use, deliberately.** Revisit an item
  when its reason stops holding.
  - `tty_winsize_or`. cyim's `_query_winsize` also clamps, and it also
    reports when it fell back, which the tests check.
  - `tty_raw_nonblock`. The main loop waits in epoll.
  - `tty_paste_enable`. Paste behaviour has to be designed first
    (1.13.x).
  - Mouse reporting. A decision first (§ Demand-gated).
  - The frame composers `tty_move_buf`, `tty_clear_to_eol_buf` and
    `tty_sgr_list_buf`. Render still writes once per line (frame
    batching, § Demand-gated).
  - The 1.4.0–1.7.0 additions: `tty_sgr_len` / `tty_sgr_strip_buf`,
    `tty_isatty_is_per_fd`, `tty_winsize_px`. cyim substitutes control
    bytes instead of stripping SGR, never asks `tty_isatty`, and lays
    out in cells, not pixels.
- **cyim-lsp: the spawned server inherits cyim's blocked signals**
  (found 2026-10-12, cyim 1.11.0).
  - `lsp_proc_spawn` calls `sys_fork` and then `sys_execve` with nothing
    in between, and a blocked signal mask survives both. A server
    started mid-session therefore begins with two signals blocked:
    SIGWINCH (cyim's resize watch, since 1.10.0) and SIGPIPE (the 1.11.0
    guard). So do the server's own children, unless it resets them.
  - cyim cannot act between the fork and the exec. It also cannot drop
    its SIGPIPE guard around the spawn, because the handshake write to a
    server that dies at start-up is the race the guard exists for.
  - **Ask for cyim-lsp:** in the child, before `execve`, clear the
    signal mask and reset SIGPIPE to its default. The cyrius stdlib's
    exec functions already do this for their own children.
  - Not addressed as of cyim-lsp 1.5.4.
- **cyim-lsp: `lsp_doc_lazy_start` re-spawns the server on every edit
  while it will not start.** Measured at 1.11.0 with a `cyrius-lsp`
  that exits at once: 10 edits in a `.cyr` file gave 10 spawns.
  **Ask:** back off after a failed start, for example until
  `:lsp-restart`.

---

## Open Bugs

### BUG-009 — Text past the window's width cannot be reached

Filed 2026-11-11 (cyim 1.13.1), found while fixing vertical scrolling, and
planned for **1.14.x**. Each line is drawn cut at the window's width, and
nothing scrolls sideways or wraps. On a longer line the cursor goes past the
right edge, where the terminal pins it, and the rest of the line never
appears. Measured: on a 40-column terminal, `$` on a 128-byte line moves the
cursor to column 128, and the text from column 41 on is not drawn.

- **Two ways to fix it.** Scroll each view sideways (vim's `nowrap` with
  `sidescroll`), or wrap long lines onto the next rows (vim's default `wrap`).
- **Either needs a column model first.** Today one byte is one column, except
  `^X` (2 columns), `<xx>` (4), and Tab, which is drawn raw so the terminal
  moves to its own tab stop. Decide this with the `:set tabstop` item below
  and F-7 (§ 2.x), because all three change what a column is.

Closed bugs are recorded in CHANGELOG.md. The next ID is **BUG-010**.

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
- **No plugin system beyond the sandhi pattern.** A vendored bundle
  plus cyim-side glue is the plugin system: there is no plugin sandbox
  and no runtime loading.

---

## Naming

`cy` (Cyrius) + `im` (the lineage `vi → vim → nvim → cyim`). A
name in the tradition, written in the language of the library.

---

*Last updated: 2026-11-11, at 1.13.1. Replace this line on each update; do not
add to it.*
