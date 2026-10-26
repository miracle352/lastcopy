import json
from pathlib import Path
from lastcopy.inventory import digest


def test_public_replays_preserve_real_receipts_and_never_publish_raw_objects():
    root=Path('web/public/verification')
    summaries=json.loads((root/'sponsor-replays.json').read_bytes())
    assert len(summaries)==2
    for summary in summaries:
        path=root/Path(summary['download']).name
        assert digest(path.read_bytes())==summary['sha256']
        value=json.loads(path.read_bytes())
        assert value['display_mode']=='Replay' and value['captured_mode']=='connected'
        assert value['independent_verification']['status']=='PASS'
        assert len(value['queries'])==summary['query_count']==4
        assert summary['model_calls']==3 and summary['models'] and summary['reported_tokens']>0
        assert len([e for e in value['events'] if e['kind']=='graph_read'])==3
        assert not (root/'objects').exists()
    assert summaries[0]['graph_next_actions']==['review','fetch_raw','export_guidance']
    assert summaries[1]['next_action']=='manual_review'
