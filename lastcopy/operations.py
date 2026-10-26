"""Owner-only operational observations; no credential/configuration export."""
import json
import shutil
from datetime import datetime, timezone
from .models import Contract


class OperationsStatus(Contract):
    backup_state: str
    last_success: str | None
    free_bytes: int
    reserve_bytes: int
    attention: list[str]
    off_host_automatic: bool = False
    off_host_state: str = 'unknown'
    off_host_last_success: str | None = None
    full_machine_restore_verified: bool = False


def status(store):
    path = store.directory/'operations'/'backup.json'
    value = {}
    try:
        if not path.is_symlink() and path.stat().st_size <= 4096:
            value = json.loads(path.read_bytes())
            if not isinstance(value, dict):value = {}
    except (OSError, ValueError):pass
    state = value.get('state') if value.get('state') in ('running','success','failed') else 'unknown'
    last = value.get('last_success')
    attention = []
    try:
        at = datetime.fromisoformat(last)
        if at.tzinfo is None or not 0 <= (datetime.now(timezone.utc)-at).total_seconds() <= 129600:
            raise ValueError()
    except (ValueError,TypeError):
        last = None
        attention.append('No verified successful backup in the past 36 hours. Check the backup service.')
    if state == 'failed':attention.append('The latest backup attempt failed. Older copies were retained.')
    free = shutil.disk_usage(store.directory).free
    reserve = 5*1024**3
    if free < reserve:attention.append('Free space is below the 5 GiB backup reserve. No files were deleted.')
    offsite={}
    try:
        path=store.directory/'operations'/'offsite.json'
        if not path.is_symlink() and path.stat().st_size<=4096:
            offsite=json.loads(path.read_bytes())
            if not isinstance(offsite,dict):offsite={}
    except (OSError,ValueError):pass
    off_state=offsite.get('state') if offsite.get('state') in ('verified','failed') else 'unknown'
    off_last=offsite.get('last_success')
    try:
        at=datetime.fromisoformat(off_last)
        if at.tzinfo is None or not 0<=(datetime.now(timezone.utc)-at).total_seconds()<=129600:raise ValueError()
    except (ValueError,TypeError):off_last=None
    if off_state=='failed':attention.append('Off-host upload or readback failed. Local and older remote backups were retained.')
    elif off_state=='verified' and not off_last:attention.append('No verified off-host readback in the past 36 hours.')
    return {'backup_state':state, 'last_success':last, 'free_bytes':free, 'reserve_bytes':reserve,
            'attention':attention,'off_host_automatic':off_state=='verified' and bool(off_last),
            'off_host_state':off_state,'off_host_last_success':off_last,'full_machine_restore_verified':False}
