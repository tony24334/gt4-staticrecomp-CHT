"""Reconstruct an experimental EE ELF from the verified SCAJ-30007 CORE.GT4."""

import argparse
from hashlib import sha256
from pathlib import Path
import struct
import zlib

from spec2_beta_elf import R5900_FLAGS, parse_container


CORE_SIZE = 2_005_087
CORE_SHA256 = "3e9bcd6312dfcd10d854d32f0f1cc72b9c107e78223edf1d2279655a8a890226"
PAYLOAD_SIZE = 6_078_900
# This is the retail USA ELF's zero-fill policy. The CHT loader still needs validation.
DATA_ZERO_FILL = 8 * 1024 * 1024


def reconstruct(core):
    if len(core) != CORE_SIZE or sha256(core).hexdigest() != CORE_SHA256:
        raise ValueError("unexpected SCAJ-30007 CORE.GT4 identity")

    decoder = zlib.decompressobj(-15)
    payload = decoder.decompress(core[6:], PAYLOAD_SIZE + 1)
    # This pinned CORE declares the USA length and contains eight bytes after DEFLATE.
    if (len(payload) != PAYLOAD_SIZE or not decoder.eof or
            len(decoder.unused_data) != 8 or decoder.unconsumed_tail):
        raise ValueError("unexpected SCAJ-30007 DEFLATE layout")
    _, entry, (reginfo, text, data) = parse_container(payload)

    text_offset = 0x1000
    text_end = text["address"] + text["size"]
    reginfo_offset = text_offset + text["size"]
    reginfo_end = reginfo_offset + reginfo["size"]
    # ELF PT_LOAD requires the file offset and virtual address to agree modulo alignment.
    data_offset = reginfo_end + (data["address"] - reginfo_end) % 0x1000
    parts = [
        (1, text_offset, text["address"], text, 0, 7, 0x1000),
        (0x70000000, reginfo_offset, text_end, reginfo, 0, 4, 4),
        (1, data_offset, data["address"], data, DATA_ZERO_FILL, 6, 0x1000),
    ]
    output = bytearray(data_offset + data["size"])
    output[:7] = b"\x7fELF\x01\x01\x01"
    struct.pack_into("<HHIIIIIHHHHHH", output, 16, 2, 8, 1, entry, 52, 0, R5900_FLAGS,
                     52, 32, len(parts), 0, 0, 0)
    for index, (kind, offset, address, record, zero_fill, flags, alignment) in enumerate(parts):
        size = record["size"]
        struct.pack_into("<8I", output, 52 + 32 * index, kind, offset, address, address,
                         size, size + zero_fill, flags, alignment)
        output[offset:offset + size] = record["body"]
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso", type=Path)
    parser.add_argument("output", type=Path, help="new path for the experimental ELF")
    args = parser.parse_args()

    import pycdlib

    iso = pycdlib.PyCdlib()
    iso.open(str(args.iso))
    try:
        with iso.open_file_from_iso(iso_path="/CORE.GT4;1") as stream:
            elf = reconstruct(stream.read(CORE_SIZE + 1))
    finally:
        iso.close()
    with args.output.open("xb") as stream:
        stream.write(elf)
    print(f"{len(elf)} bytes, SHA-256 {sha256(elf).hexdigest()}")


if __name__ == "__main__":
    main()
