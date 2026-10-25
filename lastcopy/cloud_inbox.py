"""Restricted authenticated device delivery. Delivery is never preservation proof."""
from .inventory import inventory,digest
from .monitor import Monitor
from .device_transfer import immutable_write
from .store import encoded
from .monitor import stamp
from datetime import datetime,timezone

STATES={'waiting_for_device','waiting_for_stable_export','waiting_for_records','watching','device_unreachable',
        'invalid_export','error','paused','budget_reached','not_configured'}


def initialize(store):
    with store.connect() as c:c.executescript('''
        CREATE TABLE IF NOT EXISTS scoped_remote_links(config TEXT PRIMARY KEY,state TEXT,seen TEXT);
        CREATE TABLE IF NOT EXISTS scoped_remote_deliveries(config TEXT,sha TEXT,received TEXT,PRIMARY KEY(config,sha));
    ''')


def poll(store,state):
    if store.settings.sample:raise ValueError('Sample mode prohibits device links')
    if state not in STATES:raise ValueError('Unsupported device state')
    initialize(store)
    key,_,roster,_,_,_=Monitor(store).config()
    with store.connect() as c:c.execute('INSERT OR REPLACE INTO scoped_remote_links VALUES(?,?,?)',(key,state,stamp()))
    return {'enabled':bool(Monitor(store).row(key)['enabled']),'interval_seconds':30,'source_device_ids':roster}


def status(store):
    initialize(store)
    try:key,*_=Monitor(store).config()
    except (ValueError,KeyError):return {'configured':False,'state':'not_configured','message':'The cloud device scope is not configured.'}
    with store.connect() as c:
        link=c.execute('SELECT state,seen FROM scoped_remote_links WHERE config=?',(key,)).fetchone()
        count,last=c.execute('SELECT COUNT(*),MAX(received) FROM scoped_remote_deliveries WHERE config=?',(key,)).fetchone()
    state=link[0] if link else 'waiting_for_device'
    if link and (datetime.now(timezone.utc)-datetime.fromisoformat(link[1])).total_seconds()>150:state='device_unreachable'
    message=('Desktop link is connected. Waiting for completed device exports.' if state in ('waiting_for_device','waiting_for_records','watching') and link else
        'Waiting for the paired desktop link. Saved results do not establish fresh device coverage.')
    if state in ('invalid_export','error','budget_reached'):message='The desktop link needs attention. No new complete device export was accepted.'
    return {'configured':True,'state':state,'message':message,'exports_completed':count,'max_exports':40,
        'last_device_seen_at':link[1] if link else None,'last_export_at':last,'interval_seconds':30}


def accept(store,data):
    if store.settings.sample:raise ValueError('Sample mode prohibits remote device delivery')
    key,root,roster,_,_,target=Monitor(store).config()
    observed=inventory(data,store.settings)
    if observed.manifest.device_id not in roster or any(v.form_id!=target['form_id'] for v in observed.versions):
        raise ValueError('Device or form is outside the configured collection scope')
    if observed.manifest.captured_at=='unknown':raise ValueError('A known capture time is required')
    sha=digest(data)
    name='received-'+sha+'.zip'
    path=root/name
    # This is an operator-configured directory. Requests supply bytes, no paths.
    with store.lock:
        if not path.exists() and len(list(root.glob('*.zip')))>=40:
            raise ValueError('Device inbox budget reached; operator retention review required')
        item=store.register('device',data)
        immutable_write(path,data)
        immutable_write(path.with_name(name+'.ready.json'),encoded({'schema_version':1,'sha256':sha,'bytes':len(data)}))
        initialize(store)
        with store.connect() as c:c.execute('INSERT OR IGNORE INTO scoped_remote_deliveries VALUES(?,?,?)',(key,sha,stamp()))
    return {'input_id':item.input_id,'sha256':sha,'bytes':len(data),'preservation_proof':False}
