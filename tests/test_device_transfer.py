"""A device observation must be stable, scoped and durable before publishing."""
import io
import json
import tarfile
import sqlite3

import pytest

from lastcopy.config import Settings
from lastcopy.inventory import inventory
from lastcopy.store import RunStore
from tests.test_collect_packaging import copied_project


def tar_project(source):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w') as stream:
        for p in sorted(source.rglob('*')):
            if p.is_file():
                data = p.read_bytes()
                info = tarfile.TarInfo(p.relative_to(source).as_posix())
                info.size = len(data)
                stream.addfile(info, io.BytesIO(data))
    return out.getvalue()


def setup(tmp_path):
    source, form = copied_project(tmp_path, 'complete')
    inbox = tmp_path / 'inbox'
    inbox.mkdir()
    settings = Settings({'SAMPLE_MODE': 'false', 'LASTCOPY_WATCH_INBOX': str(inbox),
                         'LASTCOPY_DEVICE_TRANSFER_ENABLED': 'true', 'LASTCOPY_DEVICE_SERIAL': 'emulator-5558',
                         'LASTCOPY_COLLECT_PROJECT_ID': 'c7ee4de9-247c-42ac-8d78-d5bb9e7d8d4d',
                         'LASTCOPY_TRANSFER_DEVICE_ID': 'device-one', 'LASTCOPY_TRANSFER_FORM_ID': form,
                         'LASTCOPY_TRANSFER_SYNTHETIC': 'true'})
    return source, inbox, RunStore(tmp_path / 'ledger', settings)


def test_stable_native_export_publishes_once_and_restart_retains_identity(tmp_path):
    # Removing persisted content deduplication would make restart publish again.
    from lastcopy.device_transfer import DeviceTransfer
    source, inbox, store = setup(tmp_path)
    native = tar_project(source)
    transfer = DeviceTransfer(store, pull=lambda: native)
    transfer.tick(now=1000)
    archives = list(inbox.glob('*.zip'))
    assert len(archives) == 1 and len(list(inbox.glob('*.ready.json'))) == 1
    data = archives[0].read_bytes()
    observed = inventory(data, store.settings)
    assert observed.manifest.device_id == 'device-one'
    assert observed.versions[0].completion_status == 'complete'
    assert b'unrelated-private-form' not in b''.join(__import__('lastcopy.inventory', fromlist=['read_archive']).read_archive(data, store.settings).values())
    DeviceTransfer(store, pull=lambda: native).tick(now=1061)
    assert list(inbox.glob('*.zip')) == archives and archives[0].read_bytes() == data
    assert transfer.status()['exports_completed'] == 1


def test_device_changes_during_copy_never_publish_a_complete_snapshot(tmp_path):
    # Comparing only the first copy would accept a torn source snapshot.
    from lastcopy.device_transfer import DeviceTransfer
    source, inbox, store = setup(tmp_path)
    first = tar_project(source)
    target = next((source / 'instances').rglob('*.xml'))
    target.write_bytes(target.read_bytes().replace(b'0017', b'0099'))
    second = tar_project(source)
    assert first != second
    values = iter([first, second])
    transfer = DeviceTransfer(store, pull=lambda: next(values))
    transfer.tick(now=1000)
    assert transfer.status()['state'] == 'waiting_for_stable_export'
    assert not list(inbox.iterdir())


def test_disconnected_device_is_unknown_and_sample_mode_cannot_pull(tmp_path):
    from lastcopy.device_transfer import DeviceTransfer
    _, inbox, store = setup(tmp_path)
    def offline():
        raise OSError('device unavailable')
    transfer = DeviceTransfer(store, pull=offline)
    transfer.tick(now=1000)
    assert transfer.status()['state'] == 'device_unreachable'
    assert transfer.status()['last_export_at'] is None and not list(inbox.iterdir())
    sample = RunStore(tmp_path / 'sample', Settings({**store.settings.values, 'SAMPLE_MODE': 'true'}))
    def forbidden():
        pytest.fail('Sample mode touched the device')
    disabled = DeviceTransfer(sample, pull=forbidden)
    disabled.tick(now=1000)
    assert not disabled.status()['configured']


@pytest.mark.parametrize('name,kind', [('../escape', tarfile.REGTYPE), ('forms/link', tarfile.SYMTYPE), ('metadata/instances.db', tarfile.LNKTYPE)])
def test_hostile_transport_archive_never_reaches_the_inbox(tmp_path, name, kind):
    from lastcopy.device_transfer import DeviceTransfer
    _, inbox, store = setup(tmp_path)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as stream:
        entry = tarfile.TarInfo(name)
        entry.type = kind
        entry.linkname = '/outside'
        stream.addfile(entry)
    transfer = DeviceTransfer(store, pull=lambda: output.getvalue())
    transfer.tick(now=1000)
    assert transfer.status()['state'] == 'invalid_export'
    assert not list(inbox.iterdir()) and not (tmp_path / 'escape').exists()


@pytest.mark.parametrize('alias', ['forms/./x.xml', 'forms//x.xml', 'forms/x.xml.', 'forms/CON'])
def test_transport_paths_cannot_alias_or_target_windows_special_files(alias):
    from lastcopy.device_transfer import unpack
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w') as stream:
        for name in ('metadata/instances.db', 'forms/x.xml', alias):
            entry = tarfile.TarInfo(name)
            entry.size = 6
            stream.addfile(entry, io.BytesIO(b'source'))
    with pytest.raises(ValueError):
        unpack(out.getvalue())


def test_empty_collection_waits_for_records_without_inventing_an_export(tmp_path):
    from lastcopy.device_transfer import DeviceTransfer
    source, inbox, store = setup(tmp_path)
    with sqlite3.connect(source / 'metadata/instances.db') as c:
        c.execute("DELETE FROM instances WHERE jrFormId != 'unrelated-private-form'")
    native = tar_project(source)
    transfer = DeviceTransfer(store, pull=lambda: native)
    transfer.tick(now=1000)
    assert transfer.status()['state'] == 'waiting_for_records'
    assert not list(inbox.iterdir())


def test_restart_finishes_a_lost_seal_acknowledgement_without_recapturing(tmp_path, monkeypatch):
    import lastcopy.device_transfer as module
    source, inbox, store = setup(tmp_path)
    native = tar_project(source)
    write = module.immutable_write
    def lose_seal(path, data):
        if path.name.endswith('.ready.json'):
            raise OSError('process lost before the seal was acknowledged')
        return write(path, data)
    monkeypatch.setattr(module, 'immutable_write', lose_seal)
    module.DeviceTransfer(store, pull=lambda: native).tick(now=1000)
    assert len(list(inbox.glob('*.zip'))) == 1 and not list(inbox.glob('*.ready.json'))
    monkeypatch.setattr(module, 'immutable_write', write)
    def forbidden():
        pytest.fail('Already-captured pending source must resume without another device observation')
    restarted = module.DeviceTransfer(store, pull=forbidden)
    restarted.tick(now=1061)
    assert len(list(inbox.glob('*.zip'))) == 1 and len(list(inbox.glob('*.ready.json'))) == 1
    assert restarted.status()['exports_completed'] == 1 and restarted.status()['state'] == 'watching'
