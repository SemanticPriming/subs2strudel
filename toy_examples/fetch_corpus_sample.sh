#!/usr/bin/env bash
# Pulls a small (~8MB compressed) byte-range slice of the OPUS-OpenSubtitles
# v2024 English mono corpus - NOT the whole ~9.5GB file - so there is real
# corpus text to prototype against locally. Output is plain text, one
# subtitle line per line, gitignored (data/subs/) since it's a corpus we
# don't have redistribution rights to.
set -euo pipefail
cd "$(dirname "$0")"   # run from this folder

OUT_DIR="data/subs"
URL="https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2024/mono/en.txt.gz"
RANGE="${1:-0-8000000}"

mkdir -p "$OUT_DIR"
curl -s --max-time 60 -r "$RANGE" "$URL" -o "$OUT_DIR/opensubtitles_v2024_en_sample.gz"
gunzip -c "$OUT_DIR/opensubtitles_v2024_en_sample.gz" > "$OUT_DIR/opensubtitles_v2024_en_sample.txt" 2>/dev/null || true
rm "$OUT_DIR/opensubtitles_v2024_en_sample.gz"
wc -l "$OUT_DIR/opensubtitles_v2024_en_sample.txt"
