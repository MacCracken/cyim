# Line-anchored edits, a dry run, and Cyrius-aware guardrails

**Filed:** 2026-08-29
**Filer:** agnos (one session: ~60 cyim edits across 19 `.cyr` files, including a 25-site atomic conversion)
**Status:** PROPOSAL — five independent asks, ordered by how often they bit. Each stands alone.
**Related issue:** [`../issues/2026-08-29-batch-and-expect-diagnostics.md`](../issues/2026-08-29-batch-and-expect-diagnostics.md)

---

## Context

cyim was the only editor used on `kernel/**/*.cyr` for an entire agnos audit-remediation cut. It did the
job and its assertions caught real mistakes — mistyped anchors, a wrong `--expect-N`, and a non-unique
OLD that would have been a silent half-edit under `sed`. These are the places where the *shape* of the
tool made me work around it rather than with it.

---

## 1. `--replace-lines A:B` — the operation that pairs with `owl --line-range=A:B`

**The friction.** The read tool is line-addressed (`owl --line-range=138:256`); the write tool is
content-addressed. Every edit therefore needs a round trip to invent a unique content anchor for a
region I *already know by line number*.

Where this actually broke: converting 25 `return 0 - 1;` sites in `elf.cyr` to a cleanup helper. All 25
lines are non-unique (`if (p_offset < 0) { return 0 - 1; }` appears in both loaders). Adding surrounding
context made the anchors **overlap each other**, and because `--batch` applies pairs sequentially against
the mutating buffer, pair *k+1*'s OLD no longer matched once pair *k* had rewritten part of it:

    cyim --batch: pair OLD not unique — use --all or specify more     # first attempt
    cyim --batch: pair OLD not found in file                          # after expanding context

I ended up replacing each loader's **entire 119-line span** as one pair — which works, but means a
119-line OLD to change 12 lines, and the diff is unreadable.

**Ask.** `cyim --replace-lines A:B <newfile> <file>`, with a mandatory guard so it cannot silently
target the wrong region after an earlier edit shifts the file:

    cyim --replace-lines 138:149 new.txt elf.cyr --expect-first='            if (p_offset < 0) {'

Multiple `--replace-lines` in one `--batch`, resolved against the ORIGINAL buffer and applied
back-to-front, would express the 25-site case exactly and readably. This is the single ask I would take
over the other four combined.

## 2. `--dry-run` (unified diff, no write)

There is no way to see what an edit *would* do. For `--replace-all` — where the count is the only
feedback — I was choosing between "run it and inspect afterwards" and "grep first and hope the grep
matched cyim's matcher". `--dry-run` emitting a unified diff to stdout and exiting non-zero if nothing
would change closes that, and makes a generated batch reviewable before it touches the tree.

## 3. `--expect` / `--expect-not` on `--replace`

`--help` offers post-save assertions only on `--write` / `--batch`; `--replace` takes `--expect-N`
(a *pre*-substitution count) and rejects `--expect` outright (`unexpected extra argument`, exit 2).
So a one-shot `--replace` can assert how many matches existed but not what the file looks like
afterwards. Allowing both on `--replace` would make single edits as self-checking as batches.

## 4. Cyrius-aware guardrails — the reason to use cyim over a generic editor

cyim already parses Cyrius. Three checks it is uniquely placed to make, each corresponding to a bug
class that cost real time in this very session:

- **`kprint`/`kprintln`/`serial_print` literal lengths.** These carry a hardcoded byte count that must
  match the string; agnos gates it with a dedicated `scripts/check/kprint-len-check.sh`. I tripped it
  **three times**, twice because an em-dash is 3 UTF-8 bytes, not 1. cyim could warn at edit time —
  `warning: kprint literal is 41 bytes, declared 39` — instead of at build time.
- **Duplicate `var` in the same scope.** I added `var ilen2` to a function that already had one; the
  compiler caught it (`duplicate variable`) but only after a full rebuild.
- **`var x[N]` scope sizing.** Module-scope is N u64 = **8N bytes**; function-local is **N bytes**.
  Getting this backwards generated a whole cluster of phantom buffer-overflow findings in an agnos
  audit, and the agnos tree carries hand-written comments warning about it at individual sites. A
  `--warn-array-sizing` that flags a newly-introduced `var x[N]` with the resolved byte count would
  retire the class.

These should be **warnings on stderr, not refusals** — the tool must never refuse an edit it merely
does not understand.

## 5. Multi-file transactions

Some changes are only correct as a set. The clearest example from this session: `fmt_hex_buf` writes 17
bytes, and fixing its negative-value bug is what makes 16-digit output *common* — so the one-token loop
fix and the widening of **seven caller buffers in seven different files** had to land together, or the
first change would turn a never-fires out-of-bounds write into one that fires on every page fault. I
sequenced them by hand and verified with a build.

**Ask.** A `--batch` that accepts `file\0OLD\0NEW\0…` triples and is atomic across *all* named files, so
a set like that either lands whole or not at all.

---

## Explicitly not asking for

- **Change `--batch` atomicity** — it is already correct (a failing pair leaves the file byte-identical).
- **Change the exit codes** — 4 / 5 / 6 / 2 are distinct, non-zero and `&&`-safe as they are.
- **Relax uniqueness** — being forced to disambiguate is a feature; it caught a real would-be half-edit.
