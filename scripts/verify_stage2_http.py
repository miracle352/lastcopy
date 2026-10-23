"""Exercise the documented real loopback HTTP API against literal sample expectations."""
import argparse
import hashlib
import json
import time
from urllib.parse import urlsplit
import httpx
from lastcopy.config import ROOT
from scripts.run import bundle_snapshot


def verify(base):
    url = urlsplit(base)
    if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost') or url.username or url.password or url.path not in ('', '/'):
        raise ValueError('Verifier accepts the configured loopback HTTP origin only')
    results = []
    with httpx.Client(base_url=base, timeout=20, trust_env=False) as client:
        health = client.get('/health')
        health.raise_for_status()
        if health.json().get('mode') != 'sample' or health.json().get('stage') != 2:
            raise ValueError('Start the Stage 2 API with SAMPLE_MODE=true')
        for case in ['stranded', 'media', 'export', 'history']:
            directory = ROOT / 'fixtures/stage2' / case
            manifest = (directory / 'run-manifest.json').read_bytes()
            device = (directory / 'device.zip').read_bytes()
            envelope = (directory / 'server-snapshot.json').read_bytes()
            payload = (directory / 'server-payload.zip').read_bytes()
            expected = json.loads((directory / 'expected.json').read_bytes())
            registered = {}
            for kind, data in [('manifest', manifest), ('device', device), ('server', bundle_snapshot(envelope, payload))]:
                response = client.post('/inputs/' + kind, content=data, headers={'Content-Type': 'application/octet-stream'})
                response.raise_for_status()
                registered[kind] = response.json()['input_id']
            request = {'manifest_id': registered['manifest'], 'device_input_ids': [registered['device']], 'server_input_id': registered['server']}
            started = client.post('/run', json=request)
            started.raise_for_status()
            rid = started.json()['run_id']
            deadline = time.monotonic() + 60
            while True:
                response = client.get('/runs/' + rid)
                response.raise_for_status()
                job = response.json()
                if job['state'] not in ('queued', 'running'):
                    break
                if time.monotonic() >= deadline:
                    raise ValueError('HTTP sample job did not finish within verifier deadline')
                time.sleep(.1)
            if job['state'] != 'completed':
                raise ValueError('HTTP sample job failed or was cancelled')
            outputs = {}
            for name, sha in job['output_hashes'].items():
                response = client.get('/runs/' + rid + '/artifacts/' + name)
                response.raise_for_status()
                if hashlib.sha256(response.content).hexdigest() != sha:
                    raise ValueError('HTTP artifact hash mismatch')
                outputs[name] = response.content
            report = json.loads(outputs['report.json'])
            if {f['version_id']: f['verdict'] for f in report['findings']} != expected['verdicts']:
                raise ValueError('HTTP result differs from authored expectations')
            if sum(f['recovery_eligible'] for f in report['findings']) != expected['eligible_count']:
                raise ValueError('HTTP recovery eligibility differs from authored expectations')
            if report['provider_calls'] != 0 or report['recovery_executed']:
                raise ValueError('Offline comparison must not use providers or execute recovery')
            results.append({'sample': case, 'status': 'PASS', 'run_id': rid,
                'findings': {f['version_id']: f['verdict'] for f in report['findings']},
                'coverage_complete': report['coverage']['complete'], 'preservation_outcome': report['preservation_outcome'],
                'output_hashes': job['output_hashes']})
        if client.post('/run', json={'manifest_path': '../.env'}).status_code != 422:
            raise ValueError('API accepted an arbitrary path')
        if client.post('/inputs/device', content=b'not a ZIP').status_code != 422:
            raise ValueError('API accepted malformed archive')
    return {'transport': 'real loopback HTTP', 'base_url': base, 'sample_mode': True,
            'external_services_called': False, 'results': results, 'invalid_path_and_archive_rejected': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    result = verify(args.base_url)
    directory = ROOT / 'private/verification'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'stage2-http.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
