# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-05-06 (v1.3.7 — **closeout pass before v1.4.0**. All 11 CLAUDE.md closeout steps passed; no source changes. Dead-code floor recorded (7 intentional plugin ABI public surface + 17 stable legacy helpers). v1.4.0 awaits cyim-lsp v0.5.0 — sibling repo `MacCracken/cyim-lsp` scaffolded today at v0.1.0.)*

---

## Version

- **VERSION**: `1.3.7`
- **Cyrius toolchain pin**: `5.9.16` (unchanged from v1.3.6)
- **Last release**: `1.3.7` — Closeout pass before v1.4.0 per CLAUDE.md Closeout Pass policy. All 11 audit steps passed: full clean test + fuzz from `rm -rf build`, dead-code floor recorded (24 functions: 7 plugin ABI public surface kept intentional per ADR 0004, 17 legacy helpers below the third-instance threshold), refactor pass found no parallel codepaths warranting consolidation, code review walked `1.3.0..HEAD` diff end-to-end with no findings, security re-scan found no new `sys_system` / unchecked syscalls (3 new `var buf[N]` all bounded), doc sync confirmed, version-verify across all surfaces. cyim-lsp v0.1.0 scaffolded as sibling repo `MacCracken/cyim-lsp` (sandhi pattern); v1.4.0 picks it up once cyim-lsp's v0.5.0 publishDiagnostics behaviour ships. Pure verification cut; no source changes; binary byte-identical to v1.3.6, 2026-05-06
- **Prior release**: `1.3.6` — ADR 0004 freezes the plugin ABI surface at the v1.3.5 shape. All six hook registration functions, callback signatures, 24 B diag record layout, and DIAG_* severity constants stable across cyim 1.x. Compatibility envelope: backwards-compatible additions allowed within 1.x (new hook types via ADR, new helpers, new severity values appended); breaking changes wait for cyim 2.x. Cyrius toolchain pin bumped 5.9.13 → 5.9.16 (re-vendored `lib/fs.cyr` lost `dir_walk_with_prunes` upstream — cyim doesn't consume, DCE-stripped). Pure doc + toolchain cut; no cyim source changes. Binary byte-identical to v1.3.5 (cyim doesn't consume the changed paths — DCE delivers an exact match). v1.4.0 (cyim-lsp) unblocked, 2026-05-06
- **Prior release**: `1.3.5` — Four remaining hook fire-points wired: `status_segment` (in `render_status`), `normal_key` (in `editor_dispatch`'s NORMAL arm; falls through after built-in keymap miss), `ex_command` (in `command_execute`'s parser; falls through after every built-in `:cmd` miss), `diagnostic_provider` (in `render_frame`'s top — populates `plugin_last_diags()` once per frame). Built-ins win on conflict per ADR 0003 §3. Diag record shape pinned at v1.3.5: 24 B `{line, severity, msg_ptr}` with `DIAG_HINT/INFO/WARNING/ERROR` constants + `diag_new(...)` helper. First inline plugin shipped: `src/plugins/trailing_ws.cyr` registers post_change_hook (recompute line-set), diagnostic_provider (1 DIAG_HINT per trailing-ws line), status_segment ("TWS:N", omits at N==0). 6 of 6 hooks now active. 4 more test files needed `include "src/plugin.cyr"` before `include "src/mode.cyr"` (mode.cyr now references `_plugin_lookup_normal_key`). New `tests/trailing_ws.tcyr` (24 assertions, 8 groups). `tests/plugin.tcyr` extended with dispatch integration tests (33 total, was 27). CLAUDE.md Work Loop step 3 + Closeout step 1 now call out `cyrius fuzz` (closes the v1.3.4 CI-fuzz-gap). All gates green: cyrius test, cli_smoke 118/118, integration smoke PASS, cyrius fuzz 3/3, lint clean. ABI freezes at ADR 0004 (1.3.6 plan), 2026-05-06
- **Prior release**: `1.3.4` — Plugin ABI scaffold per ADR 0003. `src/plugin.cyr` (230 lines): 6-hook registry, `plugin_init()`, register/fire/lookup/collect API. Wired `post_save` + `post_change` fire-points; other 4 hooks deferred to 1.3.5. New `tests/plugin.tcyr` (27 assertions). New `docs/architecture/001-plugin-system.md`. 8 test files + 1 fuzz file gained `include "src/plugin.cyr"`, 2026-05-06
- **Prior prior**: `1.3.3` — BUG-001 retirement cut. Cyrius pin bumped 5.9.2 → 5.9.13. Removed `_cli_args_reload_big()` workaround, 2026-05-06

## Binary

- `build/cyim` — DCE build size: **899,488 B** (v1.3.7 closeout cut; byte-identical to v1.3.6 — pure verification, no source or toolchain changes). v1.3.6 was 899,488 B (ABI freeze + toolchain bump; byte-identical to v1.3.5 — the cyrius 5.9.13 → 5.9.16 stdlib paths cyim consumes are byte-equivalent after DCE). v1.3.5 was 899,488 B (plugin ABI end-to-end + trailing_ws inline plugin; +4,592 B over v1.3.4's 894,896 B — trailing_ws plugin (~700 B) + 4 fire-point integrations (~2.5 KB across render.cyr / mode.cyr / command.cyr) + diag record helpers (~600 B); all 4 previously-DCE'd register/lookup/collect helpers now have active call sites). v1.3.4 was 894,896 B (plugin ABI scaffold; +4,544 B over v1.3.3's 890,352 B — `src/plugin.cyr` 230 lines + fire-point wiring ~30 LOC; the 4 non-wired hooks' register/lookup/collect helpers are linked but DCE-stripped until a plugin uses them). v1.3.3 was 890,352 B (BUG-001 retirement + cyrius 5.9.13 pickup; −4,400 B from v1.3.2's 894,752 B — `_cli_args_reload_big()` removal recovers ~600 B; balance is downstream benefit from cyrius 5.9.3-5.9.13 stdlib improvements consumed by cyim's regex/niyama paths). v1.3.2 was 894,752 B (fuzzy precision + `--fuzzy-edits` wiring + closeout; +5,624 B over v1.3.1's 889,128 B — `_fuzzy_span_end` helper, `_regex_opts_set_fuzzy_edits`, `--fuzzy-edits=` parser arm × 6 dispatchers, threading through 4 `run_*` functions, expanded `--help` flavor table). v1.3.1 was 889,128 B (fuzzy wiring; +720 B over v1.3.0's 888,408 B — fuzzy compile arm + cstring-offset pseudo-`_search_at` + plen-approximation `_group_end` inline at two call sites + expanded `--help` flavor table; niyama_fuzzy + unicode tables already linked in v1.3.0 so no engine-level expansion). v1.3.0 was 888,408 B (v1.3.0 niyama fold + 4 engine flavors; +518,640 B over v1.2.2's 369,768 B = niyama dist (~6.6 KLOC of engine code: bre/re2/pcre/fuzzy/vim engines + posix_classes + unicode_props shared shims) plus the unicode normalization tables (`lib/unicode/_normalize_data.cyr` is ~300 KB on its own). The flat 4-engine dispatch in `src/cli.cyr` (FLAVOR_BRE/RE2/PCRE/VIM constants, `_re_search_at` / `_re_search` / `_re_group_end` helpers, `_flavor_validate` parser arm) adds <2 KB. v1.2.2 was 369,768 B (toolchain bump 5.7.23 → 5.9.1 + version-string cleanup; +13,344 B over v1.2.1's 356,424 B = +13,264 B stdlib drift between the two cyrius releases plus +80 B for the `src/version_str.cyr` extraction (single-source-of-truth for `cyim --version`, regenerated by `scripts/version-bump.sh` per the cyrius pattern). v1.2.1 added `editor_feed` + 8-byte read buffer in `run_editor`/`run_headless` for driver-side CSI parsing, +1,168 B over v1.2.0's 355,256 B; v1.2.0 added the Matcher + RegexOpts abstractions, `_cli_count_matches_m` / `_cli_substitute_regex` / `_cli_substitute_m` matcher-dispatching helpers, six `_dispatch_<verb>(ac)` extraction functions, and the cyrius stdlib `regex` dep — Pike NFA engine consumed via `regex_compile`/`regex_search`/`regex_search_at`/`regex_group_*`. The bulk of the +44,336 B delta from 1.1.4 is the engine itself; cyim consumer code adds ~4 KB; the dispatch extraction is byte-neutral. v1.1.4 was 312,088 B; v1.1.3 was 300,640 B with 8 duplicate-flag guards across four verbs in `src/main.cyr` + a slightly longer `--grep` help string; v1.1.2 was 298,392 B with `run_batch` + `_cli_drain_stdin_raw` in `src/cli.cyr` and `--batch` dispatch in `src/main.cyr`; v1.1.0 was 293,192 B; v1.0.2 was 283,984 B; v1.0.0 was 274,656 B; M6 was 273,912 B; M5 was 262,504 B; M4 was 256,344 B; M3 was 226,064 B; M2 was 162,184 B; M1 was 101,560 B; M0 stub was 57,728 B).

## Tests

- Test suites: M0 + M1 (8) + M2 (4) + M3 (2) + M4 (4)
- Assertion count: 847 (M1 350; M2 +117 = 467; M3 +192 = 659; M4 +153 = 812; M6 +26 = 838; M7 +9 = 847)
- Integration smoke: `tests/integration_smoke.py` — 45 PASS assertions across PTY-driven + headless-subprocess sections: `--headless`, `--write`, `--replace`, `--replace-all`, `--grep`, `--write --expect[/-not]`, `--replace[-all] --expect-N/--expect-1`, multi-window cascade
- CLI parser smoke: `tests/cli_smoke.sh` — 118 PASS assertions across 94 cases (v1.3.2 added 4 fuzzy cases — `--fuzzy-edits=0` exact-only, `--fuzzy-edits` rejected without `--regex=fuzzy`, duplicate `--fuzzy-edits` rejected; case 87 updated to assert the v1.3.2 tight-span behavior). v1.3.1 added 6 fuzzy cases. v1.3.0 added 10 cases for the four niyama flavors. (10 v1.1.1 interspersed-modifier regressions + 18 v1.1.2 `--batch` cases incl. atomicity, malformed-stdin, post-save assertions, em-dash unicode round-trip + 7 v1.1.3 cases (6 duplicate-flag refusals across the four verbs + a `--grep '^foo'` literal-substring regression) + 17 v1.1.4 cases: 5 `--grepfiles` (single/multi-file match, no-match exit 1, missing FILE exit 3, FILE:N:LINE shape), 6 `--context=N` (pre/match/post emit shape, overlapping-window merge, non-adjacent `--` separator, `--context=0` byte-for-byte back-compat regression guard, `--context=<non-int>` rejection, duplicate `--context=` refusal), and 6 `--replace-files[-all]` (multi-line OLD/NEW round-trip, empty OLD_FILE rejection, missing OLD_FILE exit 3, non-unique OLD exit 5, atomicity guard on `--expect-1` mismatch, `--wc=l` output shape) + 16 v1.2.0 cases: `--regex=ere` per-verb basics (digits / alternation / anchors), literal-default back-compat regression guard, error paths (invalid pattern / unknown flavor / empty flavor / duplicate `--regex=`), multi-file regex via `--grepfiles`, regex × file-sourced OLD/NEW via `--replace-files[-all]`, and three composition cases (`--regex × --context`, `--regex × --wc=l`, `--regex × --expect-1`))
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

- **stdlib (auto-prepend)**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex` (Pike NFA / POSIX-ERE-ish for `--regex=ere`, v1.2.0), `unicode/_decode`, `unicode/categories`, `unicode/_categories_data`, `unicode/casefold`, `unicode/_casefold_data`, `unicode/normalize`, `unicode/_normalize_data` (added v1.3.0 — required by niyama_fuzzy's NFD path; per cyrius v5.8.49 subdir-nested-stdlib resolution).
- **stdlib (sandhi-pattern, explicit-include)**: `lib/niyama.cyr` (folded byte-identical at cyrius 5.9.0 from niyama 1.0.1 dist; pulled via `include "lib/niyama.cyr"` in `src/main.cyr` rather than `[deps].stdlib` auto-prepend, to keep preprocess_out under the 2 MB cap that motivated cyrius's opt-in fold pattern at v5.8.65). Provides `niyama_{bre,re2,pcre,vim}_*` ABI consumed by v1.3.0; `niyama_fuzzy_*` linked but parser-gated to v1.3.1.
- **External Cyrius deps**: none through M1; `vyakarana` (1.0.2) at M2 for syntax highlighting (still external).

## Verification Hosts

- x86_64 Linux (primary dev) — verified at scaffold
- aarch64 Pi — pending M1 hardware test
- Apple Silicon Mach-O — pending M1 hardware test
- Windows PE32+ — out of scope (TTY editor; Linux/macOS/BSD targets only)

## Bootstrap Chain

`cyrius` (5.9.16) → vendored stdlib in `lib/` (includes `regex.cyr` + `niyama.cyr` from 5.9.0+ fold + `unicode/*.cyr` properly packaged from 5.9.2; `args.cyr` heap-backed since 5.9.5; `fs.cyr` dir_list UAF fix in 5.9.6) → `src/main.cyr` (explicit `include "lib/niyama.cyr"` per sandhi pattern) → `build/cyim`.
Zero external dependencies as of M0.
