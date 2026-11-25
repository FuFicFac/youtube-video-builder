#!/usr/bin/env python3
"""Verify every actual final video PTS against an explicit rational frame clock."""
import argparse, json, subprocess, hashlib, math
from fractions import Fraction
from pathlib import Path

def probe(path, *args):
    return json.loads(subprocess.check_output(['ffprobe','-v','error',*args,'-of','json',str(path)]))

def check(path, expected_frames, expected_fps):
    data = probe(path, '-show_streams', '-show_format')
    video = next(x for x in data['streams'] if x['codec_type']=='video')
    audio = [x for x in data['streams'] if x['codec_type']=='audio']
    packets = probe(path, '-select_streams','v:0','-show_packets','-show_entries','packet=pts,duration')['packets']
    times = sorted(x['pts'] for x in packets if 'pts' in x)
    base = Fraction(video['time_base']); rate = Fraction(expected_fps); step = 1/rate/base
    mismatches = [{'frame':i,'actual_pts':t,'expected_rational_pts':str(i*step),'error_ticks':str(Fraction(t)-i*step)} for i,t in enumerate(times) if abs(Fraction(t)-i*step)>Fraction(1,2)]
    allowed = {math.floor(step), math.ceil(step)}
    durations = [{'packet':i, 'duration':x.get('duration')} for i,x in enumerate(packets) if x.get('duration') not in allowed]
    errors = []
    if len(times)!=expected_frames or len(packets)!=expected_frames: errors.append('Packet/presentation timestamp count differs from expected frame count')
    if not times or times[0]!=0: errors.append('Final video does not begin at frame-zero presentation time')
    if Fraction(video['r_frame_rate'])!=rate: errors.append('Video nominal frame rate differs from expected rational FPS')
    if mismatches: errors.append('Actual presentation cadence differs from the rational clock beyond half a container tick')
    if durations: errors.append('Packet durations differ from rational frame-clock quantization')
    if video.get('start_time') is not None and any(Fraction(x.get('start_time','0'))!=Fraction(video['start_time']) for x in audio): errors.append('Audio/video start times differ; investigate synchronization')
    return {'file':str(path),'pass':not errors,'errors':errors,'expected_frames':expected_frames,'actual_video_packets':len(packets),'fps':str(rate),'time_base':video['time_base'],'frame_ticks':str(step),'video_start_time':video.get('start_time'),'audio_start_times':[x.get('start_time') for x in audio],'cadence_mismatch_count':len(mismatches),'cadence_mismatches':mismatches,'duration_mismatch_count':len(durations),'duration_mismatches':durations,'maximum_rounding_error_microseconds':float(max((abs(Fraction(t)-i*step) for i,t in enumerate(times)),default=0)*base)*1e6,'limit':'Timing evidence; full decoding, frame content, audio identity and semantic/visual review remain separate gates.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video');p.add_argument('--frames',type=int,required=True);p.add_argument('--fps',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    r=check(Path(a.video),a.frames,a.fps);target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ['file','pass','errors','actual_video_packets','cadence_mismatch_count','duration_mismatch_count','maximum_rounding_error_microseconds']}));raise SystemExit(0 if r['pass'] else 1)
