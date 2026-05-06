# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-05-06 (v1.2.2 — Cyrius toolchain bump 5.7.23 → 5.9.1; no cyim source changes. niyama 1.0.1 fold trigger fired at cyrius 5.9.0 so `lib/niyama.cyr` is now vendored stdlib alongside `lib/regex.cyr` — `--regex={bre,re2,pcre,fuzzy,vim}` engine expansion queued for v1.3.0.)*

---

## Version

- **VERSION**: `1.2.2`
- **Cyrius toolchain pin**: `5.9.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `1.2.2` — Cyrius toolchain bump 5.7.23 → 5.9.1, no cyim source changes. `regex_*` ABI unchanged across the bump; niyama 1.0.1 fold trigger fired at cyrius 5.9.0 so `lib/niyama.cyr` is now vendored stdlib alongside `lib/regex.cyr`. Wiring `--regex={bre,re2,pcre,fuzzy,vim}` queued for v1.3.0, 2026-05-06
- **Prior release**: `1.2.1` — interactive-mode fixes: Enter key in INSERT now splits the line via `ACT_INSERT_NEWLINE` (was inserting CR byte 13 verbatim); arrow keys parse CSI sequences in `editor_feed` (driver-side) instead of being dispatched byte-by-byte through editor_dispatch (which previously triggered vim's destructive `A`/`B`/`C`/`D` NORMAL-mode commands), 2026-04-28
- **Prior prior**: `1.2.0` — `--regex=<flavor>` modifier on six agent-drive verbs (`--grep`, `--grepfiles`, `--replace`, `--replace-all`, `--replace-files`, `--replace-files-all`) consuming the cyrius 5.7.23 stdlib `regex_*` Pike NFA ABI + cyrius toolchain bump 5.7.13 → 5.7.23, 2026-04-28

## Binary

- `build/cyim` — DCE build size: **369,688 B** (v1.2.2 toolchain bump 5.7.23 → 5.9.1, no cyim source changes; +13,264 B over v1.2.1's 356,424 B is entirely stdlib drift between the two cyrius releases. v1.2.1 added `editor_feed` + 8-byte read buffer in `run_editor`/`run_headless` for driver-side CSI parsing, +1,168 B over v1.2.0's 355,256 B; v1.2.0 added the Matcher + RegexOpts abstractions, `_cli_count_matches_m` / `_cli_substitute_regex` / `_cli_substitute_m` matcher-dispatching helpers, six `_dispatch_<verb>(ac)` extraction functions, and the cyrius stdlib `regex` dep — Pike NFA engine consumed via `regex_compile`/`regex_search`/`regex_search_at`/`regex_group_*`. The bulk of the +44,336 B delta from 1.1.4 is the engine itself; cyim consumer code adds ~4 KB; the dispatch extraction is byte-neutral. v1.1.4 was 312,088 B; v1.1.3 was 300,640 B with 8 duplicate-flag guards across four verbs in `src/main.cyr` + a slightly longer `--grep` help string; v1.1.2 was 298,392 B with `run_batch` + `_cli_drain_stdin_raw` in `src/cli.cyr` and `--batch` dispatch in `src/main.cyr`; v1.1.0 was 293,192 B; v1.0.2 was 283,984 B; v1.0.0 was 274,656 B; M6 was 273,912 B; M5 was 262,504 B; M4 was 256,344 B; M3 was 226,064 B; M2 was 162,184 B; M1 was 101,560 B; M0 stub was 57,728 B).

## Tests

- Test suites: M0 + M1 (8) + M2 (4) + M3 (2) + M4 (4)
- Assertion count: 847 (M1 350; M2 +117 = 467; M3 +192 = 659; M4 +153 = 812; M6 +26 = 838; M7 +9 = 847)
- Integration smoke: `tests/integration_smoke.py` — 45 PASS assertions across PTY-driven + headless-subprocess sections: `--headless`, `--write`, `--replace`, `--replace-all`, `--grep`, `--write --expect[/-not]`, `--replace[-all] --expect-N/--expect-1`, multi-window cascade
- CLI parser smoke: `tests/cli_smoke.sh` — 84 PASS assertions across 74 cases (10 v1.1.1 interspersed-modifier regressions + 18 v1.1.2 `--batch` cases incl. atomicity, malformed-stdin, post-save assertions, em-dash unicode round-trip + 7 v1.1.3 cases (6 duplicate-flag refusals across the four verbs + a `--grep '^foo'` literal-substring regression) + 17 v1.1.4 cases: 5 `--grepfiles` (single/multi-file match, no-match exit 1, missing FILE exit 3, FILE:N:LINE shape), 6 `--context=N` (pre/match/post emit shape, overlapping-window merge, non-adjacent `--` separator, `--context=0` byte-for-byte back-compat regression guard, `--context=<non-int>` rejection, duplicate `--context=` refusal), and 6 `--replace-files[-all]` (multi-line OLD/NEW round-trip, empty OLD_FILE rejection, missing OLD_FILE exit 3, non-unique OLD exit 5, atomicity guard on `--expect-1` mismatch, `--wc=l` output shape) + 16 v1.2.0 cases: `--regex=ere` per-verb basics (digits / alternation / anchors), literal-default back-compat regression guard, error paths (invalid pattern / unknown flavor / empty flavor / duplicate `--regex=`), multi-file regex via `--grepfiles`, regex × file-sourced OLD/NEW via `--replace-files[-all]`, and three composition cases (`--regex × --context`, `--regex × --wc=l`, `--regex × --expect-1`))
- Fuzz harnesses: 3; all pass under `cyrius fuzz`
- Performance benches: 9; M5 baseline + M6 cache-hit win in [`BENCHMARKS.md`](../../BENCHMARKS.md)
- Security audit: initial pass [M5](../audit/2026-04-25-security-audit.md), second pass [M7](../audit/2026-04-25-m7-audit.md), 0day-corpus survey at [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md), trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md). **End-of-M7 triage: 0 CRITICAL / 0 HIGH / 0 MEDIUM**; 8 LOW findings all triaged with rationale.
- Cleanliness: `cyrius lint` **0 warnings** (down from 42 pre-v1.2.0 cleanup — see CHANGELOG § Internal); `cyrius fmt --check` clean across all `src/*.cyr`

## Active Milestone

- **M0** — scaffold. *Done.*
- **M1** — gap-buffer + raw-mode TTY + modal dispatch. *Done.*
- **M2** — syntax highlighting via `vyakarana`. *Done.*
- **M3** — multi-buffer + splits + window navigation. *Done.*
- **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc`. *Done.*
- **M5** — polish: docs, perf benchmarks, fuzz, receipts. *Done.*
- **M6** — P(-1) hardening: tokenbuf cache, F-1/F-3/F-4 closures, cleanliness gate, refactor pass. *Done.*
- **M7** — Security audit: 0day corpus, checklist re-walk, F-2 fix, trust-model ADR, M7.5 verification pass. *Done.* All CVE references in the corpus survey verified against primary sources.
- **v1.0** — release. *Done — 2026-04-25.*
- **v1.0.1** — agent-drive CLI surface: `--write`, `--replace`, `--replace-all` folded into the binary directly (src/cli.cyr). *Done — 2026-04-25.*
- **v1.0.2** — `--wc` modifier on agent-drive ops + BUG-001 fix (silent argv truncation > 4 KB). *Done — 2026-04-26.*
- **v1.1.0** — `--grep` (read-only line scan), `--expect`/`--expect-not` (post-write shape assertion on `--write`), `--expect-N`/`--expect-1` (pre-substitution count assertion on `--replace[-all]`). Closes the "tool boundary jump" — structural-invariant checks stay in one binary. *Done — 2026-04-26.*
- **v1.1.1** — agent-drive CLI flag-parser fix: modifiers (`--wc`, `--expect[-not]`, `--expect-N`, `--expect-1`) now parse in any position after the verb, including interleaved with or after positionals. *Done — 2026-04-26.*
- **v1.1.2** — `--batch` agent-drive verb: N substitutions in one call from a NUL-separated stdin stream (`OLD1\0NEW1\0OLD2\0NEW2\0…\0`). Atomic — failure mid-batch leaves the file untouched. Closes the cyim pain point in cyrius-bb's tooling field notes. Cyrius toolchain pin bumped 5.7.1 → 5.7.7. *Done — 2026-04-26.*
- **v1.1.3** — agent-drive paper cuts: duplicate modifier flags (`--expect[-not]=`, `--expect-N=`/`--expect-1`, `--wc[=…]`, `--all`) now refused with exit 2 across all four verbs (was: silent last-wins). `cyim --help` for `--grep` now states "literal substring, not regex". Surfaced in the dogfood loop as "two cyim observations to confirm next sweep". *Done — 2026-04-26.*
- **v1.1.4** — grep-surface expansion (split out of the regex bundle ahead of the upstream-gated `--regex=<flavor>`) + dogfood-driven `--replace-files[-all]`: `cyim --grepfiles <pattern> <file...>` (multi-file grep, `FILE:N:LINE` per match, exit 0/1/2/3 per `grep` convention), `--context=<n>` modifier on `--grep`/`--grepfiles` (`grep -C N` shape with overlapping-window merge + `--` separators between non-adjacent groups and between files), `cyim --replace-files OLD_FILE NEW_FILE FILE` (and `--replace-files-all`) reading OLD/NEW from file contents instead of argv (closes shell-escape friction surfaced when splicing multi-line edits via `--batch`). Cyrius toolchain pin bumped 5.7.7 → 5.7.13 (5.7.13's `lib/regex.cyr` is glob-only — *not* the planned NFA ABI — so `--regex=<flavor>` stays gated; roadmap escalates that piece to a hard pre-cyrius-5.7.x-EOL target). *Done — 2026-04-27.*
- **v1.2.0** — `--regex=<flavor>` modifier on the four pattern verbs (`--grep`, `--grepfiles`, `--replace`, `--replace-all`) and the two file-sourced variants (`--replace-files`, `--replace-files-all`). Today's only valid flavor: `ere` (cyrius stdlib `lib/regex.cyr` Pike NFA — POSIX-ERE-ish). Default stays literal substring (back-compat regression-guarded by `cli_smoke.sh` case 62). Internal threading uses a `RegexOpts` struct with reserved 8-byte slots so future per-engine options (icase, multiline, dotall, ungreedy) extend without rewrite. ADR 0002 records the extensibility shape. Cyrius toolchain pin bumped 5.7.13 → 5.7.23 — first release exposing the Pike NFA engine (landed v5.7.18) through the `regex_*` ABI. Six `_dispatch_<verb>(ac)` extraction functions added in `src/cli.cyr` to keep `main()` under Cyrius's per-function 64-return cap. Additional engines (`bre`, `re2`, `pcre`, `fuzzy`, `vim`) ship via the niyama standalone Cyrius lib; cyim's parser-side picks them up via one extra `elif` arm per flavor. *Done — 2026-04-28.*

## Post-v1.0

Demand-gated work now continues per [`roadmap.md`](roadmap.md)'s
post-v1.0 table. v1.0.1 closed the agent-drive ergonomics gap
(`--headless` + `--write` + `--replace` + `--replace-all` all
ship in the binary). v1.1.0 closes the structural-invariant
gap — `--grep` + `--expect[-not]` + `--expect-N`/`--expect-1`
let scripts assert "after this rewrite, X must / must not appear"
or "this substitution must hit exactly N times" without leaving
the binary. Remaining: system clipboard (via `aethersafha`),
LSP client (when cyrius-lsp stabilizes), terminal embed,
macros, etc.

## Consumers

| Consumer | Status | Notes |
|----------|--------|-------|
| `agnoshi` | Planned | Wires at M3 (multi-buffer ready) |
| `aethersafha` | Planned | Wires at M3 (Wayland terminal hosts cyim) |
| `daimon`-orchestrated agents | Surface ready (v1.2.0) | `cyim --headless` for full keymap drive; `cyim --write`/`--replace`/`--replace-all`/`--replace-files`/`--replace-files-all`/`--grep`/`--grepfiles`/`--batch` for one-shot ops; `--expect[-not]`, `--expect-N`/`--expect-1`, `--all` (on `--batch`), `--context=<n>` (on `--grep`/`--grepfiles`), and `--regex=<flavor>` (on the four pattern verbs + the two file-sourced variants — `ere` flavor today via cyrius stdlib Pike NFA; future flavors via niyama) modifiers compose orthogonally. `--replace-files[-all]` reads OLD/NEW from file paths so multi-line edits and regex patterns don't need argv escaping. Duplicate modifier flags refused with exit 2 (v1.1.3+); the v1.1.4 `--context=` parser machinery shape was the template for v1.2.0's `--regex=` threading. Daimon integration when that consumer is ready. |

## Dependencies

- **stdlib**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex` (added v1.2.0 — Pike NFA / POSIX-ERE-ish engine for `--regex=ere`)
- **External Cyrius deps**: none through M1; `vyakarana` added at M2 for syntax highlighting. niyama 1.0.1 (additional regex engines — `bre`, `re2`, `pcre`, `fuzzy`, `vim`) folded into cyrius stdlib at 5.9.0 per its ADR 0011 fold trigger; available as `lib/niyama.cyr` from the toolchain rather than as an external dep. cyim wires those flavors into `--regex=<flavor>` at v1.3.0.

## Verification Hosts

- x86_64 Linux (primary dev) — verified at scaffold
- aarch64 Pi — pending M1 hardware test
- Apple Silicon Mach-O — pending M1 hardware test
- Windows PE32+ — out of scope (TTY editor; Linux/macOS/BSD targets only)

## Bootstrap Chain

`cyrius` (5.9.1) → vendored stdlib in `lib/` (includes `regex.cyr` + `niyama.cyr` from 5.9.0+ fold) → `src/main.cyr` → `build/cyim`.
Zero external dependencies as of M0.
