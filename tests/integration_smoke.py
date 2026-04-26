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

    print()
    if ok:
        print("integration smoke: all checks passed")
        return 0
    print("integration smoke: FAILURES present")
    return 1


if __name__ == "__main__":
    sys.exit(main())
