#!/usr/bin/env python3
"""End-to-end smoke test for cyim's main loop.

Spawns cyim under a real PTY (so tty_raw succeeds), drives a recorded key
sequence, then asserts the on-disk file matches the expected post-edit state.

This is the bite-8 deliverable: the .tcyr suite already proves every editor
component in isolation; this script proves the TTY plumbing and main loop
connect them correctly.

Run: python3 tests/integration_smoke.py
"""
import os
import pty
import select
import sys
import time

CYIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "cyim")
FIXTURE = "/tmp/cyim-smoke-fixture.txt"


def drive(keys: bytes, fixture_initial: bytes, timeout: float = 3.0,
          fixture_path: str = FIXTURE) -> bytes:
    """Spawn cyim against `fixture_path` under a PTY, send `keys`, wait for exit.
    Returns the post-run file content."""
    with open(fixture_path, "wb") as f:
        f.write(fixture_initial)

    pid, fd = pty.fork()
    if pid == 0:
        # Child: exec cyim. PTY is wired to stdin/stdout/stderr.
        os.execv(CYIM, [CYIM, fixture_path])

    # Parent: pump keys, drain output until child exits.
    deadline = time.time() + timeout
    sent = 0
    sink = bytearray()
    while True:
        if time.time() > deadline:
            os.kill(pid, 9)
            raise TimeoutError(f"cyim did not exit within {timeout}s")
        # Reap?
        try:
            wpid, status = os.waitpid(pid, os.WNOHANG)
            if wpid == pid:
                # Drain anything left.
                try:
                    while True:
                        chunk = os.read(fd, 4096)
                        if not chunk:
                            break
                        sink.extend(chunk)
                except OSError:
                    pass
                rc = os.waitstatus_to_exitcode(status)
                if rc != 0:
                    raise RuntimeError(f"cyim exited {rc}; output: {bytes(sink)!r}")
                break
        except ChildProcessError:
            break

        ready_r, ready_w, _ = select.select([fd], [fd] if sent < len(keys) else [], [], 0.05)
        if fd in ready_r:
            try:
                chunk = os.read(fd, 4096)
                if chunk:
                    sink.extend(chunk)
            except OSError:
                pass
        if fd in ready_w and sent < len(keys):
            n = os.write(fd, keys[sent:sent + 1])  # one byte at a time, like a real TTY
            sent += n
            time.sleep(0.01)  # let cyim consume the byte before sending the next

    drive.last_pty_output = bytes(sink)
    with open(fixture_path, "rb") as f:
        return f.read()


def assert_eq(actual, expected, name):
    if actual == expected:
        print(f"  PASS: {name}")
    else:
        print(f"  FAIL: {name}\n    expected: {expected!r}\n    actual:   {actual!r}")
        return False
    return True


