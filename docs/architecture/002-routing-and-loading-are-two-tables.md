# 002 — Routing and loading are two separate tables, and they must agree

**Added:** 2026-08-23 (v1.8.3, written out of the v1.8.2 regression)

---

## The invariant

Two tables in two files decide whether a file gets syntax highlighting,
and **routed must be a subset of loaded**:

| File | Table | Decides |
|---|---|---|
| `src/lang.cyr` | `lang_name(i)` / `lang_exts(i)` / `lang_basenames(i)`, `LANG_COUNT` | which languages cyim *routes* a path to |
| `src/highlight.cyr` | `hl_grammar_name(i)`, `HL_GRAMMAR_COUNT` | which grammars `highlight_init()` *loads* |

`tests/lang.tcyr` asserts both directions: every `lang_name(i)` appears in
`hl_grammar_name`, and every `hl_grammar_name(i)` is a grammar that
`grammars/` actually ships.

## Why a missing entry is fatal rather than slow

This is the part you cannot see from either file alone.
`highlight_init()` ends with:

```cyrius
_grammars_bootstrapped = 1;
```

That is **vyakarana's** global, and setting it turns **off** the
library's own `bootstrap_grammars()`, which loads all 46 grammars by
cwd-relative path. cyim sets it because it has already loaded the
grammars by absolute path resolved from `/proc/self/exe`, and doing the
work twice would be wasteful.

The consequence: a language missing from `hl_grammar_name` does **not**
fall back to the library's loader. It gets no grammar at all.
`tokenize_stream_new` returns 0, `highlight_buf` returns 0, and the
render path treats that exactly as it treats an unknown file type —
drawing uncoloured bytes. **There is no error anywhere in that chain.**

## What it cost

v1.6.2 grew `lang.cyr` from 11 languages to 45 and left the load list at
its original 11. From v1.6.2 through v1.8.2 — six minor versions —
**34 of the 45 routed languages rendered uncoloured**: Go, SQL, HTML,
CSS, C++, Java, Ruby, PHP, Lua, `.cyml`, Dockerfiles, Makefiles, and the
rest.

Three things kept it invisible:

1. **The failure mode is "no colour"**, which is indistinguishable from
   opening a file type cyim doesn't know.
2. **`cyrius` was one of the original 11**, so editing cyim's own source
   — the thing a cyim developer does most — always looked right.
3. **The only test touching this path deliberately avoids it.**
   `tests/highlight.tcyr`'s header says so: it does not call
   `highlight_init()`, because it is exercising the cwd fallback. Under
   the fallback, vyakarana loads all 46 and the gap cannot appear.

## Why the guard compares tables instead of calling the loader

The obvious test — call `highlight_init()`, then check every
`lang_name(i)` resolves through `tokenize_stream_new` — **cannot work**,
and the reason is worth knowing before you try to write it again.

Under `cyrius test` the harness binary lives in a temp directory, so
`_hl_resolve_dir()` finds no `grammars/` beside it and returns 0.
`highlight_init()` then returns **before** setting
`_grammars_bootstrapped`, vyakarana's cwd bootstrap runs, all 46
grammars load — and the runtime check passes no matter what the load
table says. The masking mechanism is the same one that hid the original
bug.

`tests/lang.tcyr` therefore compares the two tables directly, in memory,
with no filesystem resolution involved. That check has no escape hatch.
It was mutation-tested in both directions: dropping a routed language
fails it, and pointing a table entry at a grammar that isn't shipped
fails it.

## When this note stops applying

Two if-chains that must stay in lockstep is the debt, not the design.
The roadmap's watch list carries the refactor: one table, derived rather
than restated — most likely by asking vyakarana for its bundled grammar
list (`grammar_count()` / `grammar_name_at(i)`) instead of cyim keeping
its own copy. Until then the guard is what holds the invariant, and this
note is why the guard is shaped the way it is.

## See also

- [CHANGELOG 1.8.2](../../CHANGELOG.md) § Fixed — the regression and its
  measured A/B
- `src/highlight.cyr` — the `hl_grammar_name` table's own header carries
  the short version of this warning
- `tests/lang.tcyr` — the guard
