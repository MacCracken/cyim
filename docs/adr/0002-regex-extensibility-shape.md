# ADR 0002 — `--regex=<flavor>` extensibility shape

**Status:** Accepted
**Date:** 2026-04-28
**Tags:** cli, regex, extensibility, v1.2.0

---

## Context

cyim 1.2.0 ships `--regex=<flavor>` on six agent-drive verbs
(`--grep`, `--grepfiles`, `--replace`, `--replace-all`,
`--replace-files`, `--replace-files-all`). Today only one flavor
is supported (`ere`, the cyrius stdlib `lib/regex.cyr` Pike NFA /
POSIX-ERE-ish engine that landed at cyrius v5.7.18 and is exposed
through the `regex_*` ABI in v5.7.23).

Two future-direction commitments shape the surface today:

1. **More flavors are coming.** A separate Cyrius lib —
   [`niyama`](https://github.com/MacCracken/niyama) — is being
   built to hold the additional engines (`bre`, `re2`, `pcre`,
   `fuzzy`, `vim`) per the sandhi pattern: standalone repo,
   foldable back into stdlib once it earns the consumer count.
2. **More options on the existing flavor are coming.** Case-
   insensitive matching, multiline mode, dotall, ungreedy default,
   and (eventually) backref support in `--replace` NEW are all
   plausible additions whose precise spelling — separate
   `--regex-<name>` flags vs. comma-extended value
   `--regex=ere,icase` — is not yet decided.

User constraint (recorded 2026-04-28 in
`project_regex_engine_placement.md`): **"we will need more options
to add later, but lets be setup for that without re-write."** The
1.2.0 surface and internal shape must absorb both additions
mechanically.

## Decision

Three load-bearing choices land in 1.2.0:

### 1. Surface: `--regex=<flavor>`, not `--regex` (bare)

Even with one flavor today, the surface accepts a flavor value.
Rationale: when the second engine ships, the existing `--regex=ere`
form continues to work and `--regex=re2` slots in alongside.
Reserving the value-shape now means no later cmdline-syntax break.

Unknown flavor → exit 2 with the supported-flavor list. Empty
flavor (`--regex=`) → exit 2. Duplicate `--regex=` → exit 2
(matches the v1.1.3 dup-flag pattern).

### 2. Internal: struct-threaded `RegexOpts`, not primitive flavor int

The Matcher abstraction in `src/cli.cyr` threads a heap-allocated
`RegexOpts` struct through compile, not a primitive `flavor_id`.
The struct has reserved 8-byte slots for future fields:

```text
RegexOpts (24 B):
  +0   flavor_id       FLAVOR_ERE today; future BRE/RE2/PCRE/fuzzy/vim
  +8   reserved_flags  future bit field (icase, multiline, dotall, ungreedy)
  +16  reserved_aux    future ptr (kv pairs, named-flavor data)
```

Why this matters: when a later patch adds `--regex-icase` (or
`--regex=ere,icase`), the new bit lands in `reserved_flags`. No
function signature changes anywhere in the call chain. No
`run_grep` / `_cli_grep_one` / `_cli_substitute_m` rewrite. The
extension is a struct-field add.

The Matcher itself stays minimal — kind + (needle ptr | nfa) +
nlen — because the per-call dispatch is one bit (literal vs
compiled). Engine config lives on RegexOpts so a single Matcher
shape works for every flavor.

### 3. Naming convention: `FLAVOR_LITERAL = 0`, flavors `>= 1`

Counterintuitive at first — Cyrius doesn't default-zero missing
function args (uninitialized stack contents). Literal-as-zero
turns out to be the safe default *anyway* because all callsites
of `run_grep` / `run_replace` / etc. now pass `regex_flavor`
explicitly from the parser arms. But the convention also makes
the literal path the absent-information default in any future
code path, which matches user expectation ("if I didn't ask for
a regex, treat OLD as literal").

`FLAVOR_LITERAL = 0`, `FLAVOR_ERE = 1`. Future:
`FLAVOR_BRE = 2`, `FLAVOR_RE2 = 3`, `FLAVOR_PCRE = 4`,
`FLAVOR_FUZZY = 5`, `FLAVOR_VIM = 6`.

## Consequences

**Positive:**

- New flavors land as one `elif (streq(name, "<new>")) { return FLAVOR_<X>; }`
  arm in `_regex_flavor_id` plus one `elif (flavor == FLAVOR_<X>)
  { nfa = <engine>_compile(pattern); }` arm in `_matcher_regex`.
  Zero changes to the per-call dispatch, the parser-arm shape, or
  the run_* signatures.
- New per-flavor options (icase, multiline, etc.) land as bits in
  `RegexOpts.reserved_flags` plus parser additions for the
  spelling. Zero changes to the dispatch helpers.
- The single per-call dispatch (`_matcher_kind(m) == MATCHER_LITERAL`)
  stays a one-bit branch; engine selection happens at compile time
  inside `_matcher_regex`, not on the hot per-match path.
- The cli.cyr per-verb dispatch helpers (`_dispatch_grep`,
  `_dispatch_replace`, etc., extracted at v1.2.0 from main.cyr to
  stay under Cyrius's per-function 64-return limit) localize the
  parser logic so adding a `--regex-<name>=` flag touches one
  helper per verb, not the whole main().

**Negative:**

- One extra alloc per verb invocation (the `RegexOpts` struct).
  Negligible at cyim's CLI scale (one alloc per process invocation
  × 24 B).
- The `RegexOpts` struct holds two unused 8-byte slots in 1.2.0.
  Trivial wasted memory; a non-extensible primitive `flavor_id`
  would have looked leaner today and required signature changes
  later. Tradeoff favored extensibility.
- Slightly more indirection for readers: a regex match goes
  parser → flavor lookup → RegexOpts alloc → matcher build →
  engine compile → match. Compared to a direct call into the
  engine. The indirection earns its keep when the second flavor
  lands.

## Cross-repo placement (referenced, not duplicated here)

The decision that **niyama is the home for additional engines** —
not in-tree-in-cyim, not patched into cyrius stdlib — is a
cross-repo design recorded in
`/home/macro/.claude/projects/-home-macro-Repos-cyim/memory/project_regex_engine_placement.md`.
The lineage-level home for this decision belongs in **agnosticos**
(genesis tree); when an agnosticos doc is drafted, this ADR should
link to it as the canonical reference. cyim 1.2.0 does not depend
on niyama at all — it consumes the cyrius stdlib `regex_*` ABI
directly. niyama-provided flavors light up later as additional
`elif` arms in `_regex_flavor_id` and `_matcher_regex`, with the
parser surface unchanged.

## References

- `src/cli.cyr` — Matcher / RegexOpts definitions and the
  `_matcher_*` dispatch helpers (search for "regex / matcher
  dispatch (v1.2.0)").
- `src/cli.cyr` — `_dispatch_<verb>(ac)` extracted parser arms
  (search for "per-verb dispatch helpers (v1.2.0)").
- `~/.cyrius/lib/regex.cyr` — cyrius 5.7.23 `regex_*` ABI:
  `regex_compile`, `regex_match`, `regex_search`,
  `regex_search_at`, `regex_group_start`/`_end`. No
  `regex_free` (lazy bump-init via `_re_m_lazy_init`).
- `tests/cli_smoke.sh` cases 59–74 — the v1.2.0 `--regex=`
  coverage matrix.
- `CHANGELOG.md` v1.2.0 entry — surface notes, exit codes,
  what stays back-compat.
