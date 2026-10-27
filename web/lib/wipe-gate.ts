/** TypeScript mirror of lastcopy/agents.py::wipe_gate. Same rules, same order. */
export type Verdict = 'PRESERVED'|'EXPORT_VIEW_ONLY'|'MISSING_SUBMISSION'|'MISSING_ATTACHMENT'|'CONTENT_CONFLICT'|'UNVERIFIABLE';
export type Decision = 'SAFE_TO_WIPE'|'RECOVER_FIRST'|'HOLD';
export const VERDICTS:Verdict[]=['PRESERVED','EXPORT_VIEW_ONLY','MISSING_ATTACHMENT','MISSING_SUBMISSION','CONTENT_CONFLICT','UNVERIFIABLE'];
export const VERDICT_TEXT:Record<Verdict,string>={
  PRESERVED:'Matched the server byte-for-byte',
  EXPORT_VIEW_ONLY:'Spreadsheet hides answers, raw XML has them',
  MISSING_ATTACHMENT:'A photo or file never reached the server',
  MISSING_SUBMISSION:'The whole record is only on this tablet',
  CONTENT_CONFLICT:'Server copy has different answers',
  UNVERIFIABLE:'Could not be read or compared',
};
export const DECISION_TEXT:Record<Decision,string>={SAFE_TO_WIPE:'Safe to wipe',RECOVER_FIRST:'Recover first',HOLD:'Hold'};

export function wipeGate(counts:Partial<Record<Verdict,number>>, exportReceived=true):{decision:Decision,rule:string}{
  const n=(v:Verdict)=>counts[v]??0;
  if(!exportReceived)return {decision:'HOLD',rule:'No export received → nothing on the device has been checked.'};
  if(n('MISSING_SUBMISSION')+n('MISSING_ATTACHMENT')>0)return {decision:'RECOVER_FIRST',rule:'The tablet holds the only copy of something the server lacks.'};
  if(n('CONTENT_CONFLICT')+n('UNVERIFIABLE')>0)return {decision:'HOLD',rule:'A conflict or unreadable item needs a person.'};
  if(VERDICTS.every(v=>n(v)===0))return {decision:'HOLD',rule:'No completed records found to verify.'};
  return {decision:'SAFE_TO_WIPE',rule:'Every completed record and file is positively preserved.'};
}

/** The seven evidence criteria (mirror of agents.py::evidence_criteria), computed from a decision's own verified data. */
export function criteriaFor(d:{counts:Partial<Record<Verdict,number>>;certificate:{device_export_sha256:string|null}}){
  const n=(v:Verdict)=>d.counts[v]??0;const total=VERDICTS.reduce((a,v)=>a+n(v),0);
  return [
    ['Tablet is on the coordinator’s roster',true],
    ['Export received and sealed by SHA-256',!!d.certificate.device_export_sha256],
    ['Every completed record has a server version',n('MISSING_SUBMISSION')===0],
    ['Every photo and file slot present, bytes identical',n('MISSING_ATTACHMENT')===0],
    ['Every answer matches the raw server XML',n('CONTENT_CONFLICT')===0],
    ['Nothing unreadable or unverifiable',n('UNVERIFIABLE')===0],
    ['At least one completed record verified',total>0],
  ] as [string,boolean][];
}
