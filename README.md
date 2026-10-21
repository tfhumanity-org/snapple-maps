# snapple-maps

**What Apple Maps looks like from the outside.** A clean-room functional spec of
the Maps client stack on macOS, written from static analysis of one shipped
build, plus the tooling to unpack your own copy and check the work.

Nothing proprietary is hosted here. Every tool in `tools/` reads *your* install.

## Start here: [`spec/INDEX.md`](spec/INDEX.md)

It opens with the architecture picture and the fourteen patterns worth stealing
(`P01`–`P18`), then points at ten spec files.

A taste:

- The app you click is thin. Six daemons behind it own everything with a
  lifetime longer than a window — which is why navigation survives the app
  being killed.
- One 128-bit tagged union addresses every kind of map data: tiles, 3D meshes,
  traffic, contour lines, a selected road. All fourteen variants are exactly
  120 bits wide, which is not an accident.
- Offline regions are reference-counted subscriptions over shared tile batches,
  not downloads. Two overlapping regions cost one copy, and "can I delete this
  tile" has an exact answer.
- Guidance arrives as format templates plus typed arguments. The server authors
  the sentence; the device formats the distances, durations and currencies. Every
  argument is required to carry a fallback string.
- Coarse location snaps to a grid, *merges cells in longitude above two latitude
  thresholds*, then randomises the representative point. Both of those exist
  because the naive version leaks.
- There is no single device identifier in the request path. There are six kinds,
  with different lifetimes, and the wire carries an identifier's *age* rather
  than its creation time.

## What's here

| Path | What |
|---|---|
| [`spec/INDEX.md`](spec/INDEX.md) | Architecture, patterns `P01`–`P18`, file map |
| `spec/00`–`09` | Ten functional specs: numbered requirements, confidence markers, pseudocode, constants, design takeaways, uncertainties |
| [`CLEANROOM.md`](CLEANROOM.md) | What was looked at, what crosses the wall, and the limits — read before citing |
| [`EXPLORE.md`](EXPLORE.md) | How to unpack your own copy and where to search |
| [`tools/extract/`](tools/extract/README.md) | The extraction pipeline. Runs in about a second |
| [`guide/`](guide/README.md) | Practical advice. Not written yet; scope is stated |

## Unpack your own copy

```bash
./tools/extract/extract.sh
```

Writes `.extracted/maps-<version>-macos-<os>/` (gitignored): the app binary and
six daemons, thinned to one architecture; string corpora for the eight
cache-resident frameworks; and parsed entitlements, Info.plist, App Intents
metadata and Objective-C metadata.

The interesting trick is in [`dscstrings.py`](tools/extract/dscstrings.py). Most
of the Maps stack has no file on disk — the path under `PrivateFrameworks` is a
dangling symlink into the dyld shared cache, so `strings` and `otool` return
nothing. Apple's own `dyld_info` resolves those paths anyway.

Then see [`EXPLORE.md`](EXPLORE.md) for search anchors and the ground rules.

## How this was built

Static analysis only. No instrumentation, no traffic interception, no running
Maps and watching it work. Every requirement in `spec/` is traceable to
something in a shipped artifact: a string literal, a load command, a signed
entitlement, a parsed resource.

That bounds what can be claimed, and the specs say so. Every requirement is
marked **observed**, **derived** or **inferred**, and every file ends with what
it could not establish.

## Caveats

- **Clean room, with one honest asterisk.** `spec/` contains no code,
  decompiler output, offsets or verbatim strings. But the extraction, the notes
  and the specs were produced in one session, so the wall described in
  [`CLEANROOM.md`](CLEANROOM.md) is a rule for future work rather than a claim
  about this text. No reimplementation has been written.
- **One build, one platform, one day.** Maps 3.0 (`2972.20.6.12.47`) on macOS
  27.0.1 (`26A434`), arm64e, 21 October 2026. iOS and CarPlay share most of this
  stack and were not read. Findings go stale fast.
- **The server is invisible.** Most of what makes Maps work happens at Apple.
  This describes what the client sends, what shapes it expects back, and how it
  is configured.
- **Rendering structure is covered; rendering algorithms are not.** `spec/09`
  specifies the data types, tile chapters, stylesheet format, style resolution,
  labels and the shader set. Tessellation, the collision test, the camera
  controller and draping are named and not specified.
- **Unofficial.** Not affiliated with or endorsed by Apple. "Apple", "Apple
  Maps", "MapKit" and "CarPlay" are Apple trademarks, used here only to identify
  what was studied.

If you find something, describe it in your own words and open a PR to `spec/`.
Don't paste code, decompiler output, or extracted strings.
