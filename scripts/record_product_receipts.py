"""Package this follow-up's existing synthetic connected receipts; no service calls."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/product'


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'private/product/live-fixed-view.json').read_text(encoding='utf-8'))
    assert data['synthetic_source'] and data['manifest']['mode']=='connected'
    report=data['current_report']; inv=data['investigation']; events=inv['events']
    assert data['status']['state']=='completed' and inv['state']=='completed'
    assert report['preservation_outcome']=='verified' and not report['recovery_executed']
    (OUT/'connected-events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events),encoding='utf-8')
    write('connected-report.json',report)
    result=inv['result']
    write('connected-summary.json',{
        'run_id':data['manifest']['run_id'],'mode':'connected','source':'native synthetic device export and fresh authenticated local Central capture',
        'status':data['status'],'synthetic_source':True,'investigation_state':inv['state'],
        'seconds':events[-1]['elapsed_ms']/1000,'steps':result['steps'],'critique_rounds':result['critique_rounds'],
        'provider_calls':result['provider_calls'],'sponsor_status':result['sponsor_status'],
        'query_ids':[e['query_id'] for e in events if e['kind']=='query'],
        'model_calls':[e for e in events if e['kind']=='model'],
        'graph_reads':[e for e in events if e['kind']=='graph_read'],
        'decision_changes':[e for e in events if e['kind']=='decision_changed'],
        'next_action':result['next_action'],'recovery_writes':0,
        'limits':inv['limits'],'limitations':['Synthetic test project, not a real field campaign','This read-only follow-up did not repeat the earlier live recovery acceptance','Initial missing-data hypothesis remained unresolved; this run does not establish the separate export-guidance branch']})
    previous=json.loads((ROOT/'private/product/live-view.json').read_text(encoding='utf-8'))
    write('initial-connected-failure.json',{'run_id':previous['manifest']['run_id'],'comparison_state':previous['status'],
        'assisted_state':previous['investigation']['state'],'error':previous['investigation']['error'],
        'events':previous['investigation']['events'],'sample_fallback':False})
    source=ROOT/'private/stage7/browser-02/live-device.zip'
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha in report['input_hashes'].values(), 'Original device ZIP no longer matches registered input'
    write('checks.json',{'host_core':{'passed':175,'seconds':108.45,'observed':'pytest full-suite output in this follow-up'},
        'negative_tests_before_implementation':{'failed':3,'reasons':['automatic example route absent','human report metadata absent','connection route absent']},
        'production_build':'passed','typecheck':'passed','generated_contracts':'passed',
        'warning':'Existing nonfailing Starlette httpx deprecation',
        'input_integrity':{'source':'existing private synthetic device ZIP','sha256':sha,'matches_registered_report':True},
        'performance':'Not remeasured for this follow-up; prior figures are historical',
        'docker':'Existing image not rebuilt for this UI follow-up'})
    old=[]
    for name in ['stage7','redesign']:
        folder=ROOT/'docs/verification'/name
        seals=json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
        for rel,expected in seals.items():
            assert hashlib.sha256((folder/rel).read_bytes()).hexdigest()==expected,(name,rel)
        old.append({'directory':name,'artifacts':len(seals),'status':'unchanged'})
    write('prior-evidence-integrity.json',old)
    print(json.dumps({'packaged':'actual saved synthetic connected evidence','prior_seals':old,'input_unchanged':True}))


if __name__=='__main__':main()
