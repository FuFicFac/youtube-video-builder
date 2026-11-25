#!/bin/zsh
set -euo pipefail
# Voice/music separation for the music-under-voice opening (0-100s). CPU, capped segments, caches on external.
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR to the adapted project root}"
cd "$VIDEO_PROJECT_DIR/work"
X="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a verified cache directory}"
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TMPDIR="${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT to a verified cache directory}/tmp"
export XDG_CACHE_HOME="$VIDEO_CACHE_ROOT" UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf" npm_config_cache="$VIDEO_CACHE_ROOT/npm" HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
mkdir -p "$X" "$TMPDIR" sep
echo "start $(date)  free: $(memory_pressure | tail -1 | grep -oE '[0-9]+%')  boot: $(df -h / | tail -1 | awk '{print $4}')"
ffmpeg -v error -y -ss 0 -t 100 -i ../assets/src/demo.mp4 -vn -ac 2 -ar 44100 sep/open100.wav
uvx --python 3.11 --with "torch<2.6" --with "torchaudio<2.6" --with soundfile demucs==4.0.1 --two-stems vocals -n htdemucs -d cpu -j 1 --segment 7 -o sep sep/open100.wav 2>&1 | tail -3
echo "done $(date)  free: $(memory_pressure | tail -1 | grep -oE '[0-9]+%')  boot: $(df -h / | tail -1 | awk '{print $4}')"
ls -la sep/htdemucs/open100/
echo SEPARATE DONE
