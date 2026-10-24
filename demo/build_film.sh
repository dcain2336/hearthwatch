#!/bin/bash
# build_film.sh — assemble the Hearthwatch demo film from annotated
# clips, title/result cards, and TTS narration. Every segment's video
# is cut to exactly its narration length, so the film's total length
# is the sum of the narration files (about 2:35, under the 5-minute
# competition cap). Requires ffmpeg and the DejaVu Bold font.
set -e
cd "$(dirname "$0")"
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
OUT=output

# A text card: dark background, centred white title + subtitle lines.
# $1 = segment id, $2 = title, $3 = subtitle, $4 = narration mp3.
card() {
  local id="$1" title="$2" sub="$3" audio="$4"
  local dur
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio")
  ffmpeg -y -loglevel error -f lavfi -i "color=c=0x1a1a2e:s=640x360:d=$dur" \
    -i "$audio" \
    -vf "drawtext=fontfile=$FONT:text='$title':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=130,drawtext=fontfile=$FONT:text='$sub':fontsize=18:fontcolor=0xcccccc:x=(w-text_w)/2:y=190" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT/seg_$id.mp4"
}

# A clip segment: loop the annotated clip to cover the narration.
# $1 = segment id, $2 = clip file, $3 = narration mp3.
clip() {
  local id="$1" clipf="$2" audio="$3"
  local dur
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio")
  ffmpeg -y -loglevel error -stream_loop 1 -i "$clipf" -i "$audio" \
    -t "$dur" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT/seg_$id.mp4"
}

mkdir -p "$OUT"
# Segment 1: title card.
card s1 "HEARTHWATCH" "A home-safety vision agent  |  OpenCV AI Competition 2026" narr/s1.mp3
# Segment 2: empty room (the empty scene, looped to cover narration).
ffmpeg -y -loglevel error -stream_loop 1 -i ../evaluation/testset/empty.mp4 -i narr/s2.mp3 \
  -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 narr/s2.mp3)" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT/seg_s2.mp4"
# Segment 3: walk clip (presence).
clip s3 "$OUT/../output/annotated_walk.mp4" narr/s3.mp3
# Segment 4: fall clip (fall-like escalation).
clip s4 "$OUT/../output/annotated_fall.mp4" narr/s4.mp3
# Segment 5: package clip followed by stove clip, one narration.
ffmpeg -y -loglevel error -i "$OUT/../output/annotated_package.mp4" -i "$OUT/../output/annotated_stove.mp4" -i narr/s5.mp3 \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" -map 2:a \
  -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 narr/s5.mp3)" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT/seg_s5.mp4"
# Segments 6-8: text cards (feedback, results, AWS honesty).
card s6 "THE HOUSEHOLD TRAINS IT BACK" "False alarms nudge thresholds up  |  bounded, never silencing" narr/s6.mp3
card s7 "MEASURED, NOT CLAIMED" "4 of 4 event scenes  |  0 false positives  |  4-15 frame latency" narr/s7.mp3
card s8 "ONE GAP, STATED PLAINLY" "AWS component documented, not live  |  container-ready, card-free path noted" narr/s8.mp3

# Concatenate all segments into the final film.
# Absolute paths in the list, so the concat demuxer cannot resolve
# them against the wrong directory.
for s in s1 s2 s3 s4 s5 s6 s7 s8; do
  echo "file '$PWD/$OUT/seg_$s.mp4'"
done > "$OUT/list.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$OUT/list.txt" -c copy hearthwatch-demo.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 hearthwatch-demo.mp4
echo "Film built: hearthwatch-demo.mp4"
