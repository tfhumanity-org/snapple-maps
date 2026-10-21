# Clean-room process

This repo publishes **behavioural specifications** of Apple Maps. It does not
publish Apple's code, decompiler output, or extracted resources. This file
records what was looked at, what crossed into `spec/`, and where the line sits.

```
Installed macOS copy ──(local extraction, never committed)──► analysis notes (private)
                                                                    │
                                        DIRTY SIDE: spec writers read the notes
                                                                    ▼
                                                       spec/  (paraphrased behaviour,
                                                               data shapes, constants,
                                                               own pseudocode)
                                                                    │
                                            ═══════ wall: only spec/ crosses ═══════
                                                                    ▼
                                            CLEAN SIDE: a reimplementation, when one
                                                        is written, sees only spec/
```

The wall matters even though nothing has been built on the clean side yet. A
reimplementation written later must be given `spec/` and nothing else — not the
`.extracted/` tree, not this machine's Maps install, not the string corpora.

## Participants and what they saw

| Stage | Participant | Saw | Did not see | Produced |
|---|---|---|---|---|
| Extraction & analysis | analysis agent (Oct 2026) | the locally installed Maps 2972.20.6.12.47 on macOS 27.0.1 | n/a | private analysis notes, `.extracted/` |
| Spec | same agent | those notes | n/a | `spec/` |
| Clean implementation | — | — | — | not yet written |

That single-agent column is weaker than a two-sided clean room and is stated
plainly rather than dressed up. See **Honest limits** below.

## Rules the spec obeys

**Never published:**

- Decompiler or disassembler output, in any amount.
- Verbatim user-facing strings, error messages, or localised text.
- File offsets, virtual addresses, segment addresses, or anything else that
  only means something against one build's bytes.
- Internal build paths and internal source file names.
- Internal codenames. Several map data sets and imagery products carry one in
  the shipped type names; the spec describes those by function instead and says
  where it has done so.
- Telemetry and analytics event names. The spec describes what the analytics
  pipeline collects and how it batches and uploads, not the catalogue of events.
- Unreleased-product details: unannounced features, flags for things that have
  not shipped.

**Kept, because it is the interface:**

- URL schemes, hosts, and query-parameter names.
- HTTP request header names and service endpoint paths.
- launchd labels, Mach service names, XPC service names, entitlement names,
  application-group and keychain-group identifiers.
- Preference and configuration key names.
- File format names and on-disk layout.
- Structure field widths and enumeration shapes where they define a format.
- Linker-visible Objective-C class names that a binary imports from a framework.

That last one is an **adaptation** of the reference methodology this repo
borrows from, and is called out rather than slipped in. In a minified
JavaScript bundle, identifiers are meaningless churn and reproducing them only
proves you read the bundle. Here they are stable, they are recorded in signed
system binaries, and they *are* the private API surface — a description of the
Maps architecture that refused to name them would be unfalsifiable. The spec
names them where they carry architectural meaning and does not list them
exhaustively for their own sake.

- Algorithms are written as the spec writer's own pseudocode, never transcribed.

## Confidence

Every requirement is marked:

- **observed** — read directly out of the shipped artifact (a string literal, a
  load command, a signed entitlement, a parsed plist or JSON resource).
- **derived** — follows from several observations put together, with the
  reasoning stated.
- **inferred** — a reading of the evidence that fits but is not pinned down.
  Do not build anything load-bearing on an inferred requirement alone.

Nothing here comes from running Maps and watching it work. Every requirement is
static evidence from a shipped artifact, so a behaviour that only appears at
runtime, behind a server flag, or in another region is invisible to this method
and the spec says so where it matters.

## Honest limits

- **One agent, both sides.** The extraction, the notes and `spec/` were all
  produced in one session. The wall described above is a rule for future work,
  not a claim about how this text was written. A clean-side reimplementation
  would need a fresh context given only `spec/`.
- **Procedural, not physical.** "Clean" would mean a fresh context restricted to
  a workspace containing `spec/`. It would not mean separate people on separate
  machines.
- **Copyright only.** A clean room is a defence against copyright claims on an
  implementation. It does not override terms of service, and it says nothing
  about trade secrets or patents.
- **Static, single build, single platform.** macOS only, arm64e only, one build,
  one day. Apple Maps on iOS, in CarPlay, and on watchOS share most of this
  stack but are not what was read.
- **Server-side behaviour is invisible.** Most of what makes Maps work happens
  on Apple's servers. This repo can describe what the client sends, what shapes
  it expects back, and how it is configured — not what decides the answers.
- **Not legal advice.** If you plan to rely on this commercially, get your own.
- **Unofficial.** Not affiliated with or endorsed by Apple. "Apple", "Apple
  Maps", "MapKit" and "CarPlay" are Apple trademarks, used here only to identify
  what was studied.
