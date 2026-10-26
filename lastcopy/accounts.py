"""Verified public beta accounts; private stores never inherit operator credentials.

Cognito handles passwords/email. Its access token is sent back to GetUser on the
server, never exposed to the browser. Only the returned immutable sub selects a
store. Browser sessions are random, hashed, expiring and persisted locally.
"""
import hashlib,json,re,secrets,time,sqlite3,shutil
from typing import Literal
import httpx
from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel,ConfigDict,Field
from .cloud_access import CloudAccess,COOKIE
from .config import Settings,LIMITS
from .store import RunStore
from .inventory import ImportRejected,digest

router=APIRouter(prefix='/account')

class AccountStore(RunStore):
    def __init__(self,directory,settings,root):
        super().__init__(directory,settings);self.account_root=root

    def admission(self):return RunStore(self.account_root/'account-admission',self.settings).lease()

    def register(self,kind,data):
        with self.admission() as held:
            if not held:raise ImportRejected('The beta storage gate is busy; retry shortly')
            with self.connect() as c:
                known=c.execute('SELECT 1 FROM inputs WHERE id=?',(digest(kind.encode()+b'\0'+data),)).fetchone()
                total=c.execute('SELECT COALESCE(SUM(length(data)),0) FROM inputs').fetchone()[0]
            if not known and (total+len(data)>104857600 or shutil.disk_usage(self.account_root).free<5368709120):
                raise ImportRejected('Beta input storage capacity reached (100 MiB per account, with a server free-space reserve)')
            return super().register(kind,data)

    def enqueue(self,request):
        from .models import RunManifest
        manifest=RunManifest.model_validate_json(self.input(request.manifest_id,'manifest'))
        with self.admission() as held:
            if not held:raise ImportRejected('The beta job gate is busy; retry shortly')
            with self.connect() as c:
                known=c.execute('SELECT 1 FROM jobs WHERE run_id=?',(manifest.run_id,)).fetchone()
                count=c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
            if known:return super().enqueue(request)
            if count>=25:raise ImportRejected('This beta account has reached its 25 saved-check limit. Existing reports remain available.')
            active=0
            for path in (self.account_root/'accounts').glob('*/lastcopy.sqlite3'):
                if not re.fullmatch(r'[a-f0-9]{64}',path.parent.name):continue
                with sqlite3.connect(path,timeout=2) as c:active+=c.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0]
            if active>=4:raise ImportRejected('The shared beta job limit is four active checks. Retry after a check finishes.')
            return super().enqueue(request)

class AuthInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email:str=Field(min_length=3,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password:str|None=Field(default=None,min_length=12,max_length=256)
    code:str|None=Field(default=None,min_length=6,max_length=8,pattern=r'^\d+$')

class Cognito:
    def __init__(self,settings):self.values=settings.values

    def call(self,action,body):
        pool=self.values.get('COGNITO_POOL_ID','');client=self.values.get('COGNITO_CLIENT_ID','')
        if not re.fullmatch(r'ap-southeast-1_[A-Za-z0-9]+',pool) or not re.fullmatch(r'[a-z0-9]{1,128}',client):
            raise HTTPException(503,'Account email verification is not configured yet. You can try the public demo.')
        headers={'X-Amz-Target':'AWSCognitoIdentityProviderService.'+action,'Content-Type':'application/x-amz-json-1.1'}
        with httpx.Client(trust_env=False,follow_redirects=False,timeout=20) as remote:
            with remote.stream('POST','https://cognito-idp.ap-southeast-1.amazonaws.com/',headers=headers,json=body) as r:
                raw=bytearray()
                for chunk in r.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>65536:raise ValueError('Identity response exceeded limit')
                result=json.loads(raw)
                if r.status_code!=200:
                    code=str(result.get('__type','')).split('#')[-1]
                    if code in ('TooManyRequestsException','LimitExceededException'):raise HTTPException(429,'Email or sign-in limit reached. Please wait before trying again.')
                    if code in ('NotAuthorizedException','UserNotFoundException'):raise HTTPException(401,'Email or password was not accepted.')
                    if code in ('CodeMismatchException','ExpiredCodeException','InvalidPasswordException','InvalidParameterException'):raise HTTPException(422,'Check the code and password requirements, or request a new code.')
                    if code=='UserNotConfirmedException':raise HTTPException(403,'Verify your email before signing in.')
                    # Account enumeration and upstream diagnostic bodies stay private.
                    if code=='UsernameExistsException':return {}
                    raise ValueError('Identity provider unavailable')
                if not isinstance(result,dict):raise ValueError('Invalid identity response')
                return result

class Accounts:
    def __init__(self,store):
        self.store=store;self.gate=CloudAccess(store)
        with store.connect() as c:c.executescript('''
            CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,email_key TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account_sessions(id TEXT PRIMARY KEY,account_id TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS account_limits(id TEXT PRIMARY KEY,attempts INTEGER NOT NULL,until REAL NOT NULL);
        ''')

    def throttle(self,action,email):
        now=time.time()
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM account_limits WHERE until<=?',(now,))
            # Global daily email bound protects the free pilot; the per-address
            # bound applies to every auth operation and survives restarts.
            budgets=[('address:'+self.gate.digest(email),12,900)]
            if action in ('signup','resend','forgot'):budgets.extend([('email-hour',10,3600),('email-day',40,86400)])
            else:budgets.append(('auth-hour',120,3600))
            rows=[]
            for key,limit,period in budgets:
                row=c.execute('SELECT attempts,until FROM account_limits WHERE id=?',(key,)).fetchone()
                count,until=row if row else (0,now+period)
                if count>=limit:raise HTTPException(429,'The beta request limit has been reached. Wait before trying again; judges can still use the demo.')
                rows.append((key,count+1,until))
            c.executemany('INSERT OR REPLACE INTO account_limits VALUES(?,?,?)',rows)

    def create_session(self,sub,email):
        if not re.fullmatch(r'[a-f0-9-]{36}',sub):raise ValueError('Invalid verified identity')
        account=hashlib.sha256(sub.encode()).hexdigest();now=time.time()
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            existing=c.execute('SELECT id FROM accounts WHERE id=?',(account,)).fetchone()
            if not existing and c.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]>=100:raise HTTPException(429,'This beta has reached its 100-account capacity. The public demo remains available.')
            c.execute('INSERT OR REPLACE INTO accounts VALUES(?,?)',(account,self.gate.digest(email)))
            c.execute('DELETE FROM account_sessions WHERE expires<=?',(now,))
            c.execute('DELETE FROM account_sessions WHERE id IN (SELECT id FROM account_sessions WHERE account_id=? ORDER BY expires DESC LIMIT -1 OFFSET 4)',(account,))
            token=secrets.token_urlsafe(32)
            c.execute('INSERT INTO account_sessions VALUES(?,?,?)',(self.gate.digest(token),account,now+28800))
        return token

    def store_for(self,token):
        if not token or not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):return None
        with self.store.connect() as c:row=c.execute('SELECT account_id FROM account_sessions WHERE id=? AND expires>?',(self.gate.digest(token),time.time())).fetchone()
        if not row:return None
        if not re.fullmatch(r'[a-f0-9]{64}',row[0]):raise ValueError('Invalid account identity')
        # No ODK, sponsor, device, session or transport credentials cross this boundary.
        values={k:v for k,v in self.store.settings.values.items() if k in LIMITS}
        values.update(SAMPLE_MODE='false',LASTCOPY_ACCOUNT_STORE='true')
        from .account_connection import load
        values['LASTCOPY_ALLOWED_CENTRAL_ORIGIN']=self.store.settings.values.get('ODK_BASE_URL','')
        directory=self.store.directory/'accounts'/row[0]
        try:values.update(load(directory,Settings(values)))
        except (ValueError,OSError):values['LASTCOPY_CONNECTION_ERROR']='true'
        selected=AccountStore(directory,Settings(values),self.store.directory)
        selected.recover_interrupted()
        return selected

    def revoke(self,token):
        with self.store.connect() as c:c.execute('DELETE FROM account_sessions WHERE id=?',(self.gate.digest(token or ''),))

    def revoke_email(self,email):
        with self.store.connect() as c:c.execute('DELETE FROM account_sessions WHERE account_id IN (SELECT id FROM accounts WHERE email_key=?)',(self.gate.digest(email),))

