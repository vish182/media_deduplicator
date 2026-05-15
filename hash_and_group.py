#!/usr/bin/env python3
"""Run hash_videos.py then group_similar_hashes.py with forwarded CLI args."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _run_step(argv: list[str]) -> int:
    proc = subprocess.run(argv)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compute hashes for videos in a directory, then group similar "
            "hashes (Hamming distance). Invokes hash_videos.py and "
            "group_similar_hashes.py in order."
        )
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Folder containing video files (passed to hash_videos.py).",
    )
    parser.add_argument(
        "--ext",
        default="mp4",
        help="Comma-separated extensions for hash_videos.py (default: mp4).",
    )
    parser.add_argument(
        "-o",
        "--hashes-output",
        type=Path,
        default=Path("hashes.csv"),
        metavar="CSV",
        help="Intermediate hashes CSV written by hash_videos.py (default: hashes.csv).",
    )
    parser.add_argument(
        "--hash-format",
        choices=("text", "csv", "json"),
        default=None,
        help=(
            "hash_videos.py --format. Default: same rules as hash_videos "
            "(csv if --hashes-output ends with .csv)."
        ),
    )
    parser.add_argument(
        "--max-distance",
        type=int,
        default=10,
        metavar="N",
        help="group_similar_hashes.py --max-distance (default: 10).",
    )
    parser.add_argument(
        "--groups-format",
        choices=("text", "json"),
        default="text",
        help="group_similar_hashes.py --format (default: text).",
    )
    parser.add_argument(
        "--groups-output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional path for group_similar_hashes.py -o (default: stdout).",
    )

    args = parser.parse_args()

    hashes_path = args.hashes_output.expanduser().resolve()
    if hashes_path.suffix.lower() != ".csv":
        print(
            "error: --hashes-output must end with .csv (group_similar_hashes reads CSV).",
            file=sys.stderr,
        )
        return 2

    py = sys.executable
    hash_script = _repo_root() / "hash_videos.py"
    group_script = _repo_root() / "group_similar_hashes.py"

    if not hash_script.is_file() or not group_script.is_file():
        print("error: hash_videos.py or group_similar_hashes.py not next to this script.", file=sys.stderr)
        return 2

    hash_cmd: list[str] = [
        py,
        str(hash_script),
        str(args.directory.expanduser().resolve()),
        "--ext",
        args.ext,
        "-o",
        str(hashes_path),
    ]
    if args.hash_format is not None:
        hash_cmd.extend(["--format", args.hash_format])

    rc = _run_step(hash_cmd)
    if rc != 0:
        return rc

    group_cmd: list[str] = [
        py,
        str(group_script),
        str(hashes_path),
        "--max-distance",
        str(args.max_distance),
        "--format",
        args.groups_format,
    ]
    if args.groups_output is not None:
        group_cmd.extend(["-o", str(args.groups_output.expanduser().resolve())])

    return _run_step(group_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
