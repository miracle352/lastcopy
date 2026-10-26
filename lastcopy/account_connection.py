"""Verified account-owned read scopes on the operator-approved Central origin."""
import json
import os
import time
import uuid
from urllib.parse import urlsplit
from fastapi import HTTPException
from pydantic import Field
from .config import Settings
from .models import Contract
from .store import RunStore,encoded

KEYS = {'ODK_BASE_URL', 'ODK_EMAIL', 'ODK_PASSWORD', 'ODK_READ_PROJECT_ID',
        'ODK_READ_PROJECT_NAME', 'ODK_READ_FORM_ID', 'ODK_READ_CONNECTION_ID'}


class ConnectionSetup(Contract):
    project_id: int = Field(gt=0, le=2147483647)
    form_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$', repr=False)
    password: str = Field(min_length=1, max_length=512, repr=False,json_schema_extra={'writeOnly':True})


class ConnectionSetupStatus(Contract):
    editable: bool
    server_url: str | None
    message: str


def origin(settings):
    value = settings.values.get('LASTCOPY_ALLOWED_CENTRAL_ORIGIN', '').rstrip('/')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        return None
    return value


def load(directory, settings):
    path = directory/'central-connection.json'
    if not path.exists():
        return {}
    if path.is_symlink() or path.stat().st_size > 8192:
        raise ValueError('Invalid account connection file')
    value = json.loads(path.read_bytes())
    if (not isinstance(value, dict) or set(value) != KEYS
            or any(not isinstance(v, str) for v in value.values())
            or value['ODK_BASE_URL'] != origin(settings)):
        raise ValueError('Account connection is outside the approved Central origin')
    ConnectionSetup(project_id=int(value['ODK_READ_PROJECT_ID']), form_id=value['ODK_READ_FORM_ID'],
                    email=value['ODK_EMAIL'], password=value['ODK_PASSWORD'])
    return value


def setup_status(store):
    editable = store.settings.values.get('LASTCOPY_ACCOUNT_STORE') == 'true' and bool(origin(store.settings))
    return {'editable': editable, 'server_url': origin(store.settings) if editable else None,
            'message': ('Use a Central Viewer account granted access to your project. This saves a read-only connection, not a collection or recovery credential.'
                        if editable else 'This connection is managed by the server operator.')}


def save_connection(store, body):
    from .odk_recovery import CentralRecovery
    from .ui import Workspace
    base = origin(store.settings)
    if not setup_status(store)['editable'] or not base:
        raise HTTPException(403, 'Account connection setup is not enabled on this server')
    # The fixed HTTPS origin prevents account-supplied URLs reaching metadata/internal services.
    with RunStore(store.account_root/'account-connection-admission',store.settings).lease() as admitted, store.lease() as held:
        if not admitted or not held:
            raise HTTPException(409, 'Wait for the current check to finish before changing its connection')
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("SELECT 1 FROM jobs WHERE state IN ('queued','running')").fetchone():
                raise HTTPException(409, 'Finish or cancel queued checks before changing the connection')
            c.execute('CREATE TABLE IF NOT EXISTS connection_attempts(id INTEGER PRIMARY KEY CHECK(id=1),attempts INTEGER NOT NULL,until REAL NOT NULL)')
            row=c.execute('SELECT attempts,until FROM connection_attempts WHERE id=1').fetchone()
            count,until=row if row and row[1]>time.time() else (0,time.time()+900)
            if count >= 5:
                raise HTTPException(429, 'Wait fifteen minutes before testing more Central credentials')
            c.execute('INSERT OR REPLACE INTO connection_attempts VALUES(1,?,?)', (count+1,until))
        values = {'ODK_BASE_URL': base, 'ODK_EMAIL': body.email, 'ODK_PASSWORD': body.password,
                  'ODK_READ_PROJECT_ID': str(body.project_id), 'ODK_READ_FORM_ID': body.form_id,
                  'ODK_READ_PROJECT_NAME': 'Pending authenticated identity check', 'ODK_READ_CONNECTION_ID': 'account-central-'+str(body.project_id)}
        selected = Settings(dict(store.settings.values, **values))
        remote = CentralRecovery(selected, read_only=True)
        try:
            remote.begin()
            remote.login()
            status, raw = remote.request('GET', f'/v1/projects/{body.project_id}')
            if status != 200:
                raise ValueError('Project inaccessible')
            project = json.loads(raw)
            if project.get('id') != body.project_id or not isinstance(project.get('name'), str) or not 1 <= len(project['name']) <= 512:
                raise ValueError('Project identity mismatch')
            status, raw = remote.request('GET', remote.scope())
            if status != 200 or json.loads(raw).get('xmlFormId') != body.form_id:
                raise ValueError('Form identity mismatch')
            values['ODK_READ_PROJECT_NAME'] = project['name']
        except Exception:
            raise HTTPException(409, 'Central access or project/form identity could not be verified. Nothing was saved or uploaded.') from None
        finally:
            remote.client.close()
        path = store.directory/'central-connection.json'
        temporary = store.directory/('central-'+str(uuid.uuid4())+'.tmp')
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as output:
                output.write(encoded(values))
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        store.settings = Settings(dict(store.settings.values, **values))
        return Workspace(store).connection()
