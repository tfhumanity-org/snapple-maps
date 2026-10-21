# Explore it yourself

This repo never hosts Apple's code. If you have a Mac, you can unpack **your own
copy** and look around. The extraction is read-only: the scripts copy, thin and
parse files, and never run them. Check that this is permitted for you under the
terms you agreed to, and don't redistribute what you extract.

```bash
./tools/extract/extract.sh     # → ./.extracted/ (gitignored)
```

You get `.extracted/maps-<version>-macos-<os>-<build>/`:

- **`bin/`** — the app binary and six daemons, thinned to one architecture.
- **`strings/`** — one literal per line for each of eight frameworks that have
  no file on disk.
- **`meta/`** — parsed entitlements, `Info.plist`, App Intents metadata, the
  per-library import counts, and the app's Objective-C class names and
  selectors.

Format details are in [`tools/extract/README.md`](tools/extract/README.md).

## The two kinds of target

**Things that are files.** `Maps.app`, and the daemons `navd`, `destinationd`,
`mapspushd`, `mapssyncd`, `geoanalyticsd` and the geo service bridge. Ordinary
Mach-O tools work: `strings`, `otool`, `nm`, a disassembler.

**Things that are not.** GeoServices, VectorKit, MapKit, MapsUI, MapsSupport,
Navigation, GeoKit. The path under `PrivateFrameworks` is a symlink into the
dyld shared cache, and it dangles — `[ -e ]` is false for it, `strings` returns
nothing, `otool` errors. Apple's own `dyld_info` resolves it anyway:

```bash
dyld_info -segments /System/Library/PrivateFrameworks/GeoServices.framework/GeoServices
dyld_info -section __TEXT __cstring /System/Library/PrivateFrameworks/VectorKit.framework/VectorKit
```

`dscstrings.py` wraps the second of those. Note that the cache coalesces
Objective-C name sections across images, so `__objc_classname` comes back empty
for a cache-resident framework. `__cstring` does not, and in practice it carries
most of what you want: Swift type names, assertion text, protobuf field names,
configuration keys and endpoints.

## Good anchors

Identifiers here are *not* minified, which makes this much easier than unpacking
a JavaScript bundle. Search for meaning.

| To find | Search for |
|---|---|
| Service endpoints | `ls.apple.com`, `geo.apple.com` in the GeoServices corpus |
| The configuration layers | the five human-readable source names, near the endpoint block |
| Request headers | `X-Apple-Maps-` |
| Configuration keys | `^GEO[A-Z]` — about 440 of them |
| Wire message types | `GEOPB` |
| Protobuf field names | camelCase/snake_case pairs on adjacent lines — the pair *is* the tell |
| Struct layouts | Objective-C type encodings: lines with `{`, `=`, and runs of `b<digits>` |
| Swift module structure | `.swift` in the corpus (don't publish these) |
| Enum vocabularies | `SCREAMING_SNAKE_CASE` runs |
| IPC surface | the app's entitlements, especially the Mach lookup exceptions |
| Which framework matters | `objcimports.py` on the app binary |
| Sync record set | `MapsSyncManaged` in the `mapssyncd` binary |
| Daemon wiring | `/System/Library/Launch{Daemons,Agents}/*.plist` for the Maps labels |
| Tile contents | `^Chapter[A-Za-z]+$` in the VectorKit corpus — 64 of them |
| Tile payload kinds | `^(RASTER\|VECTOR\|FLYOVER)_` — the map data type enum |
| Renderer pipeline stages | `^[A-Za-z]+(Logic\|Module\|Graph)$` |
| Shader inventory | `^[A-Za-z]+Shader(Vertex\|Fragment)?$`, suffix-stripped |
| Binary format internals | the decoder's own failure strings — `Could not read`, `Could not decode`, `strange number of bits` |
| Shipped policy | the resource directories — they stay on disk even when the binary doesn't |

Two of those rows are underrated.

`GeoServices.framework/Versions/A/Resources/` contains the throttle policy for
every geo client on the system, as a readable property list with its own
explanatory comments. `VectorKit.framework/Versions/A/Resources/` contains the
ground-rendering settings as JSON, in day and night variants. No disassembly
required for either.

And a decoder's failure strings are the cheapest way to recover a binary
format. Every field the stylesheet decoder can fail to read has a message naming
it, so the error vocabulary enumerates the format — that is where most of
`spec/09`'s stylesheet section came from.

## Reading Objective-C type encodings

The highest-value structural evidence in the corpora. A line like

```
{_GEOExampleKey=b6b26b26b14b4b4}
```

declares a struct of bitfields with those widths. Sum them. Variants of a union
that all sum to the same width are a design constraint, and finding one tells
you the key is a fixed-size value — see `spec/02` for how far that goes.

## Ground rules if you publish findings

- **Describe behaviour. Don't paste code, decompiler output, or strings.** If a
  finding is worth sharing, open a PR to `spec/` written in your own words.
- **Mark your confidence.** Observed, derived, or inferred. Most of what feels
  obvious from a string corpus is inferred.
- **Don't publish offsets or addresses.** They mean nothing against another
  build and prove only that you read the bytes.
- **Don't publish unreleased-product details** you stumble on: unannounced
  features, flags for things that have not shipped.
- **Note the version.** Findings go stale fast.
