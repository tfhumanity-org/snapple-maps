#!/usr/bin/env python3
"""Print the string literals of an image that lives in the dyld shared cache.

    dscstrings.py <image-path> [segment] [section]

Most of the Maps stack (GeoServices, VectorKit, MapsUI, Navigation, MapKit,
MapsSupport) has no standalone binary on disk: the path under
/System/Library/PrivateFrameworks is a dangling symlink into the shared cache,
so `strings` and `otool` return nothing. Apple's own /usr/bin/dyld_info does
resolve those paths, and its `-section` mode prints one `0xADDR "literal"` per
line. This wraps it and gives you just the literals.

Defaults to __TEXT,__cstring. Note that the cache coalesces Objective-C name
sections across images, so __objc_classname usually comes back empty for a
cache-resident image; __cstring does not.
"""
import re
import signal
import subprocess
import sys

# Output is meant to be piped into head/grep; die quietly when they close it.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

LINE = re.compile(r'^0x[0-9A-Fa-f]+ "(.*)"\s*$')


def literals(image, segment="__TEXT", section="__cstring"):
    proc = subprocess.run(
        ["dyld_info", "-section", segment, section, image],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if proc.returncode != 0 and not proc.stdout:
        raise SystemExit("dyld_info failed: %s" % proc.stderr.strip())
    for line in proc.stdout.splitlines():
        m = LINE.match(line)
        if m:
            yield m.group(1)


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    image = argv[1]
    segment = argv[2] if len(argv) > 2 else "__TEXT"
    section = argv[3] if len(argv) > 3 else "__cstring"
    out = sys.stdout.buffer
    for lit in literals(image, segment, section):
        out.write(lit.encode("utf-8", "replace") + b"\n")


if __name__ == "__main__":
    main(sys.argv)
