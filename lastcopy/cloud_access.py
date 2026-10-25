"""Single-owner hosted gate. Local loopback behavior remains unchanged.

The transport key is server-to-server only. An owner cookie is additionally
required; neither an arbitrary Origin nor the transport key grants owner access.
"""
import hashlib
import hmac
import re
import secrets
import time
from fastapi import HTTPException

COOKIE='lastcopy_session'


class CloudAccess:
    def __init__(self,store):
        self.store=store
        v=store.settings.values
        self.enabled=v.get('LASTCOPY_CLOUD_ACCESS')=='true'
        self.transport=v.get('LASTCOPY_TRANSPORT_KEY','')
        self.key=v.get('LASTCOPY_SESSION_KEY','')
        self.password=v.get('LASTCOPY_OWNER_PASSWORD_HASH','')
        if self.enabled and (len(self.transport)<32 or len(self.key)<32 or
                not re.fullmatch(r'[a-f0-9]{32}:[a-f0-9]{128}',self.password)):
            raise HTTPException(503,'Hosted access is not fully configured')
        if self.enabled:
            with store.connect() as c:c.executescript('''
                CREATE TABLE IF NOT EXISTS owner_sessions(id TEXT PRIMARY KEY,expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS owner_login(id INTEGER PRIMARY KEY CHECK(id=1),attempts INTEGER,until REAL);
            ''')

    def transport_ok(self,header):
        return hmac.compare_digest((header or '').encode(),('Bearer '+self.transport).encode())

    def digest(self,token):
        return hmac.new(self.key.encode(),token.encode(),hashlib.sha256).hexdigest()

    def owner_ok(self,token):
        if not token or not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):return False
        with self.store.connect() as c:
            row=c.execute('SELECT expires FROM owner_sessions WHERE id=?',(self.digest(token),)).fetchone()
        return bool(row and row[0]>time.time())

    def login(self,password):
        if not self.enabled:raise HTTPException(409,'Owner login is used only on a configured hosted service')
        now=time.time()
        # Serialize the read/check/update so parallel requests cannot evade limits.
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT attempts,until FROM owner_login WHERE id=1').fetchone()
            attempts=row[0] if row and row[1]>now else 0
            until=row[1] if row and row[1]>now else now+900
            if attempts>=5:raise HTTPException(429,'Too many attempts. Wait 15 minutes before trying again.')
            salt,expected=self.password.split(':')
            actual=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
            valid=hmac.compare_digest(actual,expected)
            c.execute('INSERT OR REPLACE INTO owner_login VALUES(1,?,?)',(0 if valid else attempts+1,until))
            if valid:
                c.execute('DELETE FROM owner_sessions WHERE expires<=?',(now,))
                # Explicitly bound the persistent session set.
                c.execute('DELETE FROM owner_sessions WHERE id IN (SELECT id FROM owner_sessions ORDER BY expires DESC LIMIT -1 OFFSET 19)')
                token=secrets.token_urlsafe(32)
                c.execute('INSERT INTO owner_sessions VALUES(?,?)',(self.digest(token),now+28800))
        if not valid:raise HTTPException(401,'The passphrase was not accepted')
        return token

    def logout(self,token):
        with self.store.connect() as c:c.execute('DELETE FROM owner_sessions WHERE id=?',(self.digest(token or ''),))
