"""Derive opt-in SCAJ-30007 crash diagnostics without modifying pinned inputs."""
import argparse
import hashlib
import json
from pathlib import Path

PINS = {
    "kernel.cpp": "003c9e0a0e2c1cb61a6fd8ec846a4798c3027ed933b6825c6377112106f0168a",
    "dispatch.cpp": "691c1d045b928ef789338f0954ec820fc0fd4e938cd2b2940743b3ad6005f995",
}
INCLUDE = '#include "cht_crash_trace.hpp"\n'

def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"Expected exactly one diagnostic anchor: {before[:100]!r}")
    return text.replace(before, after, 1)


def patches(name):
    if name == "kernel.cpp":
        return [
            ("    ThreadContext saved;\n    save_context(c, saved);", "    gt4::cht_trace::interrupt_enter(c, address);\n    ThreadContext saved;\n    save_context(c, saved);"),
            ("    g_guest_calls.pop_back();\n", "    gt4::cht_trace::interrupt_exit(c, address);\n    g_guest_calls.pop_back();\n"),
            ("    load_context(c, saved);\n    c.cop0[12] = status;", "    load_context(c, saved);\n    c.cop0[12] = status;\n    gt4::cht_trace::restored(c, saved, status);"),
        ]
    if name == "dispatch.cpp":
        return [("        record_miss(pc);\n", "        gt4::cht_trace::dump(stderr);\n        record_miss(pc);\n")]
    if name == "unit_00A1.cpp":
        before = "    { const std::uint32_t t = c.r[3].w[0]; c.r[31].sd[0] = static_cast<std::int32_t>(0x0038798Cu);"
        return [("L_00387968:\n", "L_00387968:\n    gt4::cht_trace::entry(c);\n"),
                (before, before.replace("c.r[31]", "gt4::cht_trace::target(c, t); c.r[31]", 1))]
    raise ValueError(name)


def derive(name, source):
    text = source
    for before, after in patches(name):
        text = replace_once(text, before, after)
    return INCLUDE + text


def reverse(name, source):
    if not source.startswith(INCLUDE):
        raise ValueError("Missing diagnostic include")
    source = source[len(INCLUDE):]
    for before, after in reversed(patches(name)):
        source = replace_once(source, after, before)
    return source


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(donor, generated, output):
    inputs = {name: donor / "runtime/src" / name for name in PINS}
    inputs["unit_00A1.cpp"] = generated / "unit_00A1.cpp"
    result = {}
    hashes = {}
    for name, path in inputs.items():
        raw = path.read_bytes()
        if name in PINS and digest(raw) != PINS[name]:
            raise ValueError(f"Pinned donor mismatch: {name}")
        source = raw.decode("utf-8").replace("\r\n", "\n")
        patched = derive(name, source)
        if reverse(name, patched) != source:
            raise ValueError(f"Diagnostic patch reversal failed: {name}")
        result[name] = patched.encode("utf-8")
        hashes[name] = digest(raw)
    result["units.hpp"] = (generated / "units.hpp").read_bytes()
    receipt = {"profile": "cht-crash-trace-v1", "input_sha256": hashes,
               "source_sha256": {name: digest(data) for name, data in result.items()},
               "archive_member": "ee-unit_00A1.o"}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in result.items():
        (output / name).write_bytes(data)
    (output / "runtime.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.donor, args.generated, args.output)


if __name__ == "__main__":
    main()
