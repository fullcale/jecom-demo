#!/bin/sh
# 使い方: tools/shot.sh <幅> <高さ> <出力名> <site内パス or URL>
C="/c/Program Files/Google/Chrome/Application/chrome.exe"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUTDIR="$ROOT/raw/shots"
mkdir -p "$OUTDIR"
W=$1; Hh=$2; NAME=$3; P=$4
case "$P" in
  http*) U="$P" ;;
  file*) U="$P" ;;
  *) U="file:///$(cygpath -m "$ROOT/site/$P")" ;;
esac
"$C" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$(cygpath -m "$OUTDIR/prof")" \
  --virtual-time-budget=4000 --window-size=$W,$Hh --screenshot="$(cygpath -m "$OUTDIR/$NAME.png")" "$U" 2>/dev/null
echo "$OUTDIR/$NAME.png"
