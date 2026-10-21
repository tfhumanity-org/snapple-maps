# AGENTS.md

You are an agent reading **snapple-maps**: a clean-room functional spec of the
Apple Maps client stack (`spec/`), plus the tooling that extracts the evidence
behind it (`tools/extract/`).

## What you are probably here to do

**Answer a question about how Apple Maps works.**

1. Start at [`spec/INDEX.md`](spec/INDEX.md), use its architecture picture and
   file map to pick one file.
2. Grep inside that file rather than reading all of it.
3. Quote the requirement ID and its confidence marker. An **inferred**
   requirement is not evidence for a load-bearing claim; say so when you lean on
   one.

**Extend the spec.** Run `./tools/extract/extract.sh`, work in
`.extracted/<build>/`, and write findings into the relevant `spec/` file in your
own words. Read [`CLEANROOM.md`](CLEANROOM.md) first — it is a rule set, not a
preamble.

**Fill a known gap.** `spec/INDEX.md` ends with what is deliberately absent. The
largest is rendering *algorithms* — `spec/09` covers the renderer's structure but
not tessellation, the label collision test, the camera controller or draping.
Transit is the second largest.

**Compare two builds.** Extract both, diff the string corpora and the metadata,
and write `spec/CHANGES-<old>-to-<new>.md`. This has not been done; the current
spec reads one build.

## Layout

```
spec/INDEX.md          architecture picture, patterns P01–P14, file map
spec/00–09             functional specs
CLEANROOM.md           what crosses the wall; read before writing spec/
EXPLORE.md             how to unpack your own copy, search anchors, ground rules
tools/extract/         extract.sh plus three Python helpers
guide/                 practical advice; not written yet
.extracted/            extraction output (gitignored, never committed)
```

## Rules

1. **Cite everything.**
   - A spec requirement: `04#R12`. A takeaway: `02#T5`. A pattern: `P07`.
   - Evidence in an extraction: the corpus file and what you matched, never an
     offset or an address.
   - Code in a target project: `path:line`.

2. **Confidence is part of the claim.** Every requirement is marked
   **observed** (read directly out of a shipped artifact), **derived**
   (several observations plus stated reasoning) or **inferred** (a reading that
   fits). Carry the marker when you carry the claim.

3. **Static only.** Nothing in `spec/` was observed at runtime. Do not write a
   requirement that asserts runtime behaviour, and do not let pseudocode imply
   you watched it execute — several algorithm sections are explicitly
   reconstructions and say so.

4. **Never add to `spec/`:** decompiler output, verbatim strings, offsets or
   addresses, internal build paths, internal source file names, internal
   codenames, telemetry event names, or unreleased-product details.
   **Do keep:** URL grammar, hosts, header names, Mach service and launchd
   names, entitlements, configuration keys, file formats, numeric thresholds,
   and linker-visible class names where they carry architectural meaning.
   `CLEANROOM.md` explains why that last one is an adaptation.

5. **Never commit `.extracted/` or private notes.** Both are gitignored. Keep it
   that way.

6. **If you write a reimplementation, you may not read this repo's evidence.**
   The clean side gets `spec/` and nothing else — not `.extracted/`, not the
   installed app. That is the only part of the wall that still matters, because
   nothing has been built on the clean side yet.

7. **Versions.** The reference is Maps `2972.20.6.12.47` on macOS 27.0.1
   (`26A434`), arm64e, captured October 2026. If you extract a different build,
   say so in whatever you write; do not silently update a requirement that was
   observed against this one.

## Working on this repo

- Spec files keep the same structure: **1** Purpose & scope · **2** Concepts ·
  **3** Requirements (`R-nn`, MUST/SHOULD, confidence) · **4** Algorithms ·
  **5** Constants · **6** Rationale · **7** Design takeaways (numbered) ·
  **8** Uncertainties.
- Keep requirement, takeaway and pattern numbering stable — other files cite it.
  Append; never renumber.
- A new spec file goes in `spec/INDEX.md`'s file map and, if it adds a pattern,
  its pattern table.
- The uncertainties section is not a formality. If you resolve one, delete it
  and add the requirement. If you add a requirement you are unsure of, add the
  uncertainty.
