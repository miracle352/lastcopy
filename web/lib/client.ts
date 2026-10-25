import type {components} from './api.generated';
export type RunReport=components['schemas']['ReconciliationReport'];
export type Finding=components['schemas']['Finding'];
export type Receipt=components['schemas']['EvidenceReceipt'];
export type Plan=components['schemas']['RecoveryPlan'];
export type Inventory=components['schemas']['ImportInventory'];
export type Manifest=components['schemas']['RunManifest'];
export type RunRequest=components['schemas']['RunRequest'];
export const endpoint=(path:string)=>'/api/service'+path;
export async function api<T>(path:string,body?:unknown,signal?:AbortSignal):Promise<T>{
  const response=await fetch(endpoint(path),{method:body===undefined?'GET':'POST',headers:body===undefined?undefined:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',signal});
  const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request could not be validated. Check the supplied files and scope.');return data;
}
export async function upload<T>(path:string,file:File):Promise<T>{
  if(file.size>10485760)throw new Error('Each ZIP must be 10 MiB or smaller.');
  const response=await fetch(endpoint(path),{method:'POST',headers:{'Content-Type':'application/zip'},body:file,cache:'no-store'});
  const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'This ZIP could not be validated.');return data;
}
export type Settings=components['schemas']['UISettings'];
export type Connection=components['schemas']['UIConnection'];
export type Watch=components['schemas']['WatchStatus'];
export type Draft=components['schemas']['UIDraft'];
export type PlanState=components['schemas']['UIPlanState'];
export type RunView=components['schemas']['UIRunView'];
export type Evidence=components['schemas']['UIFindingEvidence'];
export type Recent=components['schemas']['UIRecent'];
export const message=(error:unknown)=>error instanceof Error?error.message:'The action failed. Your saved results remain available.';
export const enc=encodeURIComponent;
export function label(f:Finding):string{
  if(f.original_retained_in_history && f.preservation==='preserved')return 'Original retained in history';
  return {PRESERVED:'Matching copy verified',MISSING_SUBMISSION:'Record missing in checked server scope',MISSING_ATTACHMENT:(f.media_filenames??[]).some(n=>/\.(png|jpe?g|webp|heic)$/i.test(n))?'Photo missing on server':'File missing on server',CONTENT_CONFLICT:'Answers or files differ',EXPORT_VIEW_ONLY:'Answers present; export omitted them',UNVERIFIABLE:'Could not verify'}[f.verdict];
}
