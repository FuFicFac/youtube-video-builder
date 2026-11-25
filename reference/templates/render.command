#!/bin/bash
# Bounded, resumable render (settings proven on the reference edit; verify against your installed CLI). Safe to re-run.
set -euo pipefail
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR to the adapted project root}"
P="$VIDEO_PROJECT_DIR"
CLI="${HYPERFRAMES_CLI:-$P/node_modules/hyperframes/bin/hyperframes.mjs}"
[[ -f "$CLI" ]] || { echo "Missing HyperFrames CLI: $CLI" >&2; exit 1; }
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a verified cache directory}/tmp"
export UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf"
export XDG_CACHE_HOME="$VIDEO_CACHE_ROOT"
export HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
export npm_config_cache="$VIDEO_CACHE_ROOT/npm"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$HYPERFRAMES_EXTRACT_CACHE_DIR" "$npm_config_cache" "$P/renders/shorts"
export HF_SEGMENTED_CAPTURE=true
export HF_SEGMENT_FRAMES=150
export HF_SEGMENT_BROWSER_RECYCLE=1
export HF_FORCE_DRAWELEMENT=1
FLAGS=(--quality delivery --fps 24000/1001 --workers 2 --experimental-fast-capture=true --gpu --video-bitrate 20M --resume --keep-segments)
LOG="$P/work/render.log"
# Status means process exit only; successful output still requires media verification.
trap 'result=$?; printf "exit_code=%s\n" "$result" > "$P/work/render-exit-status.txt"' EXIT
printf 'running\n' > "$P/work/render-exit-status.txt"
echo "=== $(date)  hyperframes $(node "$CLI" --version 2>/dev/null)" | tee -a "$LOG"
cd "$P"
echo "MAIN start $(date)" | tee -a "$LOG"
caffeinate -i node "$CLI" render "${FLAGS[@]}" --output "$P/renders/main.mp4" >> "$LOG" 2>&1
echo "MAIN EXIT $? $(date)" | tee -a "$LOG"
for s in "$P"/shorts/*/; do
  [[ -d "$s" ]] || continue
  n=$(basename "$s"); cd "$s"
  echo "$n start $(date)" | tee -a "$LOG"
  caffeinate -i node "$CLI" render "${FLAGS[@]}" --output "$P/renders/shorts/$n.mp4" >> "$LOG" 2>&1
  echo "$n EXIT $? $(date)" | tee -a "$LOG"
done
echo "ALLDONE $(date)" | tee -a "$LOG"
echo; echo "Render finished — you can close this window."
