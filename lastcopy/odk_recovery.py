"""Documented Central endpoints, bounded captures, no arbitrary target URLs.

Normalized scope/attachment indexes are explicitly LOCAL derivations linked to
captured authenticated GET responses; they are never labelled native HTTP bodies.
Session credentials and authorization headers are neither persisted nor logged.
"""
import json
import time
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit
import httpx
from .inventory import digest, parse_xml
from .models import Destination, EvidenceReceipt, SourceSnapshot, SubmissionVersion, MediaReference
from .recovery import archive
from .store import encoded


def configured_target(settings):
    v = settings.values
    if v.get('ODK_TEST_PROJECT') != 'true': raise ValueError('Dedicated ODK test project is not configured')
    target = Destination(connection_id=v.get('ODK_CONNECTION_ID','local-central-test'),
        project_id=int(v.get('ODK_RECOVERY_PROJECT_ID') or v['ODK_PROJECT_ID']),
        form_id=v.get('ODK_RECOVERY_FORM_ID') or v['ODK_FORM_ID'], environment='dedicated_synthetic_test',
        mapping_provenance={'origin':'coordinator_attestation','reference':v.get('ODK_MAPPING_REFERENCE','configured-synthetic-test-project')})
    return target.model_dump()


def configured_read_target(settings):
    v=settings.values
    if not v.get('ODK_READ_PROJECT_ID'):return configured_target(settings)
    if not all(v.get(k) for k in ('ODK_READ_FORM_ID','ODK_READ_PROJECT_NAME')):
        raise ValueError('Explicit read project name and form ID are required')
    return Destination(connection_id=v.get('ODK_READ_CONNECTION_ID','local-central-collection'),
        project_id=int(v['ODK_READ_PROJECT_ID']),form_id=v['ODK_READ_FORM_ID'],environment='read_only_collection',
        mapping_provenance={'origin':'coordinator_attestation','reference':'Operator configured collection read scope'}).model_dump()


