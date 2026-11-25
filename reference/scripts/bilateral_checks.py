#!/usr/bin/env python3
"""Validate evidence contracts for transcript-driven illustrated talking-head edits.

Usage: bilateral_checks.py PROJECT --phase authoring|final --report QA.json
No dependencies; does not infer artistic quality or claim listening.
"""
import argparse,json,hashlib,math
from pathlib import Path
def check(project,phase):
 p=Path(project);c=json.loads((p/'STORYTELLING-AUDIT.json').read_text());fps=c['fps_numerator']/c['fps_denominator'];errs=[]
 require=lambda ok,msg:errs.append(msg) if not ok else None
 sections=c['sections'];last=0
 for s in sections:
  require(abs(s['start']-last)<=1/fps,'Uncovered or overlapping narrative section '+s['id']);require(s['end']>s['start'],'Empty section '+s['id']);require(bool(s['reason'].strip()),'Missing semantic decision '+s['id']);require(s['decision'] in ['illustrate','real-demo','presenter-hold','brand','closing'],'Invalid section decision '+s['id']);last=s['end']
 require(abs(last-c['duration'])<=1/fps,'Whole-video audit does not reach ending')
 for b in c['beats']:
  require(bool(b['purpose']),'Missing purpose '+b['id']);require(b['end']>b['start'],'Empty visual beat '+b['id']);require(b['layout'] in ['bilateral','real-demo','fullscreen','brand'],'Undeclared layout '+b['id'])
  if b['layout']=='bilateral':
   require(set(b['used_sides'])=={'left','right'},'Bilateral scene does not use both sides '+b['id'])
   for r in b['graphic_regions']:
    ex=b['presenter_exclusion'];x,y,w,h=r;xx,yy,ww,hh=ex
    require(x+w<=xx or x>=xx+ww or y+h<=yy or y>=yy+hh,'Graphic region intrudes into presenter exclusion '+b['id'])
  if b['layout']=='fullscreen':require(b['presenter_visible'] is False and bool(b['return_reason']),'Unplanned full-screen takeover '+b['id'])
  for a in b['actions']:
   require(bool(a['phrase']) and bool(a['change']),'Action lacks spoken cause '+b['id']);require(b['start']-1/fps<=a['time']<b['end']+1/fps,'Action outside scene '+b['id']);require(abs(a['time']*fps-round(a['time']*fps))<1e-6,'Action not frame-exact '+b['id'])
  if phase=='final':
   require(bool(b['encoded_frames']),'No actual encoded frame evidence '+b['id'])
   for f in b['encoded_frames']:require((p/f).is_file(),'Missing encoded frame '+f)
 cue=json.loads((p/c['cue_ledger']).read_text())
 for z in cue['cues']:
  require(not z.get('requires_review'), 'Unreviewed cue '+z['phrase']);require(abs(z['time']-z['clean_asr_start'])*fps<=.500001,'Cue not nearest ASR frame '+z['phrase'])
 sync=json.loads((p/c['av_sync_ledger']).read_text());require(sync['voice_shifted'] is False,'Speech shifted to accommodate effects')
 for z in sync['transitions']:require(abs(z['alignment_error_frames'])<=1,'Effect peak misses visual center '+z['id'])
 generated=c['generated_assets'];require(len(generated)<=c['generated_asset_budget'],'Image-generation budget exceeded')
 for z in generated:
  f=p/z['file'];require(f.is_file(),'Missing generated asset '+str(f));require(z['symbolic'] and not z['likeness'],'Generated likeness or unlabeled realism')
  if f.is_file():require(hashlib.sha256(f.read_bytes()).hexdigest()==z['sha256'],'Generated asset identity changed')
 if phase=='final':
  for key in ['encoded_frame_count_pass','encoded_clock_pass','full_decode_pass','final_word_review_pass','retained_source_identity_pass','encoded_loudness_pass','qr_encoded_decode_pass','finished_frame_review_pass']:
   require(c['final_gates'].get(key) is True,'Final gate absent: '+key)
 return dict(phase=phase,pass_=not errs,errors=errs,sections=len(sections),beats=len(c['beats']),effects=len(sync['transitions']),limit='Evidence contract checks geometry, clocks, provenance and declared gates; inspect real encoded motion and hear audio when available. This tool cannot establish subjective engagement or listening.')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('project');a.add_argument('--phase',choices=['authoring','final'],required=True);a.add_argument('--report',required=True);v=a.parse_args();r=check(v.project,v.phase);Path(v.report).write_text(json.dumps(r,indent=2));print(json.dumps(r));raise SystemExit(0 if r['pass_'] else 1)
