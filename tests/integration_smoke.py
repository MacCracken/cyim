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

    print()
    if ok:
        print("integration smoke: all checks passed")
        return 0
    print("integration smoke: FAILURES present")
    return 1


if __name__ == "__main__":
    sys.exit(main())
