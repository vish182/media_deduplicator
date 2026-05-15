USAGE: 



end-to-end: pass the path of the directory that you want to process (./sample in example), adjust the dis-similarity threshold via the max-distance flag (0 means strictest)

python3 hash_and_group.py ./samples \
  -o ./hashes.csv \
  --groups-output ./groups.json \
  --groups-format json \
  --max-distance 12

Intermediate scripts:
python3 hash_videos.py ./samples/ --output ./hashes.csv
python3 group_similar_hashes.py hashes.csv --format json -o groups.json