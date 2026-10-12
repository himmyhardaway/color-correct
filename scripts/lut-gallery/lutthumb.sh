#!/bin/zsh
# $1 = lut path, $2 = gallery dir
f="$1"; G="$2"; rel="${f#/Volumes/Extreme/LUT collection/}"
id=$(print -r -- "$rel" | md5 | cut -c1-12)
esc=$(print -r -- "$f" | sed -e "s/'/\\\\\\\\'/g" -e 's/:/\\\\:/g' -e 's/ /\\ /g')
ffmpeg -v error -y -i "$G/original.png" -vf "lut3d=file='$(print -r -- "$f" | sed "s/'/'\\\\\\\\''/g")'" -q:v 3 "$G/thumbs/$id.jpg" 2>>"$G/errors.log" && print -r -- "$id	$rel" >> "$G/index.tsv" || print -r -- "FAIL	$rel" >> "$G/index.tsv"
