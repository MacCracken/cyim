# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.1.2] — 2026-04-26

Patch release — `--batch` agent-drive verb + cyrius toolchain bump to
5.7.7. Closes the cyim pain point in cyrius-bb's tooling field notes
(`tooling-pain-points.md`): "no multi-edit-in-one-call mode … a batch
mode (read a list of <old>=>new> pairs) would be cleaner for larger
refactors."

### Added

- `cyim --batch <file>` — apply N substitutions from stdin, save once.
  Stdin format: NUL-separated alternating tokens
  `OLD1\0NEW1\0OLD2\0NEW2\0…\0`. Token count must be even and ≥ 2;
  the stream must end with a NUL. Each pair applies in order to the
  in-memory buffer; the file is written **once** at the end. **Atomic**
  — failure mid-batch (pair K's OLD missing or non-unique) leaves
  FILE untouched on disk.

  Default per-pair semantics match `--replace`: OLD must be unique in
  the (in-progress) buffer at apply time, exit 5 if not. `--all`
  switches every pair to `--replace-all` (substitute every occurrence).

  Composes with the existing modifier surface:
  - `--wc[=l|=long]` — print `wc(1)` on the post-save buffer.
  - `--expect=<pat>` / `--expect-not=<pat>` — post-save assertion on
    the result; exit 6 on mismatch (file is already saved at that
    point — the assertion is a contract on the *final* result).

  Exit codes:
  - **0** — every pair applied; file saved
  - **1** — save failed
  - **2** — bad CLI args (missing FILE; malformed stdin: empty,
    odd token count, missing trailing NUL, empty OLD)
  - **3** — file not found
  - **4** — pair K's OLD not found in (in-progress) buffer
  - **5** — pair K's OLD occurs more than once and `--all` not passed
  - **6** — `--expect` / `--expect-not` mismatch on final buffer

  Closes the workflow gap noted in `tooling-pain-points.md` — the
  three-chained `--replace` block in cyrius-bb's `cyrius.cyml` rewrite
  is now one call. Stdin format byte-clean: handles em-dashes,
  newlines, the literal `=>` (the sigil the field-notes author
  proposed) — no escape ceremony required because separators are
  NUL bytes, not text.

  Sequel to v1.1.0's `--grep`/`--expect[-not]`/`--expect-N` primitives:
  v1.1.0 closed the *check* boundary jump (no more `cyim … && rg …`),
  v1.1.2 closes the *substitution* boundary jump (no more
  `cyim --replace … && cyim --replace … && …`).

### Changed

- Cyrius toolchain pin: `5.7.1` → `5.7.7` (in `cyrius.cyml [package].cyrius`).

### Tests

- `tests/cli_smoke.sh` extended from 10 → 28 cases. New cases
  (11–25) cover: single pair, sequential multi-pair, non-unique-OLD
  rejection without `--all` (with explicit on-disk atomicity check),
  `--all` global mode, mid-batch failure with on-disk atomicity check,
  empty stdin, odd token count, missing trailing NUL, empty OLD,
  `--expect` / `--expect-not` post-save semantics, interspersed
  modifiers, extra-positional rejection, and a multi-byte-Unicode
  (em-dash) round-trip via `--grep` post-substitution.

## [1.1.1] — 2026-04-26

Patch release — agent-drive CLI flag-parser fix.

### Fixed

- `--write`, `--replace`, `--replace-all`: modifier flags
  (`--wc[=l|=long]`, `--expect=<pat>`, `--expect-not=<pat>`,
  `--expect-N=<n>`, `--expect-1`) are now parseable in any position
  *after the verb*, including interleaved with the positionals or
  after them. v1.1.0 had a front-only modifier loop that bailed at
  the first non-flag arg, so:
  - `cyim --replace OLD NEW --expect-1 FILE` parsed `--expect-1` as
    `FILE` and dropped the real `FILE`, surfacing as exit-3
    `file not found` against the literal path `--expect-1`.
  - `cyim --write FILE --wc=l` silently dropped `--wc=l` (treated as
    a stray after-positional arg, exit 0 with no `wc` output).
  - `cyim --replace OLD NEW --expect-N=1 FILE` had the same shape as
    the `--expect-1` case.

  The fix walks the full argv after the verb, segregating recognized
  modifier flags vs positionals; an unexpected fourth positional
  yields `exit 2` with `unexpected extra argument` on stderr (was
  silently consumed before).

  Note: modifiers BEFORE the verb (`cyim --expect-1 --replace ...`)
  remain out-of-spec — `cyim --help` and the CLAUDE.md surface both
  document modifiers as living between the verb and the positionals.
  An unrecognized first arg falls through to the editor-launch path,
  the same as v1.1.0.

## [1.1.0] — 2026-04-26

Agent-drive CLI surface grows three structural-invariant primitives:
`--grep` (read-only line scan), `--expect` / `--expect-not` (post-write
shape assertion), `--expect-N` / `--expect-1` (pre-substitution count
assertion). Each closes a "tool boundary jump" that previously forced
scripts to chain `rg` / `wc` / `grep -c` around cyim — every check stays
in one binary, one decision, one exit code.

### Added

- `cyim --grep <pattern> <file>` — read-only line scan. Emits
  `FILE:N:LINE` (matches `grep -n` exactly: no spaces around the
  second colon) for every line containing `<pattern>` as a literal
  substring (same matching semantics as `--replace`'s `OLD` — no regex,
  byte-wise compare). Exit codes follow grep(1) convention:
  - **0** — at least one match
  - **1** — no match (file scanned cleanly, just nothing found)
  - **2** — usage error (missing args, empty pattern)
  - **3** — file not found

  Keeps the workflow inside cyim — no `rg` in `PATH`, no shell-escape
  ceremony for special characters in `<pattern>`. Lines without a
  trailing newline still emit (unlike a naive `while read line`).
- `--expect=<pat>` / `--expect-not=<pat>` modifiers on `--write`. After
  the new file content is saved, the resulting buffer is scanned for
  `<pat>`; mismatch returns **exit 6** with a message on stderr
  (`cyim --write: --expect pattern not found in result` or
  `cyim --write: --expect-not pattern present in result`). The file is
  saved either way — the assertion is a contract on the *result*, not
  a save gate. Composes with `--wc` in any order:
  `cyim --write --wc=l --expect="ROUTE_TABLE" handlers.cyr`.

  Closes the structural-invariant case: "after this rewrite,
  `TS_LEX_JSX_SKIP` MUST NOT appear" is now one call (one decision,
  one exit code), not a `cyim --write … && rg -q TS_LEX_JSX_SKIP …`
  chain that loses the connection between edit and check on failure.
- `--expect-N=<n>` / `--expect-1` modifiers on `--replace` and
  `--replace-all`. Asserts `OLD` occurs *exactly* `<n>` times in the
  file *before* substitution; mismatch returns **exit 6** without
  writing. `--expect-1` is sugar for `--expect-N=1`.
  - Takes precedence over the implicit unique/no-match rules — an
    explicit count assertion is the strongest contract the caller can
    express.
  - `--expect-N=0` is the "must be a no-op" idiom: succeeds without
    writing when `OLD` is absent (and honors `--wc` on the unchanged
    file); exits 6 if `OLD` is present.
  - Closes the silent-no-op gap: `--replace OLD NEW FILE` exits 4 when
    `OLD` is missing, but exit 4 is easy to miss in scripts. Pair with
    `--expect-1` and the assertion is explicit.
- `src/cli.cyr` — new helpers backing the surface:
  `_cli_argprefix(arg, prefix)` (modifier-suffix splitter for
  `--expect=…`), `_cli_atoi_nn(s)` (non-negative decimal parser for
  `--expect-N=…`), `_cli_write_buf_range(b, start, end, chunk, cap)`
  (chunked stdout writer for grep line emission — O(N/cap) syscalls
  instead of one per byte), `run_grep(pattern, file_path)` (the line
  walker; handles files without trailing newlines and empty files
  correctly).
- `tests/integration_smoke.py` — 18 new checks covering: `--grep` hit,
  miss, no-args, missing-file, empty-pattern, no-trailing-newline;
  `--write --expect` pass + miss; `--write --expect-not` pass + hit;
  `--wc` + `--expect` compose in either order; `--replace --expect-1`
  match + miss; `--replace-all --expect-N=N` match + mismatch;
  `--replace --expect-N=0` defensive no-op (both branches);
  malformed `--expect-N=<non-int>` exits 2.

### Changed

