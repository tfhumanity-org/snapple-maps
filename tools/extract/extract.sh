#!/bin/bash
# Collect your own installed copy of the Maps stack into ./.extracted/ (gitignored).
#
# Read-only: everything here copies, thins or parses files. Nothing is launched,
# patched or sent anywhere. Check that this is permitted for you under the terms
# you agreed to, and don't redistribute what you extract.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ARCH="${ARCH:-$(uname -m | sed 's/^arm64$/arm64e/')}"

APP=/System/Applications/Maps.app
if [ ! -d "$APP" ]; then
  echo "Maps.app not found at $APP" >&2
  exit 1
fi

VER="$(/usr/bin/defaults read "$APP/Contents/Info.plist" CFBundleVersion)"
OS="$(sw_vers -productVersion)-$(sw_vers -buildVersion)"
OUT="$ROOT/.extracted/maps-$VER-macos-$OS"
mkdir -p "$OUT/bin" "$OUT/strings" "$OUT/meta"
echo "Maps $VER on macOS $OS ($ARCH) -> $OUT"

# ---------------------------------------------------------------- on-disk code
# The app and the Maps daemons are real files. Thin them so the Mach-O tools and
# any disassembler see a single architecture.
thin() {
  local src="$1" name
  name="$(basename "$src")"
  [ -f "$src" ] || { echo "  (absent) $src"; return 0; }
  cp "$src" "$OUT/bin/$name.fat"
  lipo -thin "$ARCH" "$OUT/bin/$name.fat" -output "$OUT/bin/$name" 2>/dev/null \
    || mv "$OUT/bin/$name.fat" "$OUT/bin/$name"
  rm -f "${OUT:?}/bin/${name:?}.fat"
  printf "  %10d  %s\n" "$(stat -f%z "$OUT/bin/$name")" "$name"
}

echo "on-disk binaries:"
thin "$APP/Contents/MacOS/Maps"
thin /System/Library/CoreServices/navd
thin /System/Library/CoreServices/destinationd
thin /System/Library/CoreServices/mapspushd
thin /System/Library/PrivateFrameworks/MapsSync.framework/mapssyncd
thin /System/Library/PrivateFrameworks/GeoAnalytics.framework/geoanalyticsd
thin /System/Library/PrivateFrameworks/GeoServices.framework/geodMachServiceBridge
thin /System/Library/PrivateFrameworks/GeoServices.framework/Versions/A/XPCServices/com.apple.geod.xpc/Contents/MacOS/com.apple.geod

# -------------------------------------------------------------- cache-resident
# These frameworks exist only inside the dyld shared cache. dyld_info can still
# read their sections; dscstrings.py turns that into one literal per line.
echo "shared-cache string literals:"
for fw in GeoServices VectorKit MapsSupport Navigation GeoKit GeoServicesCore; do
  path=/System/Library/PrivateFrameworks/$fw.framework/$fw
  if python3 -I "$HERE/dscstrings.py" "$path" > "$OUT/strings/$fw.txt" 2>/dev/null \
     && [ -s "$OUT/strings/$fw.txt" ]; then
    printf "  %10d  %s\n" "$(wc -l < "$OUT/strings/$fw.txt")" "$fw.txt"
  else
    rm -f "$OUT/strings/$fw.txt"
    echo "  (no literals) $fw"
  fi
done
for fw in MapKit MapsUI; do
  for base in /System/Library/Frameworks /System/iOSSupport/System/Library/Frameworks \
              /System/iOSSupport/System/Library/PrivateFrameworks; do
    path=$base/$fw.framework/$fw
    # -e is false for the dangling symlink a cache-resident framework leaves
    # behind, so test for the link itself as well.
    [ -e "$path" ] || [ -L "$path" ] || continue
    if python3 -I "$HERE/dscstrings.py" "$path" > "$OUT/strings/$fw.txt" 2>/dev/null \
       && [ -s "$OUT/strings/$fw.txt" ]; then
      printf "  %10d  %s\n" "$(wc -l < "$OUT/strings/$fw.txt")" "$fw.txt"
      break
    fi
    rm -f "$OUT/strings/$fw.txt"
  done
done

# -------------------------------------------------------------------- metadata
echo "metadata:"
codesign -d --entitlements - --xml "$APP/Contents/MacOS/Maps" 2>/dev/null \
  | plutil -convert json -o "$OUT/meta/entitlements.json" - || true
plutil -convert json -o "$OUT/meta/Info.json" "$APP/Contents/Info.plist"
cp "$APP/Contents/Resources/Metadata.appintents/extract.actionsdata" \
   "$OUT/meta/appintents.json" 2>/dev/null || true
python3 -I "$HERE/objcimports.py" "$OUT/bin/Maps" > "$OUT/meta/maps-imports.txt"
python3 -I "$HERE/machosect.py" "$OUT/bin/Maps" __TEXT __objc_classname --strings \
  | sort -u > "$OUT/meta/maps-classnames.txt"
python3 -I "$HERE/machosect.py" "$OUT/bin/Maps" __TEXT __objc_methname --strings \
  | sort -u > "$OUT/meta/maps-selectors.txt"
for f in entitlements.json Info.json appintents.json maps-imports.txt \
         maps-classnames.txt maps-selectors.txt; do
  [ -f "$OUT/meta/$f" ] && printf "  %10d  %s\n" "$(stat -f%z "$OUT/meta/$f")" "$f"
done

echo
echo "done. See EXPLORE.md for search anchors and ground rules."
