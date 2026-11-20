"""Derive the existing license-demo mitigation for the verified CHT runtime."""

import argparse
import hashlib
import json
from pathlib import Path

import prepare_cht_crash_trace as trace
import prepare_license_guard as guard

DISPATCH_SHA256 = "691c1d045b928ef789338f0954ec820fc0fd4e938cd2b2940743b3ad6005f995"
PROFILE = "cht-license-guard-v1"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def derive(source, diagnostic=False):
    # Keep the shared CRC/layout predicate and mutation rule exactly as on US.
    base = trace.derive("dispatch.cpp", source) if diagnostic else source
    return guard.apply_license_guard(base)


def prepare(donor, output, diagnostic=False):
    raw = (donor / "runtime/src/dispatch.cpp").read_bytes()
    if sha256(raw) != DISPATCH_SHA256:
        raise ValueError("Pinned donor mismatch: dispatch.cpp")
    source = raw.decode("utf-8").replace("\r\n", "\n")
    result = derive(source, diagnostic).encode("utf-8")
    receipt = {
        "profile": PROFILE,
        "diagnostic": diagnostic,
        "donor_dispatch_sha256": DISPATCH_SHA256,
        "guard_overlay_sha256": sha256(guard.GUARD_OVERLAY_PATH.read_bytes()),
        "dispatch_sha256": sha256(result),
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "dispatch.cpp").write_bytes(result)
    (output / "runtime.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    prepare(args.donor, args.output, args.diagnostic)


if __name__ == "__main__":
    main()
