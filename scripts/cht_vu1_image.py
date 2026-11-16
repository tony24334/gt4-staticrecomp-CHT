"""Extract the verified SCAJ-30007 VU1 image from its reconstructed ELF."""

import argparse
import hashlib
import json
from pathlib import Path

from vu1_image import BLOB_BYTES, IMAGE_BYTES, ROOT, decrypt_blob

ELF_OFFSET = 0x51E290
IMAGE_SHA256 = "9e5bc86098904fa8a4bd82fdea0872d5b1d8220269471014dd4630c46796cdff"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    pins = json.loads((ROOT / "docs/inputs/cht-scaj-30007-native.json").read_text(encoding="utf-8"))
    elf = args.elf.read_bytes()
    if len(elf) != pins["native_elf_size"] or hashlib.sha256(elf).hexdigest() != pins["native_elf_sha256"]:
        parser.error("ELF differs from the pinned SCAJ-30007 reconstruction")
    # The last two VU1 instructions are zero in the captured CHT runtime image.
    image = decrypt_blob(elf[ELF_OFFSET:ELF_OFFSET + BLOB_BYTES]) + bytes(IMAGE_BYTES - BLOB_BYTES)
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        parser.error("extracted VU1 image differs from the captured CHT runtime image")
    with args.output.open("xb") as output:
        output.write(image)


if __name__ == "__main__":
    main()
