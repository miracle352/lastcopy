"""Validate merged Compose JSON on the host; never print its environment values."""
import json
import sys


def validate(config):
    services = config['services']
    private = {'postgres14': 'lastcopy_database', 'enketo_redis_main': 'lastcopy_redis',
               'enketo_redis_cache': 'lastcopy_redis'}
    for name, network in private.items():
        row = services[name]
        assert set(row['networks']) == {network}, f'{name} has an unexpected network'
        assert config['networks'][network]['internal'] is True, f'{network} has external egress'
        assert not row.get('ports'), f'{name} publishes a data-service port'
    assert set(services['service']['networks']) == {'default', 'lastcopy_database'}
    assert set(services['enketo']['networks']) == {'default', 'lastcopy_redis'}
    ports = services['nginx']['ports']
    assert len(ports) == 1 and ports[0]['host_ip'] == '127.0.0.1' and str(ports[0]['published']) == '8384' and ports[0]['target'] == 80, 'Central proxy must remain loopback-only'
    for name in ('service', 'enketo', 'postgres14', 'enketo_redis_main', 'enketo_redis_cache', 'nginx', 'mail', 'pyxform'):
        row = services[name]
        assert not row.get('build'), f'{name} could rebuild the unpatched upstream image'
        assert not row.get('privileged', False), f'{name} is privileged'
        assert 'no-new-privileges:true' in row['security_opt'], f'{name} lacks process protection'
        assert 0 < row['pids_limit'] <= 256, f'{name} has an unbounded process count'
        assert row['logging'] == {'driver': 'local', 'options': {'max-size': '10m', 'max-file': '3'}}, f'{name} has unbounded logs'


if __name__ == '__main__':
    validate(json.load(sys.stdin))
    print('PASS merged stack isolation, process protection and bounded logs; no environment values exported')
