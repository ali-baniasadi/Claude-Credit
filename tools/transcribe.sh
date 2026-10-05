#!/bin/zsh
# Word-level timestamps for a slice of audio (to sync text with recitation/narration).
# Usage: tools/transcribe.sh <audio> <start_sec> <duration_sec> [ar|fa]
set -e
ROOT=${0:A:h:h}
tmp=$(mktemp -t seg).wav
ffmpeg -v error -y -ss "$2" -t "$3" -i "$1" -ac 1 -ar 16000 "$tmp"
whisper-cli -m "$ROOT/models/ggml-medium-q5_0.bin" -l "${4:-ar}" -f "$tmp" -t 8 -np -ml 1 2>/dev/null
rm -f "$tmp"
