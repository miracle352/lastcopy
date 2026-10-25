"""One bounded read-only acceptance of the actual dedicated Collect emulator.

The selected version-2 cohort is synthetic. No Central uploads, recovery writes,
provider calls or new instance identifiers are performed here.
"""
import json
from pathlib import Path

from dotenv import dotenv_values
from lastcopy.config import ROOT, Settings
from lastcopy.device_transfer import DeviceTransfer
from lastcopy.monitor import Monitor
from lastcopy.store import RunStore
from lastcopy.ui import Workspace


def main():
    values = dict(dotenv_values(ROOT / '.env'))
    assert values['ODK_BASE_URL'] == 'http://localhost:8384'
    inbox = ROOT / 'private/realtime-pilot-inbox'
    inbox.mkdir(exist_ok=True)
    values.update(SAMPLE_MODE='false', ODK_READ_PROJECT_ID='4', ODK_READ_FORM_ID='lastcopy_water_point_v1',
                  ODK_READ_PROJECT_NAME='LastCopy water-point pilot (synthetic)', ODK_READ_CONNECTION_ID='local-central-water-pilot',
                  LASTCOPY_WATCH_INBOX=str(inbox), LASTCOPY_WATCH_DEVICE_IDS='["water-emulator-01"]',
                  LASTCOPY_DEVICE_TRANSFER_ENABLED='true', LASTCOPY_ADB_PATH=str(ROOT / 'private/android/sdk/platform-tools/adb.exe'),
                  LASTCOPY_DEVICE_SERIAL='emulator-5558', LASTCOPY_COLLECT_PROJECT_ID='c7ee4de9-247c-42ac-8d78-d5bb9e7d8d4d',
                  LASTCOPY_TRANSFER_DEVICE_ID='water-emulator-01', LASTCOPY_TRANSFER_FORM_ID='lastcopy_water_point_v1',
                  LASTCOPY_TRANSFER_FORM_VERSION='2026102502', LASTCOPY_TRANSFER_SYNTHETIC='true', LASTCOPY_TRANSFER_COLLECTOR_VERSION='v2026.3.5')
    store = RunStore(ROOT / 'private/realtime-pilot', Settings(values))
    transfer = DeviceTransfer(store)
    transfer.tick()
    state = transfer.status()
    assert state['state'] == 'watching' and state['exports_completed'] == 1, state['state']
    archive = next(inbox.glob('*.zip'))
    original = archive.read_bytes()
    monitor = Monitor(store)
    monitor.control('start')
    monitor.tick()
    status = monitor.status()
    assert status['last_run_id']
    view = Workspace(store).view(status['last_run_id'])
    report = view['current_report']
    assert len(report['findings']) == 1 and report['findings'][0]['verdict'] == 'PRESERVED'
    assert report['provider_calls'] == 0 and not report['recovery_executed']
    # A new process observation of unchanged native bytes must not publish again.
    key, *_ = transfer.config()
    transfer.update(key, due=0)
    DeviceTransfer(store).tick()
    assert len(list(inbox.glob('*.zip'))) == 1 and archive.read_bytes() == original
    monitor.control('pause')
    out = ROOT / 'docs/verification/realtime'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'actual-device.json').write_text(json.dumps({'status': 'passed', 'mode': 'Connected · actual emulator-native synthetic evidence',
        'transfer': transfer.status(), 'run_id': report['run_id'], 'verdicts': [f['verdict'] for f in report['findings']],
        'provider_calls': 0, 'central_writes': 0, 'recovery_apply': False, 'input_hashes': report['input_hashes'],
        'deduplicated_after_new_observation': True, 'limitations': ['AOSP test emulator debug access; no physical-phone compatibility claim',
        'Selected synthetic version-2 cohort; version-1 negative control remains retained', 'Near-real-time polling, not uninterrupted device coverage']}, indent=2) + '\n', encoding='utf-8')
    (out / 'actual-device-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS actual automatic ADB export, integrity seal, Central XML/media readback and deterministic preservation; unchanged source deduplicated')


if __name__ == '__main__':
    main()
