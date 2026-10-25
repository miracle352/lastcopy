"""Bounded delivery of sealed exports to an explicitly configured HTTPS inbox."""
import json
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from .inventory import digest
from .models import WatchReady
from .monitor import stamp


class Relay:
    def __init__(self,store,*,client=None):
        self.store=store
        if store.settings.sample:raise ValueError('Sample mode prohibits cloud delivery')
        v=store.settings.values
        self.origin=v.get('LASTCOPY_CLOUD_ORIGIN','').rstrip('/')
        u=urlsplit(self.origin)
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path:
            raise ValueError('Explicit HTTPS cloud origin required')
        self.key=v.get('LASTCOPY_TRANSFER_KEY','')
        if len(self.key)<32:raise ValueError('Scoped cloud delivery key required')
        self.root=Path(v['LASTCOPY_WATCH_INBOX']).absolute()
        if not self.root.is_dir() or self.root.is_symlink() or self.root.is_junction():raise ValueError('Ordinary private export inbox required')
        self.owned=client is None
        self.client=client or httpx.Client(timeout=25,trust_env=False,follow_redirects=False)
        self.identity=digest(self.origin.encode())
        with store.connect() as c:c.execute('CREATE TABLE IF NOT EXISTS relay_sent(destination TEXT,sha TEXT,input_id TEXT,acknowledged TEXT,PRIMARY KEY(destination,sha))')

    def poll(self,state):
        r=self.client.get(self.origin+'/device-transfer/status',headers={'Authorization':'Bearer '+self.key,'X-LastCopy-Device-State':state})
        if r.status_code!=200:raise ValueError('Cloud link control unavailable; no sample was substituted')
        body=r.json()
        if (set(body)!={'enabled','interval_seconds','source_device_ids'} or type(body['enabled']) is not bool
                or type(body['interval_seconds']) is not int or not 15<=body['interval_seconds']<=3600
                or not isinstance(body['source_device_ids'],list) or not 1<=len(body['source_device_ids'])<=8
                or any(not isinstance(d,str) or not 1<=len(d)<=512 for d in body['source_device_ids'])):
            raise ValueError('Cloud link control was not validated')
        return body

    def flush(self):
        delivered=0
        seals=sorted(self.root.glob('*.zip.ready.json'))
        if len(seals)>40:raise ValueError('Device delivery budget exceeded')
        for seal in seals:
            if seal.is_symlink() or seal.is_junction() or seal.stat().st_size>4096:raise ValueError('Invalid export seal')
            ready=WatchReady.model_validate_json(seal.read_bytes())
            source=seal.with_name(seal.name[:-11])
            if source.is_symlink() or source.is_junction() or source.stat().st_size!=ready.bytes:raise ValueError('Export changed after sealing')
            with self.store.connect() as c:done=c.execute('SELECT 1 FROM relay_sent WHERE destination=? AND sha=?',(self.identity,ready.sha256)).fetchone()
            if done:continue
            data=source.read_bytes()
            if digest(data)!=ready.sha256:raise ValueError('Export hash differs from its seal')
            r=self.client.post(self.origin+'/device-transfer',headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/zip'},content=data)
            if r.status_code!=201:raise ValueError('Cloud export delivery was not acknowledged')
            receipt=r.json()
            expected={'sha256':ready.sha256,'bytes':len(data),'input_id':digest(b'device\0'+data),'preservation_proof':False}
            if receipt!=expected:raise ValueError('Cloud delivery receipt differs from the original bytes')
            with self.store.connect() as c:c.execute('INSERT OR IGNORE INTO relay_sent VALUES(?,?,?,?)',(self.identity,ready.sha256,receipt['input_id'],stamp()))
            delivered+=1
        return delivered

    def close(self):
        if self.owned:self.client.close()
