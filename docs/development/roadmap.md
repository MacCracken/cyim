# cyim — Roadmap

A phased plan for building cyim from scaffold to a daily-driver modal
text editor. Each milestone is independently shippable and adds a
coherent layer. The goal is to have something a user can actually edit
text with at the end of every phase past M1.

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
- **Two consumer classes, designed in parallel.** Humans drive cyim at
  a TTY. AI agents (daimon-orchestrated, Claude-style assistants
  included) drive cyim programmatically. The modal grammar is the
  same; the I/O harness differs. Don't retrofit headless drive — the
  keymap dispatch is the API surface for both.
- **Every milestone is dogfoodable.** From M1 onward, the user should
  be able to open this very file in cyim and edit it. M0 is the only
  exception — it just boots and exits.
- **Defer what you can.** LSP, tree-sitter equivalents, plugin
  systems, terminal emulator embedding, clipboards — all post-v1.0.

---

## Milestone 0 — Scaffold (this release, v0.1.0)

**Goal:** the repo exists, compiles, builds clean.

- Project structure: `src/`, `tests/`, `docs/`, `lib/` (vendored stdlib)
- `cyrius.cyml` with stdlib footprint chosen for the modal-editor arc
  (`fs`, `hashmap`, `args`, `vec`, `string`, `str`, `io`, `fmt`)
- `cyim --version`, `cyim --help` (stub)
- CI builds, tests pass

**Done when:** `cyrius build` succeeds and `./build/cyim` exits 0.

---

## Milestone 1 — Modal core

**Goal:** the editor works end-to-end on one buffer. Proves the runtime shape.

- **Gap-buffer** primitive (`src/buffer.cyr`) — insert/delete/move-cursor
- **Raw-mode TTY** (`src/tty.cyr`) — termios via syscalls, alternate screen, no curses dep
- **Modal dispatch** (`src/mode.cyr`) — normal/insert/command tables in `hashmap`
- Normal-mode motions: `h j k l w b 0 $ gg G`
- Insert-mode: type to insert, `Esc` to exit
- Command-mode: `:q` / `:q!` / `:w` / `:wq` / `:e <file>`
- `cyim <file>` opens; `cyim` opens scratch
- Coverage invariant: round-trip read → buffer → write is byte-identical

**Done when:** you can edit `src/main.cyr` in cyim, save, and the
diff is exactly your edits.

---

## Milestone 2 — Syntax highlighting via vyakarana

**Goal:** color shows up. Proves the consumer relationship with vyakarana.

- Add `[deps.vyakarana]` to `cyrius.cyml`
- `src/highlight.cyr` — call `tokenize_source(buf, lang)`, map kinds to
  ANSI palette
- Detect language from file extension (vyakarana already exposes this)
- Configurable palette via `.cyimrc` (data, not code)
- Repaint on edit — no incremental retokenize yet, full-buffer is fine
  for M2

**Done when:** opening `src/buffer.cyr` shows Cyrius highlighting
matching vyakarana's reference output.

---

## Milestone 3 — Multi-buffer & splits

**Goal:** real editing day, not toy demo.

- Buffer list (`:ls`, `:b <n>`, `:bn`, `:bp`)
- Horizontal split (`:sp`), vertical split (`:vsp`)
- Window navigation (`Ctrl-w h/j/k/l`)
- `:e <file>` opens into current window
- Status line per window (filename, modified flag, line/col)
- Close-on-`:q` cascades correctly when last window closes

**Done when:** you can hold three files open in two splits and
navigate without losing state.

---

## Milestone 4 — Search, undo, config

**Goal:** the editor *feels* like vim under your fingers.