def main():
    if not os.path.exists(CYIM):
        print(f"error: {CYIM} not found. Run `cyrius build src/main.cyr build/cyim` first.")
        return 1

    ok = True

    print("=== :q on clean buffer exits 0 without modifying file ===")
    out = drive(b":q\r", b"hello\n")
    ok &= assert_eq(out, b"hello\n", "fixture unchanged")

    print("=== iEDIT<Esc>:wq writes 'EDIThello\\n' ===")
    out = drive(b"iEDIT\x1b:wq\r", b"hello\n")
    ok &= assert_eq(out, b"EDIThello\n", "buffer prepended with 'EDIT'")

    print("=== A<append><Esc>:wq writes 'hello!!\\n' ===")
    # `A` pre-positions cursor at the '\n'. Insert '!!' before it.
    out = drive(b"A!!\x1b:wq\r", b"hello\n")
    ok &= assert_eq(out, b"hello!!\n", "appended '!!' before newline")

    print("=== xx (delete first two chars) :wq writes 'llo\\n' ===")
    out = drive(b"xx:wq\r", b"hello\n")
    ok &= assert_eq(out, b"llo\n", "deleted first two chars via x x")

    print("=== :q on dirty buffer is refused; :q! quits without saving ===")
    out = drive(b"iJUNK\x1b:q\r:q!\r", b"original\n")
    ok &= assert_eq(out, b"original\n", "dirty :q refused, :q! discards")

    print("=== Cyrius file: ANSI fg escapes appear in PTY output ===")
    cyr_fixture = "/tmp/cyim-smoke-fixture.cyr"
    drive(b":q!\r", b"var x = 42\n", fixture_path=cyr_fixture)
    pty_out = drive.last_pty_output
    # The keyword "var" should produce an ANSI fg escape ESC[38;5;141m
    # (purple, per render.cyr's theme_token_color). Look for that exact
    # sequence anywhere in the captured PTY output.
    needle = b"\x1b[38;5;141m"
    if needle in pty_out:
        print("  PASS: ESC[38;5;141m (keyword fg) present in render output")
    else:
        print(f"  FAIL: keyword fg escape not found in {len(pty_out)} bytes of PTY output")
        ok = False
    # And the trailing reset.
    if b"\x1b[0m" in pty_out:
        print("  PASS: ESC[0m (reset) present in render output")
    else:
        print("  FAIL: reset escape not found in PTY output")
        ok = False

    print("=== M4 search + undo: /foo<Enter> jumps cursor; u rolls back an edit ===")
    # Layout (positions of "foo"):  alpha foo beta foo gamma foo
    #                                     6      15     25
    # Drive: /foo<Enter> i_X<Esc> u :wq
    # After the edit the cursor is on the 'foo' that we modified, then `u`
    # rolls it back, so the saved file should match the fixture.
    out = drive(
        b"/foo\riX\x1bu:wq\r",
        b"alpha foo beta foo gamma\n",
    )
    ok &= assert_eq(out, b"alpha foo beta foo gamma\n", "search + edit + undo + save = identity")

    print("=== M4 . repeat: insert once, repeat at new cursor ===")
    # Drive: iAB<Esc> $ a CD<Esc> 0 . :wq
    # Result expected: AB at start; CD appended at end of original line; then
    # `.` at start re-runs the LAST insert ("a CD<Esc>") at cursor 0:
    #   `a` advances cursor by 1 (past 'A'), inserts 'C' 'D' at pos 1, Esc.
    # Final buffer: "ACDB hello CD\n" wait — let's compute precisely.
    #   Initial:  "hello\n"   cursor 0
    #   iAB<Esc>: "ABhello\n" cursor 1 (on 'B')
    #   $:         cursor 6 (line_end of "ABhello")
    #   aCD<Esc>:  cursor advances to 7, inserts CD, Esc steps back: "ABhelloCD\n" cursor 8
    #   0:         cursor 0 (line_start)
    #   .:         replay "aCD<Esc>" at cursor 0:
    #              `a` -> cursor 1 (past 'A'), insert 'C' 'D' at 1: "ACDBhelloCD\n" cursor 3
    #   :wq saves "ACDBhelloCD\n"
    out = drive(
        b"iAB\x1b$aCD\x1b0.:wq\r",
        b"hello\n",
    )
    ok &= assert_eq(out, b"ACDBhelloCD\n", ". repeat replays last insert at new cursor")

    print("=== M4 visual + d: vlld removes 3 chars; p pastes them ===")
    # Drive: v l l d p  :wq
    # Initial: "abcdef\n" cursor 0 (on 'a')
    # vlld: visual select a,b,c (3 chars), d deletes, register holds "abc"
    #       buffer: "def\n" cursor 0
    # p: paste after cursor — cursor advances to 1 (between 'd' and 'e'),
    #    inserts "abc" → "dabcef\n" cursor 3
    # :wq saves "dabcef\n"
    out = drive(
        b"vlld" + b"p:wq\r",
        b"abcdef\n",
    )
    ok &= assert_eq(out, b"dabcef\n", "vlld then p produces 'dabcef'")

    print("=== --write: stdin replaces file content ===")
    import subprocess
    write_fixture = "/tmp/cyim-write-fixture.txt"
    with open(write_fixture, "wb") as f:
        f.write(b"OLD CONTENT\n")
    proc = subprocess.run(
        [CYIM, "--write", write_fixture],
        input=b"replaced\n",
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write exited {proc.returncode}")
        ok = False
    else:
        with open(write_fixture, "rb") as f:
            ok &= assert_eq(f.read(), b"replaced\n", "--write replaces file with stdin")

    print("=== --write --wc: prints `wc <file>` after success ===")
    wc_fixture = "/tmp/cyim-wc-fixture.txt"
    payload = b"hello world\nfoo bar baz\n"
    proc = subprocess.run(
        [CYIM, "--write", "--wc", wc_fixture],
        input=payload,
        capture_output=True,
        timeout=5,
    )
    expected = f"2 5 {len(payload)} {wc_fixture}\n".encode()
    if proc.returncode != 0:
        print(f"  FAIL: --write --wc exited {proc.returncode}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, expected, "--wc prints '<lines> <words> <bytes> <file>'")
        with open(wc_fixture, "rb") as f:
            ok &= assert_eq(f.read(), payload, "--wc still wrote payload to file")

    print("=== --write --wc=l: prints `wc -l <file>` after success ===")
    proc = subprocess.run(
        [CYIM, "--write", "--wc=l", wc_fixture],
        input=payload,
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write --wc=l exited {proc.returncode}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, f"2 {wc_fixture}\n".encode(), "--wc=l prints '<lines> <file>'")

    print("=== --write --wc=long: alias for --wc=l ===")
    proc = subprocess.run(
        [CYIM, "--write", "--wc=long", wc_fixture],
        input=payload,
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write --wc=long exited {proc.returncode}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, f"2 {wc_fixture}\n".encode(), "--wc=long matches --wc=l")

    print("=== --replace: unique OLD substitutes; non-unique exits 5 ===")
    repl_fixture = "/tmp/cyim-replace-fixture.txt"
    # Unique-mode success
    with open(repl_fixture, "wb") as f:
        f.write(b"alpha foo bravo\n")
    proc = subprocess.run([CYIM, "--replace", b"foo", b"BAR", repl_fixture], timeout=5)
    if proc.returncode != 0:
        print(f"  FAIL: --replace exited {proc.returncode}")
        ok = False
    else:
        with open(repl_fixture, "rb") as f:
            ok &= assert_eq(f.read(), b"alpha BAR bravo\n", "--replace substituted unique OLD")
    # Non-unique exits 5; file untouched
    with open(repl_fixture, "wb") as f:
        f.write(b"foo and foo\n")
    proc = subprocess.run([CYIM, "--replace", b"foo", b"BAR", repl_fixture], timeout=5,
                          capture_output=True)
    if proc.returncode != 5:
        print(f"  FAIL: --replace on non-unique OLD exited {proc.returncode}, expected 5")
        ok = False
    else:
        print("  PASS: --replace on non-unique OLD exits 5")
    with open(repl_fixture, "rb") as f:
        ok &= assert_eq(f.read(), b"foo and foo\n", "--replace left file untouched on refusal")

    print("=== --replace-all: substitutes every occurrence ===")
    with open(repl_fixture, "wb") as f:
        f.write(b"foo and foo and foo\n")
    proc = subprocess.run([CYIM, "--replace-all", b"foo", b"BAR", repl_fixture], timeout=5)
    if proc.returncode != 0:
        print(f"  FAIL: --replace-all exited {proc.returncode}")
        ok = False
    else:
        with open(repl_fixture, "rb") as f:
            ok &= assert_eq(f.read(), b"BAR and BAR and BAR\n", "--replace-all hits every match")

    print("=== BUG-001 — --replace handles NEW arg larger than 4 KB ===")
    # Pre-1.0.2, cyrius's lib/args.cyr read /proc/self/cmdline into a
    # 4096 B stack buffer; total cmdline >4 KB silently truncated argv,
    # so --replace fell through to "usage" error (exit 2). Workaround
    # in src/cli.cyr re-reads cmdline into a 2 MB heap buffer.
    bug001_fixture = "/tmp/cyim-bug001-fixture.txt"
    with open(bug001_fixture, "wb") as f:
        f.write(b"line1\nMARKER\nline3\n")
    big_new_8k = b"X" * 8192
    proc = subprocess.run(
        [CYIM, "--replace", b"MARKER", big_new_8k, bug001_fixture],
        timeout=5,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --replace 8 KB NEW exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        with open(bug001_fixture, "rb") as f:
            content = f.read()
        ok &= assert_eq(content, b"line1\n" + big_new_8k + b"\nline3\n",
                        "--replace handled 8 KB NEW arg correctly")

    with open(bug001_fixture, "wb") as f:
        f.write(b"line1\nMARKER\nline3\n")
    big_new_64k = b"Y" * 65536
    proc = subprocess.run(
        [CYIM, "--replace", b"MARKER", big_new_64k, bug001_fixture],
        timeout=5,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --replace 64 KB NEW exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        with open(bug001_fixture, "rb") as f:
            content = f.read()
        ok &= assert_eq(content, b"line1\n" + big_new_64k + b"\nline3\n",
                        "--replace handled 64 KB NEW arg correctly")

    print("=== --headless: read keystrokes from stdin, no PTY required ===")
    # The headless drive doesn't need pty.fork — it reads stdin directly
    # and never touches termios. Agent-friendly: just pipe bytes.
    headless_fixture = "/tmp/cyim-headless-fixture.txt"
    with open(headless_fixture, "wb") as f:
        f.write(b"hello\n")
    proc = subprocess.run(
        [CYIM, "--headless", headless_fixture],
        input=b"iEDIT\x1b:wq\r",
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --headless exited {proc.returncode}")
        ok = False
    else:
        with open(headless_fixture, "rb") as f:
            content = f.read()
        ok &= assert_eq(content, b"EDIThello\n", "--headless iEDIT<Esc>:wq writes 'EDIThello'")

    print("=== --grep: emit FILE:N:LINE for every line containing PATTERN ===")
    grep_fixture = "/tmp/cyim-grep-fixture.txt"
    with open(grep_fixture, "wb") as f:
        f.write(b"alpha foo\nbeta bar\ngamma foo\ndelta\n")
    proc = subprocess.run(
        [CYIM, "--grep", "foo", grep_fixture],
        capture_output=True,
        timeout=5,
    )
    expected = (
        f"{grep_fixture}:1:alpha foo\n"
        f"{grep_fixture}:3:gamma foo\n"
    ).encode()
    if proc.returncode != 0:
        print(f"  FAIL: --grep hit exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, expected, "--grep emits FILE:N:LINE for each match")

    print("=== --grep: no match exits 1 with empty stdout ===")
    proc = subprocess.run(
        [CYIM, "--grep", "zzzzz", grep_fixture],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 1:
        print(f"  FAIL: --grep no-match exited {proc.returncode}, expected 1")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, b"", "--grep no-match produces empty stdout")

    print("=== --grep: missing args exits 2 ===")
    proc = subprocess.run([CYIM, "--grep"], capture_output=True, timeout=5)
    if proc.returncode != 2:
        print(f"  FAIL: --grep no-args exited {proc.returncode}, expected 2")
        ok = False
    else:
        print("  PASS: --grep with no args exits 2")

    print("=== --grep: file not found exits 3 ===")
    proc = subprocess.run(
        [CYIM, "--grep", "x", "/tmp/cyim-grep-does-not-exist.txt"],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 3:
        print(f"  FAIL: --grep missing file exited {proc.returncode}, expected 3")
        ok = False
    else:
        print("  PASS: --grep missing file exits 3")

    print("=== --grep: empty pattern exits 2 ===")
    proc = subprocess.run(
        [CYIM, "--grep", "", grep_fixture],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 2:
        print(f"  FAIL: --grep empty pattern exited {proc.returncode}, expected 2")
        ok = False
    else:
        print("  PASS: --grep empty pattern exits 2")

    print("=== --grep: file without trailing newline still emits last line ===")
    no_nl_fixture = "/tmp/cyim-grep-nonl.txt"
    with open(no_nl_fixture, "wb") as f:
        f.write(b"alpha\nbeta MARK")  # no trailing \n
    proc = subprocess.run(
        [CYIM, "--grep", "MARK", no_nl_fixture],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --grep no-trailing-nl exited {proc.returncode}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, f"{no_nl_fixture}:2:beta MARK\n".encode(),
                        "--grep matches final line without trailing newline")

    print("=== --write --expect: post-save assertion (must contain) ===")
    expect_fixture = "/tmp/cyim-expect-fixture.txt"
    # Pass: pattern present in stdin → exit 0, file saved
    proc = subprocess.run(
        [CYIM, "--write", "--expect=KEEP", expect_fixture],
        input=b"line with KEEP marker\n",
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write --expect (pass) exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        with open(expect_fixture, "rb") as f:
            ok &= assert_eq(f.read(), b"line with KEEP marker\n",
                            "--write --expect (matched) saves file")
    # Fail: pattern absent → exit 6 (file is still saved per spec — assertion is on result)
    proc = subprocess.run(
        [CYIM, "--write", "--expect=MISSING", expect_fixture],
        input=b"this stdin lacks the marker\n",
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 6:
        print(f"  FAIL: --write --expect (miss) exited {proc.returncode}, expected 6")
        ok = False
    else:
        print("  PASS: --write --expect mismatch exits 6")

    print("=== --write --expect-not: post-save assertion (must not contain) ===")
    proc = subprocess.run(
        [CYIM, "--write", "--expect-not=DEAD_SYMBOL", expect_fixture],
        input=b"clean rewrite\n",
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write --expect-not (pass) exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        with open(expect_fixture, "rb") as f:
            ok &= assert_eq(f.read(), b"clean rewrite\n",
                            "--write --expect-not (absent) saves file")
    proc = subprocess.run(
        [CYIM, "--write", "--expect-not=DEAD_SYMBOL", expect_fixture],
        input=b"oops DEAD_SYMBOL slipped in\n",
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 6:
        print(f"  FAIL: --write --expect-not (hit) exited {proc.returncode}, expected 6")
        ok = False
    else:
        print("  PASS: --write --expect-not hit exits 6")

    print("=== --write --wc --expect composes (modifier order independent) ===")
    payload = b"three\nshort\nlines\n"
    proc = subprocess.run(
        [CYIM, "--write", "--wc", "--expect=lines", expect_fixture],
        input=payload,
        capture_output=True,
        timeout=5,
    )
    expected = f"3 3 {len(payload)} {expect_fixture}\n".encode()
    if proc.returncode != 0:
        print(f"  FAIL: --write --wc --expect (composed) exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, expected, "--wc + --expect compose, both honored")
    # Reverse modifier order — same result
    proc = subprocess.run(
        [CYIM, "--write", "--expect=lines", "--wc", expect_fixture],
        input=payload,
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --write --expect --wc (reverse order) exited {proc.returncode}")
        ok = False
    else:
        ok &= assert_eq(proc.stdout, expected,
                        "--expect + --wc (reversed order) gives same wc output")

    print("=== --replace --expect-1: assert OLD count == 1 ===")
    repl_expect = "/tmp/cyim-replace-expect.txt"
    with open(repl_expect, "wb") as f:
        f.write(b"alpha OLD bravo\n")
    proc = subprocess.run(
        [CYIM, "--replace", "--expect-1", "OLD", "NEW", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --replace --expect-1 (count=1) exited {proc.returncode}; stderr: {proc.stderr!r}")
        ok = False
    else:
        with open(repl_expect, "rb") as f:
            ok &= assert_eq(f.read(), b"alpha NEW bravo\n",
                            "--replace --expect-1 substitutes when count matches")
    # --expect-1 with count=0 → exit 6
    with open(repl_expect, "wb") as f:
        f.write(b"no marker here\n")
    proc = subprocess.run(
        [CYIM, "--replace", "--expect-1", "OLD", "NEW", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 6:
        print(f"  FAIL: --replace --expect-1 (count=0) exited {proc.returncode}, expected 6")
        ok = False
    else:
        with open(repl_expect, "rb") as f:
            ok &= assert_eq(f.read(), b"no marker here\n",
                            "--replace --expect-1 (count=0) leaves file untouched")

    print("=== --replace-all --expect-N: assert exact pre-sub count ===")
    with open(repl_expect, "wb") as f:
        f.write(b"OLD OLD OLD\n")
    proc = subprocess.run(
        [CYIM, "--replace-all", "--expect-N=3", "OLD", "NEW", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --replace-all --expect-N=3 (count=3) exited {proc.returncode}")
        ok = False
    else:
        with open(repl_expect, "rb") as f:
            ok &= assert_eq(f.read(), b"NEW NEW NEW\n",
                            "--replace-all --expect-N=3 substitutes all when count matches")
    # Mismatch
    with open(repl_expect, "wb") as f:
        f.write(b"OLD OLD\n")
    proc = subprocess.run(
        [CYIM, "--replace-all", "--expect-N=3", "OLD", "NEW", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 6:
        print(f"  FAIL: --replace-all --expect-N=3 (count=2) exited {proc.returncode}, expected 6")
        ok = False
    else:
        with open(repl_expect, "rb") as f:
            ok &= assert_eq(f.read(), b"OLD OLD\n",
                            "--replace-all --expect-N mismatch leaves file untouched")

    print("=== --replace --expect-N=0: defensive no-op assertion ===")
    with open(repl_expect, "wb") as f:
        f.write(b"clean file, no marker\n")
    proc = subprocess.run(
        [CYIM, "--replace", "--expect-N=0", "MARKER", "X", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 0:
        print(f"  FAIL: --replace --expect-N=0 (count=0) exited {proc.returncode}")
        ok = False
    else:
        with open(repl_expect, "rb") as f:
            ok &= assert_eq(f.read(), b"clean file, no marker\n",
                            "--replace --expect-N=0 (count=0) is a clean no-op")
    # --expect-N=0 fails when MARKER is present
    with open(repl_expect, "wb") as f:
        f.write(b"oh no, MARKER appeared\n")
    proc = subprocess.run(
        [CYIM, "--replace", "--expect-N=0", "MARKER", "X", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 6:
        print(f"  FAIL: --replace --expect-N=0 (count=1) exited {proc.returncode}, expected 6")
        ok = False
    else:
        print("  PASS: --replace --expect-N=0 (count>0) exits 6")

    print("=== --replace --expect-N: malformed value exits 2 ===")
    proc = subprocess.run(
        [CYIM, "--replace", "--expect-N=abc", "OLD", "NEW", repl_expect],
        capture_output=True,
        timeout=5,
    )
    if proc.returncode != 2:
        print(f"  FAIL: --replace --expect-N=abc exited {proc.returncode}, expected 2")
        ok = False
    else:
        print("  PASS: --replace --expect-N=<non-int> exits 2")

    print("=== M3 multi-window: 3 files in 2 splits, navigate, :q cascades ===")
    file_a = "/tmp/cyim-smoke-a.cyr"
    file_b = "/tmp/cyim-smoke-b.cyr"
    file_c = "/tmp/cyim-smoke-c.cyr"
    with open(file_a, "wb") as f:
        f.write(b"# file A\nvar a = 1\n")
    with open(file_b, "wb") as f:
        f.write(b"# file B\nvar b = 2\n")
    with open(file_c, "wb") as f:
        f.write(b"# file C\nvar c = 3\n")
    # Open A, vsplit, :e B (loads B in active leaf), Ctrl-w l (right),
    # :sp (horizontal split), :e C in new leaf, then :q :q :q :q to
    # close all four leaves and exit.
    seq = b""
    seq += b":vsp\r"
    seq += b":e " + file_b.encode() + b"\r"
    seq += b"\x17l"                     # Ctrl-w l (move right)
    seq += b":sp\r"
    seq += b":e " + file_c.encode() + b"\r"
    seq += b":q\r"                       # close current leaf
    seq += b":q\r"
    seq += b":q\r"
    seq += b":q\r"
    drive(seq, b"# file A\nvar a = 1\n", fixture_path=file_a)
    pty_out = drive.last_pty_output
    # Each filename should have appeared in the per-leaf status line at
    # some point during the multi-window phase.
    if file_a.encode() in pty_out:
        print(f"  PASS: '{file_a}' appears in render stream")
    else:
        print(f"  FAIL: '{file_a}' not found in PTY output")
        ok = False
    if file_b.encode() in pty_out:
        print(f"  PASS: '{file_b}' appears in render stream")
    else:
        print(f"  FAIL: '{file_b}' not found in PTY output")
        ok = False
    if file_c.encode() in pty_out:
        print(f"  PASS: '{file_c}' appears in render stream")
    else:
        print(f"  FAIL: '{file_c}' not found in PTY output")
        ok = False
    # Active-leaf reverse-video escape should fire at some point.
    if b"\x1b[7m" in pty_out:
        print("  PASS: ESC[7m (active-leaf reverse video) present")
    else:
        print("  FAIL: active-leaf reverse video missing")
        ok = False

    # ── v1.10.0 — terminal geometry and live resize ──────────────────────
    #
    # Both halves need a REAL pty with a settable window size, which is why
    # they live here rather than in a .tcyr: `_query_winsize` reads fd 0, and
    # under `cyrius test` fd 0 is not a terminal, so the unit suite can only
    # assert the fallback contract.
    print()
    print("=== v1.10.0 terminal geometry ===")
    import fcntl, termios, struct, signal, re, subprocess

    geom_fixture = "".join("L%02d " % i + "x" * 95 + "\n" for i in range(60))

    def run_sized(rows, cols, resize_to=None):
        """Launch cyim on a pty of the given size. If resize_to is set,
        resize + SIGWINCH partway through WITHOUT sending a keystroke and
        return the bytes emitted after that point."""
        path = "/tmp/cyim-geom-smoke.txt"
        with open(path, "w") as fh:
            fh.write(geom_fixture)
        m, sl = pty.openpty()
        fcntl.ioctl(sl, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        pid = os.fork()
        if pid == 0:
            os.setsid()
            fcntl.ioctl(sl, termios.TIOCSCTTY, 0)
            os.dup2(sl, 0); os.dup2(sl, 1); os.dup2(sl, 2)
            os.close(m); os.close(sl)
            os.execv(CYIM, [CYIM, path])
        os.close(sl)
        fcntl.fcntl(m, fcntl.F_SETFL, os.O_NONBLOCK)

        def drain(sec):
            buf = b""; t0 = time.time()
            while time.time() - t0 < sec:
                try:
                    buf += os.read(m, 65536)
                except BlockingIOError:
                    time.sleep(0.02)
                except OSError:
                    break
            return buf

        first = drain(0.6)
        after = b""
        if resize_to is not None:
            fcntl.ioctl(m, termios.TIOCSWINSZ,
                        struct.pack("HHHH", resize_to[0], resize_to[1], 0, 0))
            os.kill(pid, signal.SIGWINCH)
            after = drain(0.8)
        try:
            os.write(m, b"\x1b:q!\r")
        except OSError:
            pass
        drain(0.4)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        os.close(m)
        return first, after

    def n_lines(b):
        return len(set(re.findall(rb"L(\d\d) ", b)))

    # Geometry is honoured, not hardcoded to 24x80.
    small, _ = run_sized(12, 40)
    large, _ = run_sized(50, 200)
    if n_lines(large) > n_lines(small):
        print(f"  PASS: taller terminal draws more lines ({n_lines(small)} -> {n_lines(large)})")
    else:
        print(f"  FAIL: geometry ignored ({n_lines(small)} vs {n_lines(large)} lines)")
        ok = False

    widest = lambda b: max((len(x) for x in re.findall(rb"x+", b)), default=0)
    if widest(small) < widest(large):
        print(f"  PASS: wider terminal draws wider lines ({widest(small)} -> {widest(large)})")
    else:
        print(f"  FAIL: width ignored ({widest(small)} vs {widest(large)})")
        ok = False

    # An absurd u16 geometry must be clamped, not crash or hang. ws_col is
    # u16, so a terminal is free to claim this.
    huge, _ = run_sized(65535, 65535)
    if len(huge) > 0 and n_lines(huge) > 0:
        print(f"  PASS: 65535x65535 clamped and rendered ({n_lines(huge)} lines)")
    else:
        print("  FAIL: absurd geometry produced no render")
        ok = False

    # Live resize: repaint on SIGWINCH with NO keystroke.
    before, after = run_sized(24, 80, resize_to=(50, 200))
    if n_lines(after) > n_lines(before):
        print(f"  PASS: repaints on SIGWINCH without a keystroke "
              f"({n_lines(before)} -> {n_lines(after)} lines)")
    else:
        print(f"  FAIL: no live repaint ({n_lines(before)} -> {n_lines(after)}, "
              f"{len(after)} bytes after resize)")
        ok = False

    try:
        os.unlink("/tmp/cyim-geom-smoke.txt")
    except OSError:
        pass

    print()
    if ok:
        print("integration smoke: all checks passed")
        return 0
    print("integration smoke: FAILURES present")
    return 1


if __name__ == "__main__":
    sys.exit(main())
