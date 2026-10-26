import json
from unittest.mock import patch
from scripts.audit_debian_image import WORKER


def test_advisories_follow_actual_image_release(tmp_path, capsys):
    database = tmp_path/'advisories.json'
    database.write_text(json.dumps({'example': {
        'OLD-ONLY': {'releases': {'bookworm': {'status': 'open', 'urgency': 'high'}}},
        'CURRENT': {'releases': {'trixie': {'status': 'open', 'urgency': 'low'}}}
    }}))
    with patch('builtins.open', return_value=database.open()), \
         patch('subprocess.check_output', return_value='example\t1.0\n'), \
         patch('platform.freedesktop_os_release', return_value={'VERSION_CODENAME': 'trixie'}):
        exec(WORKER, {})
    result = json.loads(capsys.readouterr().out)
    assert [f['cve'] for f in result['findings']] == ['CURRENT']
    assert result['debian_release'] == 'trixie'
