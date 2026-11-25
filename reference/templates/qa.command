#!/bin/zsh
set -euo pipefail
setopt null_glob
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR to the adapted project root}"
cd "$VIDEO_PROJECT_DIR/work"
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a verified cache directory}/tmp"
export XDG_CACHE_HOME="$VIDEO_CACHE_ROOT" UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf" npm_config_cache="$VIDEO_CACHE_ROOT/npm" HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
mkdir -p qa; rm -f qa/*.json
ffmpeg -v error -y -i ../assets/edit/voice.wav -ac 1 -ar 16000 qa/v16.wav
for s in $(seq 0 120 840); do
  f=qa/c_$(printf %03d $s).wav
  ffmpeg -v error -y -ss $s -t 120 -i qa/v16.wav $f
  uvx --from parakeet-mlx parakeet-mlx $f --output-format json --output-dir qa >/dev/null 2>&1
  rm -f $f
  echo "qa chunk $s  free $(memory_pressure | tail -1 | grep -oE '[0-9]+%')" | tee -a qa.log
done
echo "QA transcription complete; comparison and render checks pending" | tee -a qa.log
