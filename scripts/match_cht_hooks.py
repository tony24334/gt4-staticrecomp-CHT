"""Rank SCAJ-30007 functions against qualified v2.00 MIPS functions.

This is a research aid: it never edits either ELF.  Direct jump targets and
PC-relative branch displacements are normalized, while opcode/register fields
and ordinary immediates remain significant.  A candidate still requires a
translated-unit review before it may enter game_target.hpp.
"""

import argparse
import struct
from pathlib import Path


FUNCTIONS = {
    "init_monitor": (0x00388A80, 0x180),
    "race_display_render": (0x0039F498, 0x240),
    "camera_yaw_spring": (0x00345658, 0x100),
    "fov_projection": (0x0037A170, 0xB0),
    "analog_loop": (0x0043BBC0, 0x400),
    "menu_overlay": (0x00214FB0, 0x220),
    "strobe_overlay": (0x003EC0B0, 0x1A0),
    "render_world": (0x0033DEA8, 0x240),
    "text_style": (0x00490290, 0x130),
    "pad_setup": (0x00551810, 0x200),
}


def segments(blob):
    if blob[:4] != b"\x7fELF" or blob[4] != 1 or blob[5] != 1:
        raise ValueError("expected a little-endian ELF32")
    phoff, = struct.unpack_from("<I", blob, 28)
    phentsize, phnum = struct.unpack_from("<HH", blob, 42)
    out = []
    for index in range(phnum):
        off = phoff + index * phentsize
        kind, file_off, va, _, file_size, _, flags = struct.unpack_from("<IIIIIII", blob, off)
        if kind == 1 and file_size and flags & 1:
            out.append((va, blob[file_off:file_off + file_size]))
    return out


def read_va(parts, address, size):
    for va, data in parts:
        offset = address - va
        if 0 <= offset and offset + size <= len(data):
            return data[offset:offset + size]
    raise ValueError(f"VA 0x{address:08X} is outside executable segments")


def norm(word):
    op = word >> 26
    if op in (2, 3):                    # j / jal: target is image-specific
        return word & 0xFC000000
    if op in (1, 4, 5, 6, 7, 20, 21, 22, 23):  # PC-relative branches
        return word & 0xFFFF0000
    return word


def words(data):
    return [norm(word) for word in struct.unpack(f"<{len(data) // 4}I", data)]


def score(reference, candidate):
    return sum(a == b for a, b in zip(reference, candidate)) / len(reference)


def rank(reference_parts, target_parts, address, size, limit=8):
    ref = words(read_va(reference_parts, address, size))
    ranked = []
    for va, data in target_parts:
        target = words(data)
        width = len(ref)
        for index in range(0, len(target) - width + 1):
            value = score(ref, target[index:index + width])
            if len(ranked) < limit or value > ranked[0][0]:
                ranked.append((value, va + index * 4))
                ranked.sort()
                if len(ranked) > limit:
                    ranked.pop(0)
    return list(reversed(ranked))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("v200", type=Path)
    parser.add_argument("cht", type=Path)
    parser.add_argument("names", nargs="*", choices=sorted(FUNCTIONS))
    args = parser.parse_args()
    ref = segments(args.v200.read_bytes())
    target = segments(args.cht.read_bytes())
    selected = args.names or FUNCTIONS
    for name in selected:
        address, size = FUNCTIONS[name]
        print(name)
        for value, candidate in rank(ref, target, address, size):
            print(f"  0x{candidate:08X} {value:.3f}")


if __name__ == "__main__":
    main()
