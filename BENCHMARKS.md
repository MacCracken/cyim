# cyim — Performance Benchmarks

Numbers from `cyrius bench tests/perf.bcyr` on x86_64 Linux. The
benchmark file lives at [`tests/perf.bcyr`](tests/perf.bcyr) and is
the source of truth for what's measured.

> **Reproducibility:** `cyrius bench tests/perf.bcyr`. Numbers below
> are single-iteration; treat as ±10% noise. Bench harness uses
> `clock_gettime(CLOCK_MONOTONIC_RAW)` via `lib/bench.cyr`.

---

## M6 — 2026-04-25 (tokenbuf cache landed)

The headline result of M6.1 — closes the M5-flagged tokenize hot path:

| Workload                              | M5 baseline | M6        | Δ |
|---------------------------------------|-------------|-----------|---|
| `highlight_buf` 1 MB cyrius (cold)    | 265 ms      | 265 ms    | unchanged (first call always misses) |
| `highlight_buf` × 1000, 1 MB unchanged| (no cache)  | 17 μs total | **~15.5 M× faster** |
| `buf_fill_1MB` (cost of version bump) | 10.0 ms     | 12.7 ms   | +27% (one extra `store64` per byte) |
| `buf_fill_100MB`                      | 974 ms      | 1.32 s    | +35% |

**Read:** the cache turns the M5 "3.7 fps for per-frame retokenize"
worry into a non-issue. Read-only render frames now hit a 17 ns
pointer-compare path. The cost shows up in raw-fill: every
`buf_insert_byte` now bumps a version counter, +2.7 ns per byte. Net
win for any workflow with more renders than mutations — i.e. all
editing workflows.

Other M5-vs-M6 deltas (unchanged within noise):

| Workload                       | M5    | M6    |
|--------------------------------|-------|-------|
| `buf_move_10K_cycles_10MB`     | 50 ms | 51 ms |
| `search_forward_10MB_worst`    | 105 ms| 108 ms|
| `render_build_line` × 1000     | 225 μs| 214 μs|

---

## M5 baseline — 2026-04-25

Host: x86_64 Linux. cyim v0.1.0 + M0–M5.1 work; DCE binary 256 KB.

### Gap-buffer fill (sequential bytes)

| Workload   | Time     | Throughput | Notes |
|------------|----------|-----------:|-------|
| 1 MB fill  | 10.0 ms  | ~100 MB/s  | Geometric growth amortized; ~14 reallocs |
| 10 MB fill | 105 ms   | ~95 MB/s   | ~17 reallocs |
| 100 MB fill| 974 ms   | ~103 MB/s  | ~21 reallocs; throughput stable |

**Read:** `buf_insert_byte` is ~100 ns / byte. Dominated by per-byte
`store8` + the amortized `buf_grow` copy. Acceptable for opening
typical files; opening a 1 GB file would block for ~10 s.

**Action:** none for M5. M6 hardening can consider replacing the
naive doubling-grow with an mmap-backed growable region for large
files, but the bump-allocator design makes per-block `mremap`
non-trivial.

### Gap-buffer cursor moves

| Workload                       | Time   | Per move |
|--------------------------------|--------|---------:|
| 10 K back-and-forth, 10 MB buf | 50 ms  | ~2.5 μs  |

**Read:** the gap migration in `buf_move` is the cost. 2.5 μs / move
on a 10 MB buffer is fast enough that motion-key spam doesn't lag.

### Search scan

| Workload                              | Time     | Throughput  |
|---------------------------------------|----------|-------------|
| 10 MB, best case (match at byte 6)    | 2 μs     | — (early exit) |
| 10 MB, worst case (no match)          | 105 ms   | ~95 MB/s |
| 10 MB, worst case + ignorecase        | 170 ms   | ~59 MB/s |

**Read:** worst-case search scans every byte. Case-fold adds ~62 ns /
byte for the per-byte `_search_lower` call.

**Action:** for typical edit sessions (small files, frequent
matches), this is fine. For large-file search, Boyer-Moore would
help — queued for M6 if a real workload complains.

### Per-line render

| Workload                            | Total    | Per render |
|-------------------------------------|----------|-----------:|
| `render_build_line` × 1000, 80 cols | 225 μs   | ~225 ns    |

**Read:** the per-line render is sub-microsecond. A 24-row frame
takes ~5.4 μs of pure render work — well below the perceptual
threshold. The render path is *not* the bottleneck.

### Syntax highlighting (the hot path)