- `/pattern` and `?pattern` search; `n`/`N` repeat; `*`/`#` word search
- Undo tree (gap-buffer snapshots) — `u` undo, `Ctrl-r` redo
- `.cyimrc` (CYML) — keymaps, palette, tab width, line numbers
- Visual mode (`v`, `V`, `Ctrl-v`) + yank/paste registers (one register,
  no system clipboard yet — that's post-v1.0)
- Repeat (`.`)
- `:set` for runtime toggles backed by the `.cyimrc` schema

**Done when:** muscle memory from vim survives the switch for a full
editing session.

---

## Milestone 5 — Polish

**Goal:** the editor stops surprising you. Edges smoothed, perf measured,
fuzz catches the next class of bugs.

- **Documentation pass**:
  - `docs/usage.md` — getting started; day-1 vim user moving to cyim
  - `docs/keymap.md` — full reference (NORMAL / INSERT / COMMAND /
    SEARCH / VISUAL keymaps; Ctrl-w prefix; `:` ex-style commands)
  - `docs/cyimrc.md` — config schema; every `:set` option; palette
    overrides; bundled-grammar list
  - `docs/architecture/` ADRs as earned during the loop
- **Performance pass**:
  - Large-file fixtures: 1 MB / 10 MB / 100 MB
  - Open + load + render-frame cost (per-leaf retokenize is the obvious
    M5 hot-path candidate; M2 left a "deferred until perf surfaces"
    note specifically here)
  - Search latency on 100 MB
  - Track in `BENCHMARKS.md`; numbers vs. claims in CHANGELOG
- **Stability pass**:
  - Fuzz the tokenizer → highlighter pipeline (random bytes; vyakarana
    already ships fuzz infra to borrow against)
  - Fuzz the gap-buffer (random `insert`/`delete`/`move` sequences)
  - Fuzz the `editor_step` driver (random keystroke sequences against
    random fixtures — exercises the dispatch / undo / dot interactions)
- **Receipts**: lines-of-code, binary size, .tcyr assertion count,
  PTY-smoke check count, all vs. `vim`/`neovim` baselines

**Done when:** docs read end-to-end, benchmarks land in `BENCHMARKS.md`,
fuzz harnesses run clean for a sustained run.

> **Consumer integration** (`agnoshi`, `aethersafha`) is owner-driven
> from the consumer side and tracked in those projects — when each
> consumer is ready to embed cyim, that work happens there, not here.

---

## Milestone 6 — P(-1) Hardening

**Goal:** internal review pass before going public — per CLAUDE.md's
P(-1) discipline, applied to the whole codebase now that the editor is
feature-complete.

- **Cleanliness gate**: `cyrius build`, `cyrius lint`, `cyrius audit`
  all clean on every source file
- **Internal deep review** — gaps, optimizations, correctness, docs;
  walk every module end-to-end with a fresh head
- **Performance deltas vs. M5 baseline** — prove the wins from any
  M6 changes against the M5 numbers, or accept the cost in writing
- **Refactor pass** — consolidate parallel codepaths that accreted
  through M1–M4 (e.g. the per-mode dispatch arms in `editor_dispatch`,
  the duplicated cmdline-prefix render arms in `render.cyr`)
- **Dead code audit** — record the floor in CHANGELOG; remove
  unreferenced helpers
- **Additional tests / benchmarks** from review findings
- **Documentation audit** — ADRs for decisions made during the
  hardening loop; source citations for any non-obvious algorithm or
  reference; user-facing guides updated

**Done when:** the internal review notebook is empty; perf is justified
or improved; refactor pass produces zero behavior change.

---

## Milestone 7 — Security Audit

**Goal:** external CVE corpus review + security findings filed.
The "external research around 0-days and CVEs" half of P(-1), elevated
to its own milestone because the editor's threat model deserves a
dedicated drill.

- **External research**:
  - vim CVE history — modeline RCE, escape-sequence injection, regex
    catastrophic backtracking, integer overflow in Ex-mode
  - neovim CVE history — Lua sandbox escapes (N/A for cyim by design,
    but instructive for the no-embedded-scripting refusal)
  - terminal-app CVE patterns — escape-sequence handling, large-input
    DoS, paste-as-command attacks
  - File the corpus survey in `docs/security/0day-corpus-YYYY-MM-DD.md`
- **Security audit** per CLAUDE.md's security-hardening checklist:
  1. **Input validation** — file content, key escape sequences, command-
     mode input all bounds-checked
  2. **Buffer safety** — every `var buf[N]` verified; gap-buffer bounds
     tested at edges; no memory-corrupting overruns
  3. **Syscall review** — termios, read/write, fs syscalls all checked:
     args, return values, error paths
  4. **Pointer validation** — no raw pointer dereference of untrusted
     input without bounds
  5. **No command injection** — no `:!cmd` shipped (still); confirm
     `exec_vec()` if it ever lands; never `sys_system()` with
     unsanitized input
  6. **No path traversal** — `:e <path>` validates if a restricted-
     mode lands; document the assumed trust model
  7. **Document findings** in `docs/audit/YYYY-MM-DD-audit.md` with
     severity (CRITICAL / HIGH / MEDIUM / LOW)
  8. **Triage**: CRITICAL / HIGH MUST be fixed before v1.0; MEDIUM /
     LOW tracked with explicit rationale

**Done when:** audit report filed; all CRITICAL / HIGH findings closed;
the 0-day corpus survey is checked in and referenced from CHANGELOG.

---

## Milestone v1.0 — Release ✅ *Done — 2026-04-25*

**Goal:** ship.

- ✅ `VERSION` = `1.0.0`
- ✅ All M0–M7 work landed, audited, documented
- ✅ CHANGELOG header in sync; closeout pass per CLAUDE.md run end-to-end
- ✅ DCE binary 274,656 B; 847 .tcyr assertions; 14 PTY E2E; 3 fuzz; 9 benches; all green from a fresh `rm -rf build && cyrius deps && cyrius build`
- ✅ Security audit: 0 CRITICAL / 0 HIGH / 0 MEDIUM at v1.0
- Tag + release notes pushed; downstream consumers (`agnoshi`,
  `aethersafha`, `daimon`-orchestrated agents) take over from here

---

## Active Bugs — v1.0.x patch slate

### BUG-001 — `cyim --replace` fixed-size `<new>` arg buffer (4064 B) — **FIXED in 1.0.2 (workaround); upstream cyrius fix pending**

**Status (2026-04-26):** worked around in `src/cli.cyr` via
`_cli_args_reload_big()` — re-reads `/proc/self/cmdline` into a 2 MB
heap buffer at startup and rebinds `lib/args.cyr`'s `_args_base` /
`_args_len` globals. Linux ARG_MAX is 2 MB, so the workaround covers
the full kernel-accepted argv range. Verified at 8 KB and 64 KB
`<new>`; 256 KB hits the kernel's `MAX_ARG_STRLEN` per-arg cap
(unrelated to this bug).

The **upstream fix** still needs to land in cyrius/agnosticos
`lib/args.cyr` — replace the `var buf[4096]` stack buffer in
`args_init()` with a heap-backed read sized to ARG_MAX. CLAUDE.md
forbids editing the vendored stdlib from this repo, so the cyim-side
helper stays in place until cyrius is patched and re-vendored, then
`_cli_args_reload_big()` can be retired.

**Severity:** P1 (silent failure on a scriptable surface)

**Symptom.** `cyim --replace <old> <new> <file>` aborts with
`usage: cyim --replace [--wc[=l]] <old> <new> <file>` (exit 2) when
the `<new>` arg is **≥ 4064 bytes**. Below 4064 B: succeeds.

The "usage" message implies "wrong number of args" — it does **not**
indicate the real cause is `<new>` exceeding an internal cap. A caller
sees a usage-shape error and assumes their invocation is wrong.

**Threshold (bisected 2026-04-25):**
| `<new>` size | exit | stderr |
|---|---|---|
| 4063 B | 0 | (clean) |
| 4064 B | 2 | `usage: ...` |

4064 = 4096 − 32 → strongly suggests a `char buf[4096]` (or equivalent)
in arg handling with a ~32 B reservation for null terminator / length
prefix / structural overhead.

**Repro:**
```sh
printf 'foo\nold\nbar\n' > /tmp/tgt.txt
head -c 4063 /dev/urandom | base64 > /tmp/small.txt   # <4064 B
cyim --replace "old" "$(cat /tmp/small.txt)" /tmp/tgt.txt && echo "small ok"
head -c 5000 /dev/urandom | base64 > /tmp/big.txt     # >4064 B
cyim --replace "old" "$(cat /tmp/big.txt)" /tmp/tgt.txt; echo "big exit=$?"
# small ok
# usage: cyim --replace [--wc[=l]] <old> <new> <file>
# big exit=2
```

**Discovered:** 2026-04-25 during cyrius v5.7.5 P4.3a — splicing a
~13 KB `TS_LEX_JSX` block into `src/frontend/ts/lex.cyr`. cyim
`--replace` failed silently (usage error) before the obvious
hypotheses (shell escaping, backtick expansion, `$` substitution)
ruled out via `${#NEW}` byte-count + first/last-80-bytes inspection.
Workaround was `cyim --write` (reads from stdin, no arg-size limit).

**Why this matters.** Per cyim's "Two consumer classes" guiding
principle: **AI agents drive cyim programmatically — the keymap
dispatch is the API surface for both humans and agents.** A scripted
edit surface that silently truncates at 4064 bytes with a misleading
error is exactly the failure mode that breaks agent-driven pipelines
without surfacing root cause. Editor edits over 4 KB are common
(refactor diffs, code generation, large block inserts).

**Fix (suggested):**
1. **Replace the fixed-size buffer with dynamic allocation** sized to
   `ARG_MAX` (Linux: 2 MB) or larger via `cyrius alloc`. The
   underlying syscall surface accepts up to `ARG_MAX`, so cyim's cap
   should be `ARG_MAX` or unbounded (read into a growable buffer).
2. **If a cap stays for safety, distinguish the error.** Replace the
   "usage" fallthrough with a specific message:
   ```
   cyim --replace: <new> arg is N bytes (limit: M); use --write for larger replacements
   ```
   Exit code distinct from 2 (usage) — e.g. exit 5 (arg-too-large).
3. **Audit `<old>` and `<file>` for the same cap.** Same buffer
   pattern likely affects all three positional args. Test all three.
4. **Add a regression** in `tests/` that runs `cyim --replace` with
   `<new>` at 4063 B (must succeed), 4064 B (must succeed after fix),
   65536 B (proves the cap is actually large), and `ARG_MAX − 1024` B
   (proves we use the full syscall surface).

**Workaround until fixed:** for `<new>` over 4 KB, use
`cyim --write <file> < input.txt` (stdin, no arg-size constraint).

---

## v1.0.x / v1.1.x — Shipped

| Version | Date | Scope |
|---------|------|-------|
| **v1.0.1** | 2026-04-25 | Agent-drive CLI surface in-binary: `--headless`, `--write`, `--replace`, `--replace-all` (`src/cli.cyr` lands). |
| **v1.0.2** | 2026-04-26 | `--wc[=l|=long]` modifier on agent-drive ops + BUG-001 fix (cyrius `args_init` 4 KB stack-buffer truncation, worked around with a 2 MB heap re-read of `/proc/self/cmdline`). |
| **v1.1.0** | 2026-04-26 | Structural-invariant primitives: `cyim --grep <pattern> <file>` (read-only line scan, `FILE:N:LINE` per `grep -n`); `--expect=<pat>` / `--expect-not=<pat>` modifiers on `--write` (post-save shape assertion, exit 6); `--expect-N=<n>` / `--expect-1` modifiers on `--replace[-all]` (pre-substitution count assertion, exit 6). Closes the "tool boundary jump" — agent-driven flows assert shape and count without leaving the binary. |
| **v1.1.1** | 2026-04-26 | Agent-drive CLI flag-parser fix: modifiers parse in any position after the verb, including interleaved with or after positionals. |
| **v1.1.2** | 2026-04-26 | `--batch` agent-drive verb (NUL-separated multi-pair stdin substitutions, atomic). Cyrius pin 5.7.1 → 5.7.7. |
| **v1.1.3** | 2026-04-26 | Agent-drive paper cuts: duplicate modifier flags refused with exit 2 across all four verbs (was: silent last-wins); `--grep` `--help` clarifies "literal substring, not regex". |
| **v1.1.4** | 2026-04-27 | Grep-surface expansion (split out of regex bundle, ahead of upstream-gated regex piece) + dogfood-driven file-source replace: `cyim --grepfiles <pattern> <file...>` (multi-file grep, `FILE:N:LINE` shape, exit 0/1/2/3 per `grep` convention); `--context=<n>` modifier on `--grep`/`--grepfiles` (`grep -C N` shape, overlap-merge, `--` between non-adjacent groups and between files); `cyim --replace-files OLD_FILE NEW_FILE FILE` and `--replace-files-all` (OLD/NEW from file contents instead of argv — closes shell-escape friction surfaced in the v1.1.4 dogfood loop when splicing multi-line edits via `--batch`). Cyrius pin 5.7.7 → 5.7.13 (5.7.13 ships `lib/regex.cyr` as glob-only, *not* the planned NFA ABI — `--regex=<flavor>` stays gated, escalated to hard pre-cyrius-5.7.x-EOL target). |

---

## Post-v1.0 — Demand-Gated

| Feature | Trigger | Notes |
|---------|---------|-------|
| **Headless / agent-drive mode** | daimon agent first calls cyim non-interactively | *Shipped in v1.0.1.* Same keymap dispatch, no TTY harness. |
| **Agent-drive ergonomics** | Workflow surfaces a missing primitive | *Shipped iteratively:* `--write`/`--replace`/`--replace-all` (1.0.1), `--wc` + BUG-001 (1.0.2), `--grep` + `--expect[-not]` + `--expect-N` (1.1.0), interspersed-modifier parser (1.1.1), `--batch` (1.1.2), duplicate-flag refusal (1.1.3), `--grepfiles` + `--context=N` + `--replace-files[-all]` (1.1.4). Continue per-need. |
| **`--regex=<flavor>` modifier on grep/replace verbs** | *Shipped: v1.2.0 (ere), v1.3.0 (bre/re2/pcre/vim), v1.3.1 (fuzzy with plen-approximation), v1.3.2 (fuzzy precision + `--fuzzy-edits=<n>`).* All six niyama flavors live across all six pattern verbs. Backreferences (`\1`-style) still deferred per niyama's long-term security-against-misuse plan. Surfaced in `cyim --help`. | v1.3.2 tightened fuzzy substitute span via post-match candidate-length walk scored by `niyama_fuzzy_distance` (tie-break smallest L → newline preservation on deletion edits). Added `--fuzzy-edits=<n>` modifier on all six pattern verbs; encoding stores k+1 in `RegexOpts +8` so `k=0` (exact-fuzzy) is distinguishable from "user didn't set". Backref support added when surface demand shows. |
| **System clipboard** | Wayland integration via `aethersafha` | Belongs in compositor layer, not editor |
| **LSP client** | *Promoted to v1.4.0 (2026-05-06)* — `cyrius-lsp` server is stable in the cyrius toolchain (`programs/cyrius-lsp.cyr`; JSON-RPC 2.0 over stdin/stdout; diagnostics today, definition / references / documentSymbol queued upstream). cyim-side scope: subprocess spawn, JSON-RPC framing, diagnostic rendering in buffer (highlight + status line + `:errors` jump), keymap for `gd` (go-to-definition) / `gr` (find-references). Out of scope for first cut: completion, hover, formatting (those land later patches once the diagnostic loop is solid). Note: the `cyrius-plugins` marketplace at `MacCracken/cyrius-plugins` packages cyrius-lsp for **Claude Code's** LSP wiring — separate consumer; cyim's LSP client is its own implementation. | Own milestone; not a 1.3.x patch. v1.3.x continues for fuzzy / agent-drive paper-cuts; v1.4.0 is the LSP cut. |
| **Terminal emulator embed** | Third user asks for `:term` | Until then, `Ctrl-z` + shell is fine |
| **Macros** | Recurring need surfaces | `q<reg>` recording; not v1.0 scope |
| **Plugin system** | Probably never | Refusal §0 — if cyim needs to do X, cyim should do X |

---

## Non-Goals

- **No Vimscript / Lua / Python / any embedded scripting.** This is
  the load-bearing constraint of the project. If a feature requires a
  language to express, the feature gets data syntax or doesn't ship.
- **No `:set compatible`.** We are not a vim clone. We are a modal
  editor in the lineage.
- **No GUI.** cyim is a TTY editor. The compositor (`aethersafha`)
  hosts a terminal; the editor is in the terminal.
- **No "IDE" features.** Project drawer, fuzzy file finder,
  integrated debugger — those compose externally via the AGNOS
  library, not internally via plugin sprawl.

---

## Naming

`cy` (Cyrius) + `im` (the lineage `vi → vim → nvim → cyim`). A name
in the tradition, written in the language of the library.

---

*Last updated: 2026-05-06 (v1.3.2 shipped: fuzzy substitute precision via post-match candidate-length walk + `--fuzzy-edits=<n>` modifier across all six pattern verbs + closeout pass. LSP client promoted from demand-gated to v1.4.0 since cyrius-lsp is stable in the toolchain.).*
