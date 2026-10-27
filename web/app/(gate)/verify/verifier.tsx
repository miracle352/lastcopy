'use client';
import {useCallback, useEffect, useState} from 'react';

type Cert = {decision: string; device_export_sha256: string | null; device_id: string; records: {verdict: string}[]; rule: string; run_id: string; server_capture_sha256: string | null; challenge?: unknown};
type Decision = {device_id: string; decision: string; certificate: Cert; certificate_sha256: string};
type Doc = {run_id: string; mode: string; captured_at?: string; decisions: Decision[]};
type Check = {name: string; pass: boolean; detail: string};
type Row = {device: string; decision: string; checks: Check[]; guard: 'ALLOW' | 'BLOCK' | 'NEEDS_EXPORT'; why: string};

const MISSING = new Set(['MISSING_SUBMISSION', 'MISSING_ATTACHMENT']);
const UNCERTAIN = new Set(['CONTENT_CONFLICT', 'UNVERIFIABLE']);
const RAW = '/fixtures/fleet/';  // byte-identical copies of the repo's fixtures/fleet archives
const SAMPLE_FILES = ['tablet-01.zip', 'tablet-02.zip', 'tablet-03.zip', 'tablet-04.zip', 'server-payload.zip'];

// Same canonical form as Python's json.dumps(sort_keys=True, separators=(',', ':')), ASCII-escaped.
function canonical(v: unknown): string {
  if (v === null || typeof v !== 'object') {
    return JSON.stringify(v).replace(/[\u007f-￿]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  }
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
  const o = v as Record<string, unknown>;
  return '{' + Object.keys(o).sort().map(k => canonical(k) + ':' + canonical(o[k])).join(',') + '}';
}
async function sha256(data: BufferSource): Promise<string> {
  const h = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function ruleDecision(c: Cert): string {
  const v = new Set(c.records.map(r => r.verdict));
  if (c.challenge) return 'HOLD';
  if (c.device_export_sha256 === null) return 'HOLD';
  if ([...v].some(x => MISSING.has(x))) return 'RECOVER_FIRST';
  if ([...v].some(x => UNCERTAIN.has(x))) return 'HOLD';
  if (v.size === 0) return 'HOLD';
  return 'SAFE_TO_WIPE';
}

async function verify(doc: Doc, archives: Map<string, string>): Promise<Row[]> {
  const rows: Row[] = [];
  for (const d of doc.decisions) {
    const c = d.certificate, checks: Check[] = [];
    const h = await sha256(new TextEncoder().encode(canonical(c)));
    checks.push({name: 'Certificate unedited (SHA-256)', pass: h === d.certificate_sha256, detail: d.certificate_sha256.slice(0, 16) + '…'});
    const want = ruleDecision(c);
    checks.push({name: 'Decision follows the wipe rule', pass: c.rule === 'lastcopy-wipe-gate/1' && want === c.decision && c.decision === d.decision, detail: `${c.decision} (rule gives ${want})`});
    const exp = c.device_export_sha256, srv = c.server_capture_sha256;
    const expName = exp ? archives.get(exp) : undefined, srvName = srv ? archives.get(srv) : undefined;
    if (expName) checks.push({name: 'Tablet export bytes match', pass: true, detail: expName});
    if (srvName) checks.push({name: 'Server capture bytes match', pass: true, detail: srvName});
    const valid = checks.every(x => x.pass);
    let guard: Row['guard'], why: string;
    if (!valid) { guard = 'BLOCK'; why = 'certificate failed a check'; }
    else if (c.decision !== 'SAFE_TO_WIPE') { guard = 'BLOCK'; why = c.decision === 'RECOVER_FIRST' ? 'recover the named data first' : 'a person must look first'; }
    else if (c.challenge) { guard = 'BLOCK'; why = 'an Adversary objection is open'; }
    else if (!expName) { guard = 'NEEDS_EXPORT'; why = 'add a fresh export of this tablet to confirm nothing changed'; }
    else { guard = 'ALLOW'; why = 'export unchanged since the check'; }
    rows.push({device: d.device_id, decision: d.decision, checks, guard, why});
  }
  return rows;
}

export default function Verifier() {
  const [doc, setDoc] = useState<Doc | null>(null);
  const [docName, setDocName] = useState('live_connected_fleet.json (live run, 27 Oct 2026)');
  const [archives, setArchives] = useState<Map<string, string>>(new Map());
  const [unknown, setUnknown] = useState<string[]>([]);
  const [rows, setRows] = useState<Row[] | null>(null);
  const [busy, setBusy] = useState('');

  useEffect(() => { fetch('/runs/live-fleet.json').then(r => r.json()).then(setDoc).catch(() => setBusy('Could not load the live run.')); }, []);
  useEffect(() => {
    if (!doc) return;
    verify(doc, archives).then(setRows);
    const named = new Set(doc.decisions.flatMap(d => [d.certificate.device_export_sha256, d.certificate.server_capture_sha256]));
    setUnknown([...archives].filter(([h]) => !named.has(h)).map(([, n]) => n));
  }, [doc, archives]);

  const addFiles = useCallback(async (files: FileList | File[]) => {
    const next = new Map(archives);
    for (const f of Array.from(files)) {
      const buf = await f.arrayBuffer();
      if (f.name.endsWith('.json')) {
        try { const j = JSON.parse(new TextDecoder().decode(buf)); if (j.decisions) { setDoc(j); setDocName(f.name); continue; } } catch { /* fall through: hash it */ }
      }
      next.set(await sha256(buf), f.name);
    }
    setArchives(next);
  }, [archives]);

  const fetchSamples = async () => {
    setBusy('Hashing the original archives…');
    try {
      const files = await Promise.all(SAMPLE_FILES.map(async n => new File([await (await fetch(RAW + n)).arrayBuffer()], n)));
      await addFiles(files);
      setBusy('');
    } catch { setBusy('Could not fetch the archives. Download them from GitHub and drop them here instead.'); }
  };

  const passed = rows ? rows.reduce((a, r) => a + r.checks.filter(c => c.pass).length, 0) : 0;
  const total = rows ? rows.reduce((a, r) => a + r.checks.length, 0) : 0;

  return <div>
    <div className="card" style={{padding: 26, display: 'grid', gap: 18}}
      onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); addFiles(e.dataTransfer.files); }}>
      <div style={{display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center'}}>
        <button className="btn primary" onClick={fetchSamples}>Check against the original archives</button>
        <label className="btn" style={{cursor: 'pointer'}}>Add your own files<input type="file" multiple hidden onChange={e => e.target.files && addFiles(e.target.files)}/></label>
        <span className="fig" style={{margin: 0}}>or drop a LastCopy output JSON and its ZIP archives anywhere on this box</span>
      </div>
      <div className="mono" style={{fontSize: 13, color: 'var(--muted)'}}>
        Run: {docName}{doc ? ` · ${doc.run_id} · ${doc.mode}` : ''} · Archives hashed: {archives.size ? [...archives.values()].join(', ') : 'none yet'}
      </div>
      {busy && <div className="fig" style={{margin: 0}}>{busy}</div>}
      {unknown.length > 0 && <div className="fig" style={{margin: 0, color: 'var(--rose)'}}>Not named by any certificate: {unknown.join(', ')}</div>}
    </div>

    {rows && <div style={{marginTop: 22, display: 'grid', gap: 14}}>
      <div className="mono" style={{fontSize: 14, color: passed === total ? 'var(--mint-2)' : 'var(--rose)'}}>{passed}/{total} checks passed in your browser · SHA-256 via Web Crypto · nothing uploaded</div>
      {rows.map(r => <div key={r.device} className="card vrow">
        <div><div className="mono" style={{fontSize: 15}}>{r.device}</div><div className="dec" data-d={r.decision} style={{fontSize: 14, marginTop: 4}}>{r.decision}</div></div>
        <div style={{display: 'grid', gap: 6}}>{r.checks.map(c => <div key={c.name} style={{display: 'flex', flexWrap: 'wrap', gap: '2px 10px', fontSize: 14}}>
          <span style={{color: c.pass ? 'var(--mint-2)' : 'var(--rose)', fontWeight: 600, width: 14}}>{c.pass ? '✓' : '✕'}</span>
          <span style={{color: 'var(--text)'}}>{c.name}</span><span className="mono" style={{color: 'var(--muted)', fontSize: 12.5, marginLeft: 'auto', textAlign: 'right'}}>{c.detail}</span></div>)}</div>
        <div className="vguard">
          <div className="mono" style={{fontSize: 12, letterSpacing: '.14em', color: 'var(--muted)'}}>RESET GUARD</div>
          <div style={{fontSize: 22, fontWeight: 700, marginTop: 4, color: r.guard === 'ALLOW' ? 'var(--mint-2)' : r.guard === 'BLOCK' ? 'var(--rose)' : 'var(--amber)'}}>{r.guard === 'NEEDS_EXPORT' ? 'NEEDS EXPORT' : r.guard}</div>
          <div style={{fontSize: 13, color: 'var(--muted)', marginTop: 4}}>{r.why}</div>
        </div>
      </div>)}
    </div>}
  </div>;
}
