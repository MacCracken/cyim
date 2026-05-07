# Upstream issue — cyrius `args_init()` 4 KB stack-buffer truncation

**Filed:** 2026-05-06
**Filer:** cyim (downstream consumer)
**Target repository:** [MacCracken/cyrius](https://github.com/MacCracken/cyrius)
**Affects file:** `lib/args.cyr` (line 42)
**Severity:** P1 — silent argc undercount on a scriptable surface
**Status:** **RESOLVED upstream in cyrius 5.9.5** (heap-backed 2 MB buffer); verified 2026-05-06 against cyrius 5.9.13. cyim-side workaround `_cli_args_reload_big()` retires in cyim v1.3.3.
**Internal label (cyim):** BUG-001 ([`../roadmap.md`](../roadmap.md) § Active Bugs)

---

## Resolution (2026-05-06)

Upstream fix landed in **cyrius 5.9.5** — `lib/args.cyr` switched
to a heap-backed 2 MB buffer (matches Linux ARG_MAX). The new
`args_init()` includes a comment block explicitly referencing this
issue file by name and threshold (4063 / 4064 byte boundary). cyim
verified against cyrius 5.9.13:

- `lib/args.cyr` SHA `cde23315...` (was `7fc65fa1...` through 5.9.4)
- 4063 B / 8192 B / 65536 B `<new>` arg sizes all succeed with the
  cyim-side `_cli_args_reload_big()` workaround **disabled**, on a
  binary built against 5.9.13
- All cyim test gates still green (cyrius test 130/130, cli_smoke
  118/118, integration_smoke PASS)

cyim's `_cli_args_reload_big()` workaround retires in cyim v1.3.3
(separate patch — bumps the cyrius pin and removes the helper +
its main.cyr call site). The integration_smoke regression for
BUG-001 stays in place against the upstream fix as a guard.

---

## Summary

`args_init()` in `lib/args.cyr` reads `/proc/self/cmdline` into a
fixed 4096-byte stack buffer. When the cmdline (program path +
flags + args, NUL-separated) exceeds ~4 KB, the read truncates
and `argc()` silently undercounts the trailing args. Downstream
verbs that depend on argc-correctness (e.g. `cyim --replace OLD
NEW FILE`) see a positional-count mismatch and fall through to
their "usage" error branch — an unhelpful diagnostic that doesn't
surface the real cause.

The kernel's `ARG_MAX` on Linux is 2 MB (`getconf ARG_MAX`). The
cyrius runtime is rejecting ~99.8% of the kernel-accepted argv
range without a diagnostic.

## Source

`lib/args.cyr:42` (verified 2026-05-06 against cyrius 5.9.4):

```cyrius
fn args_init() {
    ...
    # For now: use /proc/self/cmdline as a portable approach.
    var buf[4096];
    var fd = syscall(2, "/proc/self/cmdline", 0, 0);
    if (fd < 0) { return 0; }
    var n = syscall(0, fd, &buf, 4096);
    syscall(3, fd);
    _args_base = &buf;
    _args_len = n;
    return n;
}
```

The buffer is stack-allocated and capped at the literal `4096`,
both in the declaration and the read-size argument.

## Threshold (bisected against cyim, 2026-04-25)

| `<new>` arg size | Behaviour                                    |
|------------------|----------------------------------------------|
| 4063 B           | clean — `argc()` correct                     |
| 4064 B           | truncates — trailing arg silently lost       |

`4064 = 4096 − 32`, consistent with a 4 KB buffer reserving ~32
bytes for null terminators / structural overhead between
NUL-separated argv entries.

## Repro

The simplest reproduction is via cyim (which is the user-facing
surface where the bug bites). Strip cyim's workaround
(`_cli_args_reload_big()` in `src/cli.cyr`) and run:

```sh
printf 'foo\nold\nbar\n' > /tmp/tgt.txt
SMALL=$(head -c 4063 /dev/urandom | base64 | head -c 4063)
BIG=$(head -c 8192 /dev/urandom | base64 | head -c 8192)

cyim --replace "old" "$SMALL" /tmp/tgt.txt   # exit 0
cyim --replace "old" "$BIG"   /tmp/tgt.txt   # exit 2 (usage)
```

Without the workaround, the `>4064`-byte case takes the "usage"
branch instead of writing. The "usage" message ("missing FILE")
implies "wrong number of args" — it does not indicate the real
cause is the cmdline read truncating.

A pure cyrius repro (no cyim involvement) — write a 30-line program
that calls `argc()` and prints the result, then invoke it with one
huge arg:

```sh
SIZE=$((1024 * 1024))   # 1 MB arg
BIG=$(head -c $SIZE /dev/urandom | base64 | head -c $SIZE)
./your_argv_program "$BIG" final
# Expected: argc() == 3 (program + 2 args)
# Actual:   argc() == 1 (program only — both args lost)
```

## Suggested fix

Replace the fixed-size stack buffer with a heap-backed read sized
to `ARG_MAX`:

```cyrius
fn args_init() {
    # Linux ARG_MAX is 2 MB (the kernel's hard cap on argv+envp
    # combined). Allocate the full window so we never truncate.
    var cap = 2097152;
    var buf = alloc(cap);
    if (buf == 0) { return 0; }
    var fd = syscall(2, "/proc/self/cmdline", 0, 0);
    if (fd < 0) { return 0; }
    var n = syscall(0, fd, buf, cap);
    syscall(3, fd);
    _args_base = buf;
    _args_len = n;
    return n;
}
```

Memory overhead: 2 MB bump-allocated per process up-front. For
CLI tools (cyim, cyrius itself, any consumer of `args_init`) this
is acceptable on every modern Linux host; benchmarks should
confirm no measurable regression.

**Alternative (lower-overhead, one extra syscall pair)**: probe
the cmdline size first via `lseek(SEEK_END)`, then exact-allocate.
Trades 1 syscall for ~1.99 MB of saved heap on small invocations.
Either approach is acceptable; the choice is a trade-off we
defer to upstream.

## Downstream context

cyim cannot patch `lib/args.cyr` directly (CLAUDE.md forbids
edits to vendored stdlib). The current cyim workaround is
`_cli_args_reload_big()` (`src/cli.cyr:532`), which:

1. Allocates a 2 MB heap buffer.
2. Re-reads `/proc/self/cmdline` into it.
3. Rebinds `lib/args.cyr`'s `_args_base` / `_args_len` globals to
   point at the heap buffer.

It runs unconditionally on every cyim invocation. Cost is one
syscall + one `alloc(2 MB)` at startup; the workaround retires
the moment the upstream fix lands and cyim's cyrius pin picks it
up.

cyim's bug record:
[`docs/development/roadmap.md`](../roadmap.md) § Active Bugs §
BUG-001 (full P1 spec, threshold table, discovery context).

## Verification

After the upstream fix lands:

1. **Smoke against cyrius itself.** Write a CLI program that
   echoes `argc()` for each invocation; call it with one >4064 B
   arg and verify `argc() == 2` (program + arg).
2. **Smoke against cyim** with the workaround removed (delete
   `_cli_args_reload_big()` from `src/cli.cyr` + the
   corresponding call in `main`). The BIG case in the repro
   above should still succeed.
3. **`tests/integration_smoke.py`** in cyim has a regression for
   this exact case (BUG-001 row) — the test should pass without
   the workaround.

## Re-confirmation history

- **2026-04-25**: bisected against cyrius 5.7.5 during cyim
  v1.0.2 work. Threshold confirmed at 4063 / 4064 byte boundary.
- **2026-04-26**: cyim ships workaround in v1.0.2.
- **2026-05-06 (cyim 1.3.2 closeout)**: re-checked against cyrius
  5.9.2; unchanged.
- **2026-05-06 (cyim 1.3.x roadmap pass)**: re-checked against
  cyrius **5.9.4**; `lib/args.cyr` SHA `7fc65fa1b313cbb3...`
  byte-identical across 5.9.1 / 5.9.2 / 5.9.3 / 5.9.4. Last
  commit touching the file is `53301cc fixing repo` (pre-5.4
  era). The file has not been edited in ~6 cyrius minor releases.

## Out of scope (for upstream)

- The macOS arm64 dispatch (`lib/args_macos.cyr`) reads argv from
  the kernel-stashed `x28` register at entry — not via
  `/proc/self/cmdline` — so it does not have this bug. Fix is
  Linux-only.
- Windows PE32+ is out of scope for both cyrius and cyim today.
