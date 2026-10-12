#!/bin/zsh
# Rebuild the LUT gallery: one thumbnail per .cube in the collection, on original.png.
# usage: rebuild.sh [collection dir] [gallery dir]
COL="${1:-/Volumes/Extreme/LUT collection}"; G="${2:-$HOME/Desktop/Q4 Content/library/lut-gallery}"
H="${0:A:h}"; mkdir -p "$G/thumbs"; : > "$G/index.tsv"; : > "$G/errors.log"
find "$COL" -type f -iname '*.cube' ! -name '._*' | sort | while IFS= read -r f; do zsh "$H/lutthumb.sh" "$f" "$G"; done
python3 "$H/mkgallery.py" "$G"
echo "$(grep -vc '^FAIL' "$G/index.tsv") LUTs, $(grep -c '^FAIL' "$G/index.tsv") failed (see errors.log)"
