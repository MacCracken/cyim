#!/bin/sh
# tests/cli_smoke.sh — interspersed-modifier smoke test for the
# agent-drive CLI surface (introduced in v1.1.1).
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

rm -f "$FIX" "$WRITE_FIX"

echo "$PASS passed, $FAIL failed (10 total)"
[ "$FAIL" = "0" ] || exit 1
