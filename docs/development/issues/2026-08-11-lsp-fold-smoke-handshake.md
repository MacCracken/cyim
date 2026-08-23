# LSP fold smoke — `lsp_client_start_default()` handshake never completes

**Filed:** 2026-08-11
**Filer:** cyim (self)
**Affects file:** `tests/smcyr/lsp_fold.smcyr` — subject under test is `lib/cyim-lsp.cyr`'s client path (`lsp_client_start_default` → `_lsp_client_start_with` → `lsp_proc_spawn` + `_lsp_initialize`)
**Severity:** P2 — an opt-in feature is dead on its only supported platform, but nothing ships broken: no CI gate covers it, the editor is unaffected, and no user-visible surface regressed
**Status:** **ROOT-CAUSED 2026-08-23 (1.8.2)** — the defect is upstream, in `cyim-lsp`'s `src/subprocess.cyr`. Still OPEN from cyim's side: the fix is not cyim's to make, and cyim cannot pick it up until a `cyim-lsp` release carries it. See [§ Root cause](#root-cause-found-2026-08-23) below.
**Internal label (cyim):** BUG-002 ([`../roadmap.md`](../roadmap.md) § Open Bugs)

---

## Summary

`cyrius smoke` reports **4 passed, 9 failed (13 total)**. The first failure is
the one that causes the rest:

```
FAIL: lsp_client_start_default returns 0 (got -1, expected 0)
FAIL: cyrius-lsp pid registered post-spawn
FAIL: describe[0] == 'c' (got 40, expected 99)     # 40 = '(' — "(not attached)"
FAIL: describe[1] == 'y' (got 110, expected 121)   # 110 = 'n'
FAIL: describe[2] == 'r' (got 111, expected 114)   # 111 = 'o'
FAIL: describe[3] == 'i' (got 116, expected 105)   # 116 = 't'
FAIL: describe[4] == 'u' (got 32, expected 117)    # 32  = ' '
FAIL: second start succeeds (idempotent re-attach) (got -1, expected 0)
FAIL: second pid registered
```

`lsp_client_describe()` answers `"(not attached)"`, so no server is attached.
The 5 `describe[N]` rows and both `second start` rows are downstream of the
single `start_default` failure, not independent defects.

`_lsp_client_start_with` returns -1 from exactly two places, and the smoke does
not distinguish them:

```cyrius
var p = lsp_proc_spawn(cmd, arg1, arg2);
if (p == 0) { return 0 - 1; }          # (a) spawn failed
_lsp_proc = p;
var rc = _lsp_initialize();
if (rc != 0) {                          # (b) handshake failed
    lsp_proc_close(_lsp_proc);
    _lsp_proc = 0;
    return 0 - 1;
}
```

**Narrowing (a) vs (b) is the first step for whoever picks this up** — they are
different bugs with different owners (process plumbing vs. protocol).

## Not caused by the cyim-lsp 1.5.2 bump

Pinning `[deps.cyim-lsp]` back to **1.5.0** in `cyrius.cyml` and re-running
`cyrius smoke` reproduces the **identical 4 passed / 9 failed** split. Both
bundles fail the same way, so this predates 1.5.2 and is not a regression from
the agnos capability gate landed in that cut.

It is also **not an agnos issue**. This is the host/Linux path, where
`LSP_HAVE_SUBPROC == 1` and the full `sys_fork` / `sys_execve` / `sys_dup2`
branch is compiled in exactly as before.

## Ruled out

- **The server is not the fault.** `cyrius-lsp` is installed at
  `~/.cyrius/bin/cyrius-lsp` and on `PATH`. Fed an `initialize` request by hand
  it answers correctly:

  ```
  Content-Length: 374\r\n\r\n{"jsonrpc":"2.0","id":1,"result":{"capabilities":{...
  ```

