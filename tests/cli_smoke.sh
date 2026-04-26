#!/bin/sh
# tests/cli_smoke.sh — interspersed-modifier smoke test for the
# agent-drive CLI surface (introduced in v1.1.1; --batch added in v1.1.2).
#
# v1.1.0 had a front-only modifier loop that bailed at the first
# non-flag argv slot, so flags appearing AFTER positionals were
# silently mis-parsed (treated as the FILE positional, or dropped
# entirely on --write). This script asserts the v1.1.1 walk-all-argv
# parser handles each shape correctly.
#
# Run: sh tests/cli_smoke.sh
# Exits 0 if all cases pass; non-zero with a per-case failure message
# on the first regression.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/build/cyim"

if [ ! -x "$BIN" ]; then
    echo "skip: $BIN not present (run 'cyrius build src/main.cyr build/cyim' first)"
    exit 0
fi

FIX=/tmp/cyim-cli-smoke.txt
WRITE_FIX=/tmp/cyim-cli-smoke-write.txt
PASS=0
FAIL=0

assert_rc() {
    desc="$1"
    expected="$2"
    actual="$3"
    if [ "$expected" = "$actual" ]; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        echo "FAIL: $desc — expected rc=$expected, got rc=$actual"
    fi
}

# Fresh fixture per run.
printf 'alpha\nbeta\nUNIQUE_TOKEN\ngamma\n' > "$FIX"

# Case 1 — modifier AFTER positionals on --replace (v1.1.0 → rc=3).
"$BIN" --replace 'UNIQUE_TOKEN' 'UNIQUE_TOKEN' --expect-1 "$FIX" >/dev/null 2>&1
assert_rc '--replace OLD NEW --expect-1 FILE' 0 $?

# Case 2 — --expect-N=<n> with equals after positionals (v1.1.0 → rc=3).
"$BIN" --replace 'UNIQUE_TOKEN' 'UNIQUE_TOKEN' --expect-N=1 "$FIX" >/dev/null 2>&1
assert_rc '--replace OLD NEW --expect-N=1 FILE' 0 $?

# Case 3 — --expect-N count mismatch must still fire on this path (exit 6).
"$BIN" --replace 'UNIQUE_TOKEN' 'UNIQUE_TOKEN' --expect-N=2 "$FIX" >/dev/null 2>&1
assert_rc '--replace OLD NEW --expect-N=2 FILE (count mismatch)' 6 $?

# Case 4 — --replace-all with --wc trailing (v1.1.0 silently dropped).
"$BIN" --replace-all 'beta' 'beta' --wc "$FIX" >/dev/null 2>&1
assert_rc '--replace-all OLD NEW --wc FILE' 0 $?

# Case 5 — --write FILE --wc=l (v1.1.0 dropped --wc=l silently).
printf 'one\ntwo\nthree\n' | "$BIN" --write "$WRITE_FIX" --wc=l >/dev/null 2>&1
assert_rc '--write FILE --wc=l' 0 $?

# Case 6 — flag interleaved between OLD and NEW (always supported, but
# regression-guard for the new walk-all parser).
"$BIN" --replace 'UNIQUE_TOKEN' --expect-1 'UNIQUE_TOKEN' "$FIX" >/dev/null 2>&1
assert_rc '--replace OLD --expect-1 NEW FILE' 0 $?

# Case 7 — extra positional must error (was silently consumed in v1.1.0).
"$BIN" --replace 'foo' 'bar' "$FIX" EXTRA_POS 2>/dev/null
assert_rc '--replace OLD NEW FILE EXTRA (extra positional)' 2 $?

# Case 8 — pre-fix regression check: original "modifiers all up front"
# shape must still work.
"$BIN" --replace --expect-1 'UNIQUE_TOKEN' 'UNIQUE_TOKEN' "$FIX" >/dev/null 2>&1
assert_rc '--replace --expect-1 OLD NEW FILE (front-loaded, regression)' 0 $?

# Case 9 — --write all-front shape regression check.
printf 'x\n' | "$BIN" --write --wc=l "$WRITE_FIX" >/dev/null 2>&1
assert_rc '--write --wc=l FILE (front-loaded, regression)' 0 $?

# Case 10 — bad --expect-N value still rejected.
"$BIN" --replace 'foo' 'bar' --expect-N=abc "$FIX" 2>/dev/null
assert_rc '--replace OLD NEW --expect-N=abc FILE (bad N)' 2 $?


