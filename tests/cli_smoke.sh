#!/bin/sh
# tests/cli_smoke.sh — interspersed-modifier smoke test for the
# agent-drive CLI surface (v1.1.1 walk-all-argv parser; v1.1.2 --batch;
# v1.1.3 duplicate-flag refusal + --grep literal regression; v1.1.4
# --grepfiles + --context=N + --replace-files[-all]).
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

# ── duplicate-flag refusal (introduced in v1.1.3) ──────────────────
# Modifier flags occupy single scalar slots in the parser. v1.1.2 and
# earlier silently last-won when a flag appeared twice; v1.1.3 refuses
# with exit 2 and a stderr "duplicate flag: --NAME" message.
#
# Family grouping (a duplicate within any family trips the check):
#   --expect= and --expect-not=     (post-save assertion, --write/--batch)
#   --expect-N= and --expect-1      (count assertion, --replace[-all])
#   --wc / --wc=l / --wc=long       (wc-on-success modifier)
#   --all                           (--batch global mode)

# Case 26 — duplicate --expect= on --write.
printf 'x\n' | "$BIN" --write --expect=foo --expect=bar "$WRITE_FIX" 2>/dev/null
assert_rc '--write --expect=foo --expect=bar (duplicate --expect)' 2 $?

# Case 27 — --expect= and --expect-not= collide on the same scalar slot.
printf 'x\n' | "$BIN" --write --expect=foo --expect-not=bar "$WRITE_FIX" 2>/dev/null
assert_rc '--write --expect=foo --expect-not=bar (cross-family duplicate)' 2 $?

# Case 28 — duplicate --expect-1 on --replace.
printf 'alpha\nbeta\nUNIQUE_TOKEN\ngamma\n' > "$FIX"
"$BIN" --replace 'UNIQUE_TOKEN' 'NEW_TOKEN' --expect-1 --expect-1 "$FIX" 2>/dev/null
assert_rc '--replace --expect-1 --expect-1 (duplicate --expect-1)' 2 $?

# Case 29 — --expect-1 and --expect-N= collide on the same scalar slot.
"$BIN" --replace 'UNIQUE_TOKEN' 'NEW_TOKEN' --expect-1 --expect-N=2 "$FIX" 2>/dev/null
assert_rc '--replace --expect-1 --expect-N=2 (cross-family duplicate)' 2 $?

# Case 30 — duplicate --wc on --write.
printf 'x\n' | "$BIN" --write --wc --wc "$WRITE_FIX" 2>/dev/null
assert_rc '--write --wc --wc (duplicate --wc)' 2 $?

# Case 31 — duplicate --all on --batch.
printf 'foo\nbar\nfoo\n' > "$BATCH_FIX"
printf 'foo\0FOO\0' | "$BIN" --batch --all --all "$BATCH_FIX" 2>/dev/null
assert_rc '--batch --all --all (duplicate --all)' 2 $?

# ── --grep literal-substring assertion (clarified in v1.1.3) ────────
# --grep PATTERN treats PATTERN as a literal byte sequence; regex
# metacharacters (^, $, ., *, etc.) are not special. v1.1.3 added
# "literal substring, not regex" to --help; this case asserts the
# actual byte-for-byte matching behavior so any future regex creep
# would regress here loudly.

