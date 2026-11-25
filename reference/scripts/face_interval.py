"""Choose scene-local face samples; protect clips shorter than sampling cadence."""
import json,sys
from pathlib import Path

def select_interval(samples,start,end):
 if end<=start:raise ValueError('Positive interval required')
 if not samples:raise ValueError('No face samples: review source rather than guess')
 inside=[x for x in samples if start<=x[0]<end]
 if inside:return inside
 midpoint=(start+end)/2
 return [min(samples,key=lambda x:(abs(x[0]-midpoint),x[0]))]

if __name__=='__main__':
 config=json.loads(Path(sys.argv[1]).read_text());result=select_interval(config['samples'],config['start'],config['end']);print(json.dumps({'samples':result,'nearest_fallback':not any(config['start']<=x[0]<config['end'] for x in config['samples'])}))
