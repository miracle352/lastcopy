"""Publish verified synthetic receipts, never raw private evidence objects or keys."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from scripts.verify_stage3_live import verify
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path,required=True)
    parser.add_argument('--conflict',type=Path,required=True)
    args=parser.parse_args();summaries=[]
    output=ROOT/'web/public/verification';output.mkdir(parents=True,exist_ok=True)
    for case,fixture,folder in [('export-review','export-review',args.export),('conflict','unresolved-conflict',args.conflict)]:
        independent=verify(folder,ROOT/'fixtures/stage3'/fixture)
        result=json.loads((folder/'investigation.json').read_bytes())
        events=[json.loads(line) for line in (folder/'events.jsonl').read_bytes().splitlines()]
        queries=[json.loads((folder/'queries'/(e['evidence_object']+'.json')).read_bytes()) for e in events if e['kind']=='query']
        world=[json.loads(line) for line in (folder/'world.jsonl').read_bytes().splitlines()]
        bundle={'display_mode':'Replay','captured_mode':'connected','source_scope':'Authored synthetic fixtures; original source objects remain private',
                'captured_at':datetime.fromtimestamp((folder/'investigation.json').stat().st_mtime,timezone.utc).isoformat(),
                'independent_verification':independent,'events':events,'queries':queries,'world_revisions':world,
                'report':result['report'],'report_sha256':result['report_sha256']}
        data=(json.dumps(bundle,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
        filename='sponsor-'+case+'.json';(output/filename).write_bytes(data)
        summaries.append({'case':case,'display_mode':'Replay','run_id':result['run_id'],'captured_at':bundle['captured_at'],
            'next_action':result['next_action'],'verdict':independent['verdict'],'models':independent['models'],
            'query_count':len(queries),'model_calls':result['provider_calls'],'graph_next_actions':independent['graph_next_actions'],
            'reported_tokens':sum(e.get('usage',{}).get('total_tokens',0) for e in events if e['kind']=='model'),
            'download':'/verification/'+filename,'sha256':digest(data),'report_sha256':result['report_sha256']})
    (output/'sponsor-replays.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verified_captures':len(summaries),'raw_source_objects_published':False,'model_calls_during_export':0}))


if __name__=='__main__':main()
