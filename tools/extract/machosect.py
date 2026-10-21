#!/usr/bin/env python3
"""Dump one Mach-O section from a file on disk.

    machosect.py <binary> <segment> <section> [--strings]

Thin, 64-bit, little-endian Mach-O only; run `lipo -thin arm64e` first.
`--strings` splits the section on NUL and prints the non-empty pieces, which
is what you want for __objc_classname, __objc_methname and __cstring.

Use dscstrings.py instead for images that live in the dyld shared cache.
"""
import signal
import struct
import sys

# Output is meant to be piped into head/grep; die quietly when they close it.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

LC_SEGMENT_64 = 0x19
MH_MAGIC_64 = 0xFEEDFACF
FAT_MAGICS = (0xCAFEBABE, 0xBEBAFECA, 0xCAFEBABF, 0xBFBAFECA)


def sections(path):
    """Map (segment, section) -> (file offset, size, vmaddr)."""
    data = open(path, "rb").read()
    (magic,) = struct.unpack_from("<I", data, 0)
    if magic in FAT_MAGICS:
        raise SystemExit("universal binary: run `lipo -thin <arch>` first")
    if magic != MH_MAGIC_64:
        raise SystemExit("not a thin 64-bit little-endian Mach-O (magic %#x)" % magic)

    (ncmds,) = struct.unpack_from("<I", data, 16)
    off = 32
    found = {}
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, off)
        if cmd == LC_SEGMENT_64:
            segname = data[off + 8 : off + 24].rstrip(b"\0").decode()
            (nsects,) = struct.unpack_from("<I", data, off + 64)
            so = off + 72
            for _ in range(nsects):
                sectname = data[so : so + 16].rstrip(b"\0").decode()
                addr, size = struct.unpack_from("<QQ", data, so + 32)
                (fileoff,) = struct.unpack_from("<I", data, so + 48)
                found[(segname, sectname)] = (fileoff, size, addr)
                so += 80
        off += cmdsize
    return data, found


def main(argv):
    if len(argv) < 4:
        raise SystemExit(__doc__)
    path, seg, sect = argv[1:4]
    data, found = sections(path)
    if (seg, sect) not in found:
        raise SystemExit(
            "no %s,%s; this binary has:\n  %s"
            % (seg, sect, "\n  ".join("%s,%s" % k for k in sorted(found)))
        )
    fileoff, size, _ = found[(seg, sect)]
    blob = data[fileoff : fileoff + size]
    if "--strings" in argv:
        for piece in blob.split(b"\0"):
            if piece:
                sys.stdout.write(piece.decode("utf-8", "replace") + "\n")
    else:
        sys.stdout.buffer.write(blob)


if __name__ == "__main__":
    main(sys.argv)
