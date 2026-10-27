import copy
import pytest
from scripts.verify_stack_config import validate


def configured():
    names = ('service', 'enketo', 'postgres14', 'enketo_redis_main', 'enketo_redis_cache', 'nginx', 'mail', 'pyxform')
    services = {name: {'networks': {'default': {}}, 'security_opt': ['no-new-privileges:true'],
                       'pids_limit': 256, 'logging': {'driver': 'local', 'options': {'max-size': '10m', 'max-file': '3'}}} for name in names}
    for name in ('postgres14', 'enketo_redis_main', 'enketo_redis_cache'):
        services[name]['networks'] = {'lastcopy_database' if name == 'postgres14' else 'lastcopy_redis': {}}
    services['service']['networks']['lastcopy_database'] = {}
    services['enketo']['networks']['lastcopy_redis'] = {}
    services['nginx']['ports'] = [{'host_ip': '127.0.0.1', 'published': '8384', 'target': 80}]
    return {'services': services, 'networks': {'lastcopy_database': {'internal': True}, 'lastcopy_redis': {'internal': True}}}


def test_expected_stack_and_unpublished_data_services():
    config = configured(); validate(config)
    config['services']['postgres14']['ports'] = [{'published': '5432', 'target': 5432}]
    with pytest.raises(AssertionError, match='publishes'): validate(config)


@pytest.mark.parametrize('failure', ('shared_network', 'egress', 'privilege', 'logs', 'public_proxy', 'old_build'))
def test_material_guard_regressions_fail(failure):
    config = copy.deepcopy(configured())
    if failure == 'shared_network': config['services']['enketo_redis_main']['networks']['default'] = {}
    elif failure == 'egress': config['networks']['lastcopy_database']['internal'] = False
    elif failure == 'privilege': config['services']['service']['security_opt'] = []
    elif failure == 'logs': config['services']['nginx']['logging']['options']['max-size'] = '500m'
    elif failure == 'public_proxy': config['services']['nginx']['ports'][0]['host_ip'] = '0.0.0.0'
    else: config['services']['service']['build'] = {'context': '.'}
    with pytest.raises(AssertionError): validate(config)
