#!/bin/zsh
# Sequential prep: voice -> room plate -> Vision mattes -> cut-out layer. Does NOT render.
set -euo pipefail
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR}"
cd "$VIDEO_PROJECT_DIR/work"
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT}/tmp" XDG_CACHE_HOME="$VIDEO_CACHE_ROOT"
export UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf" npm_config_cache="$VIDEO_CACHE_ROOT/npm" HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
mkdir -p "$TMPDIR"
rm -f prep.done
{
  echo "START $(date)  free: $(memory_pressure | tail -1)"
  python3 cut.py audio src.mp4 tmp/voice_raw.wav
  python3 loud.py tmp/voice_raw.wav ../assets/edit/voice.wav
  echo "PLATE $(date)"
  [ -f ../assets/edit/aroll.mp4 ] || caffeinate -i python3 cut.py video src.mp4 ../assets/edit/aroll.mp4
  echo "MASKS $(date)  free: $(memory_pressure | tail -1)"
  caffeinate -i python3 masks.py
  echo "FG $(date)"
  caffeinate -i python3 fg_build.py
  echo "PREP DONE $(date)"
} 2>&1 | tee prep.log
echo PREP DONE > prep.done
echo; echo "Done — you can close this window."
