#!/usr/bin/env python3
"""Read-only image metadata probe used by Thalarch visual QA.

Uses only the Python standard library. Supports PNG, JPEG, GIF, and basic WebP
container inspection. Prints dimensions when they can be determined and reports
whether an alpha channel is explicitly present for formats where that can be
inferred safely.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def png_info(data: bytes):
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 33:
        return None
    width, height = struct.unpack(">II", data[16:24])
    color_type = data[25]
    alpha = color_type in (4, 6) or b"tRNS" in data
    return {"format": "PNG", "width": width, "height": height, "has_alpha": alpha}


def gif_info(data: bytes):
    if data[:6] not in (b"GIF87a", b"GIF89a") or len(data) < 10:
        return None
    width, height = struct.unpack("<HH", data[6:10])
    return {"format": "GIF", "width": width, "height": height, "has_alpha": "unknown"}


def jpeg_info(data: bytes):
    if not data.startswith(b"\xff\xd8"):
        return None
    i = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            break
        length = struct.unpack(">H", data[i:i + 2])[0]
        if length < 2 or i + length > len(data):
            break
        if marker in sof and length >= 7:
            height, width = struct.unpack(">HH", data[i + 3:i + 7])
            return {"format": "JPEG", "width": width, "height": height, "has_alpha": False}
        i += length
    return {"format": "JPEG", "width": None, "height": None, "has_alpha": False}


def webp_info(data: bytes):
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        flags = data[20]
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return {"format": "WEBP", "width": width, "height": height, "has_alpha": bool(flags & 0x10)}
    return {"format": "WEBP", "width": None, "height": None, "has_alpha": "unknown"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect image metadata without modifying the file.")
    parser.add_argument("image")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.image).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Not a file: {path}")

    data = path.read_bytes()
    info = None
    for probe in (png_info, jpeg_info, gif_info, webp_info):
        info = probe(data)
        if info:
            break
    if info is None:
        info = {"format": "unknown", "width": None, "height": None, "has_alpha": "unknown"}

    info.update({"path": str(path), "size_bytes": len(data)})
    w, h = info.get("width"), info.get("height")
    info["aspect_ratio"] = round(w / h, 6) if isinstance(w, int) and isinstance(h, int) and h else None

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        for key, value in info.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