class CentralRecovery:
    def __init__(self, settings, *, client=None, read_only=False):
        if settings.sample: raise ValueError('SAMPLE_MODE prohibits Central requests')
        self.settings = settings
        self.read_only=read_only
        self.target = configured_read_target(settings) if read_only else configured_target(settings)
        self.base = settings.values['ODK_BASE_URL'].rstrip('/')
        url = urlsplit(self.base)
        if (url.scheme != 'https' and not (url.scheme=='http' and url.hostname in ('localhost','127.0.0.1','::1'))
            or url.username or url.password or url.query or url.fragment or url.path not in ('','/')):
            raise ValueError('Central requires HTTPS or loopback HTTP without URL credentials/path')
        self.client = client or httpx.Client(timeout=15, follow_redirects=False, trust_env=False)
        self.token = None
        self.deadline = 0
        self.calls = 0
        self.total_bytes = 0

    def begin(self):
        self.deadline = min(time.monotonic()+120,getattr(self,'apply_deadline',float('inf')))
        self.calls = self.total_bytes = 0

    def request(self, method, path, **kwargs):
        if time.monotonic() > self.deadline or self.calls >= 200: raise ValueError('Central request budget exceeded')
        self.calls += 1
        headers = dict(kwargs.pop('headers',{}))
        if self.token: headers['Authorization'] = 'Bearer '+self.token
        # Stream untrusted responses, enforcing byte limits before buffering.
        with self.client.stream(method,self.base+path,headers=headers,**kwargs) as response:
            data = bytearray()
            for chunk in response.iter_bytes():
                if time.monotonic()>self.deadline: raise ValueError('Central capture deadline exceeded')
                self.total_bytes += len(chunk)
                if len(data)+len(chunk)>1048576 or self.total_bytes>8388608:
                    raise ValueError('Central capture exceeds response/aggregate byte budget')
                data.extend(chunk)
            return response.status_code,bytes(data)

    def login(self):
        status, body = self.request('POST','/v1/sessions',json={
            'email':self.settings.values['ODK_EMAIL'], 'password':self.settings.values['ODK_PASSWORD']})
        if status != 200: raise ValueError(f'Central authentication failed HTTP {status}')
        self.token = json.loads(body)['token']

    def scope(self):
        return f"/v1/projects/{self.target['project_id']}/forms/{quote(self.target['form_id'],safe='')}"

    def capture(self, run):
        if run.destination.model_dump() != self.target: raise ValueError('Central capture target mismatch')
        self.begin(); self.login()
        at = datetime.now(timezone.utc).isoformat()
        sid = 'central-readback-'+digest((at+str(self.target)).encode())[:24]
        files,receipts,versions,lists = {},[],[],{}
        scope = self.scope()

        def get(path, *, version=None, attachment=None, allow_missing=False):
            status,body = self.request('GET',path)
            if status != 200 and not (allow_missing and status==404):
                raise ValueError(f'Central GET failed HTTP {status}; absence not established')
            name = f'native/{len(receipts)+1:04}.bin'
            files[name] = body
            rid = sid+'-get-'+str(len(receipts)+1)
            receipts.append(EvidenceReceipt(evidence_id=rid,source_snapshot_id=sid,source_file=name,
                archive_sha256=None,captured_at=at,query_receipt_id=None,request_method='GET',
                outcome='success' if status==200 else 'failed',http_status=status,request_scope=path,
                response_sha256=digest(body),comparison=None,form_id=self.target['form_id'],
                version_id=version,xml_path=None,attachment_filename=attachment))
            return status,body,name,rid

        def normalized(name, doc, native, version=None):
            files[name] = encoded(doc)
            rid = sid+'-normalized-'+str(len(receipts)+1)
            receipts.append(EvidenceReceipt(evidence_id=rid,source_snapshot_id=sid,source_file=name,
                archive_sha256=None,captured_at=at,query_receipt_id=native,request_method='LOCAL',outcome='success',
                http_status=None,request_scope='normalized authenticated Central capture; see native receipt',
                response_sha256=digest(files[name]),comparison=None,form_id=self.target['form_id'],version_id=version,xml_path=None))
            return rid

        # Explicit project/form access establishes authentication and correct scope.
        _,project,_,_ = get(f"/v1/projects/{self.target['project_id']}")
        expected=(self.settings.values.get('ODK_READ_PROJECT_NAME') if self.read_only and self.settings.values.get('ODK_READ_PROJECT_ID')
            else self.settings.values.get('ODK_RECOVERY_PROJECT_NAME','LastCopy synthetic Stage 4 recovery') if self.settings.values.get('ODK_RECOVERY_PROJECT_ID') else None)
        if expected and json.loads(project).get('name') != expected:
            raise ValueError('Configured dedicated synthetic project identity changed')
        get(scope)
        get(scope+'.xml')
        _,body,_,listing_id = get(scope+'/submissions')
        submissions = json.loads(body)
        if not isinstance(submissions,list) or len(submissions)>30:
            raise ValueError('Dedicated synthetic form exceeds 30-submission capture budget')
        for submission in submissions:
            logical = submission['instanceId']
            base = scope+'/submissions/'+quote(logical,safe='')
            _,history,_,_ = get(base+'/versions')
            history = json.loads(history)
            if not isinstance(history,list) or not 1<=len(history)<=10:
                raise ValueError('Version history exceeds supported budget')
            for meta in history:
                vid = meta['instanceId']
                vb = base+'/versions/'+quote(vid,safe='')
                _,xml,xpath,_ = get(vb+'.xml',version=vid)
                root = parse_xml(xml,self.settings)
                deprecated = root.findall('./{*}meta/{*}deprecatedID')
                _,slots,_,slot_receipt = get(vb+'/attachments',version=vid)
                slots = json.loads(slots)
                if not isinstance(slots,list) or len(slots)>50: raise ValueError('Attachment count budget exceeded')
                media,available = [],[]
                for slot in slots:
                    name = slot['name']
                    # Validate filenames before joining encoded native routes.
                    from .models import safe_path
                    safe_path(name)
                    if not isinstance(slot.get('exists'),bool): raise ValueError('Unknown Central attachment metadata')
                    if not slot['exists']: continue
                    _,blob,mp,mr = get(vb+'/attachments/'+quote(name,safe=''),version=vid,attachment=name)
                    available.append(name)
                    media.append(MediaReference(version_id=vid,filename=name,xml_path='/native-attachment-slot',
                        occurrence_indices=[],archive_path=mp,sha256=digest(blob),readback_receipt_id=mr))
                lr = normalized(f'normalized/attachments-{len(versions)}.json',{'version_id':vid,'filenames':available},slot_receipt,vid)
                lists[vid] = lr
                versions.append(SubmissionVersion(snapshot_id=sid,form_id=root.get('id'),form_version=root.get('version'),
                    logical_submission_id=logical,version_id=vid,deprecated_id=deprecated[0].text if deprecated else None,
                    xml_path=xpath,xml_sha256=digest(xml),completion_status='complete',current=meta['current'],media=media))
        fields = ['form_id','form_version','logical_submission_id','version_id','deprecated_id','current']
        lr = normalized('normalized/scope.json',{'connection_id':self.target['connection_id'],
            'project_id':self.target['project_id'],'form_ids':[self.target['form_id']], 'history_complete':True,
            'versions':[{k:getattr(v,k) for k in fields} for v in versions]},listing_id)
        payload = archive(files)
        snapshot = SourceSnapshot(schema_version=1,snapshot_id=sid,kind='central_raw',archive_sha256=digest(payload),
            captured_at=at,synthetic=False,scope_complete=True,project_id=self.target['project_id'],
            connection_id=self.target['connection_id'],form_ids=[self.target['form_id']],receipt_ids=[r.evidence_id for r in receipts],
            receipts=receipts,versions=versions,listing_receipt_id=lr,history_complete=True,attachment_listing_receipt_ids=lists)
        return snapshot.model_dump_json().encode(),payload

    def write(self, plan, files, filename=None):
        if self.read_only or plan['target'].get('environment')!='dedicated_synthetic_test':
            raise ValueError('Collection read connection cannot write submissions')
        if plan['target'] != self.target: raise ValueError('Central write target mismatch')
        # A final narrowly scoped preflight follows the full comparator capture.
        # Native Central has no attachment CAS: isolation from external writers
        # is still required, and fresh post-write readback detects later changes.
        scope = self.scope()
        base = scope+'/submissions/'+quote(plan['logical_submission_id'],safe='')
        status,body = self.request('GET',base)
        checks = [{'method':'GET','path':base,'status':status,'response_sha256':digest(body)}]
        if filename is None:
            if status != 404: raise ValueError(f'Immediate create precondition HTTP {status}; target no longer verified absent')
        else:
            if status != 200: raise ValueError(f'Immediate media precondition HTTP {status}; target unreadable')
            status,body = self.request('GET',base+'/versions')
            checks.append({'method':'GET','path':base+'/versions','status':status,'response_sha256':digest(body)})
            if status!=200: raise ValueError('Immediate version metadata unavailable')
            current = [v['instanceId'] for v in json.loads(body) if v['current']]
            if current != [plan['version_id']]: raise ValueError('Immediate target version changed')
            status,body = self.request('GET',base+'.xml')
            checks.append({'method':'GET','path':base+'.xml','status':status,'response_sha256':digest(body)})
            from .xml_compare import compare_xml
            if status!=200 or not compare_xml(files[plan['xml_path']],body,self.settings)['equal']:
                raise ValueError('Immediate target XML conflicts or is unavailable')
            status,body = self.request('GET',base+'/attachments')
            checks.append({'method':'GET','path':base+'/attachments','status':status,'response_sha256':digest(body)})
            if status!=200: raise ValueError('Immediate attachment listing unavailable')
            slot = [s for s in json.loads(body) if s['name']==filename]
            if len(slot)!=1 or slot[0].get('exists') is not False:
                raise ValueError('Immediate attachment slot is not verified missing; read back before retry')
        if filename is None:
            path = f"/v1/projects/{self.target['project_id']}/submission"
            parts = [('xml_submission_file',('original.xml',files[plan['xml_path']],'application/xml'))]
            for name,mp in sorted(plan['media_paths'].items()):
                parts.append((name,(name,files[mp],'application/octet-stream')))
            status,body = self.request('POST',path,files=parts,headers={'X-OpenRosa-Version':'1.0'})
            expected = 201
        else:
            if filename not in plan['media_filenames']: raise ValueError('Unplanned attachment')
            path = scope+'/submissions/'+quote(plan['logical_submission_id'],safe='')+'/attachments/'+quote(filename,safe='')
            status,body = self.request('POST',path,content=files[plan['media_paths'][filename]],headers={'Content-Type':'application/octet-stream'})
            expected = 200
        receipt = {'method':'POST','path':path,'status':status,'response_sha256':digest(body),
            'target':self.target,'filename':filename,'version_id':plan['version_id'],'immediate_preconditions':checks}
        # 409 is a conflict, never a reason to generate a different identity.
        if status != expected: raise ValueError(f'Central write HTTP {status}; readback required before retry')
        return receipt
