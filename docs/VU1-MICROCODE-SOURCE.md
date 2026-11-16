# Where GT4 Keeps Its VU1 Microcode

2026-10-14, slice 151.

## Confirmed

The whole VU1 microcode of GT4 USA v2.00 is one static image stored
XOR-encrypted inside the executable.

- Location: `SCUS_973.28` reconstructed ELF (pinned in `docs/inputs`), file
  offset `0x525DD0`, length `0x3FF0` bytes (VU1 code address 0 upward).
- Keystream (from Nenkai's `gt-modding-hub` notes,
  `docs/ps2/reverse_engineering_notes.md`, documented there for GT3 EU and GT4
  Online): `state = 0x32277070`; for each byte `i` from the blob start,
  `state = 0x5D588B65 * state + 1 (mod 2^32)`, `plain[i] = enc[i] ^ (state & 0xFF)`.
- Control: all 86 VU1 snapshots recorded in two owner sessions (slice 151) are a
  single identical 16 KiB image. That image equals the decrypted blob at every
  instruction except `0x3FF0` and `0x3FF8`, which lie beyond the stored blob
  length. All 86 recorded entry windows match.

Earlier byte searches of the ISO, ELF and all 18,352 decoded GT4.VOL files
found nothing because the stored bytes are encrypted.

## Consequences

- The VU1 program set is closed and known statically: every program is an
  entry point into this one image. AOT coverage no longer depends on gameplay
  recording; recording only helps confirm which entry points are used.
- Remaining work for full coverage: enumerate entry points statically (MSCAL
  targets in EE code and VIF streams, program boundaries after E-bit, jump
  targets) and confirm the content of the last two instructions.
- Hypothesis: the VU0 microcode is a separate, unencrypted blob (Nenkai lists one
  for GT4 Online, size `0x920`); not yet located in USA v2.00.

## SCAJ-30007 Traditional Chinese

The pinned CHT ELF stores the same-sized encrypted VU1 blob at file offset
`0x51E290`, with the keystream above. Two live 16 KiB snapshots agreed on the
entire image, including the last two instructions, which are zero. The CHT
image has SHA-256 `9e5bc86098904fa8a4bd82fdea0872d5b1d8220269471014dd4630c46796cdff`.

Extract it with `scripts/cht_vu1_image.py <CHT ELF> <new image file>`, and
generate the entry list with `scripts/vu1_image.py entries --policy all
--image <image> --out <new list>`. Run the upstream emitter with
`--image <image> --entries <list> --entry-policy all --programs-per-file 16
<new generated directory>`. Prepare the upstream runtime using
`scripts/prepare_perf_runtime.py <new private runtime directory> --split-vu
--vu1-aot`. Pass the generated directory as `GT4_VU1_GENERATED_DIR` and the
prepared runtime as `GT4_CHT_VU1_RUNTIME_SOURCE` in the CHT native build.
This retains the upstream runtime's live identity checks and interpreter
fallback for any unmatched program.