- Exit code **6** added for assertion failures (`--expect` /
  `--expect-not` / `--expect-N` mismatches). Codes 0–5 unchanged.
  `--grep` overloads exit 1 with grep(1)-conventional "no match"
  semantics — disjoint verb, no collision with the `--write`/`--replace`
  "save failed" meaning of 1.
- `run_write` signature: now `(file_path, wc_mode, expect_pat,
  expect_pol)`. Pass `0, 0` for the trailing pair to preserve pre-1.1
  behavior. `expect_pol`: `0` none, `1` must contain, `2` must not.
- `run_replace` signature: now `(old_str, new_str, file_path, mode,
  wc_mode, expect_n)`. Pass `-1` for `expect_n` to preserve pre-1.1
  behavior (no count assertion).
- Modifier parsing in `src/main.cyr` now uses a per-verb consume loop
  so `--wc`, `--expect`, `--expect-not`, `--expect-N`, `--expect-1`
  can appear in any order between the verb and its positional args.
  Pre-1.1 `--wc` placement (immediately after the verb) still works —
  the new behavior is a strict superset.

## [1.0.2] — 2026-04-26

`--wc` modifier on the agent-drive CLI ops + BUG-001 fix
(silent truncation of `cyim --replace` for `<new>` ≥ ~4 KB).

### Added

- `--wc` modifier may follow `--write`, `--replace`, or `--replace-all`.
  On a successful save, prints `wc(1)` output for the resulting file
  to stdout (matches GNU `wc`'s field order so it drops in for
  existing wrappers):
  - **bare** `--wc`     → `<lines> <words> <bytes> <file>\n`  (matches `wc <file>`)
  - `--wc=l`            → `<lines> <file>\n`                  (matches `wc -l <file>`)
  - `--wc=long`         → alias for `--wc=l`
  Modifier sits between the operation flag and its positional args:
  `cyim --write --wc <file>`,
  `cyim --replace --wc=l <old> <new> <file>`,
  `cyim --replace-all --wc <old> <new> <file>`.
- `src/cli.cyr` — `_cli_count_lines`, `_cli_count_words`,
  `_cli_print_wc` helpers. Word counter follows the POSIX `wc`
  whitespace set (space, tab, LF, VT, FF, CR).
- `tests/integration_smoke.py` — three new checks: `--write --wc`
  full output; `--write --wc=l` lines-only output; `--write --wc=long`
  alias.

### Changed

- `run_write` and `run_replace` now take a trailing `wc_mode`
  parameter (`0` silent, `1` full, `2` lines). Silent (`0`) is the
  pre-1.0.2 behaviour, so existing callers and the `cyim-edit` wrapper
  one-liners need no changes.

### Fixed

- **BUG-001 (P1):** `cyim --replace OLD NEW FILE` no longer falls
  through to a misleading "usage" error (exit 2) when the cmdline
  exceeds 4 KB. Root cause is in `cyrius/lib/args.cyr` —
  `args_init()` reads `/proc/self/cmdline` into a 4096 B stack buffer,
  so any cmdline beyond that gets truncated and `argc` undercounts.
  The upstream stdlib fix lands in cyrius/agnosticos and is re-vendored
  when ready (CLAUDE.md: `lib/` is vendored, never edited from this repo).

  Until then, `src/cli.cyr` ships `_cli_args_reload_big()` — a 2 MB
  heap buffer (Linux ARG_MAX, the kernel's hard cap on argv+envp
  combined) that re-reads `/proc/self/cmdline` and rebinds the
  `args.cyr` globals at startup. Verified at 8 KB and 64 KB NEW args;
  256 KB hits the kernel's per-arg `MAX_ARG_STRLEN` cap before cyim
  runs (out of our control). The workaround is additive (one syscall
  + one `alloc(2 MB)` per invocation) and is retired automatically
  once upstream cyrius lifts the 4096 B cap and we re-vendor.

- `tests/integration_smoke.py` — BUG-001 regression: `--replace`
  with an 8 KB NEW arg and a 64 KB NEW arg both succeed and produce
  the expected substituted file.

## [1.0.1] — 2026-04-25

Agent-drive surface, first-class.

### Added

- `cyim --write <file>` — read stdin, replace `<file>`'s contents
  with it. One syscall path: `buf_load_file` skipped, `buf_clear`
  + `buf_insert` from stdin chunks, `buf_save_file`. No dispatch
  detour. Use case: shell-script "Write the new content here, please."
- `cyim --replace <old> <new> <file>` — substitute the first
  occurrence of `<old>` with `<new>`. **`<old>` must be unique
  in the file.** If it occurs more than once, the command refuses
  with exit 5 (matches the Claude Code Edit invariant — pick a
  more specific OLD or use `--replace-all`).
- `cyim --replace-all <old> <new> <file>` — same, every
  occurrence. Returns exit 0 with the file rewritten regardless
  of count (zero matches still exits 4 — "OLD not found").
- `src/cli.cyr` — new module hosting the three runners +
  `_cli_drain_stdin`, `_cli_match_at`, `_cli_count_matches`,
  `_cli_substitute` helpers. Direct gap-buffer ops; no
  dispatch-chain detour because there's no edit-history /
  mode-state / undo to model — these are tools, not user edits.
- `tests/integration_smoke.py` — three new regression checks:
  `--write` round-trip, `--replace` unique-mode success +
  not-unique exit-5 refusal, `--replace-all` multi-substitution.

### Exit codes (consumer contract)

Mirrors `~/.local/bin/cyim-edit` so existing wrapper scripts can
collapse to `exec cyim --write "$@"` / `exec cyim --replace "$@"`
one-liners:

| Code | Meaning |
|------|---------|
| 0    | Success                                                |
| 1    | Save failed (disk full, permission denied)             |
| 2    | Bad CLI args (missing OLD/NEW/FILE, empty OLD)         |
| 3    | File not found                                         |
| 4    | OLD not found in FILE                                  |
| 5    | OLD occurs more than once and `--replace-all` not used |

### Daimon-orchestrated agent surface

CLAUDE.md's consumer story now points at four CLI shapes:

1. `cyim <file>` — interactive (humans).
2. `cyim --headless <file>` — keystroke stream (low-level agent
   drive, full editor semantics including search/undo/dot/visual).
3. `cyim --write <file>` — high-level "set file content" (matches
   the Claude Code `Write` tool shape).
4. `cyim --replace [--all] OLD NEW <file>` — high-level
   "find/replace" (matches the Claude Code `Edit` tool shape, with
   the same uniqueness invariant by default).

`~/.local/bin/cyim-write` and `cyim-edit` wrapper scripts can now
become `exec` shims; they predated the native surface.

### Receipts at v1.0.1

- DCE binary: 283,984 B (1.0.0 was 275,640 B; +8,344 B for the
  three new runners + helpers).
- 18 / 18 .tcyr suites pass.
- 18 integration checks (15 from 1.0.0 + 3 new for `--write` /
  `--replace` / `--replace-all`).
- 0 CRITICAL / HIGH / MEDIUM security findings (unchanged).

## [1.0.0] — 2026-04-25

First release. The M0–M7 work that started as the M0 scaffold
on 2026-04-25 lands as v1.0.0 the same day — every milestone's
output is in this release because we accumulated everything in
the `[Unreleased]` block and bumped at the close. Future
releases will follow the more typical "ship 0.X.Y patches
between minor bumps" cadence.

### Headline features (v1.0)

- **Modal editor** in the vim lineage: NORMAL / INSERT / COMMAND
  / SEARCH / SEARCH_BACK / VISUAL / VISUAL_LINE.
- **Gap-buffer** with full motion + edit surface.
- **Multi-buffer** registry with `:bn` / `:bp` / `:b N` / `:ls`.
- **Multi-window** splits (`:sp` / `:vsp`) with Ctrl-w h/j/k/l
  navigation and per-leaf status row.
