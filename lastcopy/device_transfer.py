"""Bounded, read-only native Collect export producer for an operator-paired device.

No device is discovered, rooted, stopped, edited or submitted by this service.
Two byte-identical observations are required. Recovery remains a separate action.
"""
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import threading
import time
from pathlib import Path, PurePosixPath

from .inventory import digest
from .models import WatchReady
from .store import RunStore, encoded
from .monitor import stamp
from scripts.package_collect_project import package, NoCollectedRecords

MAX_TAR = 40 * 1024 * 1024


def unpack(data):
    if len(data) > MAX_TAR:
        raise ValueError('Native export exceeds transport limit')
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as stream:
        for count, member in enumerate(stream, 1):
            path = PurePosixPath(member.name)
            if (count > 500 or path.is_absolute() or '..' in path.parts or '\\' in member.name or ':' in member.name
                    or member.name.rstrip('/') != path.as_posix()
                    or any(p.endswith(('.', ' ')) or p.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for p in path.parts)
                    or not path.parts or path.parts[0] not in ('forms', 'instances', 'metadata') or member.name in files):
                raise ValueError('Unsupported native export path')
            if member.isdir():
                continue
            if not member.isfile() or member.size > 10485760:
                raise ValueError('Native export contains a linked or oversized entry')
            total += member.size
            if total > 33554432:
                raise ValueError('Native export exceeds expanded byte budget')
            with stream.extractfile(member) as source:
                files[member.name] = source.read(member.size + 1)
            if len(files[member.name]) != member.size:
                raise ValueError('Incomplete native export')
    if 'metadata/instances.db' not in files:
        raise ValueError('Native completion database is absent')
    return files


