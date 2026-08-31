# `--batch` / `--expect-N` failures do not say *which* pair or *what* count

**Filed:** 2026-08-29
**Filer:** agnos (heavy `--batch` / `--replace-files` user; ~60 edits across 19 `.cyr` files in one session)
**Affects file:** the `--batch` and `--expect-N` argument paths (error emission)
**Severity:** P3 — no wrong edit is ever produced. `--batch` is correctly ATOMIC on failure (verified: a
3-pair batch whose 3rd pair misses leaves the file byte-identical, exit 4), and the exit codes are already
properly distinct and non-zero (4 = OLD not found, 5 = OLD not unique, 6 = expect mismatch, 2 = usage), so
`&&`-chaining is safe. This is purely a *diagnosis* cost.
**Status:** OPEN

---

## Summary

Three failure messages omit the one fact needed to act on them. Each cost a round trip during a long
agnos editing session; with a 25-pair batch the first one costs several.

### 1. `--batch` does not name the failing pair

    $ printf 'A\0X\0B\0Y\0NOPE\0Z\0' | cyim --batch p.cyr
    cyim --batch: pair OLD not found in file          # which of the three?

With N pairs generated programmatically, "not found" identifies a needle in a haystack the caller
built. **Ask:** `cyim --batch: pair 3/3 OLD not found in file` — and ideally the first line of that
pair's OLD, truncated.

### 2. `--expect-N` does not report the count it actually saw

    $ cyim --replace '    var x = 1;' '    var y = 2;' t.cyr --expect-N=3
    cyim --replace: --expect-N count mismatch          # saw how many?

The whole point of `--expect-N` is to assert a count, so the observed count is the payload of the
failure. **Ask:** `--expect-N count mismatch: expected 3, found 1`. This one is the highest
value-per-line-of-code of the three: it turns a failure into an answer. In the agnos session it would
have directly told me `ramdisk_blk_write_sectors` does not exist, instead of my having to grep to
discover why `--expect-N=2` failed.

### 3. "OLD not found" is ambiguous between *wrong anchor* and *already applied*

Re-running an already-applied `--replace` reports `OLD not found in FILE` — the same message as a
genuinely mistyped anchor. For an agent retrying a partially-completed sequence, "this edit is already
in place" and "your anchor is wrong" call for opposite responses. **Ask:** if NEW is already present at
a unique site and OLD is absent, say so — `OLD not found (NEW already present — already applied?)`.
A distinct exit code would be better still, since it makes idempotent retry scriptable.

## What is NOT wrong here

Recording these so the fix does not "improve" them away:

- **`--batch` atomicity is correct.** Verified directly — a failing pair leaves the file untouched.
- **Exit codes are already good.** 4 / 5 / 6 / 2 are distinct and non-zero. An earlier suspicion that a
  failed `--replace` returned 0 was **wrong** — it was `head` in the pipeline swallowing the status.
- **The `--batch` trailing-NUL requirement** (`stdin must end with NUL after final NEW`) has a clear,
  actionable message and is fine as-is.

## Related

The sequential-application limitation that makes overlapping-OLD pairs inexpressible is a design
question, not a defect, and is filed separately under
`proposals/2026-08-29-line-anchored-and-cyrius-aware-edits.md` § 1.
