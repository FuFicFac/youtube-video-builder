"""File-calibrated quiet pass. Run with a JSON configuration; no inherited universal threshold."""
import json,sys,math
from pathlib import Path
import numpy as np
config=json.loads(Path(sys.argv[1]).read_text());r=np.load(config['rms_file']);step=config['rms_step_seconds'];fps=config['fps'];gate=config['gate_db'];minimum=config['minimum_run_seconds'];cuts=[];audit=[]
mask=r<gate;z=np.flatnonzero(np.diff(np.r_[False,mask,False]))
for i,j in zip(z[::2],z[1::2]):
 a,b=i*step,j*step
 if b-a<minimum:continue
 # Candidates are wholly below measured gate. Human contextual decisions override automatic trimming.
 decision=next((v for v in config['exceptions'] if abs(v['start']-a)<.04),None)
 if decision and decision['action']=='retain':audit.append(dict(start=a,end=b,action='retain',reason=decision['reason']));continue
 tail,lead=config['tail_handle'],config['lead_handle']
 if decision:tail,lead=decision.get('tail_handle',tail),decision.get('lead_handle',lead)
 lo=math.ceil((a+tail)*fps)/fps;hi=math.floor((b-lead)*fps)/fps
 # Both frame-exact edges must still lie inside measured quiet; preserve starts AND tails with positive handles.
 review=config.get('context_reviews',{}).get(f'{a:.3f}',{})
 evidence=review.get('evidence',[])
 reviewed=bool(review.get('notes')) and bool(evidence) and all(Path(v).is_file() for v in evidence)
 if not reviewed and any(x<=lo and hi<=y for x,y in config['ranges']):
  audit.append(dict(start=a,end=b,action='pending contextual review',reason='No candidate-specific evidence; no removal applied'));continue
 if hi>lo and a<lo<hi<b and any(x<=lo and hi<=y for x,y in config['ranges']):
  cuts.append([lo,hi]);audit.append(dict(start=a,end=b,cut_start=lo,cut_end=hi,action='tighten',tail_handle=lo-a,lead_handle=b-hi,reason=decision['reason'] if decision else review['notes'],context_review=review))
 else:audit.append(dict(start=a,end=b,action='outside retained scope',reason='Opening, deliberate bumper handoff, production take or terminal fade handled semantically'))
Path(config['output']).write_text(json.dumps(dict(calibration=config,cuts=cuts,audit=audit),indent=2))
print(json.dumps(audit,indent=2))