# Case 32 — '^foo' is a literal byte sequence: matches the line that
# *contains* literal '^foo', NOT a line containing only 'foo'. A
# regex flavor that treats '^' as a line anchor would invert the hits.
GREP_FIX=/tmp/cyim-cli-smoke-grep.txt
printf 'plain foo here\n^foo at start\nbaseline\n' > "$GREP_FIX"
GREP_OUT=$("$BIN" --grep '^foo' "$GREP_FIX" 2>/dev/null)
HIT_LITERAL=0
HIT_PLAIN=0
case "$GREP_OUT" in *":2:^foo at start"*) HIT_LITERAL=1 ;; esac
case "$GREP_OUT" in *":1:plain foo here"*) HIT_PLAIN=1 ;; esac
if [ "$HIT_LITERAL" = "1" ] && [ "$HIT_PLAIN" = "0" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --grep '^foo' literal: expected hit on line 2, no hit on line 1; got:"
    echo "$GREP_OUT"
fi
rm -f "$GREP_FIX"

# ── v1.1.4 — --grepfiles, --context=N, --replace-files[-all] ────────
# v1.1.4 splits the bundled grep-surface expansion: --grepfiles (multi-
# file grep) + --context=N (grep -C-shaped context windows) ship ahead
# of the upstream-gated --regex= modifier (still gated on the cyrius
# stdlib NFA module before 5.7.x EOL). --replace-files[-all] ships
# alongside as a dogfood-driven addition that closes the friction of
# constructing multi-line OLD/NEW through argv or NUL-separated stdin.
GF1=/tmp/cyim-cli-smoke-gf1.txt
GF2=/tmp/cyim-cli-smoke-gf2.txt
GREPFIX=/tmp/cyim-cli-smoke-gctx.txt

# Case 33 — --grepfiles match across two files (exit 0, FILE:N:LINE
# disambiguates per file).
printf 'a\nfoo here\nb\n' > "$GF1"
printf 'c\nd\nfoo there\n' > "$GF2"
GF_OUT=$("$BIN" --grepfiles foo "$GF1" "$GF2" 2>&1)
GF_RC=$?
assert_rc '--grepfiles PAT FILE1 FILE2 (matches in both)' 0 $GF_RC
HIT_F1=0; HIT_F2=0
case "$GF_OUT" in *"$GF1:2:foo here"*) HIT_F1=1 ;; esac
case "$GF_OUT" in *"$GF2:3:foo there"*) HIT_F2=1 ;; esac
if [ "$HIT_F1" = "1" ] && [ "$HIT_F2" = "1" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --grepfiles output missing per-file FILE:N:LINE; got:"
    echo "$GF_OUT"
fi

# Case 34 — --grepfiles no match anywhere (exit 1, grep convention).
printf 'a\nb\nc\n' > "$GF1"
printf 'd\ne\nf\n' > "$GF2"
"$BIN" --grepfiles XYZNONESUCH "$GF1" "$GF2" >/dev/null 2>&1
assert_rc '--grepfiles PAT FILE1 FILE2 (no matches)' 1 $?

# Case 35 — --grepfiles missing FILE (exit 3, fail-fast on first miss).
"$BIN" --grepfiles foo "$GF1" /tmp/cyim-cli-smoke-NONEXISTENT 2>/dev/null
assert_rc '--grepfiles FILE missing (exit 3)' 3 $?

# Case 36 — --grep --context=1 emits before+after lines with `-`
# separators (FILE-N-LINE for context, FILE:N:LINE for match).
printf 'one\ntwo\nMATCH\nthree\nfour\n' > "$GREPFIX"
CTX_OUT=$("$BIN" --grep --context=1 MATCH "$GREPFIX" 2>&1)
assert_rc '--grep --context=1 MATCH FILE' 0 $?
HIT_CTX_PRE=0; HIT_CTX_MATCH=0; HIT_CTX_POST=0
case "$CTX_OUT" in *"$GREPFIX-2-two"*) HIT_CTX_PRE=1 ;; esac
case "$CTX_OUT" in *"$GREPFIX:3:MATCH"*) HIT_CTX_MATCH=1 ;; esac
case "$CTX_OUT" in *"$GREPFIX-4-three"*) HIT_CTX_POST=1 ;; esac
if [ "$HIT_CTX_PRE" = "1" ] && [ "$HIT_CTX_MATCH" = "1" ] && [ "$HIT_CTX_POST" = "1" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --grep --context=1 missing pre/match/post; got:"
    echo "$CTX_OUT"
fi

# Case 37 — overlapping windows merge: matches at lines 2,4 with N=2
# emit one continuous run, no `--` separator between them.
printf 'a\nMATCH\nb\nMATCH\nc\nd\n' > "$GREPFIX"
OVERLAP_OUT=$("$BIN" --grep --context=2 MATCH "$GREPFIX" 2>&1)
HAS_SEP=0
case "$OVERLAP_OUT" in *"--"*) HAS_SEP=1 ;; esac
if [ "$HAS_SEP" = "0" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --context=2 overlapping windows should merge (no -- separator); got:"
    echo "$OVERLAP_OUT"
fi

# Case 38 — non-adjacent groups get a `--` separator between them.
printf 'a\nMATCH\nb\nc\nd\nMATCH\ne\n' > "$GREPFIX"
SEP_OUT=$("$BIN" --grep --context=1 MATCH "$GREPFIX" 2>&1)
HAS_SEP=0
case "$SEP_OUT" in *"
--
"*) HAS_SEP=1 ;; esac
if [ "$HAS_SEP" = "1" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --context=1 non-adjacent groups should emit -- separator; got:"
    echo "$SEP_OUT"
fi

# Case 39 — --context=0 must produce identical output to omitting the
# flag (back-compat regression guard).
printf 'a\nMATCH\nb\nMATCH\nc\n' > "$GREPFIX"
PLAIN_OUT=$("$BIN" --grep MATCH "$GREPFIX" 2>&1)
ZERO_OUT=$("$BIN" --grep --context=0 MATCH "$GREPFIX" 2>&1)
if [ "$PLAIN_OUT" = "$ZERO_OUT" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --context=0 should match no-flag output bytes-for-bytes"
    echo "  no-flag: $PLAIN_OUT"
    echo "  ctx=0:   $ZERO_OUT"
fi

# Case 40 — --context=<non-int> usage error (exit 2).
"$BIN" --grep --context=abc MATCH "$GREPFIX" 2>/dev/null
assert_rc '--grep --context=abc (bad N)' 2 $?

# Case 41 — duplicate --context refused (mirrors v1.1.3 dup-flag pattern).
"$BIN" --grep --context=1 --context=2 MATCH "$GREPFIX" 2>/dev/null
assert_rc '--grep --context=1 --context=2 (duplicate)' 2 $?

# Case 42 — --grepfiles --context=N puts a `--` separator between files
# (matches `grep -n -C N`'s cross-file behavior).
printf 'a\nMATCH\nb\n' > "$GF1"
printf 'c\nMATCH\nd\n' > "$GF2"
GF_CTX_OUT=$("$BIN" --grepfiles --context=1 MATCH "$GF1" "$GF2" 2>&1)
HAS_SEP=0
case "$GF_CTX_OUT" in *"
--
"*) HAS_SEP=1 ;; esac
if [ "$HAS_SEP" = "1" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --grepfiles --context=1 should emit -- between files; got:"
    echo "$GF_CTX_OUT"
fi

rm -f "$GF1" "$GF2" "$GREPFIX"

# ── v1.1.4 — --replace-files / --replace-files-all ──────────────────
# Dogfood-driven: closes the friction of constructing multi-line OLD/NEW
# through argv (shell-escape pain) or NUL-separated stdin (--batch
# stream construction). Same modifier surface as --replace[-all]; reads
# OLD and NEW from named files.
RF_TARGET=/tmp/cyim-cli-smoke-rftgt.txt
RF_OLD=/tmp/cyim-cli-smoke-rfold.txt
RF_NEW=/tmp/cyim-cli-smoke-rfnew.txt

# Case 43 — multi-line OLD/NEW round-trip through file paths.
printf 'header\nblock A\nblock B\nblock C\nfooter\n' > "$RF_TARGET"
printf 'block A\nblock B\nblock C' > "$RF_OLD"
printf 'NEW1\nNEW2\nNEW3\nNEW4' > "$RF_NEW"
"$BIN" --replace-files "$RF_OLD" "$RF_NEW" "$RF_TARGET" >/dev/null 2>&1
assert_rc '--replace-files OLD_FILE NEW_FILE FILE (multi-line)' 0 $?
EXPECTED='header
NEW1
NEW2
NEW3
NEW4
footer'
ACTUAL=$(cat "$RF_TARGET")
if [ "$EXPECTED" = "$ACTUAL" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --replace-files content mismatch"
    echo "  expected:"; printf '%s\n' "$EXPECTED"
    echo "  actual:"; printf '%s\n' "$ACTUAL"
fi

# Case 44 — --replace-files OLD_FILE empty (exit 2).
: > "$RF_OLD"
"$BIN" --replace-files "$RF_OLD" "$RF_NEW" "$RF_TARGET" 2>/dev/null
assert_rc '--replace-files OLD_FILE empty' 2 $?

# Case 45 — --replace-files OLD_FILE missing (exit 3).
"$BIN" --replace-files /tmp/cyim-cli-smoke-NONEXISTENT-OLD "$RF_NEW" "$RF_TARGET" 2>/dev/null
assert_rc '--replace-files OLD_FILE missing' 3 $?

# Case 46 — --replace-files OLD not unique without -all (exit 5).
printf 'foo\nbar\nfoo\n' > "$RF_TARGET"
printf 'foo' > "$RF_OLD"
printf 'BAR' > "$RF_NEW"
"$BIN" --replace-files "$RF_OLD" "$RF_NEW" "$RF_TARGET" 2>/dev/null
assert_rc '--replace-files OLD non-unique (without -all)' 5 $?

# Case 47 — --replace-files-all succeeds where --replace-files exits 5.
"$BIN" --replace-files-all "$RF_OLD" "$RF_NEW" "$RF_TARGET" >/dev/null 2>&1
assert_rc '--replace-files-all OLD non-unique' 0 $?
ACTUAL=$(cat "$RF_TARGET")
EXPECTED='BAR
bar
BAR'
if [ "$EXPECTED" = "$ACTUAL" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --replace-files-all all-occurrence substitution"
fi

# Case 48 — --replace-files --expect-1 mismatch returns 6 before
# touching FILE (delegates to run_replace's pre-substitution check).
printf 'a\nb\na\n' > "$RF_TARGET"
printf 'a' > "$RF_OLD"
printf 'A' > "$RF_NEW"
"$BIN" --replace-files --expect-1 "$RF_OLD" "$RF_NEW" "$RF_TARGET" 2>/dev/null
assert_rc '--replace-files --expect-1 (count mismatch)' 6 $?
ACTUAL=$(cat "$RF_TARGET")
EXPECTED='a
b
a'
if [ "$EXPECTED" = "$ACTUAL" ]; then
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + 1))
    echo "FAIL: --replace-files atomicity (file changed despite exit 6)"
fi

# Case 49 — --replace-files --wc=l prints `<lines> <file>` to stdout.
printf 'one\ntwo\nthree\n' > "$RF_TARGET"
printf 'two' > "$RF_OLD"
printf 'TWO' > "$RF_NEW"
WC_OUT=$("$BIN" --replace-files --wc=l "$RF_OLD" "$RF_NEW" "$RF_TARGET" 2>&1)
assert_rc '--replace-files --wc=l' 0 $?
case "$WC_OUT" in
    "3 $RF_TARGET")
        PASS=$((PASS + 1))
        ;;
    *)
        FAIL=$((FAIL + 1))
        echo "FAIL: --replace-files --wc=l output: expected '3 $RF_TARGET', got '$WC_OUT'"
        ;;
esac

rm -f "$RF_TARGET" "$RF_OLD" "$RF_NEW"

rm -f "$BATCH_FIX"

rm -f "$FIX" "$WRITE_FIX" "$BATCH_FIX"

echo "$PASS passed, $FAIL failed (58 total)"
[ "$FAIL" = "0" ] || exit 1
