#!/usr/bin/env python3
"""Group the Objective-C classes a Mach-O binds at load time by source library.

    objcimports.py <binary> [--library NAME] [--counts]

Maps.app ships stripped, so its *own* class symbols are gone. The classes it
imports are not: every `_OBJC_CLASS_$_Name` the linker recorded carries the
dylib it came from. That list is the cleanest statement available of which
framework surface the app actually touches, without decompiling anything.

`--counts` prints one line per library with a count (the default).
`--library GeoServices` prints that library's class names instead.
"""
import re
import subprocess
import sys
from collections import Counter, defaultdict

ENTRY = re.compile(r"_OBJC_CLASS_\$_([A-Za-z0-9_]+).*\(from ([A-Za-z0-9_.+-]+)\)")


def imports(path):
    """Map library name -> sorted class names bound from it."""
    proc = subprocess.run(
        ["nm", "-m", path], capture_output=True, text=True, errors="replace"
    )
    by_lib = defaultdict(set)
    for line in proc.stdout.splitlines():
        if "undefined" not in line:
            continue
        m = ENTRY.search(line)
        if m:
            by_lib[m.group(2)].add(m.group(1))
    return {lib: sorted(names) for lib, names in by_lib.items()}


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    by_lib = imports(argv[1])
    if "--library" in argv:
        lib = argv[argv.index("--library") + 1]
        for name in by_lib.get(lib, []):
            print(name)
        return
    counts = Counter({lib: len(names) for lib, names in by_lib.items()})
    for lib, n in counts.most_common():
        print("%5d  %s" % (n, lib))


if __name__ == "__main__":
    main(sys.argv)
