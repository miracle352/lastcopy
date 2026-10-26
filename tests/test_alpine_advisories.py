import pytest
from scripts.audit_alpine_image import findings, inventory


def test_subpackage_uses_source_identity_and_keeps_old_version():
    raw = 'P:libssl3\nV:3.5.8-r0\no:openssl\n\nP:libcrypto3\nV:3.5.8-r0\no:openssl\n'
    assert inventory(raw) == [('openssl', '3.5.8-r0')]
    db = {'distroversion': 'v3.23', 'reponame': 'main', 'packages': [
        {'pkg': {'name': 'openssl', 'secfixes': {'3.5.9-r0': ['CVE-test']}}}]}
    rows = findings(inventory(raw), [db], lambda a, b: a < b)
    assert [row['cve'] for row in rows] == ['CVE-test']
    assert findings([('openssl', '3.5.9-r0')], [db], lambda a, b: a < b) == []
    assert findings([('openssl', '3.5.10-r0')], [db], lambda a, b: False) == []


def test_wrong_release_or_empty_inventory_cannot_report_clean():
    with pytest.raises(ValueError, match='release'):
        findings([('openssl', 'old')], [{'distroversion': 'v3.22'}], lambda a, b: True)
    with pytest.raises(ValueError, match='inventory'):
        inventory('')
