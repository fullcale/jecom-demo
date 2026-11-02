#!/bin/sh
# スマホ幅(390px)で撮る: iframe に入れて撮影。使い方: tools/shot_sp.sh <高さ> <出力名> <site内パス>
ROOT=$(cd "$(dirname "$0")/.." && pwd)
Hh=$1; NAME=$2; P=$3
U="file:///$(cygpath -m "$ROOT/site/$P")"
F="$ROOT/raw/shots/_sp.html"
printf '<html><body style="margin:0;background:#888"><iframe src="%s" style="width:390px;height:%spx;border:0;background:#fff"></iframe></body></html>' "$U" "$Hh" > "$F"
sh "$ROOT/tools/shot.sh" 520 $Hh $NAME "file:///$(cygpath -m "$F")"
