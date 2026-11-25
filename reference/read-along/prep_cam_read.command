#!/bin/zsh
# Read-Along cut-out prep: crop the presenter's head-and-shoulders strip for the reading span and matte it to a
# transparent WebM. HEAVY JOB (u2net over every frame): ask the creator first, run alone, via `open -a Terminal`.
#
# Edit these (a Terminal launched with `open -a` may not inherit env vars: hard-code PROJECT and the cache
# root here if so), then: open -a Terminal prep_cam_read.command
PROJECT="${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR to the absolute project root}"
SRC="$PROJECT/assets/src/source.mp4"   # the attached recording (or the cleaned full-length aroll)
START=158.0                            # source second where the reading begins (minus ~0.5 s handle)
DUR=139.0                              # source seconds through the end of the reading (+ handle)
# Head-and-shoulders strip, measured from THIS footage (face track union over the span, room for leaning):
#   OBS screen-share layout (example): 428:753:0:165, the cam strip
#   full-frame talking head: e.g. 608:1080:<face_cx-304>:0, vertical, whole head + shoulders + mic
CROP="428:753:0:165"
OUT="$PROJECT/assets/alpha/cam_read.webm"
CHOKE=1                                # 1 = tighten soft matte edges (mild; won't fix a solid wall patch)
# Locked camera => draw ONE hold-out from a full-res strip frame (PIL polygon, 1.5 px blur): white = keep,
# black = always transparent. Fixes the grey wall patch u2net AND Vision keep beside the mic (tested).
GARBAGE=""                             # e.g. "$PROJECT/work/read_garbage.png" (same size as the crop)

set -e
setopt null_glob
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a cache folder on a volume with free space}/tmp"; mkdir -p "$TMPDIR" "$(dirname "$OUT")"
HF="${HYPERFRAMES_CLI:-$HOME/Library/Application Support/HyperFrames/agent-cli/bin/hyperframes}"
W="$PROJECT/work"; mkdir -p "$W"

ffmpeg -v error -y -ss "$START" -t "$DUR" -i "$SRC" -an -vf "crop=$CROP" -threads 4 \
  -c:v libx264 -crf 14 -preset fast "$W/cam_read_src.mp4"
"$HF" remove-background "$W/cam_read_src.mp4" -o "$W/cam_read_raw.webm" --quality best

if [[ $CHOKE == 1 ]]; then
  # alpha choke clip((a-70)*1.9): the fix for u2net mic ghosting
  ffmpeg -v error -y -c:v libvpx-vp9 -i "$W/cam_read_raw.webm" -threads 4 \
    -vf "format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='clip((alpha(X,Y)-70)*1.9,0,255)'" \
    -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 18 -auto-alt-ref 0 "$OUT"
else
  cp "$W/cam_read_raw.webm" "$OUT"
fi
if [[ -n $GARBAGE ]]; then
  ffmpeg -v error -y -c:v libvpx-vp9 -i "$OUT" -loop 1 -i "$GARBAGE" -threads 4 -filter_complex \
    "[0:v]format=yuva420p,split[c][a];[a]alphaextract[al];[1:v]format=gray,scale=iw:ih[g];[al][g]blend=all_mode=multiply:shortest=1[m];[c][m]alphamerge" \
    -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 18 -auto-alt-ref 0 "$W/cam_read_g.webm" && mv "$W/cam_read_g.webm" "$OUT"
fi

ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height \
  -of compact "$OUT" | tee "$W/cam_read.ok"
echo "DONE: $OUT  (matte begins at source $START s; use it as cam.source_start in the read-along config)"
