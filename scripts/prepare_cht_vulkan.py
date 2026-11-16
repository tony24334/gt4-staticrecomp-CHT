"""Derive the GS stream sources for the SCAJ-30007 native candidate."""

import argparse
from pathlib import Path

from prepare_external_vulkan import ROOT, prepare
from prepare_perf_runtime import GS_STREAM_PATCHES


def derive(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f"Donor source does not match GS stream anchor: {before!r}")
    return source.replace(before, after, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    prepare(output, gs_stream=True)
    runtime = ROOT / "private/references/ps2-web-recomp/runtime/src"
    prefix = '#include "gs_stream_client.hpp"\n'
    gif = (runtime / "gs/gif.cpp").read_text(encoding="utf-8")
    for before, after in GS_STREAM_PATCHES["gif.cpp"]:
        before = before.replace("    gt4::mtvu::note_render(path, data, qwc);\n", "")
        after = after.replace("    gt4::mtvu::note_render(path, data, qwc);\n", "")
        after = after.replace(" || gt4::mtvu::signal_pre_applied(path, address)", "")
        gif = derive(gif, before, after)
    (output / "gif.cpp").write_text(prefix + gif, encoding="utf-8")
    hardware = (runtime / "hw.cpp").read_text(encoding="utf-8")
    (output / "hw.cpp").write_text(prefix + derive(hardware, *GS_STREAM_PATCHES["hw.cpp"][0]),
                                   encoding="utf-8")


if __name__ == "__main__":
    main()