| Workload                              | Time   | Throughput |
|---------------------------------------|--------|------------|
| `highlight_buf` 1 MB, cyrius grammar  | 269 ms | ~3.7 MB/s  |

**Read:** vyakarana tokenization runs at ~3.7 MB/s for the cyrius
grammar. Per-frame retokenize on a 1 MB file would yield ~3.7 fps —
**this is the M2 "deferred until perf surfaces" point now surfacing**.

**Action:** M6 hardening should add a tokenbuf cache keyed by
(buffer-pointer, version-counter). Invalidate on every edit; reuse
between renders. Expected win: ~100× for the frame-render path on
read-only editing (which is the common case while you're navigating
or paging through code).

---

## What's *not* benchmarked yet

These are queued for M5 bite 3 (fuzz harnesses) or follow-up bites:

- **Open-from-disk** end-to-end (`cyim foo.cyr` cold start). Includes
  tty_raw, alt-screen enter, file load, first render. Hard to
  benchmark inside `cyrius bench` because it needs a real PTY —
  candidate for the Python integration smoke instead.
- **Edit-cycle latency under load** — type → render → repeat. Same
  PTY-bound issue.
- **Multi-window render** — `_render_frame_multi` walks N leaves.
  Cost scales linearly with leaf count + buffer size.
- **Undo snapshot cost** — `_snap_new_from_buf` is O(buf_len). On a
  10 MB buffer, every `i` press currently allocates 10 MB. Likely
  the next perf surface to surface; M6 candidate.

---

## Comparison receipts — M5 closeout — 2026-04-25

| Metric                       | cyim    | vim          | neovim       |
|------------------------------|---------|--------------|--------------|
| DCE binary size              | 263 KB  | ~3 MB        | ~10 MB       |
| Source LOC (editor + parser) | 4 058   | ~500 K (C)   | ~700 K (C)   |
| Source LOC (tests + grammars)| 4 927   | ~50 K        | ~80 K        |
| Source language              | Cyrius  | C            | C            |
| Embedded scripting           | none    | Vimscript    | Vimscript + Lua |
| Plugin system                | none    | yes          | yes          |
| Configuration syntax         | data (CYML) | code (Vimscript) | code (Vimscript / Lua) |

Numbers worth highlighting:

- **Binary is ~10× smaller than vim**, ~38× smaller than neovim.
- **Source is ~125× smaller than vim's editor core**, with full
  syntax highlighting (via vyakarana) and a working multi-buffer /
  multi-window / undo / search / visual / dot-repeat surface.
- The 4 058-line editor compiles to a 263 KB binary. That's
  **~64 source bytes per binary byte** — the Cyrius compiler does
  significant work, mostly through DCE.
- **No embedded scripting language.** This is the load-bearing
  refusal. Most vim / neovim CVE classes (Vimscript injection,
  Lua sandbox escapes, plugin escapes) are absent by design.

These numbers are receipts, not goals. cyim's win condition is
**zero attack surface + sovereign codebase + auditable end-to-end**,
not raw perf. The perf bar is "doesn't make you wait."

### Test surface receipts

| Suite               | Count    |
|---------------------|----------|
| .tcyr suites        | 18       |
| .tcyr assertions    | 812      |
| PTY-driven E2E checks | 14     |
| Fuzz harnesses      | 3        |
| Performance benches | 8        |
| Bundled grammars    | 11       |

### Build receipts

| Build               | Size     | Note |
|---------------------|----------|------|
| `cyrius build` (default) | 263 KB | DCE on by default |
| `CYRIUS_DCE=1 cyrius build` | 263 KB | Explicit DCE; same |
| M0 stub             | 58 KB    | Hello-world baseline |
| M1 closer (no highlighting) | 102 KB | +44 KB for the editor |
| M2 closer (with vyakarana) | 162 KB | +60 KB for tokenize + grammars |
| M3 closer (multi-window) | 226 KB | +64 KB for registry + windows |
| M4 closer (search + undo + visual) | 256 KB | +30 KB for the muscle-memory layer |
| M5 closer (this) | 263 KB | +7 KB for `:set` + bench dep wiring |

Each milestone added ~30–60 KB. The largest single addition was M3's
multi-window layer (+64 KB for the registry + window tree + per-leaf
status row). The smallest was M5's polish layer (+7 KB).

---

*Format: timestamps from `cyrius bench`'s `bench_report` output;
human-readable summaries above each table. Add new runs by
appending sections — never overwrite, so the history is recoverable
from this file alone.*
