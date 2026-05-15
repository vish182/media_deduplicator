#!/usr/bin/env python3
"""Batch-compute perceptual binary hashes for video files in a directory."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from hasher import compute_video_phash


def parse_extensions(raw: str) -> list[str]:
    parts = [p.strip().lower() for p in raw.split(",")]
    out = []
    for p in parts:
        if not p:
            continue
        out.append(p if p.startswith(".") else f".{p}")
    return out or [".mp4"]


def collect_videos(directory: Path, extensions: list[str]) -> list[Path]:
    ext_set = {e.lower() for e in extensions}
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in ext_set
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute perceptual hashes (binary strings) for videos in a directory."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Folder containing video files (not recursive).",
    )
    parser.add_argument(
        "--ext",
        default="mp4",
        help="Comma-separated extensions (default: mp4). Example: mp4,mkv,avi",
    )
    parser.add_argument(
        "--format",
        choices=("text", "csv", "json"),
        default=None,
        help=(
            "Output format. Default: csv if -o/--output ends with .csv, otherwise text."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write results to this file instead of stdout.",
    )
    args = parser.parse_args()

    out_format = args.format
    if out_format is None:
        if args.output and args.output.suffix.lower() == ".csv":
            out_format = "csv"
        else:
            out_format = "text"

    root = args.directory.expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    extensions = parse_extensions(args.ext)
    videos = collect_videos(root, extensions)
    if not videos:
        print(f"No matching files in {root} (extensions: {', '.join(extensions)})", file=sys.stderr)
        return 1

    rows: list[tuple[str, str | None]] = []
    for path in videos:
        phash = compute_video_phash(path)
        rows.append((path.name, phash))

    stream = open(args.output, "w", encoding="utf-8", newline="") if args.output else sys.stdout
    try:
        if out_format == "text":
            for name, phash in rows:
                if phash is None:
                    print(f"{name}\tERROR", file=stream)
                else:
                    print(f"{name}\t{phash}", file=stream)
        elif out_format == "csv":
            writer = csv.writer(stream)
            writer.writerow(["filename", "phash"])
            for name, phash in rows:
                writer.writerow([name, phash if phash is not None else ""])
        else:
            json.dump(
                [{"filename": n, "phash": h} for n, h in rows],
                stream,
                indent=2,
            )
            stream.write("\n")
    finally:
        if args.output:
            stream.close()

    failed = sum(1 for _, h in rows if h is None)
    return 1 if failed == len(rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
