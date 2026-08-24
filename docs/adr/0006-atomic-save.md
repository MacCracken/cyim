# ADR 0006 — Saving is atomic by default, with an enumerated in-place fallback

**Status:** Accepted
**Date:** 2026-08-23
**Tags:** security, data-integrity, filesystem, v1.8.4

---

## Context

The [1.8.x hardening audit](../audit/2026-08-23-1.8x-hardening.md) found
that `buf_save_file` treated a short `write(2)` as a completed one, so
`:w` cleared the modified flag and all six agent CLI verbs exited 0 on a
truncated file. Measured: 475 of 575 bytes destroyed, exit code 0.

v1.8.3 fixed the **reporting** — writes now loop to completion, `fsync`
and `close` are checked, and a failure is a negative return that every
caller already tests. It did not fix the **damage**. The file is opened
`O_TRUNC`, so by the time a write fails the original content is already
gone. The audit recorded that as residual **R-1**:

> cyim's save is as atomic as vim's default, which is to say not.

This ADR closes R-1.

### What is actually being defended against

In rough order of how often it bites:

1. **`ENOSPC` / `EFBIG` part way through a write.** The common case, and
   the one the audit measured. Today it destroys the file.
2. **A concurrent reader seeing a half-written file.** Directly relevant
   to cyim's `daimon` consumer: an agent edits, a build tool reads. A
   torn read produces a confusing failure a long way from its cause.
3. **Crash or power loss mid-write.** Rarer, worse when it happens.

All three are solved by the same mechanism — write a sibling temp, then
`rename(2)` over the target — because rename is atomic within a
filesystem: a reader sees either the whole old file or the whole new one.

### Why "just use `file_write_atomic`" was rejected at 1.8.3

The stdlib already ships that exact loop. Adopting it wholesale changes
the inode on every save, and that is not a neutral act for an editor:

- **Symlinks are replaced by regular files.** Editing a dotfile that
  symlinks into a dotfiles repository silently destroys the link. This
  is common enough to be disqualifying on its own.
- **Hardlink sets are broken.** The other names keep the old content.
- **Mode, ownership, ACLs and xattrs are discarded** — the new file gets
  whatever the `open` call asked for and the invoking user's uid. Editing
  a mode-`600` file and getting `644` back is a security regression, not
  a cosmetic one.
- **A writable file in a non-writable directory becomes unsaveable**,
  because the temp cannot be created.

It also contradicts [ADR 0001](0001-trust-model.md) § 3, which
*accepts* write-in-place TOCTOU semantics on the grounds that they match
vim's default. That clause is amended by this ADR.

## Decision

**cyim saves atomically by default, and falls back to writing in place
only under conditions it can name.**

The save path is:

1. `stat` the target. If it does not exist, take the atomic path.
2. Take the **in-place** path if any of the conditions below holds.
3. Otherwise: create a sibling temp with `O_EXCL`, `fchmod` it to the
   target's mode, write every byte, `fsync`, `close`, `rename` over the
   target, then `fsync` the containing directory. On any failure, unlink
   the temp and return the error — **the original is untouched**.

### The in-place conditions, and why each is on the list

| # | Condition | Why rename is wrong here |
|---|---|---|
| 1 | Target is a **symlink** | `rename` replaces the link itself, not what it points at. The user asked to edit a file, not to delete a link |
| 2 | `st_nlink > 1` (**hardlinked**) | `rename` breaks the set; every other name silently keeps the old content |
| 3 | Target exists and is **not a regular file** | FIFOs, devices, `/dev/stdout`. Renaming over one is meaningless or destructive |
| 4 | Target is owned by a **different uid** than the process | Rename silently transfers ownership to the writer. Matters most under `sudo`, which is exactly when it is least welcome |
| 5 | The temp **cannot be created** next to the target | A writable file in a non-writable directory. Discovered by attempting, not pre-checked — the pre-check would be its own TOCTOU |
| 6 | Target platform is **agnos** | No `fchmod`, no uid in its `stat`, and `fsync` is a whole-system `sync()`. A platform that cannot preserve mode should not be silently resetting it |

Conditions 1–4 are checked from a single `stat`, plus one `readlink`
probe for the symlink test. Condition 5 is the `O_EXCL` open failing.
Condition 6 is a compile-time `#ifdef`.

**The in-place path is not a degraded path.** It is 1.8.3's
`buf_save_file` unchanged: loop until every byte lands, `fsync`, check
`close`, return negative on failure. What the caller loses in that mode
is the *guarantee that a failure leaves the original intact* — which is
exactly the guarantee the conditions above say cannot be provided
without breaking something the user cares about more.

### What callers can rely on

