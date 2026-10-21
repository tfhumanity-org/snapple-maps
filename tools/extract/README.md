# tools/extract

Collects your own installed copy of the Maps stack into `.extracted/`
(gitignored). Read-only: everything here copies, thins or parses. Nothing is
launched, patched or sent anywhere.

```bash
./tools/extract/extract.sh
```

Runs in about a second. Set `ARCH` to override the architecture (defaults to
this machine's, mapping `arm64` to `arm64e`).

## Output

```
.extracted/maps-<version>-macos-<os>-<build>/
  bin/        Maps, navd, destinationd, mapspushd, mapssyncd,
              geoanalyticsd, geodMachServiceBridge, com.apple.geod
              — thinned to one architecture
  strings/    GeoServices, VectorKit, MapsSupport, Navigation, GeoKit,
              GeoServicesCore, MapKit, MapsUI — one literal per line
  meta/       entitlements.json, Info.json, appintents.json,
              maps-imports.txt, maps-classnames.txt, maps-selectors.txt
```

Rough sizes on the reference build: the app binary is about 25 MB thinned, the
GeoServices corpus about 26,000 literals, the VectorKit corpus about 21,000, and
the selector list about 1.3 MB.

## The scripts

### `extract.sh`

Orchestrates everything. Two things in it are worth knowing:

- It thins every binary with `lipo` before anything else touches it. Most
  Mach-O tooling, and every disassembler, wants one architecture.
- It tests cache-resident framework paths with `[ -e ] || [ -L ]`. A framework
  that lives in the dyld shared cache leaves a *dangling* symlink on disk, so
  `-e` alone is false and the framework is silently skipped. This cost an
  hour the first time.

### `dscstrings.py`

Prints the string literals of an image inside the dyld shared cache.

```bash
python3 -I tools/extract/dscstrings.py \
  /System/Library/PrivateFrameworks/GeoServices.framework/GeoServices
python3 -I tools/extract/dscstrings.py <image> __TEXT __objc_methname
```

Most of the Maps stack has no standalone binary on disk, so `strings` and
`otool` return nothing. Apple's `/usr/bin/dyld_info` resolves those paths and
its `-section` mode prints `0xADDR "literal"` per line; this keeps the literal
and discards the address.

Caveat: the cache coalesces Objective-C name sections across images, so
`__objc_classname` comes back empty for a cache-resident image. `__cstring`
does not.

### `machosect.py`

Dumps one section from a real file on disk, raw or split into strings.

```bash
python3 -I tools/extract/machosect.py .extracted/*/bin/Maps \
  __TEXT __objc_classname --strings
```

Parses `LC_SEGMENT_64` directly rather than shelling out, because `otool -s`
prints hex in word order and the obvious reassembly comes out byte-swapped.
Rejects fat binaries with a message telling you to `lipo -thin` first.

### `objcimports.py`

Groups the Objective-C classes a binary binds at load time by source library.

```bash
python3 -I tools/extract/objcimports.py .extracted/*/bin/Maps
python3 -I tools/extract/objcimports.py .extracted/*/bin/Maps --library GeoServices
```

Maps ships stripped, so its own class symbols are gone — but every class it
*imports* carries the dylib it came from. Counting them per library ranks the
dependencies exactly, with no disassembly. It is the cheapest useful thing in
this directory and it is where `spec/00` starts.

## Adding a target

Add a `thin` line in `extract.sh` for a binary on disk, or a framework name to
one of the two loops for a cache-resident one. If a framework yields no
literals, check whether its path is a dangling symlink before concluding it has
none.
