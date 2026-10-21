# guide/ — not written yet

This directory is empty on purpose, and this file says what belongs in it rather
than pretending it already does.

The spec is written for someone asking *how does Apple Maps work*. A guide would
be written for someone with a job to do, with every tip citing the requirement
behind it — the way `spec/` files cite each other (`04#R12`, `02#T5`, `P07`).

Three audiences are worth writing for, in this order:

## 1. Building a mapping or location feature

The best-supported chapter, because the specs are already full of transferable
design decisions. The fourteen patterns in [`spec/INDEX.md`](../spec/INDEX.md)
and the takeaways at the end of each spec file are the raw material. Likely
chapters:

- **Addressing and caching map data** — one key type for everything, fixed-width
  unions, reference-counted local copies, version domains (`P04`–`P06`, `02#T1`–`T9`).
- **Server-driven clients** — ship shapes not content, and the fallback
  discipline that makes it survivable (`P08`, `03#T1`–`T2`, `04#T4`).
- **Location privacy that actually holds** — why grid snapping alone leaks, and
  the two corrections (`P12`, `07#T4`–`T6`).
- **Splitting an app across daemons** — matching state lifetime to process
  lifetime (`P09`, `00#T1`–`T3`).
- **Configuration and rollout** — layered sources, expiring cohorts, a single
  hard-coded URL (`P01`–`P03`, `01#T1`–`T7`).

## 2. Integrating with Maps from another app

What `spec/08` describes, turned into practice: the URL grammar and its traps,
which parameters are stable and which are clearly internal, App Intents versus
URLs, document types, and what the Maps-only entitlements mean for what a
third-party app can reach (`00#R19`).

## 3. Reverse-engineering a system framework on macOS

What [`EXPLORE.md`](../EXPLORE.md) covers, written as method rather than
reference: the two kinds of target, reading Objective-C type encodings for
struct layouts, using shipped resource directories before touching a
disassembler, and ranking a binary's dependencies in one command.

---

Contributions welcome. The constraint on anything written here is the same one
`spec/` lives under: cite the requirement, carry its confidence marker, and do
not promote an **inferred** requirement into advice without saying so.
