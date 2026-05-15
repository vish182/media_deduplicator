# Media deduplicator

Find duplicate to near-duplicate videos in a folder by computing **perceptual hashes** (pHash) for each file and clustering them when the similarity score between hashes is within a limit you choose. This utility will help you identify duplicate media accross bit-rates and resolutions.

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## One-shot: hash and group

Point at a directory of videos (non-recursive; only files directly in that folder). Use `--max-distance` to control how strict grouping is:

- **`0`** — only identical hashes end up in the same group (strictest).
- **Higher values** — allow more visual difference before splitting groups.

```bash
python3 hash_and_group.py ./samples \
  -o ./hashes.csv \
  --groups-output ./groups.json \
  --groups-format json \
  --max-distance 12
```

Common options from the underlying steps are forwarded from `hash_and_group.py`:

| Flag | Role |
|------|------|
| `--ext` | Comma-separated extensions (default: `mp4`) |
| `-o` / `--hashes-output` | CSV path for intermediate hashes (default: `hashes.csv`) |
| `--hash-format` | `text`, `csv`, or `json` for the hashes step |
| `--max-distance` | Max Hamming distance for merging (default: `10`) |
| `--groups-format` | `text` or `json` for groups |
| `--groups-output` | File path for group output (omit to print groups to stdout) |

---

## Two-step workflow

**1. Hash every video in a directory**

```bash
python3 hash_videos.py ./samples/ --output ./hashes.csv
```

**2. Group rows from the CSV**

```bash
python3 group_similar_hashes.py ./hashes.csv --format json -o ./groups.json
```

---

## Sample JSON output

Groups are lists of members; each member has `filename` and a binary `phash` string (`0b...`). Below, hashes are shortened for readability; real output contains the full bit string.

```json
[
  {
    "group_id": 0,
    "members": [
      {
        "filename": "game_1024x576.mp4",
        "phash": "0b0000001000001100011110111110110001111001111011000111100111101100..."
      },
      {
        "filename": "game_640x360.mp4",
        "phash": "0b0000101000001100011110111110110001111001111011000111100111101100..."
      }
    ]
  },
  {
    "group_id": 1,
    "members": [
      {
        "filename": "vanish_spanish.mp4",
        "phash": "0b0000000000000000000000000000000000001000110000000000000111000010..."
      }
    ]
  }
]
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `hash_and_group.py` | Run hashing then grouping with one command |
| `hash_videos.py` | Write `hashes.csv` (or text/JSON) from a directory |
| `group_similar_hashes.py` | Cluster rows in a hashes CSV by Hamming distance |
| `hasher.py` | Library: compute video pHash |