def immutable_write(path, data):
    if path.is_symlink() or path.is_junction():
        raise ValueError('Linked output is not accepted')
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Existing output differs; no source was overwritten')
        return
    partial = path.with_name(path.name + '.partial')
    # A partial is producer-owned unfinished output, never an accepted source.
    if partial.exists():
        if partial.is_symlink() or partial.is_junction():
            raise ValueError('Linked temporary output is not accepted')
        partial.unlink()
    with partial.open('xb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    partial.rename(path)


class DeviceTransfer:
    def __init__(self, store, *, pull=None):
        self.store = store
        self.pull = pull or self.adb_pull
        with store.connect() as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS transfer_state(id TEXT PRIMARY KEY,state TEXT,message TEXT,due REAL DEFAULT 0,
                    seen TEXT,last_export TEXT,exports INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS transfer_jobs(config TEXT,fingerprint TEXT,input_id TEXT,state TEXT,
                    PRIMARY KEY(config,fingerprint));
            ''')

    def config(self):
        v = self.store.settings.values
        if self.store.settings.sample or v.get('LASTCOPY_DEVICE_TRANSFER_ENABLED') != 'true':
            raise ValueError('Device transfer is not enabled')
        project = v.get('LASTCOPY_COLLECT_PROJECT_ID', '')
        serial = v.get('LASTCOPY_DEVICE_SERIAL', '')
        device = v.get('LASTCOPY_TRANSFER_DEVICE_ID', '')
        form = v.get('LASTCOPY_TRANSFER_FORM_ID', '')
        version = v.get('LASTCOPY_TRANSFER_FORM_VERSION')
        if not re.fullmatch(r'[a-fA-F0-9-]{36}', project) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', serial):
            raise ValueError('Explicit paired-device and native-project identities are required')
        if not device or len(device) > 512 or not form or len(form) > 512:
            raise ValueError('Explicit device and form scope required')
        synthetic = v.get('LASTCOPY_TRANSFER_SYNTHETIC')
        if synthetic not in ('true', 'false') or (version and synthetic != 'true'):
            raise ValueError('Explicit provenance required; version filtering is limited to synthetic cohorts')
        inbox = Path(v['LASTCOPY_WATCH_INBOX']).absolute()
        if not inbox.is_dir() or inbox.is_symlink() or inbox.is_junction():
            raise ValueError('Ordinary private inbox required')
        interval = int(v.get('LASTCOPY_TRANSFER_INTERVAL_SECONDS', '30'))
        maximum = int(v.get('LASTCOPY_TRANSFER_MAX_EXPORTS', '40'))
        if not 15 <= interval <= 3600 or not 1 <= maximum <= 40:
            raise ValueError('Device polling/export budget outside supported bounds')
        config = {'project': project, 'serial': serial, 'device': device, 'form': form, 'version': version,
                  'synthetic': synthetic == 'true', 'inbox': str(inbox.resolve()), 'collector': v.get('LASTCOPY_TRANSFER_COLLECTOR_VERSION', 'unknown')}
        key = digest(encoded(config))
        with self.store.connect() as c:
            c.execute("INSERT OR IGNORE INTO transfer_state(id,state,message) VALUES(?,'waiting_for_device','Waiting for the paired device')", (key,))
        return key, config, interval, maximum

    def update(self, key, **values):
        if not set(values) <= {'state', 'message', 'due', 'seen', 'last_export', 'exports'}:
            raise ValueError('Unknown transfer state')
        with self.store.connect() as c:
            c.execute('UPDATE transfer_state SET ' + ','.join(k + '=?' for k in values) + ' WHERE id=?', (*values.values(), key))

    def row(self, key):
        with self.store.connect() as c:
            c.row_factory = __import__('sqlite3').Row
            return dict(c.execute('SELECT * FROM transfer_state WHERE id=?', (key,)).fetchone())

    def status(self):
        try:
            key, cfg, interval, maximum = self.config()
        except (ValueError, KeyError, TypeError):
            return {'configured': False, 'state': 'not_configured', 'message': 'Automatic device transfer is not configured. Reviewed ZIP uploads remain available.'}
        row = self.row(key)
        return {'configured': True, 'state': row['state'], 'message': row['message'], 'device_id': cfg['device'],
                'synthetic': cfg['synthetic'], 'interval_seconds': interval, 'exports_completed': row['exports'],
                'max_exports': maximum, 'last_device_seen_at': row['seen'], 'last_export_at': row['last_export']}

    def adb_pull(self):
        _, cfg, _, _ = self.config()
        executable = Path(self.store.settings.values.get('LASTCOPY_ADB_PATH', ''))
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError('Operator-configured adb executable is unavailable')
        remote = '/sdcard/Android/data/org.odk.collect.android/files/projects/' + cfg['project']
        # No shell interpolation, selectors, arbitrary paths, root or write commands.
        process = subprocess.Popen([str(executable), '-s', cfg['serial'], 'exec-out', 'tar', '-C', remote,
                                    '-cf', '-', 'forms', 'instances', 'metadata'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        result = []
        def read():
            result.append(process.stdout.read(MAX_TAR + 1))
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        reader.join(45)
        if reader.is_alive():
            process.kill(); process.wait(timeout=5); reader.join(5)
            raise OSError('Paired device export timed out')
        try:
            code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=5)
            raise OSError('Paired device export did not finish') from None
        finally:
            process.stdout.close()
        if code or not result or not result[0]:
            raise OSError('Paired device export is unavailable')
        if len(result[0]) > MAX_TAR:
            raise ValueError('Native export exceeds transport byte limit')
        return result[0]

    def publish(self, key, fingerprint, input_id, cfg):
        data = self.store.input(input_id, 'device')
        inbox = Path(cfg['inbox'])
        if len(list(inbox.iterdir())) > 97:
            raise ValueError('Private inbox file budget reached')
        path = inbox / ('device-' + fingerprint + '.zip')
        immutable_write(path, data)
        immutable_write(path.with_name(path.name + '.ready.json'), encoded(WatchReady(schema_version=1, sha256=digest(data), bytes=len(data)).model_dump()))
        # Intent was persisted before publication; a lost acknowledgement reuses it.
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            changed = c.execute("UPDATE transfer_jobs SET state='published' WHERE config=? AND fingerprint=? AND state='pending'", (key, fingerprint)).rowcount
            if changed:
                c.execute("UPDATE transfer_state SET exports=exports+1,last_export=? WHERE id=?", (stamp(), key))

    def tick(self, now=None):
        try:
            key, cfg, interval, maximum = self.config()
        except (ValueError, KeyError, TypeError):
            return
        now = time.time() if now is None else now
        with RunStore(self.store.directory / 'transfer-lease', self.store.settings).lease() as held:
            if not held or now < self.row(key)['due']:
                return
            self.update(key, due=now + interval)
            try:
                with self.store.connect() as c:
                    pending = c.execute("SELECT fingerprint,input_id FROM transfer_jobs WHERE config=? AND state='pending' LIMIT 1", (key,)).fetchone()
                if pending:
                    self.publish(key, *pending, cfg)
                    self.update(key, state='watching', message='The previously captured export was delivered after restart. Its original capture time is retained.')
                    return
                if self.row(key)['exports'] >= maximum:
                    self.update(key, state='budget_reached', message='Device export budget reached. Retained sources were not deleted; review this session.')
                    return
                first_raw = self.pull()
                first = unpack(first_raw)
                second = unpack(self.pull())
                self.update(key, seen=stamp())
                if first != second:
                    self.update(key, state='waiting_for_stable_export', message='The device is still saving changes. We will check again when its files settle.')
                    return
                fingerprint = digest(encoded({name: digest(data) for name, data in sorted(first.items())}))
                with self.store.connect() as c:
                    previous = c.execute('SELECT state FROM transfer_jobs WHERE config=? AND fingerprint=?', (key, fingerprint)).fetchone()
                if previous:
                    self.update(key, state='watching', message='Device checked. No new or changed inspections were found.')
                    return
                capture = self.store.directory / 'device-captures'
                capture.mkdir(exist_ok=True)
                if sum(p.stat().st_size for p in capture.iterdir() if p.is_file()) + len(first_raw) > 268435456:
                    raise ValueError('Private native-capture storage budget reached')
                with tempfile.TemporaryDirectory(prefix='collect-transfer-') as directory:
                    source = Path(directory) / cfg['project']
                    source.mkdir()
                    for name, data in first.items():
                        path = source / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                    data, _ = package(source, cfg['form'], cfg['device'], cfg['synthetic'], cfg['collector'], cfg['version'])
                immutable_write(capture / (digest(first_raw) + '.tar'), first_raw)
                registered = self.store.register('device', data)
                with self.store.connect() as c:
                    c.execute("INSERT INTO transfer_jobs VALUES(?,?,?,'pending')", (key, fingerprint, registered.input_id))
                self.publish(key, fingerprint, registered.input_id, cfg)
                self.update(key, state='watching', message='New device files received. Checking their server copies next.')
            except NoCollectedRecords:
                self.update(key, state='waiting_for_records', message='Your device is ready. Complete an inspection in Collect to start checking its server copy.')
            except OSError:
                self.update(key, state='device_unreachable', message='We cannot reach the paired device. Reconnect it to resume checks. Saved results still refer to earlier exports.')
            except (ValueError, tarfile.TarError, KeyError):
                self.update(key, state='invalid_export', message='Device export could not be validated or a storage limit was reached. No new complete source was accepted.')


class DeviceTransferService:
    def __init__(self, store):
        self.transfer = DeviceTransfer(store)
        self.stop = threading.Event()
        self.thread = None

    def start(self):
        if not self.transfer.status()['configured']:
            return
        def work():
            from .monitor import Monitor
            while not self.stop.is_set():
                try:
                    if Monitor(self.transfer.store).status().get('enabled'):
                        self.transfer.tick()
                except Exception:
                    # Persist a code-owned error, never raw device output or success.
                    try:
                        key, *_ = self.transfer.config()
                        self.transfer.update(key, state='error', message='Device transfer stopped on an unexpected local error. No new coverage was established.')
                    except (ValueError, KeyError, TypeError):
                        pass
                self.stop.wait(5)
        self.thread = threading.Thread(target=work, name='lastcopy-native-device-transfer', daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=2)