- **The startup banner is not corrupting the protocol stream.** `cyrius-lsp`
  prints `[cyrius-lsp] found cycc: …` / `found cyrius wrapper: …` at startup —
  the obvious suspect for a framing failure, since anything on stdout ahead of
  the first `Content-Length:` would desynchronise the reader. Verified with
  `2>/dev/null` that both lines go to **stderr**; stdout begins directly with
  the header. Not it.

## Why it went unnoticed

`cyrius smoke` is **not a step in `.github/workflows/ci.yml`**. That workflow
runs build, ELF check, lint, `cyrius test`, `cyrius fuzz`, bench, PTY
integration smoke, and the DCE parity re-run — no `cyrius smoke`. So this
harness could rot without turning anything red, and
`docs/development/state.md` went on recording "LSP smoke: 13 PASS" (corrected
at 1.8.1 to the measured 4/9).

**Whatever the root cause turns out to be, the durable fix is to put `cyrius
smoke` behind a CI gate** — otherwise the next silent rot is only a matter of
time. Note it needs `cyrius-lsp` present on the runner, which is why it was
plausibly left out originally; that is a solvable packaging problem, not a
reason to leave the harness unwatched.

---

## Root cause (found 2026-08-23, during the 1.8.2 dep refresh)

**`var argv[4]` in `cyim-lsp`'s `_lsp_proc_exec` is sized in POINTER SLOTS, not
BYTES.** In Cyrius, `var buf[N]` reserves **N bytes** — cyim's own CLAUDE.md
states this as a contract ("every buffer declaration is a contract: `var buf[N]`
= N *bytes*, not N entries"). The function then writes up to four 64-bit
pointers into it:

```cyrius
fn _lsp_proc_exec(cmd, arg1, arg2) {
    var argv[4];                                  # 4 BYTES
    store64(&argv, cmd);                          # writes bytes 0..7
    var ai = 1;
    if (arg1 != 0) { store64(&argv + ai * 8, arg1); ai = ai + 1; }   # 8..15
    if (arg2 != 0) { store64(&argv + ai * 8, arg2); ai = ai + 1; }   # 16..23
    store64(&argv + ai * 8, 0);                   # NULL terminator, up to 24..31
    ...
```

**32 bytes written into a 4-byte stack slot.** `lsp_client_start_default()`
passes `("/usr/bin/env", "cyrius-lsp", 0)`, so `ai` reaches 2 and the write
range is `[0, 24)` — six times the declared size. The adjacent stack is
clobbered, `execve` receives a malformed `argv`, it fails, and the child falls
through to its own `sys_exit(127)`.

The same file has a second instance two statements down:

```cyrius
        var fallback[1];        # 1 BYTE
        store64(&fallback, 0);  # writes 8
```

Locations upstream: [`cyim-lsp/src/subprocess.cyr:180`] (`argv`) and
[`:191`] (`fallback`); in cyim's vendored bundle they land at
`lib/cyim-lsp.cyr:433` and `:444`.

### Evidence

A four-step diagnostic against the **1.5.2** bundle (spawn → hand-framed
`initialize` → blocking read → reap) splits the two candidate failure modes the
"first step" note below asked for:

```
--- step 1: lsp_proc_spawn(/usr/bin/env, cyrius-lsp, 0)
  spawn handle = <non-zero>          # (a) spawn SUCCEEDS — pipes + fork are fine
  pid = 776950
--- step 2: raw send of an initialize frame
  wrote hdr=23 body=107              # the parent's write half is fine too
--- step 3: blocking read of the response
  read n = 0                         # EOF: the child is already gone
--- step 4: reap child, report wait status
  status = 32512  ->  exit code 127, term signal 0
```

So it is **(b), and specifically the exec inside the child** — not the protocol
reader, not the framing, not the server. Exit 127 with **no `env:` diagnostic on
stderr** is the tell: had `execve` succeeded and `env` merely failed to find
`cyrius-lsp`, `env` would have printed `env: 'cyrius-lsp': No such file or
directory` before exiting 127. Nothing was printed, so `execve` itself never
took.

Confirmed by construction: a second harness re-implementing `lsp_proc_spawn` /
`_lsp_proc_exec` **byte-for-byte except `argv[4]` → `argv[32]` and
`fallback[1]` → `fallback[8]`**, linked against the same unmodified bundle for
everything else, completes the handshake on the first try:

```
  pid = 777411
[cyrius-lsp] found cycc: /home/macro/.cyrius/bin/cycc
[cyrius-lsp] found cyrius wrapper: /home/macro/.cyrius/bin/cyrius
[cyrius-lsp] initialized
  read n = 397
  RESULT: SERVER ANSWERED -> argv sizing was the bug
```

397 bytes of well-formed `initialize` response, and the server's stderr banner
appears for the first time — because until now the child never got as far as
being `cyrius-lsp`.

### Why it went unnoticed for so long, and why it surfaced now

This is the **same bug class the 1.5.2 audit already fixed once in this file**.
`lsp_proc_close`'s reap buffer carries the fix and the explanation in a comment
that sits 150 lines above the survivors:

> a 4-byte status word here, so `var status_buf[1]` was a 3-byte stack
> overwrite on every reap. Latent before cyrius 6.3.13 moved locals onto the
> stack behind a guard page; not worth leaving armed either way.

That sweep caught `status_buf` and missed `argv` / `fallback`. The
**6.3.13 guard-paged stack** is why the failure became deterministic: before it,
a 24-byte overrun of a 4-byte local scribbled on whatever happened to be
adjacent and often got away with it. cyim's pin crossed 6.3.13 at the 1.8.1 cut
(`6.2.36 → 6.5.18`) — which is exactly when the smoke was first observed
failing. The 1.5.0 control run reproduces the same 4/9 because the control
varied the *bundle*, not the *toolchain*; both bundles carry the same
`argv[4]`.

### Fix

**Upstream, in `cyim-lsp`** — `src/subprocess.cyr`, `argv[4]` → `argv[32]` and
`fallback[1]` → `fallback[8]`, then `cyrius distlib` to regenerate
`dist/cyim-lsp.cyr`. cyim picks it up with a `tag` bump under
`[deps.cyim-lsp]`; **no cyim source change is involved**, exactly as at 1.8.1.

cyim's own tree was swept for the same class during this cut — every
`var NAME[N]` in `src/`, `tests/` and `fuzz/` that is subsequently accessed with
`load64` / `store64` was checked against its maximum written offset. **Zero
findings**; `src/lang.cyr`'s and `src/render.cyr`'s fixed buffers are all
byte-indexed via `store8`.

### Still open after the fix lands

The CI-gate half of this issue stands unchanged: `cyrius smoke` is still not a
step in `.github/workflows/ci.yml`, which is *why* a dead feature could sit
unobserved across seven cuts. Fixing `argv` makes the harness pass; it does not
make anyone watch it.

---

## Why P2 and not higher

- **Nothing ships broken.** The editor is unaffected on every target; the
  1.8.1 gates are green (21 suites / 1129 assertions, 4 fuzz harnesses, 118
  CLI smoke, PTY integration smoke, DCE parity).
- **LSP is opt-in** — it is registered only when a language server is
  configured, and is already absent by design on agnos.
- Not P1: no silent wrong answer on a scriptable surface (the BUG-001 bar). The
  failure is loud and self-announcing — `:lsp-status` reports "(not attached)".
- Not P3: this is the whole of the LSP feature being non-functional on its only
  supported platform, and cyim has shipped seven cuts of consumer-side LSP glue
  against a bundle whose end-to-end path is currently unproven.

## Reproduce

```sh
cd ~/Repos/cyim && cyrius smoke
```

Control run (proves it predates 1.5.2) — set `tag = "1.5.0"` under
`[deps.cyim-lsp]` in `cyrius.cyml`, re-run, observe the same 4/9, then restore
`tag = "1.5.2"`.
