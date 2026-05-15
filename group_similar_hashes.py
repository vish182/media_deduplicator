#!/usr/bin/env python3
"""Group rows from hashes.csv by Hamming similarity of binary phash strings."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def parse_binary_hash(raw: str) -> tuple[int, int]:
    """Return ``(value, bit_width)`` for a ``0b...`` or bare binary string."""
    s = raw.strip()
    if not s:
        raise ValueError("empty hash")
    if s.startswith(("0b", "0B")):
        s = s[2:]
    if not s or any(c not in "01" for c in s):
        raise ValueError("hash must be binary digits only (optional 0b prefix)")
    return int(s, 2), len(s)


def hamming_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Hamming distance between two hashes; left-pads the shorter with zeros."""
    va, wa = a
    vb, wb = b
    if wa < wb:
        va <<= wb - wa
    elif wb < wa:
        vb <<= wa - wb
    return (va ^ vb).bit_count()


class UnionFind:
    def __init__(self, n: int) -> None:
        self._parent = list(range(n))
        self._rank = [0] * n

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self._rank[px] < self._rank[py]:
            px, py = py, px
        self._parent[py] = px
        if self._rank[px] == self._rank[py]:
            self._rank[px] += 1


def load_hashes_csv(path: Path) -> list[tuple[str, tuple[int, int]]]:
    rows: list[tuple[str, tuple[int, int]]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print(f"No header row in {path}", file=sys.stderr)
            return rows
        fn_col = "filename"
        hash_col = "phash"
        lower = {n.lower(): n for n in reader.fieldnames}
        if fn_col not in reader.fieldnames and "filename" in lower:
            fn_col = lower["filename"]
        if hash_col not in reader.fieldnames and "phash" in lower:
            hash_col = lower["phash"]

        for i, row in enumerate(reader, start=2):
            name = (row.get(fn_col) or "").strip()
            ph_raw = (row.get(hash_col) or "").strip()
            if not name:
                print(f"{path}:{i}: skipping row with empty filename", file=sys.stderr)
                continue
            if not ph_raw:
                print(f"{path}:{i}: skipping {name!r} (empty phash)", file=sys.stderr)
                continue
            try:
                parsed = parse_binary_hash(ph_raw)
            except ValueError as e:
                print(f"{path}:{i}: skipping {name!r}: {e}", file=sys.stderr)
                continue
            rows.append((name, parsed))
    return rows


def build_groups(
    rows: list[tuple[str, tuple[int, int]]], max_distance: int
) -> list[list[int]]:
    """Return list of groups; each group is a list of indices into ``rows``.

    Two entries are in the same group if there is a chain of pairwise Hamming
    distances each ``<= max_distance`` (transitive closure / single-linkage at
    the threshold).
    """
    n = len(rows)
    uf = UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if hamming_distance(rows[i][1], rows[j][1]) <= max_distance:
                uf.union(i, j)

    buckets: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        buckets[uf.find(i)].append(i)

    # Stable-ish ordering: sort indices inside each group, groups by min index
    groups = [sorted(bucket) for _, bucket in sorted(buckets.items())]
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Group videos from a hashes.csv file when binary phash Hamming "
            "distance is within a threshold (transitive groups)."
        )
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="CSV file with filename and phash columns (e.g. from hash_videos.py).",
    )
    parser.add_argument(
        "--max-distance",
        type=int,
        default=10,
        metavar="N",
        help=(
            "Maximum Hamming distance for merging two hashes into the same "
            "group (default: 10). Use 0 for exact matches only."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write results to this file instead of stdout.",
    )
    args = parser.parse_args()

    if args.max_distance < 0:
        print("--max-distance must be >= 0", file=sys.stderr)
        return 1

    path = args.csv_path.expanduser().resolve()
    if not path.is_file():
        print(f"Not a file: {path}", file=sys.stderr)
        return 1

    rows = load_hashes_csv(path)
    if not rows:
        print("No usable rows.", file=sys.stderr)
        return 1

    groups = build_groups(rows, args.max_distance)

    stream = (
        open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    )
    try:
        if args.format == "json":
            payload = []
            for gid, idxs in enumerate(groups):
                members = []
                for i in idxs:
                    val, width = rows[i][1]
                    ph_str = f"0b{val:0{width}b}" if width else ""
                    members.append({"filename": rows[i][0], "phash": ph_str})
                payload.append({"group_id": gid, "members": members})
            json.dump(payload, stream, indent=2)
            stream.write("\n")
        else:
            for gid, idxs in enumerate(groups):
                print(f"Group {gid} ({len(idxs)} file(s)):", file=stream)
                for i in idxs:
                    print(f"  {rows[i][0]}", file=stream)
                print(file=stream)
    finally:
        if args.output:
            stream.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