# ── --batch (introduced in v1.1.2) ──────────────────────────────────
BATCH_FIX=/tmp/cyim-cli-smoke-batch.txt

# Case 11 — single OLD/NEW pair from stdin.
printf 'alpha\nbeta\nUNIQUE_TOKEN\ngamma\n' > "$BATCH_FIX"
printf 'UNIQUE_TOKEN\0NEW_TOKEN\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (single pair)' 0 $?

# Case 12 — multi-pair sequential, each unique.
printf 'one\ntwo\nthree\n' > "$BATCH_FIX"
printf 'one\0ONE\0two\0TWO\0three\0THREE\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (3 sequential pairs)' 0 $?

# Case 13 — non-unique OLD without --all → exit 5, file UNTOUCHED.
printf 'foo\nbar\nfoo\n' > "$BATCH_FIX"
printf 'foo\0FOO\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (non-unique OLD without --all)' 5 $?
EXPECTED='foo
bar
foo'
ACTUAL=$(cat "$BATCH_FIX")
if [ "$EXPECTED" = "$ACTUAL" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --batch atomicity (file changed despite exit 5)"
fi

# Case 14 — non-unique OLD with --all succeeds.
printf 'foo\0FOO\0' | "$BIN" --batch --all "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch --all FILE (non-unique OLD)' 0 $?

# Case 15 — pair K's OLD missing → exit 4, file UNTOUCHED.
printf 'a\nb\nc\n' > "$BATCH_FIX"
printf 'a\0A\0NOPE\0X\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (pair-2 OLD missing)' 4 $?
ACTUAL=$(cat "$BATCH_FIX")
EXPECTED='a
b
c'
if [ "$EXPECTED" = "$ACTUAL" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --batch atomicity (mid-batch failure modified file)"
fi

# Case 16 — empty stdin rejected.
: | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (empty stdin)' 2 $?

# Case 17 — odd token count rejected.
printf 'a\0b\0c\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (odd token count)' 2 $?

# Case 18 — missing trailing NUL rejected.
printf 'a\0b' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (missing trailing NUL)' 2 $?

# Case 19 — empty OLD rejected.
printf '\0NEW\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (empty OLD)' 2 $?

# Case 20 — --expect post-save assertion (success).
printf 'alpha\nbeta\n' > "$BATCH_FIX"
printf 'alpha\0AAA\0' | "$BIN" --batch --expect=AAA "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch --expect=PAT FILE (present)' 0 $?

# Case 21 — --expect post-save miss → exit 6.
printf 'alpha\nbeta\n' > "$BATCH_FIX"
printf 'alpha\0AAA\0' | "$BIN" --batch --expect=NOSUCH "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch --expect=PAT FILE (miss)' 6 $?

# Case 22 — --expect-not present after batch → exit 6.
printf 'alpha\nbeta\n' > "$BATCH_FIX"
printf 'alpha\0AAA\0' | "$BIN" --batch --expect-not=AAA "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch --expect-not=PAT FILE (present)' 6 $?

# Case 23 — interspersed modifiers + positional (parser shape).
printf 'x\ny\n' > "$BATCH_FIX"
printf 'x\0X\0' | "$BIN" --batch "$BATCH_FIX" --wc=l --all >/dev/null 2>&1
assert_rc '--batch FILE --wc=l --all (interleaved)' 0 $?

# Case 24 — extra positional rejected.
printf 'x\nz\n' > "$BATCH_FIX"
printf 'x\0X\0' | "$BIN" --batch "$BATCH_FIX" EXTRA 2>/dev/null
assert_rc '--batch FILE EXTRA (extra positional)' 2 $?

# Case 25 — newlines / em-dash inside OLD and NEW round-trip cleanly.
printf 'before\nold line — keep\nafter\n' > "$BATCH_FIX"
printf 'old line — keep\0new line — kept\0' | "$BIN" --batch "$BATCH_FIX" >/dev/null 2>&1
assert_rc '--batch FILE (multi-byte unicode in pair)' 0 $?
GREP_HIT=$("$BIN" --grep 'new line — kept' "$BATCH_FIX")
if [ -n "$GREP_HIT" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --batch unicode round-trip (substituted text not present)"
fi

rm -f "$BATCH_FIX"

rm -f "$FIX" "$WRITE_FIX" "$BATCH_FIX"

echo "$PASS passed, $FAIL failed (28 total)"
[ "$FAIL" = "0" ] || exit 1