@router.post('/{action}')
async def account_action(action:Literal['signup','confirm','resend','login','forgot','reset'],request:Request):
    from .api import app,get_store,bounded_body
    store=app.dependency_overrides.get(get_store,get_store)();accounts=Accounts(store)
    if not accounts.gate.enabled:raise HTTPException(409,'Public accounts require the configured hosted application')
    try:body=AuthInput.model_validate_json(await bounded_body(request,2048))
    except ValueError:raise HTTPException(422,'Enter a valid email, password and confirmation code as required.') from None
    email=body.email.lower();accounts.throttle(action,email)
    remote=Cognito(store.settings);client=remote.values.get('COGNITO_CLIENT_ID','')
    payload={'ClientId':client,'Username':email}
    try:
        if action in ('signup','login','reset') and not body.password:raise HTTPException(422,'Enter a password of at least 12 characters, including upper/lowercase letters and a number.')
        if action in ('confirm','reset') and not body.code:raise HTTPException(422,'Enter the code from your email.')
        if action=='login':
            result=await run_in_threadpool(remote.call,'InitiateAuth',{'ClientId':client,'AuthFlow':'USER_PASSWORD_AUTH','AuthParameters':{'USERNAME':email,'PASSWORD':body.password}})
            token=result.get('AuthenticationResult',{}).get('AccessToken')
            if not token:raise HTTPException(403,'Additional authentication is required. No session was created.')
            user=await run_in_threadpool(remote.call,'GetUser',{'AccessToken':token})
            attributes={a['Name']:a['Value'] for a in user['UserAttributes']}
            if attributes.get('email_verified')!='true':raise HTTPException(403,'Verify your email before signing in.')
            session=accounts.create_session(attributes['sub'],email)
            response=JSONResponse({'authenticated':True},headers={'Cache-Control':'no-store'})
            response.set_cookie(COOKIE,session,max_age=28800,httponly=True,secure=True,samesite='strict',path='/')
            return response
        if action=='signup':payload.update(Password=body.password,UserAttributes=[{'Name':'email','Value':email}])
        if action=='confirm':payload.update(ConfirmationCode=body.code,ForceAliasCreation=False)
        if action=='reset':payload.update(ConfirmationCode=body.code,Password=body.password)
        await run_in_threadpool(remote.call,{'signup':'SignUp','confirm':'ConfirmSignUp','resend':'ResendConfirmationCode','forgot':'ForgotPassword','reset':'ConfirmForgotPassword'}[action],payload)
        if action=='reset':accounts.revoke_email(email)
        return JSONResponse({'accepted':True,'next':'verify_email' if action in ('signup','resend') else 'sign_in' if action in ('confirm','reset') else 'reset_password'},headers={'Cache-Control':'no-store'})
    except HTTPException:raise
    except (ValueError,KeyError,TypeError,httpx.HTTPError):raise HTTPException(503,'Account verification is unavailable. No sign-in was completed; please retry later.') from None