`buf_save_file` returns bytes written, or negative on any failure.
Unchanged — no call site needed a change.

`buf_save_was_atomic()` reports whether the most recent save took the
atomic path. It exists so tests can assert *which* path ran (otherwise
both look identical from outside) and so a future `:w` status message
can tell the user when their save was not crash-safe. It is not part of
the plugin ABI.

## Options considered

| Option | What it costs | What it buys | Verdict |
|---|---|---|---|
| **A.** Status quo — in place, failures reported | Nothing | Nothing. A full disk still destroys the file | Rejected: this is R-1 |
| **B.** Always temp + rename | Symlinks, hardlinks, mode, ownership, non-writable directories | Simplest code | Rejected: trades a rare failure for four common ones |
| **C.** Atomic by default, enumerated in-place fallback | One `stat` + one `readlink` per save; six conditions to keep correct | Atomicity where it is safe, correctness where it is not | **Chosen** |
| **D.** A user-facing option, vim's `backupcopy=` | A config key, its documentation, and a way for users to choose wrong | Control for the person who needs it | Deferred — see below |

**On D.** vim ships `backupcopy=yes|no|auto` and defaults to `auto`,
which is option C. cyim ships the `auto` behaviour without the knob,
because the knob's other two settings are "always break symlinks" and
"never be atomic", and neither has a use case that the enumerated
conditions do not already handle correctly. Per
[`CLAUDE.md`](../../CLAUDE.md)'s "reference, don't mimic": the *reasoning*
behind `backupcopy=auto` is right; the compatibility surface around it is
not something cyim has to inherit. If a real consumer needs to force one
mode, it becomes a `.cyimrc` key then — and gets weighed against
[ADR 0005](0005-cyimrc-cwd-trust-boundary.md) at that point, because a
config that can force non-atomic saves is a more interesting thing to
accept from a directory than a colour.

## Consequences

### What this enables

- A failed save no longer destroys the previous contents in the common
  case. `ENOSPC` mid-write leaves the file exactly as it was.
- Concurrent readers never observe a partially written file.
- `--batch`'s documented "leaves FILE untouched on disk" becomes true for
  write failure, not just for logical mid-batch failure. `CLAUDE.md` is
  updated accordingly.

### What this forbids (without a follow-up ADR)

- **Silently taking ownership of another user's file.** Condition 4 is
  load-bearing; removing it makes `sudo cyim` a privilege-shaped
  surprise.
- **Adding a "just always rename" fast path.** Every condition on the
  list is there because removing it breaks something a user relies on.

### Residuals

- **Extended attributes and ACLs are not preserved** across the atomic
  path. `fchmod` carries the permission bits; xattrs, POSIX ACLs and
  SELinux labels are not copied. A file with a non-trivial ACL is
  therefore best saved in place — but cyim cannot currently *detect*
  one without an `listxattr`/`getxattr` surface the stdlib does not
  expose. Recorded as **R-1a**. The exposure is narrow: it needs a file
  with an ACL, owned by the invoking user, not a symlink, not hardlinked.
- **agnos saves in place** (condition 6) and therefore keeps R-1 on that
  target. Its `xfsync` is already a whole-system `sync()`, so crash
  durability there is coarse regardless. Revisit when agnos grows
  `fchmod` and a uid-carrying `stat`.
- **The directory `fsync` is best-effort.** It is what makes the rename
  itself durable rather than merely atomic. If opening the parent
  directory fails, the save still reports success — the data is fsynced
  and the rename has happened; only the ordering guarantee across a
  power loss is weakened. Failing an otherwise-complete save because a
  directory could not be opened for `fsync` would trade a real success
  for a theoretical one.

### Amendment to ADR 0001

[ADR 0001](0001-trust-model.md) § 3 reads:

> **TOCTOU on save is accepted.** `:w` opens the same path string it was
> given; if a symlink moved between `:e` and `:w`, the write follows.
> This matches vim's default behavior.

That clause stands for the **in-place** path and for symlink *following*
— condition 1 exists precisely so that editing through a symlink keeps
working the way ADR 0001 describes. What no longer holds is the implied
consequence that a failed write may destroy the file. ADR 0001 carries a
pointer here.

## References

- [2026-08-23 — 1.8.x P(-1) hardening audit](../audit/2026-08-23-1.8x-hardening.md), F-1 and residual R-1
- [ADR 0001 — Trust model: interactive local user](0001-trust-model.md) § 3
- `lib/io.cyr`'s `file_write_atomic` — the shape this borrows, and the
  reason it is not used directly
- vim `:help 'backupcopy'` — the same per-file decision, and the prior
  art for conditions 1–4
