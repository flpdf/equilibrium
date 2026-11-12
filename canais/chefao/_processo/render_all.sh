#!/bin/bash
# uso: bash render_all.sh <saida.mp4> [narracao_sync.wav]
set -e
OUT="$1"; AUD="$2"; mkdir -p parts; rm -f parts/*.mp4
node render.js 0 7.4 parts/p1 & node render.js 7.4 14.8 parts/p2 & node render.js 14.8 22.2 parts/p3 & node render.js 22.2 29.6 parts/p4 & node render.js 29.6 37 parts/p5 & wait
for i in 1 2 3 4 5; do test -f parts/p$i.mp4 || { echo "parte $i faltando"; exit 1; }; done
printf "file 'p1.mp4'\nfile 'p2.mp4'\nfile 'p3.mp4'\nfile 'p4.mp4'\nfile 'p5.mp4'\n" > parts/list.txt
ffmpeg -y -v error -f concat -safe 0 -i parts/list.txt -c copy parts/video.mp4
if [ -n "$AUD" ]; then ffmpeg -y -v error -i parts/video.mp4 -i "$AUD" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT.part.mp4"
else ffmpeg -y -v error -i parts/video.mp4 -f lavfi -i anullsrc=r=44100:cl=stereo -map 0:v -map 1:a -c:v copy -c:a aac -shortest -movflags +faststart "$OUT.part.mp4"; fi
mv "$OUT.part.mp4" "$OUT"; ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
