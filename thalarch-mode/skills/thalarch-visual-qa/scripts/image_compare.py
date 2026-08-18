#!/usr/bin/env python3
"""Optional pixel-level image comparison for Thalarch visual QA.

Requires Pillow for decoded pixel comparison. If Pillow is unavailable, exits
with code 2 and reports the comparison as unverified instead of installing a
runtime dependency silently.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two decoded images without modifying sources.")
    parser.add_argument("baseline")
    parser.add_argument("candidate")
    parser.add_argument("--out", help="Optional diff image path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("UNVERIFIED_PIXEL_COMPARE: Pillow is not installed. No dependency was installed automatically.")
        return 2

    a_path = Path(args.baseline).expanduser().resolve()
    b_path = Path(args.candidate).expanduser().resolve()
    if not a_path.is_file() or not b_path.is_file():
        raise SystemExit("Both baseline and candidate must exist.")

    with Image.open(a_path) as a_src, Image.open(b_path) as b_src:
        a = a_src.convert("RGBA")
        b = b_src.convert("RGBA")
        result = {
            "baseline": str(a_path),
            "candidate": str(b_path),
            "baseline_size": list(a.size),
            "candidate_size": list(b.size),
            "same_dimensions": a.size == b.size,
        }
        if a.size != b.size:
            result.update({"changed_pixels": None, "changed_fraction": None, "mean_channel_delta": None})
        else:
            diff = ImageChops.difference(a, b)
            bbox = diff.getbbox()
            total = a.size[0] * a.size[1]
            if bbox is None:
                changed = 0
                mean_delta = 0.0
            else:
                changed = 0
                channel_sum = 0
                for px in diff.getdata():
                    if px != (0, 0, 0, 0):
                        changed += 1
                    channel_sum += sum(px)
                mean_delta = channel_sum / (total * 4)
            result.update({
                "changed_pixels": changed,
                "changed_fraction": changed / total if total else 0.0,
                "mean_channel_delta": round(mean_delta, 6),
            })
            if args.out:
                out = Path(args.out).expanduser().resolve()
                out.parent.mkdir(parents=True, exist_ok=True)
                diff.save(out)
                result["diff_path"] = str(out)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
