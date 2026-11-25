#!/bin/bash
# Adapt project FPS and settings before running. macOS resource monitor.
set -euo pipefail
: "${VIDEO_PROJECT_DIR:?Set VIDEO_PROJECT_DIR}"
: "${VIDEO_CACHE_ROOT:?Set VIDEO_CACHE_ROOT}"
export TMPDIR="$VIDEO_CACHE_ROOT/tmp" XDG_CACHE_HOME="$VIDEO_CACHE_ROOT"
export UV_CACHE_DIR="$VIDEO_CACHE_ROOT/uv" TORCH_HOME="$VIDEO_CACHE_ROOT/torch" HF_HOME="$VIDEO_CACHE_ROOT/hf"
export npm_config_cache="$VIDEO_CACHE_ROOT/npm" HYPERFRAMES_EXTRACT_CACHE_DIR="$VIDEO_CACHE_ROOT/frames"
export HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=150 HF_SEGMENT_BROWSER_RECYCLE=1 HF_FORCE_DRAWELEMENT=1
mkdir -p "$TMPDIR" "$HYPERFRAMES_EXTRACT_CACHE_DIR" "$npm_config_cache"
python3 - <<'PY'
import os, re, signal, subprocess, time
from pathlib import Path
p=Path(os.environ['VIDEO_PROJECT_DIR']).resolve()
cli=Path(os.environ.get('HYPERFRAMES_CLI',str(p/'node_modules/hyperframes/bin/hyperframes.mjs')))
if not cli.is_file(): raise SystemExit(f'Missing installed HyperFrames CLI: {cli}')
work=p/'work'; work.mkdir(exist_ok=True)
for name in ['render.done','render.stopped']:
    (work/name).unlink(missing_ok=True)
status=work/'render-exit-status.txt'; status.write_text('running\n')
flags=['--quality','delivery','--fps',os.environ.get('VIDEO_FPS','24000/1001'),'--workers',os.environ.get('VIDEO_RENDER_WORKERS','1'),'--browser-timeout',os.environ.get('VIDEO_BROWSER_TIMEOUT','240'),'--experimental-fast-capture=true','--gpu','--video-bitrate','20M','--resume','--keep-segments']
jobs=[(p,p/'renders/main.mp4')]+[(s,p/'renders/shorts'/f'{s.name}.mp4') for s in sorted((p/'shorts').glob('*')) if s.is_dir()]
minimum_kb=int(os.environ.get('VIDEO_MIN_BOOT_KB','716800'))
minimum_mem=int(os.environ.get('VIDEO_MIN_MEM_PERCENT','20'))
def capacity():
    free_kb=int(subprocess.check_output(['df','-k','/'],text=True).splitlines()[-1].split()[3])
    report=subprocess.check_output(['memory_pressure'],text=True)
    matches=re.findall(r'(\d+)%',report)
    if not matches: raise RuntimeError('Cannot read free-memory percentage')
    return free_kb,int(matches[-1])
def stop_group(proc):
    try: os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError: return
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL); proc.wait()
proc=None
try:
    with (work/'render.log').open('a') as log:
        subprocess.run(['node',str(cli),'--version'],stdout=log,stderr=log,check=True)
        for directory,output in jobs:
            kb,mem=capacity()
            if kb<minimum_kb or mem<minimum_mem:
                (work/'render.stopped').write_text(f'Low capacity: boot_kb={kb} mem_percent={mem}\n')
                raise RuntimeError('Insufficient capacity before render')
            output.parent.mkdir(parents=True,exist_ok=True)
            proc=subprocess.Popen(['node',str(cli),'render',*flags,'--output',str(output)],cwd=directory,stdout=log,stderr=log,start_new_session=True)
            while proc.poll() is None:
                kb,mem=capacity()
                if kb<minimum_kb or mem<minimum_mem:
                    (work/'render.stopped').write_text(f'Watchdog stop: boot_kb={kb} mem_percent={mem}\n')
                    stop_group(proc)
                    raise RuntimeError('Watchdog stopped this render; recover capacity before resuming')
                time.sleep(10)
            if proc.returncode: raise RuntimeError(f'Render exited {proc.returncode}: {output.name}')
            proc=None
    status.write_text('exit_code=0\n')
    (work/'render.done').write_text('Render processes succeeded; MP4 verification pending\n')
except BaseException:
    if proc is not None: stop_group(proc)
    status.write_text('exit_code=1\n')
    raise
PY
