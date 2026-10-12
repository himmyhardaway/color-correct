#!/bin/bash
# Install starred LUTs. stdin: the gallery's "Copy shortlist" text (one "Folder/name.cube" per line).
# Copies each to: /Volumes/Extreme/LUT Picks, Resolve LUT/Jonathan Picks, and the skill's luts/picks.
# Files are named "<source folder> - <name>.cube". Copies only; the collection is never changed.
COL="/Volumes/Extreme/LUT collection"
DESTS=("/Volumes/Extreme/LUT Picks" "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Jonathan Picks" "$HOME/.claude/skills/color-correct/luts/picks")
for d in "${DESTS[@]}"; do mkdir -p "$d"; done
grep -i '\.cube$' | while IFS= read -r rel; do
  rel="${rel#"${rel%%[![:space:]]*}"}"; src="$COL/$rel"
  [ -f "$src" ] || { echo "MISSING $rel"; continue; }
  top="${rel%%/*}"; top="${top%"${top##*[![:space:]]}"}"; name="$top - ${rel##*/}"
  for d in "${DESTS[@]}"; do cp -p "$src" "$d/$name"; done
  in=$(grep -m3 -i -E 'log|LUMIXPHOTOSTYLE|TITLE' "$src" | tr '\n' ' ' | cut -c1-80)
  echo "ok  $name   [$in]"
done
echo "In Resolve: Color page > LUTs > right-click > Refresh > Jonathan Picks"
