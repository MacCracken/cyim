# 003 — The renderer is byte-oriented, not codepoint-oriented

**Added:** 2026-08-23 (v1.8.3, out of hardening-audit finding F-7)

---

## The invariant

`render_build_line` walks the gap buffer **one byte at a time** and
treats each byte as one terminal column:

```cyrius
var c = buf_get(b, i);
var kind = highlight_kind_at(tb, i);
...
col = col + 1;
```

There is no UTF-8 decode step for WIDTH anywhere in the render path. `cols`
counts bytes emitted, not characters displayed. (Since 1.11.0 the path does
decode, but only to classify bytes >= 0x80 for control safety — see below.
Every byte still counts as one column.)

## What follows from it

These are not four separate gaps. They are one decision, and they move
together:

- **Multi-byte characters count as several columns.** A line of CJK or
  accented text truncates earlier than its visual width suggests.
- **Double-width characters are not accounted for.** A CJK glyph occupies
  two terminal cells and one buffer byte per UTF-8 byte; cyim's column
  arithmetic knows neither number.
- **Combining characters count as columns of their own**, though they
  render as zero-width.
- ~~**C1 control bytes (`0x80`–`0x9F`) pass through unsubstituted.**~~
  **Closed at 1.11.0 (BUG-005), on the terms this note set.**
  `render_ctrl_substitute` handles C0 (`0x00`–`0x1F`, Tab excepted) and
  DEL — the M6 audit's escape-injection fix — and it still cannot extend
  to C1 **because `0x80`–`0x9F` overlaps the UTF-8 continuation-byte range
  `0x80`–`0xBF`**. So C1 is decided by `render_c1_at`, which DECODES: a byte
  that is part of a well-formed RFC 3629 sequence passes byte for byte; a C1
  control — a raw 0x80–0x9F byte outside any valid sequence, or the encoded
  form `C2 80`–`C2 9F` — is shown as `<xx>` (four columns, vim's display);
  a malformed byte 0xA0–0xFF keeps its verbatim pre-1.11 form. Telling a
  continuation byte from a lone C1 byte required decoding, and decoding is
  what it got — for classification only, not for width.

## Why this is the right trade today, and where it stops being one

The gap buffer stores bytes; cursor motion, undo, marks, search offsets
and the tokenizer's spans are all byte offsets. A codepoint-aware
renderer is not a change to `render_build_line` — it is a second
coordinate system threaded through every one of those, plus a width
table (`wcwidth`-equivalent) cyim does not have and would need to vendor
or derive from `unicode/`.

The exposure it buys back is small and getting smaller. Terminals are
overwhelmingly UTF-8; a lone `0x9B` renders as a replacement glyph, not
as CSI. Honouring 8-bit C1 controls requires a terminal explicitly in
that mode, which is legacy configuration rather than a default anywhere
current.

**What would change the calculus:** a consumer editing CJK or RTL text
in earnest. `aethersafha` hosting cyim in a compositor terminal is the
likeliest trigger — that is the point where "one byte, one column" stops
being an implementation detail and starts being a visible defect.

## What NOT to do

Do not "simplify" C1 handling by moving `0x80`–`0x9F` into
`render_ctrl_substitute`. It looks like a two-line hardening patch and it
breaks every non-ASCII file cyim can open — the 1.8.3 audit considered
exactly this and rejected it, and 1.11.0 closed C1 the other way, by
decoding. `tests/render.tcyr`'s "well-formed UTF-8 passes byte for byte"
group (U+1F600 has three bytes in that range) is the guard; if a change
makes it fail, the change is wrong.

## See also

- [2026-08-23 hardening audit](../audit/2026-08-23-1.8x-hardening.md) § F-7
- [2026-04-25 M6 audit](../audit/2026-04-25-m7-audit.md) — F-1, the C0
  substitution this note bounds
- `src/render.cyr` — `render_ctrl_substitute`
