"""Derive the existing license-demo mitigation for the verified CHT runtime."""

import argparse
import hashlib
import json
from pathlib import Path

import prepare_cht_crash_trace as trace
import prepare_license_guard as guard

DISPATCH_SHA256 = "691c1d045b928ef789338f0954ec820fc0fd4e938cd2b2940743b3ad6005f995"
PROFILE = "cht-license-guard-v1"
ASPECT_PROFILE = "cht-license-guard+display-aspect-v1"
FULL_PROFILE = "cht-license-guard+display-aspect+frame-skip-v1"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def derive(source, diagnostic=False, display_aspect=False, frame_skip=False):
    # Keep the shared CRC/layout predicate and mutation rule exactly as on US.
    base = trace.derive("dispatch.cpp", source) if diagnostic else source
    result = guard.apply_license_guard(base)
    if display_aspect:
        result = guard.apply_display_aspect(result)
    if frame_skip:
        if not display_aspect:
            raise ValueError("frame skip requires the display-aspect dispatch hook")
        result = guard.apply_frame_skip(result)
    return result


def prepare(donor, output, diagnostic=False, display_aspect=False, frame_skip=False):
    raw = (donor / "runtime/src/dispatch.cpp").read_bytes()
    if sha256(raw) != DISPATCH_SHA256:
        raise ValueError("Pinned donor mismatch: dispatch.cpp")
    source = raw.decode("utf-8").replace("\r\n", "\n")
    result = derive(source, diagnostic, display_aspect, frame_skip).encode("utf-8")
    receipt = {
        "profile": FULL_PROFILE if frame_skip else ASPECT_PROFILE if display_aspect else PROFILE,
        "diagnostic": diagnostic,
        "donor_dispatch_sha256": DISPATCH_SHA256,
        "guard_overlay_sha256": sha256(guard.GUARD_OVERLAY_PATH.read_bytes()),
        "dispatch_sha256": sha256(result),
    }
    if display_aspect:
        receipt["display_aspect_overlay_sha256"] = sha256(guard.ASPECT_OVERLAY_PATH.read_bytes())
    if frame_skip:
        receipt["frame_skip_overlay_sha256"] = sha256(guard.FRAME_SKIP_OVERLAY_PATH.read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    (output / "dispatch.cpp").write_bytes(result)
    (output / "runtime.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--display-aspect", action="store_true")
    parser.add_argument("--frame-skip", action="store_true")
    args = parser.parse_args()
    prepare(args.donor, args.output, args.diagnostic, args.display_aspect, args.frame_skip)


if __name__ == "__main__":
    main()
