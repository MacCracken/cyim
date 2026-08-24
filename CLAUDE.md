# cyim — Claude Code Instructions

> **Core rule**: this file is **preferences, process, and procedures** — durable rules that change rarely. Volatile state (current version, binary sizes, test counts, in-flight work, consumers) lives in [`docs/development/state.md`](docs/development/state.md), bumped every release. Do not inline state here — inlined state rots within a minor.

---

## Project Identity

**cyim** (`cy` Cyrius + `im` editor lineage `vi → vim → nvim → cyim`) — sovereign Cyrius-native modal text editor, VIM-inspired, zero attack surface.

- **Type**: Application (TTY editor binary)
- **License**: GPL-3.0-only
- **Language**: Cyrius (toolchain pinned in `cyrius.cyml [package].cyrius`)
- **Version**: `VERSION` at the project root is the source of truth — do not inline the number here
- **Genesis repo**: [agnosticos](https://github.com/MacCracken/agnosticos)
- **Standards**: [First-Party Standards](https://github.com/MacCracken/agnosticos/blob/main/docs/development/applications/first-party-standards.md) · [First-Party Documentation](https://github.com/MacCracken/agnosticos/blob/main/docs/development/applications/first-party-documentation.md)
- **Shared crates**: [shared-crates.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/applications/shared-crates.md)

## Goal

Own the editor surface in the AGNOS library. Modal grammar in the lineage of `vi`/`vim`/`neovim` — preserved muscle memory, redesigned implementation. **No embedded scripting language.** Configuration is data (`.cyimrc`, CYML), not code. The editor's surface *is* its binary, and the binary is auditable end-to-end.

## Consumers

- **`agnoshi`** — the AI shell embeds cyim as the in-shell editor.
- **`aethersafha`** — the Wayland compositor hosts cyim in its terminal surface.
- **`daimon`-orchestrated agents** — AI assistants (Claude-style and AGNOS-native agents alike) drive cyim programmatically. The same modal surface humans use, agents drive headlessly. The edit loop closes through cyim — nothing in the loop ships from outside the library. Six CLI surfaces serve this consumer:
  1. `cyim --headless <file>` — low-level keystroke stream over stdin. Full editor semantics: search / undo / dot / visual / multi-window / multi-buffer all available. Encoding-sensitive (raw bytes, `\x1b` for Esc). Use when an agent wants to model arbitrary edits.
  2. `cyim --write <file>` — high-level "set file content from stdin" (matches the Claude Code `Write` tool shape). Direct buffer op, no dispatch detour.
  3. `cyim --replace OLD NEW <file>` — high-level find/replace; OLD must be unique (matches the Claude Code `Edit` tool's uniqueness invariant). Exit 5 if the constraint fails.
  4. `cyim --replace-all OLD NEW <file>` — same, every occurrence.
  5. `cyim --grep PATTERN <file>` — read-only line scan; emits `FILE:N:LINE` (matches `grep -n`). Literal substring (same matching as `--replace`'s OLD), not regex. Closes the "tool boundary jump" so checks stay in one binary.
  6. `cyim --batch <file>` — N substitutions in one call. Stdin format: NUL-separated alternating tokens `OLD1\0NEW1\0OLD2\0NEW2\0…\0`. Pairs apply sequentially in memory; one save at the end. Default per-pair semantics match `--replace` (OLD unique at apply time); `--all` switches every pair to `--replace-all`. Atomic with respect to *logical* mid-batch failure: a pair whose OLD is not unique aborts the whole batch and leaves FILE untouched. **Not** atomic with respect to write failure — the save opens `O_TRUNC`, so a failing write leaves a truncated file. Since 1.8.3 the failure is at least reported (non-zero exit) rather than silently swallowed; true write atomicity is residual R-1 in the [1.8.x hardening audit](docs/audit/2026-08-23-1.8x-hardening.md).

  Modifiers (parsed in any order between verb and positionals): `--wc[=l|=long]` (print `wc(1)` on success of `--write`/`--replace[-all]`/`--batch`); `--expect=<pat>` / `--expect-not=<pat>` (post-save shape assertion on `--write` and `--batch`, exit 6 on mismatch); `--expect-N=<n>` / `--expect-1` (pre-substitution count assertion on `--replace[-all]`, exit 6 on mismatch); `--all` (on `--batch`: every pair runs `--replace-all`).

  Exit codes match `~/.local/bin/cyim-edit` so wrapper scripts collapse to `exec` one-liners. The keymap dispatch (M1) was designed with this consumer first-class, not retrofit.

## Current State

> Volatile state lives in [`docs/development/state.md`](docs/development/state.md) — current version, binary size, test counts, milestone-in-flight, consumer build status. Refreshed every release.
>
> Roadmap and milestones live in [`docs/development/roadmap.md`](docs/development/roadmap.md).

This file (`CLAUDE.md`) is durable rules.

## Scaffolding

Project was scaffolded with `cyrius init cyim` (2026-04-25). **Do not manually create project structure** — use the tools. If the tools are missing something, fix the tools.

## Quick Start

```bash
cyrius deps                              # resolve stdlib deps
cyrius build src/main.cyr build/cyim     # build
cyrius test                              # run tests/*.tcyr + src/test.cyr
cyrius lint src/*.cyr                    # static checks
cyrius audit                             # full check: self-host, test, fmt, lint
CYRIUS_DCE=1 cyrius build ...            # dead-code-eliminated release build
```

## Key Principles

- **Correctness is the optimum sovereignty** — if it's wrong, you don't own it; the bugs own you
- **Modal grammar is fixed; everything else is up for grabs.** Vim's modal grammar is the inheritance. Implementation, configuration surface, rendering, extensibility are designed today.
- **Reference, don't mimic.** Vim is the reference, not the template. cyim is what a modal editor looks like designed today, in a sovereign language, without 30 years of `:set compatible` shape.
- **Refusal as architecture** ([§0](https://github.com/MacCracken/agnosticos/blob/main/docs/design-patterns.md)). Every layer must justify itself with a living reason.
- Test after EVERY change, not after the feature is "done"
- ONE change at a time — never bundle unrelated changes
- Study working programs (`cyrius/programs/*.cyr`) before writing new code
- Programs call `main()` at top level: `var exit_code = main(); syscall(SYS_EXIT, exit_code);`
- **Build with `cyrius build`, never raw `cat file | cc5`** — the manifest auto-resolves deps and prepends includes
- Source files only need project includes — stdlib / external deps auto-resolve from `cyrius.cyml`
- Every buffer declaration is a contract: `var buf[N]` = N **bytes**, not N entries
- Fuzz every parser path — edge cases get invariants, not assertions
- Benchmark before claiming perf — numbers or it didn't happen

## Rules (Hard Constraints)

- **Read the genesis repo's CLAUDE.md first** — [agnosticos/CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/CLAUDE.md)
- **No embedded scripting language. Ever.** Vimscript, Lua, Python, JS — load-bearing constraint. If a feature requires a language to express, it gets data syntax or doesn't ship.
- **No plugin sandbox.** The editor's surface is its binary. Composition happens externally via the AGNOS library, not internally via plugin sprawl.
- **No `:set compatible`.** This is not a vim clone. It is a modal editor in the lineage.
- **No GUI.** cyim is a TTY editor; the compositor (`aethersafha`) hosts a terminal.
- **Do not commit or push** — the user handles all git operations
- **NEVER use `gh` CLI** — use `curl` to the GitHub API if needed
- Do not add unnecessary dependencies — vyakarana is the only planned non-stdlib dep through M5
- Do not skip tests before claiming changes work
- Do not use `sys_system()` with unsanitized input — command injection risk
- Do not trust external data (file content, network input, user args) without validation
- Do not use `break` in while loops with `var` declarations — use flag + `continue`
- Do not add Cyrius stdlib includes in individual src files — the manifest resolves them
- Do not hardcode toolchain versions in CI YAML — `cyrius = "X.Y.Z"` in `cyrius.cyml` is the only source of truth
- Do not edit anything in `lib/` (vendored stdlib)

## Process

### P(-1): Scaffold / Project Hardening (before any new features)

1. **Cleanliness** — `cyrius build`, `cyrius lint`, `cyrius audit`; all tests pass
2. **Benchmark baseline** — `cyrius bench`, save CSV for comparison
3. **Internal deep review** — gaps, optimizations, correctness, docs
4. **External research** — domain completeness, best practices, existing CVE patterns (vim/neovim CVE history is the reference corpus here)
5. **Security audit** — input handling (file content, key sequences), syscall usage (termios, fs), buffer sizes (gap-buffer bounds), pointer validation. File findings in `docs/audit/YYYY-MM-DD-audit.md`
6. **Additional tests / benchmarks** from findings
7. **Post-review benchmarks** — prove the wins against step 2
8. **Documentation audit** — ADRs for decisions made during hardening, source citations, guides for user-facing behavior
9. **Repeat if heavy** — keep drilling until clean

### Work Loop (continuous)

1. **Work phase** — new features, roadmap items, bug fixes
2. **Build check** — `cyrius build`
3. **Test + benchmark + fuzz additions** for new code. Any change that touches `src/{driver,command,buffer,mode,edit,insert}.cyr` or adds a new `src/*.cyr` referenced from those files must re-run `cyrius fuzz` — the existing `.fcyr` harnesses include those files transitively, and single-pass symbol resolution will fail at fuzz-build time if the include order isn't right.
4. **Internal review** — performance (edit latency, repaint cost), memory (gap-buffer growth), correctness, edge cases
5. **Security check** — any new syscall usage, user input handling, buffer allocation
6. **Documentation** — update CHANGELOG, roadmap, `docs/development/state.md`, any ADR the change earned
7. **Version check** — bump via `sh scripts/version-bump.sh X.Y.Z` (writes `VERSION`, regenerates auto-generated `src/version_str.cyr` so `cyim --version` stays in sync, and inserts the CHANGELOG header). `cyrius.cyml` resolves the version via `${file:VERSION}` automatically. Never edit `src/version_str.cyr` by hand — the next bump overwrites it. CI's version-sync gate enforces this.
8. **Return to step 1**

### Security Hardening (before every release)

Every project runs a security audit pass before release — see [first-party-standards § Security Hardening](https://github.com/MacCracken/agnosticos/blob/main/docs/development/applications/first-party-standards.md#security-hardening-new--required-before-every-release) for the full list. Minimum:

1. **Input validation** — file content, key escape sequences, command-mode input all bounds-checked
2. **Buffer safety** — every `var buf[N]` verified; gap-buffer bounds always tested at edges
3. **Syscall review** — termios, read/write, fs syscalls all checked: args, returns, error paths
4. **Pointer validation** — no raw pointer dereference of untrusted input without bounds
5. **No command injection** — `:!cmd` (if ever shipped) uses `exec_vec()` with explicit argv; never `sys_system()` with unsanitized input
6. **Path handling matches [ADR 0001](docs/adr/0001-trust-model.md), and that ADR is the authority** — cyim is an interactive editor for a single local user, not a privilege boundary, so `:e <path>` deliberately does **not** validate, sandbox, or block `../`. There is no restricted mode. *(Through 1.8.2 this line claimed the opposite — "`:e <path>` validates; no `../` escape from project root in restricted mode" — describing a control that ADR 0001 explicitly declines and that has never existed. Corrected at 1.8.3.)* What the audit must actually check here: that no path is used to build a **fixed-size buffer write** without bounds, and that the trust model still holds for the surface in question — note `.cyimrc` is loaded **cwd-relative**, so it is the *directory's* input, not the user's
7. **Known CVE review** — vim/neovim CVE history (modeline RCEs, escape-sequence injection, etc.) as reference corpus
8. **Document findings** — all issues in `docs/audit/YYYY-MM-DD-audit.md`

Severity levels: **CRITICAL** (remote / privilege escalation), **HIGH** (moderate effort), **MEDIUM** (specific conditions), **LOW** (defense-in-depth).

### Closeout Pass (before every minor/major bump)

Run a closeout pass before tagging `X.Y.0` or `X.0.0`. Ship as the last patch of the current minor (e.g. `0.4.5` before `0.5.0`).

1. **Full test + fuzz suite** — all `.tcyr` pass, zero failures; `cyrius fuzz` passes all `.fcyr` harnesses (any new src/ file pulled into the include chain of an existing `.fcyr` needs the include order checked, not just the test-suite include order — single-pass resolution applies the same way)
2. **Benchmark baseline** — `cyrius bench`, save CSV; compare against prior closeout
3. **Dead code audit** — remove unused functions; record remaining floor in CHANGELOG
4. **Refactor pass** — consolidate the minor's additions where parallel codepaths accreted
5. **Code review pass** — walk diffs end-to-end for missed guards, off-by-ones, silently-ignored errors
6. **Cleanup sweep** — stale comments, unused includes, orphaned files
7. **Security re-scan** — quick grep for new `sys_system`, unchecked writes, buffer size mismatches
8. **Downstream check** — `agnoshi` and `aethersafha` still embed cyim cleanly when they reach that integration
9. **Doc sync** — CHANGELOG, roadmap, `docs/development/state.md`, CLAUDE.md (if durable content changed)
10. **Version verify** — `VERSION`, `cyrius.cyml`, CHANGELOG header, `src/version_str.cyr`, and intended git tag all match. `sh scripts/version-bump.sh "$(cat VERSION)"` regenerates `src/version_str.cyr` idempotently if you suspect drift.
11. **Full build from clean** — `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build` passes clean

### Task Sizing

- **Low/Medium effort**: batch freely — multiple items per work loop cycle
- **Large effort**: small bites only — break into sub-tasks, verify each before moving to the next
- **If unsure**: treat it as large

### Refactoring Policy

- Refactor when the code tells you to — duplication, unclear boundaries, measured bottlenecks
- Never refactor speculatively. Wait for the third instance
- Every refactor must pass the same test + fuzz + benchmark gates as new code
- 3 failed attempts = defer and document — don't burn time in a rabbit hole

## Cyrius Conventions

- All struct fields are 8 bytes (`i64`), accessed via `load64` / `store64` with offset
- Heap allocation via `fl_alloc()` / `fl_free()` (freelist) for data with individual lifetimes
- Bump allocation via `alloc()` for long-lived data (vec, str internals)
- Enum values for constants — don't consume `gvar_toks` slots (4,096 initialized globals limit)
- Heap-allocate large buffers — `var buf[256000]` bloats the binary by 256KB
- `break` in while loops with `var` declarations is unreliable — use flag + `continue`
- No negative literals — write `(0 - N)` not `-N`
- No mixed `&&` / `||` in one expression — nest `if` blocks instead
- `match` is reserved — don't use as a variable name
- `return;` without value is invalid — always `return 0;`
- All `var` declarations are function-scoped — no block scoping
- Max limits per compilation unit: 4,096 variables, 1,024 functions, 4,096 initialized globals
- Counting rule: only a top-level `var NAME = <non-literal>;` (call / identifier / expression initializer) consumes an initialized-globals slot; a bare integer-literal init (`var x = 42;`) takes the static-init fast path and enum members are const-folded, so neither counts. See the cyrius guide's **Global Initializers** section (`docs/guides/cyrius-guide.md` in the cyrius repo)

## CI / Release

- **Toolchain pin**: `cyrius = "X.Y.Z"` in `cyrius.cyml [package]`. **No separate `.cyrius-toolchain` file.** CI and release both read this; no hardcoded version strings in YAML.
- **Toolchain install in CI goes through the upstream installer** — `scripts/install.sh` fetched from the *pinned tag*, never a hand-rolled tarball unpack. A manual unpack produces the flat `~/.cyrius/{bin,lib}` layout, and `cyrius deps` resolves dep sidecar stdlib leaves out of `~/.cyrius/versions/<pin>/lib` — so a hand-rolled install fails every run at the deps step. The installer is also what verifies the release checksum and signature. Both workflows assert `~/.cyrius/versions/<pin>/lib` exists right after install.
- **Format checks are a per-file loop, never a glob.** `cyrfmt` reads only `argv[1]` and silently ignores the rest, so `cyrfmt --check src/*.cyr` checks one file and exits 0. Same trap applies to `cyrius lint`.
- **Dead code elimination**: every `cyrius build` in CI and release runs with `CYRIUS_DCE=1`. Binary size is a release metric — track it.
- **Tag filter**: release workflow triggers on `tags: ['[0-9]*']` — semver-only.
- **Version-verify gate**: release asserts `VERSION == cyrius.cyml version == git tag` before building.
- **Lint step**: CI runs `cyrius lint` per source file. Advisory by default; may escalate to blocking.
- **State sync**: release post-hook bumps `docs/development/state.md`. If the hook doesn't, fix the hook — don't hand-maintain state.

## Docs

- [`docs/adr/`](docs/adr/) — architecture decision records. *Why did we choose X over Y?*
- [`docs/architecture/`](docs/architecture/) — non-obvious constraints and quirks. *What can't I derive from the code alone?*
- [`docs/guides/`](docs/guides/) — task-oriented how-tos.
- [`docs/development/roadmap.md`](docs/development/roadmap.md) — completed, backlog, future, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — **live state snapshot, refreshed every release**.
- [`CHANGELOG.md`](CHANGELOG.md) — source of truth for all changes.

New quirks and constraints land in `docs/architecture/` as numbered items (`NNN-kebab-case.md`). New decisions land in `docs/adr/` using the template. **Never renumber either series.**

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/applications/first-party-documentation.md).

## Documentation Structure

```
Root files (required):
  README.md, CHANGELOG.md, CLAUDE.md, CONTRIBUTING.md,
  SECURITY.md, CODE_OF_CONDUCT.md, LICENSE,
  VERSION, cyrius.cyml

docs/ (minimum):
  adr/ — architectural decision records (README + template.md + NNNN-*.md)
  architecture/ — non-obvious invariants (README + NNN-*.md)
  guides/ — task-oriented how-tos
  development/
    roadmap.md — completed, backlog, future
    state.md — live state snapshot (volatile; release-hook-bumped)

docs/ (when earned):
  audit/ — security audit reports (YYYY-MM-DD-audit.md)
  api/ — keymap reference, CYML config schema
  benchmarks.md — perf history (edit latency, repaint cost, large-file open)
```

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/). Performance claims **must** include benchmark numbers. Breaking changes get a **Breaking** section with migration guide. Security fixes get a **Security** section with CVE references where applicable.
