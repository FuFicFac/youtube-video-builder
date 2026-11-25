#!/bin/zsh
set -euo pipefail
# Chunked, sequential transcription (bounded memory). Safe to re-run.
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR to the adapted project root}"
cd "$VIDEO_PROJECT_DIR/work"
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a verified cache directory}/tmp"
export XDG_CACHE_HOME="$VIDEO_CACHE_ROOT" UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf" npm_config_cache="$VIDEO_CACHE_ROOT/npm" HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
mkdir -p chunks pk
for i in $(seq 0 7); do
  s=$((i*120)); c=chunks/demo_$(printf %03d $s).wav
  [ -f pk/demo_$(printf %03d $s).json ] && continue
  ffmpeg -v error -y -ss $s -t 120 -i demo.wav $c
  echo "chunk $s  free: $(memory_pressure | tail -1 | grep -oE '[0-9]+%')"
  uvx --from parakeet-mlx parakeet-mlx $c --output-format json --output-dir pk >/dev/null 2>&1
  rm -f $c
done
echo TRANSCRIBE DONE