- **Syntax highlighting** via [vyakarana](https://github.com/MacCracken/vyakarana)
  1.0.2 — 11 bundled grammars (c, cyrius, javascript, json,
  markdown, python, rust, shell, toml, typescript, yaml). Per-buffer
  tokenbuf cache keeps render frames at sub-microsecond cost on
  unchanged buffers.
- **Search** (`/` `?` `n` `N` `*` `#`) with case-fold via
  `:set ic`; naive byte-wise scan, no regex (no ReDoS class).
- **Undo / redo** (`u` / Ctrl-r) — snapshot-based, per buffer.
- **Visual mode** + single yank register: `y` / `d` / `p` / `P`.
- **Dot repeat** (`.`) replays the last insert session.
- **`:set` runtime config**: `ic` / `noic` / `number` /
  `nonumber` / `tabstop=N` / `maxfilesize=N`.
- **`.cyimrc`** flat-CYML config with palette overrides + the
  same editor options.
- **Headless / agent-drive** entry point — `editor_run(s, keys, n)`
  drives the same dispatch+apply chain a TTY consumer takes,
  exposed via `cyim --headless [<file>]` for shell scripts and
  agents. Reads keystroke bytes from stdin until EOF or
  `editor_quit`; no `tty_raw`, no alt-screen, no per-frame
  render. Recipe:
  `printf 'iEDIT\x1b:wq\r' | cyim --headless file.cyr`.
- **No embedded scripting language. Ever.** Configuration is
  data, not code. The bulk of vim's historical CVE surface
  (Vimscript injection, modeline RCE, plugin sandbox escapes)
  is structurally absent.

### Receipts at v1.0

- DCE binary: **274,656 B** (~10× smaller than vim, ~38× smaller
  than neovim).
- Source: **~4 200 LOC editor + ~5 100 LOC tests/fuzz/grammars**
  (~125× smaller than vim's editor core).
- **847 .tcyr assertions** across 18 suites.
- **15 integration checks** in `tests/integration_smoke.py` —
  14 PTY-driven (search / undo / dot / visual / multi-window /
  highlight) + 1 headless (subprocess pipe into `cyim
  --headless`).
- **3 fuzz harnesses** (gap-buffer, tokenizer, full-driver), all
  pass `cyrius fuzz`.
- **9 perf benches** in `tests/perf.bcyr` with M5 baseline + M6
  cache-hit win recorded in [`BENCHMARKS.md`](BENCHMARKS.md).
- Security audit: **0 CRITICAL / 0 HIGH / 0 MEDIUM** findings;
  8 LOW findings all triaged with rationale per
  [`docs/audit/2026-04-25-m7-audit.md`](docs/audit/2026-04-25-m7-audit.md).
  External CVE corpus survey at
  [`docs/security/2026-04-25-0day-corpus.md`](docs/security/2026-04-25-0day-corpus.md);
  trust-model ADR at [`docs/adr/0001-trust-model.md`](docs/adr/0001-trust-model.md).
- `cyrius lint` clean of correctness warnings; `cyrius fmt --check`
  clean across all `src/*.cyr`.
- **Dead-code floor at v1.0:** two unreferenced symbols
  retained: `tty_cursor_hide` and `tty_cursor_show`. Both are
  public ANSI helpers in [`src/tty.cyr`](src/tty.cyr); they're
  the natural wiring point for "hide cursor during repaint to
  avoid flicker" — a UX polish that's plausible-near-future.
  Total binary cost of the two: ~80 B. Recorded here so a
  future audit can decide whether to delete or wire.

### Late-bite addition (rolled into 1.0.0)

- `cyim --headless [<file>]` — the agent-drive surface promised
  by M1 ("the keymap dispatch is the API for both human + agent
  drivers") finally exposed at the CLI. The internal
  `editor_run` had been in the binary since M1 bite 6 but
  reachable only from `.tcyr` tests. Discovered missing when an
  external agent tried to shell out to cyim and found the
  TTY-only surface; added before the v1.0 tag so consumers
  shipping against 1.0.x have it from day one.
- Recipe (raw bytes; `printf` for ESC / CR):
  `printf 'iEDIT\x1b:wq\r' | cyim --headless file.cyr`
- `tests/integration_smoke.py` — new headless check via
  `subprocess.run` (no PTY needed); proves the
  load → drive → save → exit path round-trips.
- `docs/guides/usage.md` — "Headless / agent-drive" section
  added under Starting cyim.

### CI / release plumbing (v1.0 ship-prep)

- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` —
  ship-prep root files. SECURITY.md cross-references the M5/M7
  audit docs, the trust-model ADR, and explains what's in/out
  of scope for security reports.
- `.github/workflows/ci.yml` rewritten — modeled on owl's
  proven shape. Now has: `workflow_call` trigger (release.yml
  reuses it as a gate), ELF verify, `cyrius lint` per-file
  with non-cosmetic-warning hard fail, `cyrius test`,
  `cyrius fuzz`, `cyrius bench tests/perf.bcyr` (compile-only
  smoke), `python3 tests/integration_smoke.py` (PTY E2E), DCE
  parity check (re-runs PTY smoke against the `CYRIUS_DCE=1`
  binary), plus a separate `security` job (regression guards
  for /bin/sh, sys_system, F-1 control-byte sub, F-2 file-size
  cap, F-3 cmdbuf cap, oversized stack buffers per CLAUDE.md
  rule) and a `docs` job (required-files coverage + version
  consistency: VERSION = CHANGELOG section = cyrius.cyml
  `${file:VERSION}` indirection = `print_version` string in
  src/main.cyr).
- `.github/workflows/release.yml` rewritten — semver-tag
  trigger, full CI gate via `workflow_call`, version-verify
  job, build matrix (x86_64-linux today; matrix expands as the
  Cyrius toolchain gains targets), source tarball, SHA256SUMS,
  `softprops/action-gh-release@v2` with the release body pulled
  from the matching CHANGELOG section (auto-prerelease on
  `0.x` tags). Packaged artifact ships binary + grammars +
  README + LICENSE + CHANGELOG + VERSION + SECURITY.md; no
  vendored lib/ (consumers run `cyrius deps` themselves).

### Milestones rolled into v1.0

- **M0** (2026-04-25) — scaffold (boots / prints / exits).
- **M1** — gap-buffer + raw-mode TTY + modal dispatch (8 bites).
- **M2** — syntax highlighting via vyakarana (6 bites).
- **M3** — multi-buffer + splits + window navigation (6 bites).
- **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc`
  (6 bites).
- **M5** — polish: docs, perf benches, fuzz, receipts (4 bites).
- **M6** — P(-1) hardening: tokenbuf cache, F-1/F-3/F-4 closures,
  cleanliness gate, refactor pass (6 bites).
- **M7** — Security audit: 0day CVE corpus survey, checklist
  re-walk, F-2 fix, trust-model ADR, M7.5 CVE verification pass
  (5 bites).

For per-milestone detail, see the M2-M7 sections below (preserved
from the [Unreleased] block at the time of release).

---

### Added (M2)
- `[deps.vyakarana]` block in `cyrius.cyml` — pinned to vyakarana
  1.0.2 via git tag; pulls `dist/vyakarana.cyr` into `lib/`.
- `grammars/` directory bundled from vyakarana (11 languages: c,
  cyrius, javascript, json, markdown, python, rust, shell, toml,
  typescript, yaml). Resolved at runtime via `/proc/self/exe` so
  the binary works regardless of cwd.
- `src/highlight.cyr` — vyakarana wrapper: `highlight_init`
  resolves grammars/ via /proc/self/exe and pre-loads bundled
  grammars (suppressing vyakarana's lazy cwd-relative bootstrap
  via `_grammars_bootstrapped = 1`). `highlight_buf(b, lang)`
  copies the gap-buffer to a NUL-terminated heap cstr and calls
  vyakarana's `tokenize_source`. `highlight_kind_at(tb, pos)`
  linear-scans for the token covering `pos`, returning a TK_*
  constant; falls back to `TK_WHITESPACE` on uncovered positions
  or a null tokenbuf.
- `tests/highlight.tcyr` — 31 assertions: unknown-lang returns 0,
  Cyrius `var x = 42` token-kind layout (KEYWORD/IDENT/OPERATOR/
  NUMBER/WHITESPACE), `fn main() { return 0; } # done` covering
  PUNCTUATION + COMMENT-to-EOL, double-quoted STRING literal,
  empty buffer is safe, null tokenbuf is safe.
- `src/lang.cyr` — extension-based language detection.
  `detect_language_from_path(path)` returns one of vyakarana's
  bundled grammar names (cyrius/shell/python/javascript/typescript/
  rust/c/toml/json/yaml) or `"plain"`. Case-insensitive on the
  extension; suffix match (not contains) so `.rsync` doesn't match
  `.rs`. NULL path safely returns `"plain"`.
- `tests/lang.tcyr` — 37 assertions over 8 groups: index lookup,
  cyim's own .cyr/.tcyr/.bcyr/.fcyr/.cyml mappings, every
  language's primary extension, case-insensitivity, full directory
  paths, no-extension misses, NULL path, suffix-vs-contains
  edge cases.
- `src/render.cyr` extended with the M2 highlighting layer:
  `theme_token_color(kind)` (ten-kind palette → 256-color ANSI
  index, -1 for "no color"); `render_build_line(b, line, cols, tb,
  out, max)` materializes one rendered line into a caller buffer,
  emitting fg-escape transitions and resets at kind boundaries with
  an unconditional reset before the trailing CRLF when a color is
  still active. `render_line` and `render_frame` gained a `tb`
  parameter — `tb == 0` is the plain fallback.
- `tests/render.tcyr` — 27 assertions: palette spot-checks, plain
  rendering (incl. empty buffer, empty interior line, `cols`
  truncation), highlighted `var x` byte-for-byte ANSI verification,
  trailing-comment final-reset path, empty interior line stays
  uncolored even with a tokenbuf.
- `src/main.cyr` wired through M2: detects language from
  `file_path` via `detect_language_from_path`, calls
  `highlight_init` once at startup, retokenizes the buffer per
  frame and threads the tokenbuf into `render_frame`. Per-frame
  retokenize is the M2 cost note (incremental retokenize lands at
  M5 perf if a real workload complains).
- `tests/integration_smoke.py` extended with one new check:
  opens `/tmp/cyim-smoke-fixture.cyr`, sends `:q!`, captures PTY
  output, asserts both `ESC[38;5;141m` (keyword fg) and `ESC[0m`
  (reset) appear in the render stream — proving end-to-end that
  syntax highlighting is firing through the live render path.
- `src/cyimrc.cyr` — flat-CYML config parser for palette
  overrides. `cyimrc_load_path(path)` reads the file and applies
  any `palette.<kind> = <code>` lines to a 10-slot table indexed
  by TK_*. `cyimrc_load()` loads `./.cyimrc` (XDG search comes at
  M4 when the config surface widens to keymaps + tab width + line
  numbers). `cyimrc_palette(kind)` returns the override value or
  -1; `theme_token_color` consults it before falling through to
  the bundled palette. Comments (`#`), blank lines, and arbitrary
  whitespace around `=` are tolerated; malformed values silently
  preserve the previous slot value.
- `tests/cyimrc.tcyr` — 22 assertions over 6 groups: missing-file
  is a no-op, basic palette overrides apply, `theme_token_color`
  honors them, comments/blank-lines/whitespace tolerance, malformed
  lines don't poison earlier good values, ident + punctuation
  overrides work too.

### Added (M3)
- `src/buflist.cyr` — buffer registry. `Buffer` record (24 B:
  `buf` / `file_path` / `modified`); editor state grew 64 → 80
  bytes for `buffer_list` (vec) + `active_buf_idx`. `bl_init`
  seeds the registry from the editor's current buf (idempotent;
  safe to call multiple times). `bl_add(buf, path)` appends
  without switching. `bl_set_active(i)` snapshots the editor's
  per-buffer fields into the previous slot, then loads the new
  slot — `editor_buf` / `editor_modified` / `editor_file_path`
  remain the fast-path read mirror so existing code is unaffected.
  `bl_next` / `bl_prev` wrap; no-op on a one-buffer registry.
- `src/command.cyr` — three new commands: `:bn` / `:bp` / `:b N`.
  `:b N` returns ERR_UNKNOWN_CMD on out-of-range or non-numeric
  argument.
- `tests/buflist.tcyr` — 52 assertions over 14 groups: lazy-init
  + idempotence, append-without-switch, snapshot/load round-trip
  preserves modified + file_path per buffer, out-of-range bad
  inputs leave state untouched, no-op switches, wrap-around for
  next/prev, single-buffer next/prev are safe no-ops, full
  end-to-end via `command_execute` for `:bn` / `:bp` / `:b N`,
  and `:ls` formatting (active marker, modified flag from live
  editor state, status cleared by next keystroke).
- `src/mode.cyr` — editor state grew 80 → 88 bytes for
  `status_message` (cstr or 0). `editor_status` /
  `editor_set_status` accessors. `editor_step` clears it at the
  top of every step so commands set it for exactly one render
  frame.
- `src/render.cyr` — `render_status` displays the message in
  place of the mode tag when present (truncated to `cols`).
- `src/command.cyr` — `:ls` writes the buffer registry into a
  static 4 KB scratch (`_cmd_ls_buf`) and pins it as the status
  message: `N[*]: path-or-[scratch] [+]?` per entry, ` | `
  separator, active marked with `*`, modified flag pulled from
  live editor state for the active slot.
- `src/window.cyr` — window tree skeleton. `Window` record
  (72 B): `type` (LEAF / SPLIT_H / SPLIT_V), `buf_idx`,
  `child_a` / `child_b`, `ratio` (out of `WIN_RATIO_FULL` =
  1000), and a four-i64 inline rect populated by `window_layout`.
  `window_new_leaf` / `window_new_split` allocate, accessors
  read each field, `window_layout` recursively assigns rects
  with a 1-cell minimum clamp on degenerate ratios,
  `window_count_leaves` / `window_collect_leaves` traverse
  depth-first, `window_leaf_at(row, col)` does point-in-rect
  lookup.
- `tests/window.tcyr` — 85 assertions over 14 groups: leaf
  construction, single-leaf full rect, h-split divides height,
  v-split divides width, nested splits compose, degenerate
  ratios clamp to 1 cell on both axes, leaf counting,
  depth-first leaf collection order, point-in-rect lookup,
  `window_init` lazy + idempotent, `window_split_active` for
  H and V (with parent links wired and a 3-leaf composite
  rect-fits assertion against an 80×24 frame), and
  `window_replace_child` rewire semantics.
- `src/window.cyr` extended with `parent` ptr (72 → 80 B per
  Window) + `window_replace_child(parent, old, new)` rewire
  helper. New editor-state integration:
  `editor_window_root` / `editor_active_leaf` accessors,
  `window_init(s)` (lazy + idempotent: builds a single LEAF
  root from `bl_active_index`), `window_split_active(s, type)`
  (replaces active leaf with a SPLIT containing two leaves of
  the same buf_idx; focus stays on the original leaf, now
  child_a).
- `src/mode.cyr` — editor state grew 88 → 104 bytes for the
  window-tree pair (`window_root` @ 88, `active_leaf` @ 96).
- `src/command.cyr` — new commands `:sp` and `:vsp` thin
  wrappers around `window_split_active`.
- `src/main.cyr` — `run_editor` now calls `window_init(s)`
  after `bl_init`, so the binary always lands on the
  multi-window render path.
- `src/render.cyr` — `render_build_line_naked` (CRLF-less
  line builder so each leaf places its lines via `tty_move`),
  `_render_leaf` (per-leaf retokenize + write, vim's `~` past
  EOF), `_render_frame_multi` (layout → walk leaves → status
  → cursor in active leaf). `render_frame` dispatches by
  `editor_window_root != 0`; legacy single-buffer path stays
  for the test suite.
- `src/mode.cyr` — multi-byte prefix state (`prefix_pending`
  at offset 104; editor state grew 104 → 112 B). New constants
  `KEY_CTRL_W = 23` and `ACT_WIN_LEFT/DOWN/UP/RIGHT` (400-403).
  `editor_dispatch` consumes Ctrl-w in NORMAL by setting the
  prefix and returning ACT_NONE; the next byte is interpreted
  with the prefix (mapped to ACT_WIN_* on h/j/k/l, otherwise
  swallowed as ACT_NONE).
- `src/window.cyr` — `window_navigate(s, dx, dy)` re-runs
  layout against an 80×23 default frame (cheap, idempotent),
  probes the cell adjacent to the active leaf's edge, and
  switches focus + buffer mirror via `bl_set_active` +
  `editor_set_active_leaf` if a different leaf covers that
  point. `window_apply` routes the four ACT_WIN_* ids;
  non-window actions return 0.
- `src/driver.cyr` — `editor_step` chain extended with
  `window_apply` after `command_apply`.
- `tests/window.tcyr` — 130 assertions total (20 new for
  close-active): last-leaf close sets `editor_quit`,
  split close moves focus to surviving sibling, nested split
  close replaces parent with sibling subtree, `:q` on dirty
  still refused, `:q` on clean leaf in a split closes that
  leaf without exiting, second `:q` exits when only one leaf
  remains.
- `src/window.cyr` — `window_close_active(s)`: collapses the
  active leaf out of its parent split (sibling becomes the
  surviving subtree); when the leaf IS the root,
  `editor_quit` is set so the main loop exits. Buffer
  registry is untouched — closed buffers stay accessible via
  `:ls` / `:b N`.
- `src/command.cyr` — `:q` / `:q!` / `:wq` route through
  `window_close_active` instead of setting `editor_quit`
  directly. Behaviour: `:q` closes the active leaf (dirty
  refusal preserved); `:q!` always closes; `:wq` saves then
  closes. `:e <path>` rewritten as registry-aware: previously
  refused on dirty current buffer; now adds the new file as
  a fresh registry slot, switches active to it, and preserves
  the previous buffer's modified state in its slot.
  `:e <already-open-path>` switches to the existing slot
  without re-reading.
- `src/render.cyr` — per-leaf status row at the bottom of
  every leaf rect (≥2 rows). Format: `[*N: path-or-[scratch] [+]?]`
  padded to rect_w; reverse-video (ESC[7m...ESC[0m) for the
  active leaf so the user can see at a glance which window
  has focus. Cursor positioning updated to clip at the
  content row (one above status), not the leaf's bottom edge.
- `tests/integration_smoke.py` — extended with the M3
  multi-window check: opens file A, vsplits, `:e B`,
  Ctrl-w l, `:sp`, `:e C`, then `:q :q :q :q` to cascade-close
  all four leaves. Asserts every filename appears in the
  rendered PTY stream and that the active-leaf reverse-video
  escape (`ESC[7m`) fires.

### Added (M4)
- `src/mode.cyr` — modes `MODE_SEARCH = 3` and
  `MODE_SEARCH_BACK = 4`. Action ids 25-30:
  `ACT_TO_SEARCH` / `ACT_TO_SEARCH_BACK` (mode-changing
  on `/` / `?`), `ACT_SEARCH_EXECUTE` / `_CANCEL` (Enter /
  Esc inside SEARCH), `ACT_SEARCH_REPEAT` / `_REPEAT_BACK`
  (`n` / `N` in NORMAL). Editor state grew 112 → 128 bytes
  for `search_pattern` (cstr) + `search_direction`
  (0=forward, 1=back) so `n`/`N` survive mode transitions.
  Dispatch reuses cmdbuf for SEARCH-mode pattern entry —
  same APPEND/BACKSPACE actions, just different
  EXECUTE/CANCEL ids that route to search instead of `:`.
- `src/search.cyr` — naive byte-wise substring scan with
  one wrap-around. `search_forward` starts at cursor + 1
  (so a repeat doesn't lock onto the current match);
  `search_backward` starts at cursor - 1 with backward
  scan + end-wrap. `search_apply` snapshots the cmdbuf
  pattern as a heap cstr on EXECUTE, dispatches to the
  right scan, sets `ERR_UNKNOWN_CMD` when no match.
- `src/render.cyr` — status row now prefixes `/` for
  MODE_SEARCH and `?` for MODE_SEARCH_BACK; cursor is
  positioned in the cmdline area for both.
- `src/driver.cyr` — `editor_step` chain extended with
  `search_apply` (after `window_apply`).
- `tests/search.tcyr` — grew to 59 assertions: 37 from the
  initial bite (forward/backward scan + `n`/`N` cycle +
  cancel + cmdbuf edits + no-match + `+1` offset + empty
  pattern), 18 added for `*` (next word under cursor) /
  `#` (previous word) including whitespace + single-
  occurrence + word-extraction edge cases, plus 4 new for
  `:set ic`-driven case-fold scans (alpha FOO ↔ foo).
- `src/search.cyr` — `_search_word_under_cursor(s)` walks
  the cursor's CCLASS_WORD run forward + backward and
  returns a NUL-terminated heap copy. `*` saves it as the
  search pattern, sets direction forward, runs the scan;
  `#` does the same in reverse. Whitespace / EOF cursor
  is a no-op. The scan helpers gained a `fold` parameter
  consulted by `search_forward` / `_backward` from
  `editor_cfg_ignorecase`; `:set ic` flips it.
- `src/undo.cyr` — snapshot-based undo / redo per buffer.
  Snapshot record (24 B): `data` heap copy + `len` +
  `cursor`. `Buffer` record grew 24 → 40 B for `undo_stack`
  and `redo_stack` vec slots. `undo_record_pre_op` is the
  single hook driver fires before any mutating action;
  `undo_pop` snapshots-then-restores via the redo stack;
  redo is symmetric. New edit clears the redo stack. M4's
  cost note: O(buf_len) per edit; M5 perf can compress.
- `tests/undo.tcyr` — 24 assertions: empty undo is no-op,
  `iabc<Esc>u` empties + Ctrl-r restores, multi-step
  unwinds insert sessions one at a time, new edit clears
  redo, `x` records its own snapshot, undo on a
  no-edits-yet buffer is no-op, undo stacks are per-buffer.
- `src/visual.cyr` — VISUAL / VISUAL_LINE selection with
  anchor stamping on entry, `y` (capture to register), `d`
  (capture + delete + mark modified), `p` / `P` paste
  from register. Single-register model (no a-z named
  registers; system clipboard deferred to post-v1.0 per
  roadmap). `_visual_delete` recorded under undo so visual
  delete is rollback-safe. Editor state grew 128 → 152 B
  for `visual_anchor` + `yank_register` + `len`.
- `tests/visual.tcyr` — 36 assertions: v / V enter
  modes + stamp anchor; selection lo / hi computed
  correctly char-wise and line-wise (snap to line); y /
  d capture-only / capture-+-delete; p / P paste at
  before / after cursor; empty register is safe; y → p
  duplicates the selection; d is undo-able; v / V
  toggling and swapping; VISUAL swallows insert/command
  transition keys.
- `src/driver.cyr` — `editor_step` chain extended with
  `visual_apply` (after `undo_apply`) and pre-mutation
  undo snapshot now covers `ACT_VISUAL_DELETE`,
  `ACT_PASTE_AFTER`, `ACT_PASTE_BEFORE`. New
  dot-repeat tracking — `_dot_begin` / `_dot_record_byte`
  / `_dot_replay` — captures byte-by-byte during INSERT
  sessions; `.` (ACT_DOT_REPEAT) snapshot-replays through
  recursive `editor_step` calls.
- `tests/dot.tcyr` — 19 assertions: dot_buf records bytes
  typed in `iabc<Esc>`; `.` replays at current cursor;
  multiple `.` accumulate; `a` (entry_key=97) recorded
  separately from `i`; `.` with no prior edit is a no-op;
  new insert overrides dot_buf; empty session (`i<Esc>`)
  replays nothing; dot state survives buffer switches.
- `src/cyimrc.cyr` — config-key parsing: `ignorecase`,
  `line_numbers`, `tabstop`. Parsed values held in
  module globals (`-1` sentinel = "not set"); `main.cyr`
  applies them to editor state right after `cyimrc_load()`
  unless the file left a sentinel.
- `src/command.cyr` — `:set <option>`: `ic` / `noic` for
  ignorecase, `number` / `nonumber` for line_numbers,
  `tabstop=N` for tab width. Unknown option →
  `ERR_UNKNOWN_CMD`. `tests/command.tcyr` extended with
  12 new assertions covering each toggle plus the
  unknown-option path.
- `src/mode.cyr` — editor state grew 152 → 200 bytes:
  `dot_entry_key` / `dot_buf` / `dot_recording` (M4.5)
  and `cfg_ignorecase` / `cfg_line_numbers` /
  `cfg_tabstop` (M4.6). New action ids: 14-15
  (TO_VISUAL / TO_VISUAL_LINE), 25-32 (search infra),
  210-211 (UNDO / REDO), 220-221 (PASTE_AFTER / BEFORE),
  230-231 (VISUAL_YANK / DELETE), 240 (DOT_REPEAT). Two
  new modes (VISUAL = 5, VISUAL_LINE = 6) with their
  own dispatch arms swallowing insert/command keys so
  the selection isn't lost mid-stream.
- `tests/integration_smoke.py` extended with three M4
  scenarios: `/foo<Enter>iX<Esc>u:wq` proves search +
  undo + save round-trip is identity; `iAB<Esc>$aCD<Esc>0.:wq`
  proves `.` replays the last insert at the new cursor;
  `vlldp:wq` proves visual-delete + paste round-trip.

### Added (M5)
- `docs/guides/usage.md` — getting started for the day-1 vim user.
  Modes table, NORMAL bindings cheat-sheet, INSERT semantics, search
  behaviour, visual + register, multi-file + windows, save/quit,
  differences-from-vim section, troubleshooting.
- `docs/guides/keymap.md` — full keybinding reference. Per-mode
  tables (NORMAL motions, edits, mode transitions, search repeat,
  Ctrl-w window navigation; INSERT; COMMAND; SEARCH; VISUAL).
  Action-id column links every binding to the dispatcher's enum. Also
  documents the action-ID space layout (10s = transitions, 100s =
  motions, 200s = edits, 220s = paste, 230s = visual, 400s = window).
- `docs/guides/cyimrc.md` — config schema. File location, format
  rules, palette overrides table (10 token kinds + bundled defaults),
  editor options table (`ignorecase`, `line_numbers`, `tabstop`),
  boot order, forward-compat policy, and an explicit
  "what's not in the config surface" section for vim users hunting
  for `:nmap` / `:autocmd` / `:!cmd`.
- `docs/audit/2026-04-25-security-audit.md` — initial security audit.
  Internal-only pass against CLAUDE.md's security-hardening checklist;
  external CVE corpus survey deferred to M7. Six findings filed:
  - **F-1 [MEDIUM]** Terminal escape injection — buffer content with
    raw ESC bytes echoes to terminal verbatim. Fix: control-byte
    substitution in render. Tracked for M5 polish or M6.
  - **F-2 [LOW]** Unbounded `:e` file load (DoS).
  - **F-3 [LOW]** Unbounded cmdbuf grow (DoS).
  - **F-4 [LOW]** `_dot_replay` silently fails on > 2048-byte
    insert.
  - **F-5 [LOW]** `:e <path>` accepts arbitrary paths (assumed
    trust model — documenting for future restricted-mode).
  - **F-6 [LOW]** `grammar_load` reads from search path
    (supply-chain shape note for future user-grammar overlays).

  No CRITICAL or HIGH findings — the obvious vim/neovim vuln classes
  are absent by design (no embedded scripting, no `:!cmd`, no
  plugins, no modeline parsing).

- `tests/perf.bcyr` — 8 microbenchmarks driven by `cyrius bench`.
  Gap-buffer fill (1 / 10 / 100 MB), cursor moves on 10 MB, search
  scan (best / worst / case-fold worst), `render_build_line` ×
  1000, `highlight_buf` 1 MB. Surfaces the M2-deferred
  tokenization hot-path: 269 ms / MB → ~3.7 fps for per-frame
  retokenize on a 1 MB file. Flagged for M6 hardening (cache
  tokenbuf keyed by version-counter).
- `BENCHMARKS.md` — top-level perf log. M5 baseline tables
  (gap-buffer, cursor moves, search, render, highlight),
  vim/nvim comparison receipts, test-surface receipts, build
  size by milestone.
- `fuzz/buffer.fcyr` — 10 K random gap-buffer ops with cursor /
  buf_len invariants. Deterministic LCG seed.
- `fuzz/tokenizer.fcyr` — 100 random 1 KB buffers through
  `highlight_buf`; walks every emitted token's kind / start /
  len; asserts spans stay inside `buf_len` and kind is in
  TK_IDENT..TK_ERROR.
- `fuzz/driver.fcyr` — 5 K random keystrokes through
  `editor_step` with a 70/30 printable/control bias; mode +
  cursor + `buf_len` invariants.
- `cyrius.cyml` — `bench` added to stdlib deps for the
  `lib/bench.cyr` framework.

### Added (M6)
- `src/buffer.cyr` — gap-buffer header grew 32 → 64 B for the
  tokenbuf cache: `version` (bumped on every content mutation),
  `cached_tb`, `cached_version`, `cached_lang`. Accessors:
  `buf_version` / `buf_bump_version` / `buf_cached_*` /
  `buf_set_cache`. Mutation helpers (`buf_insert_byte`,
  `buf_delete_left`, `buf_delete_right`, `buf_clear`) now bump
  the version. Cursor moves don't.
- `src/highlight.cyr` — `highlight_buf` consults the per-buffer
  cache: hits when (cached_tb != 0, cached_version == version,
  cached_lang ptr == lang). Pointer-equality is robust because
  `lang_name(i)` returns stable string literals. Closes the
  M5-flagged 3.7 MB/s tokenize hot path — read-only render
  frames now hit a 17 ns pointer compare.
- `src/render.cyr` — `render_ctrl_substitute(c)` returns the
  `^X`-encoded second byte for control bytes (< 0x20 except Tab,
  plus 0x7F DEL). Tab is preserved (indent display); LF never
  reaches the path (line iterator stops at line_end). Both
  `render_build_line_naked` and `render_build_line` now substitute
  control bytes before emitting them — closes M5 audit F-1
  (terminal escape injection). Substituted bytes count as 2 visible
  columns.
- `src/command.cyr` — `command_append` caps cmdbuf at
  `COMMAND_MAX_LEN = 4096`; overflow drops the byte and surfaces
  a status message. Closes audit F-3.
- `src/driver.cyr` — `_dot_replay` snapshot cap raised 2048 →
  16384; overflow surfaces a status message instead of silent
  no-op. Closes audit F-4.
- `tests/perf.bcyr` — new bench `highlight_buf_cache_hit_x1000`
  measures the cache-hit path. M6 result: 17 μs total / 1000 calls
  = ~17 ns per call. ~15.5 million× faster than the cold-tokenize
  baseline (265 ms).
- `tests/render.tcyr` — 23 new assertions covering F-1: ESC /
  BEL / DEL all substituted as `^X`; Tab preserved verbatim; the
  `render_ctrl_substitute` unit table.
- `tests/command.tcyr` — 3 new assertions covering F-3: cmdbuf
  caps at `COMMAND_MAX_LEN`, byte past cap dropped, overflow
  status message set.
- `BENCHMARKS.md` — M6 perf delta table at the top: cache-hit
  ~15.5M× win on the read-only render path; +27% raw-fill cost
  from the per-byte version bump (acceptable trade-off given
  the editing workflow has more renders than mutations).
- `src/mode.cyr` — refactor: the byte-identical SEARCH and
  SEARCH_BACK dispatch arms collapsed into one `||`-guarded
  block (zero behavior change).
- `src/render.cyr` — refactor: the three nearly-identical
  cmdline-prefix render arms (COMMAND / SEARCH / SEARCH_BACK)
  collapsed via a new `_render_cmdline(s, prefix_byte, cols)`
  helper; the three cursor-positioning arms in
  `_render_frame_multi` collapsed into a single `||` branch.
  Net: ~50 lines of duplication removed, zero behavior change.
- `cyrius/docs/development/proposals/relax-uninitialized-var-or-improve-error.md`
  — proposal filed upstream against cc5 5.7.x: relax the
  parse-time rejection of `var X;` (uninitialized) or improve the
  diagnostic to point at the missing initializer rather than the
  `;`. Discovered while writing `fuzz/driver.fcyr` — the misleading
  error message cost ~10 minutes of debugging time across two
  hits in M5.

### Added (M7)
- `docs/security/2026-04-25-0day-corpus.md` — external CVE
  corpus survey, organized into 13 attack classes (modeline RCE,
  regex backtracking, terminal escape injection, integer
  overflow, scripting sandbox escapes, plugin supply chain,
  large-input DoS, TOCTOU, format strings, paste-as-command,
  path traversal, memory corruption, Unicode parsing). Each
  class maps to cyim's posture — *refused-by-design*, *closed*,
  *open*, or *documented*. Includes a top-of-doc note: specific
  CVE references are pending external verification (M7.5
  WebFetch pass against NVD / MITRE / vim CHANGELOG); class
  taxonomy and cyim-posture mapping are independent and stand
  on their own.
- `docs/audit/2026-04-25-m7-audit.md` — second-pass audit re-walks
  CLAUDE.md's security-hardening checklist with the corpus's 13
  classes in hand. Triages M5 carryover findings and files five
  new findings (M7-1 through M7-5). All M5 audit findings now
  closed or documented; **0 CRITICAL / 0 HIGH / 0 MEDIUM**
  remaining.
- `docs/adr/0001-trust-model.md` — Architecture Decision Record
  documenting cyim's threat model: interactive editor for a
  single local user; not a privilege boundary. Fixes the
  long-running ambiguity around F-5 / M7-3 / M7-4. Future
  setuid mode, restricted mode, or daimon-driven sandbox would
  need follow-up ADRs to widen / narrow the trust model.
- `src/mode.cyr` — editor state grew 200 → 208 bytes for
  `cfg_max_filesize` (default 100 MB). New error
  `ERR_FILE_TOO_LARGE` (6) for `:e` size-cap rejections.
- `src/command.cyr` — `_cmd_file_size(path)` opens-lseeks-closes
  to get a file's byte size before allocating any buffer.
  `_cmd_e` now pre-checks against `editor_cfg_max_filesize(s)`
  and refuses with `ERR_FILE_TOO_LARGE` if the file exceeds the
  cap. Closes M5 audit F-2 (corpus Class 7).
- `src/command.cyr` — `:set maxfilesize=N` runtime toggle. The
  `_cmd_match_kv(cb, start, len, prefix)` helper consolidates
  the prefix-match logic for both `:set tabstop=N` and
  `:set maxfilesize=N` (refactor: ~20 lines of nested-if
  duplication removed).
- `tests/command.tcyr` — 9 new assertions covering F-2: `:e`
  refuses files larger than the cap with `ERR_FILE_TOO_LARGE`,
  raising the cap allows the same file, `:set maxfilesize=N`
  updates the cap at runtime.
- `docs/guides/usage.md` — troubleshooting note added for the
  M7-5 byte-vs-glyph column-counting distinction (cursor
  positions are byte offsets, not glyph offsets — matches vim's
  `:set encoding=latin1`).

### Status (M7)
- All 4 M7 bites landed (corpus survey, checklist re-walk,
  remaining-findings closure, closeout) plus M7.5 (WebFetch CVE
  verification) queued as a follow-up.
- 847 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 9 perf benches; all green.
- DCE binary: 274,656 B (M6 was 273,912 B; +744 B for F-2 fix).
- **Security audit triage at end of M7:**
  - **0 CRITICAL / 0 HIGH / 0 MEDIUM** findings.
  - 8 LOW findings, all triaged: F-2 fixed in M7; F-3 / F-4 /
    M5 F-1 closed in M6; F-5 / M7-3 / M7-4 documented per ADR
    0001 (interactive-local-user trust model); M7-1 deferred
    (tabstop overflow surfaces only when the consumer exists);
    M7-2 deferred (user-grammar overlay supply chain — feature
    not yet shipped); M7-5 documented in usage.md (byte-vs-glyph
    column counting).
- **v1.0 gate clear:** CLAUDE.md's "CRITICAL/HIGH must close
  before v1.0" rule satisfied.
- M7.5 — CVE verification pass (WebSearch + WebFetch against
  NIST NVD, MITRE, vim/neovim GitHub Security Advisories,
  Red Hat / Ubuntu / SUSE bulletins). The corpus survey now
  carries verified CVE citations with primary-source links per
  class: CVE-2019-12735 / CVE-2016-1248 / CVE-2002-1377
  (modeline RCE), CVE-2017-17087 / CVE-2017-1000382
  (swap files), CVE-2008-2712 (Vimscript injection),
  CVE-2023-4738 (heap overflow in vim_regsub_both),
  CVE-2022-0413 / CVE-2022-0351 / CVE-2021-3778 / CVE-2025-22134
  (memory corruption family), GHSA-q22m-h7m2-9mgm /
  GHSA-6g74-hr6q-pr8g / GHSA-f2m2-v387-gv87 (vim integer
  overflow advisories), GHSA-2gmj-rpqf-pxvh / CVE-2026-34714
  (tabpanel %{expr} format-string-class), CVE-2017-8386 (less
  paste-as-command bypass via git-shell), CVE-2013-1862
  (Apache mod_rewrite — exemplary terminal-escape-injection),
  GHSA-6f9m-hj8h-xjgj (neovim treesitter path traversal). The
  corpus's "verification pending" warning was removed; the
  audit-doc cross-reference updated to match.

### Status (M6)
- All 6 M6 bites landed: tokenbuf cache, F-1 escape-injection
  fix, F-3/F-4 caps, cleanliness gate, refactor pass, closeout.
- 838 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 9 perf benches; all green.
- DCE binary: 273,912 B (M5 was 262,504 B; +11 KB for the
  cache slots + control-byte substitution + cap-and-message
  handling).
- M5 audit findings closed: F-1 fixed (control-byte
  substitution); F-3 fixed (cmdbuf cap + status); F-4 fixed
  (replay cap raised + status). F-2 (file-load DoS) and F-5/F-6
  (path traversal / supply-chain notes) remain documented for
  M7 / post-v1.0 work.
- M6 perf wins: tokenbuf cache → 15.5M× on read-only render
  path. Trade-off: +27% raw-fill cost from version bump.
- `cyrius lint`: 0 correctness warnings; ~30 advisory line-length
  warnings (style only).
- `cyrius fmt --check`: clean across all `src/*.cyr`.

### Status (M5)
- All 4 M5 bites landed: docs pass (usage / keymap / cyimrc /
  initial security audit), perf benchmarks (1/10/100 MB
  fixtures), fuzz harnesses, receipts.
- 812 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 8 performance benchmarks; all
  green.
- DCE binary: 262,504 B (M4 was 256,344 B; +6 KB for `:set`
  cfg fields + `lib/bench.cyr` dep).
- M5 baseline benches recorded in `BENCHMARKS.md`. Hot path
  identified: vyakarana tokenization at ~3.7 MB/s. Flagged for
  M6 hardening with proposed fix (tokenbuf cache by version).
- Initial security audit (`docs/audit/2026-04-25-security-audit.md`)
  filed with 0 CRITICAL / 0 HIGH / 1 MEDIUM (F-1: terminal
  escape injection from buffer content) / 5 LOW. Full M7 audit
  will pair with external CVE corpus survey.

### Status (M4)
- All 6 M4 bites landed: `/?nN` search + n/N repeat,
  `*`/`#` word search, undo/redo, visual + yank/paste,
  `.` dot-repeat, `:set` + `.cyimrc` config.
- 812 .tcyr assertions across 18 suites + 14 PTY
  end-to-end checks (5 M1 + 2 M2 + 4 M3 + 3 M4).
- DCE binary: 256,344 B (M3 was 226,064 B; +30,280 B for
  search + undo stacks + visual + dot recording + config).
- M4 success criterion verified: vim muscle memory survives
  a full editing session — `/`, `?`, `n`, `N`, `*`, `#`,
  `u`, Ctrl-r, `v`, `V`, `y`, `d`, `p`, `P`, `.`, `:set`
  all behave as expected; integration smoke proves
  search + undo + dot + visual all work end-to-end through
  the live PTY.

### Status (M3)

### Status (M3)
- All 6 M3 bites landed: buffer registry + `:bn/:bp/:b N`,
  `:ls` + status channel, window-tree skeleton, `:sp/:vsp`
  splits, Ctrl-w h/j/k/l navigation, `:q` cascade + per-window
  status + integration smoke.
- 659 .tcyr assertions across 14 suites + 11 PTY-driven
  end-to-end checks (5 from M1, 2 from M2, 4 from M3); all green.
- DCE binary: 226,064 B (M2 was 162,184 B; +63,880 B for
  registry, window tree, multi-window render, per-leaf status).
- M3 success criterion verified: three files open in two splits,
  navigate without losing state, `:q` cascades cleanly to exit.

### Status (M2)
- All 6 M2 bites landed: vyakarana dep + grammars, highlight
  module, lang detection, palette + ANSI render, main.cyr wiring
  + integration smoke, `.cyimrc` palette overrides.
- 467 .tcyr assertions across 12 suites + 7 PTY-driven end-to-end
  checks; all green.
- DCE binary: 162,184 B (M1 baseline 101,560 B; +60,624 B for
  vyakarana + 11 grammars + render highlighting + cyimrc).
- M2 success criterion: `cyim src/buffer.cyr` shows Cyrius
  highlighting matching vyakarana's reference output. Verified
  via the integration smoke's `ESC[38;5;141m` keyword-fg check.

### Added
- `src/buffer.cyr` — gap-buffer primitive: `buf_new`, `buf_len`, `buf_cap`,
  `buf_gap`, `buf_cursor`, `buf_get`, `buf_move`, `buf_grow`,
  `buf_insert_byte`, `buf_insert`, `buf_delete_left`, `buf_delete_right`.
  32-byte heap header `{data, gap_start, gap_end, cap}`; doubles on growth;
  preserves cursor and content across realloc.
- `src/buffer.cyr` file I/O: `buf_load_file` (chunked read, auto-grows),
  `buf_save_file` (two-segment write — pre-gap + post-gap — so save does not
  mutate the cursor).
- `tests/buffer.tcyr` — 47 assertions covering empty-state, end/middle inserts,
  backspace + `x`, no-op edge cases at start/end, growth past initial capacity,
  and growth-with-cursor-mid-buffer.
- `tests/roundtrip.tcyr` — 23 assertions: end-cursor round-trip is
  byte-identical, mid-cursor round-trip exercises the two-segment write,
  missing-file returns -1 without touching the buffer, save-then-load
  preserves a 300-byte payload past initial capacity.
- `src/tty.cyr` — raw-mode TTY: `tty_apply_raw_flags` (pure flag-mask
  function on a 60-byte termios buffer), `tty_raw` / `tty_cooked` (TCGETS
  / TCSETS via ioctl, gated to `CYRIUS_TARGET_LINUX`, captures cooked
  state so any exit path can restore), `tty_probe` (live diagnostic),
  ANSI helpers (`tty_alt_enter` / `_leave`, `tty_clear`,
  `tty_cursor_hide` / `_show` / `_home`, `tty_move(row, col)`,
  `tty_itoa`).
- `tests/tty.tcyr` — 37 assertions: 32-bit field load/store little-endian
  round-trip, raw-flag mask clears all five iflag bits + OPOST + ECHO /
  ICANON / IEXTEN / ISIG and forces CS8 while preserving bystander bits,
  VMIN=1 / VTIME=0 are forced, the mask is idempotent (fixed point), and
  `tty_itoa` formats 0 / 7 / 42 / 1024 correctly.
- `src/mode.cyr` — modal dispatch state machine: `editor_new(buf)`,
  `editor_dispatch(s, key)`, `editor_drive(s, keys, n, out_actions)`
  (headless agent-drive entry point). Three modes (NORMAL / INSERT /
  COMMAND); single-byte NORMAL keymap (`h j k l 0 $ w b G x i a A :`)
  via `map_u64`; INSERT and COMMAND fall through to literal-insert /
  cmdline-append by default with hard-coded specials for Esc / Enter /
  Backspace / DEL. Stable action-id enum with numbered groups so future
  actions land without renumbering. Multi-byte sequences (gg, dd, arrow
  escapes) deferred.
- `tests/dispatch.tcyr` — 57 assertions over 16 groups covering each
  motion, mode-default, every transition path, Backspace/DEL/Enter/LF
  equivalences, and an 8-key headless drive (`i H i Esc l : q Enter`)
  that asserts the full action sequence and final mode.
- `src/buffer.cyr` line/column queries: `buf_line_start`, `buf_line_end`,
  `buf_line_of`, `buf_line_count`, `buf_pos_of_line` (clamps past-end
  to last actual line in a single forward pass), `buf_col_of`. Vim
  convention: trailing `\n` is a line terminator, not a new empty line.
- `src/motion.cyr` — vi motions over the gap-buffer: `motion_left`,
  `_right`, `_up`, `_down`, `_line_start`, `_line_end`, `_word_fwd`,
  `_word_back`, `_file_end`, `_file_start`, plus `motion_cclass`
  (whitespace / word / punctuation classifier — vim-style
  iskeyword) and `motion_apply` which dispatches `ACT_MOVE_*` to the
  right handler and updates `buf_move`. j/k preserve column with
  clamp to target-line end. l/h respect line boundaries. w/b honor
  class transitions and skip whitespace runs. G lands on column 0
  of the last line (first-non-blank refinement deferred).
- `tests/motion.tcyr` — 87 assertions over 11 groups: line-count
  edge cases (empty / lone-`\n` / trailing-`\n`), line/col helpers
  on a 26-byte 3-line fixture, h/l line-boundary clamps, 0/$,
  j/k column-preservation with clamp on shorter lines, w across
  newlines, b across whitespace, G/gg, `motion_apply` end-to-end
  via the editor state, and "all motions on an empty buffer are
  safe no-ops".
- `src/insert.cyr` — INSERT-mode handlers: `insert_literal`,
  `insert_delete_left`, `insert_to_after` (vim `a`: cursor +1
  clamped to buf_len), `insert_to_line_end` (vim `A`: cursor →
  line's `\n` or buf_len; empty lines stay put),
  `insert_to_normal` (vim Esc: cursor steps back one within line
  bounds), and `insert_apply(s, action, key)` which silently
  no-ops on non-INSERT actions.
- `src/driver.cyr` — `editor_step(s, key)` (the canonical
  consume-one-byte function: dispatch + insert_apply +
  motion_apply) and `editor_run(s, keys, n)` (the headless
  agent-drive entry point — same code path the TTY consumer
  takes).
- `tests/insert.tcyr` — 39 assertions over 10 groups including
  unit-level handler invariants, `insert_apply` routing, and four
  end-to-end `editor_run` drives covering `iHello<Esc>` (Esc
  step-back lands cursor on 'o'), `iHello<Esc>$a World<Esc>` to
  build "Hello Wor" via mode round-trip, backspace inside INSERT
  (DEL and ^H both work), and motion+insert mix that prepends
  "hello " before "world".
- `src/buffer.cyr` — `buf_clear` (drop logical content; capacity
  preserved).
- `src/mode.cyr` — `EditorState` grew from 24 → 64 bytes:
  `cmdbuf` (gap-buffer for the `:cmd` line, allocated in
  `editor_new`), `modified`, `quit`, `last_error`, `file_path`.
  Accessors `editor_cmdbuf`, `editor_modified`, `editor_quit`,
  `editor_last_error`, `editor_file_path`, plus paired
  `editor_set_*`. Error-code constants `ERR_NONE`, `ERR_DIRTY`,
  `ERR_NO_FILE_NAME`, `ERR_FILE_NOT_FOUND`, `ERR_SAVE_FAILED`,
  `ERR_UNKNOWN_CMD`.
- `src/insert.cyr` — `insert_literal` and `insert_delete_left`
  now mark the buffer modified (delete only marks if a byte was
  actually removed, so a no-op at line 0 col 0 stays clean).
- `src/edit.cyr` — NORMAL-mode mutations: `edit_delete_right`
  (vim `x`) and `edit_apply` dispatch. New file isolates
  NORMAL-mode edits from INSERT-mode handlers; future `dd`,
  `yy`, change-operators land here.
- `src/command.cyr` — full COMMAND-mode surface: cmdbuf
  lifecycle (`command_reset`, `_append`, `_backspace`),
  parser (`command_execute` splits on first space; matches
  `q` / `q!` / `w` / `wq` / `e`), and per-command implementations
  with modified-flag tracking. `:q` refuses dirty (sets
  `ERR_DIRTY`); `:q!` always quits; `:w` saves and clears
  modified; `:w <path>` updates `file_path`; `:wq` chains; `:e`
  refuses dirty and `ERR_FILE_NOT_FOUND` on missing path.
- `src/driver.cyr` — `editor_step` chain extended to call
  `edit_apply` and `command_apply`; handlers remain mutually
  exclusive on action ids, so the chain stays trivial.
- `tests/command.tcyr` — 58 assertions over 16 groups: cmdbuf
  lifecycle, modified-flag invariants, every command's success
  + failure path (dirty, missing path, missing file, unknown),
  and four end-to-end `editor_run` drives including `:q!` from
  INSERT, `:w <path>` byte-checking the on-disk file, mid-cmdline
  backspace, and Esc-cancels-cmdline.
- `tests/dispatch.tcyr` updated to include `src/buffer.cyr`
  (the new `editor_new` allocates a cmdbuf via `buf_new`).
- `src/render.cyr` — TTY rendering: `render_line` (per-line
  scratch-buffered write with CRLF for raw-mode terminals;
  truncates at `cols`), `render_status` (mode tag + filename +
  modified flag, or `:cmdbuf` in COMMAND mode), `render_frame`
  (clear, walk lines, vim-style `~` for past-EOF rows, position
  cursor on bottom row in COMMAND mode and at line/col
  otherwise).
- `src/main.cyr` — full editor entry point. CLI shapes:
  `cyim [<file>]`, `cyim --version`, `cyim --help`,
  `cyim --probe`. Main loop reads one byte at a time, calls
  `editor_step`, exits when `editor_quit() == 1` or stdin EOF.
  Wraps the loop with `tty_alt_enter` / `tty_raw` on the way in
  and `tty_alt_leave` / `tty_cooked` on the way out.
- `tests/integration_smoke.py` — Python PTY harness that spawns
  cyim against a fixture file, drives recorded keystrokes through
  a real pseudo-terminal, and asserts on-disk file content. Five
  end-to-end checks: `:q` clean exit doesn't modify, `iEDIT<Esc>:wq`
  prepends "EDIT", `A!!<Esc>:wq` appends "!!" before `\n`, `xx:wq`
  deletes first two chars, dirty `:q` refused + `:q!` discards.

### Status
- M1 (gap-buffer + raw-mode TTY + modal dispatch) is complete.
  All 8 bites landed.
- 350 .tcyr assertions across 8 suites + 5 PTY-driven end-to-end
  checks; all green.
- DCE binary: 101,560 B (M0 was 57,728 B; +43,832 B for the
  full editor).

## [0.1.0] — 2026-04-25

### Added
- Initial project scaffold via `cyrius init` (Cyrius 5.7.1)
- Identity locked: sovereign VIM-inspired text editor, Cyrius-native, zero attack surface
- M0–M4 roadmap drafted (gap-buffer → vyakarana highlighting → multi-buffer → search/undo/config)
- Stdlib footprint chosen for modal-editor baseline (fs, hashmap, args, vec, string)
