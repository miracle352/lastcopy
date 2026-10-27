/**
 * LastCopy investigation planner over the pinned Meterless World Model reference.
 *
 * Python appends typed, evidence-backed records to a private journal. This bridge
 * rebuilds the graph with the real WorldModel (ingest, upsertEntity, relate, views)
 * and then *chooses the next action from the graph's state*. Python dispatches
 * whatever the graph selects; it never writes the next action itself.
 *
 * Policy (deterministic code, in priority order):
 *   triage          no triage observation yet
 *   classify        a suspicion has no hypothesis, or a hypothesis was sent back for revision
 *   review          a hypothesis is proposed but not yet critiqued
 *   fetch_evidence  hypotheses are approved (or there is nothing to suspect) and no raw verification exists
 *   evaluate        raw verification exists and approved hypotheses are still untested
 *   remedy          a verified finding is not preserved and has no remedy
 *   decide          verified devices have no clearance decision
 *   explain         a decision has no explanation
 *   done
 */
import fs from 'node:fs';
import {WorldModel} from '../third_party/world-model/reference/src/index.ts';

type Rec = {id: string; type: string; key: string; revision: number; evidence: string[]; at: string; [k: string]: unknown};
const input = JSON.parse(fs.readFileSync(0, 'utf8')) as {records: Rec[]; run_id: string; max_revisions?: number};
if (!Array.isArray(input.records) || input.records.length > 512) throw Error('Bounded records required');
const maxRevisions = Number(input.max_revisions ?? 1);

const world = new WorldModel({storage: 'memory', namespace: 'lastcopy-investigation'});
const previous = new Map<string, string>();
for (const record of input.records) {
  const source = {kind: 'manual' as const, at: record.at, runId: input.run_id, by: 'lastcopy-code'};
  const report = await world.ingest([{externalId: record.id, type: 'observation', title: record.id,
    text: JSON.stringify(record), at: record.at, source}]);
  if (report.processed === 0) continue;
  const entity = await world.upsertEntity({type: record.type,
    externalKey: {system: 'lastcopy', id: `${record.type}:${record.key}:${record.revision}`}, attrs: record, source});
  const revisionKey = `${record.type}:${record.key}`;
  if (previous.has(revisionKey)) await world.relate({from: entity.id, type: 'revises', to: previous.get(revisionKey)!, source});
  previous.set(revisionKey, entity.id);
  for (const evidence of record.evidence) {
    const observation = await world.upsertEntity({type: 'observation',
      externalKey: {system: 'lastcopy-evidence', id: evidence}, attrs: {evidence}, source});
    await world.relate({from: entity.id, type: 'supported-by', to: observation.id, source});
  }
}

const graph = world.view('graph');
/** Latest revision per (type, key), read back out of the World Model graph. */
function latest(type: string): Rec[] {
  const best = new Map<string, Rec>();
  for (const e of graph.query({type})) {
    const a = e.attrs as unknown as Rec;
    const old = best.get(a.key);
    if (!old || Number(a.revision) > Number(old.revision)) best.set(a.key, a);
  }
  return [...best.values()].sort((x, y) => x.key.localeCompare(y.key));
}
const rank = (h: Rec) => -Number(h.priority ?? 0);
const byPriority = (xs: Rec[]) => [...xs].sort((a, b) => rank(a) - rank(b) || a.key.localeCompare(b.key));

const triage = latest('triage');
const suspicions = latest('suspicion');
const hypotheses = latest('hypothesis');
const verification = latest('verification');
const findings = latest('finding');
const remedies = new Set(latest('remedy').map(r => r.key));
const decisions = latest('device_decision');
const explanations = new Set(latest('explanation').map(r => r.key));
const hypothesisFor = new Map(hypotheses.map(h => [String(h.suspicion), h]));

let next = 'done';
let focus: string[] = [];
let why = 'Every device has an explained, code-made decision.';
const revise = hypotheses.filter(h => h.status === 'revise' && Number(h.revision) < maxRevisions * 2);
const unclassified = suspicions.filter(s => !hypothesisFor.has(s.key));
const proposed = hypotheses.filter(h => h.status === 'proposed');
const approvedUntested = hypotheses.filter(h => h.status === 'approved');
if (triage.length === 0) {
  next = 'triage'; why = 'No cross-source triage has run yet.';
} else if (unclassified.length || revise.length) {
  next = 'classify'; focus = [...unclassified, ...revise].map(r => r.key);
  why = unclassified.length ? `${unclassified.length} suspicion(s) have no hypothesis.` : `${revise.length} hypothesis(es) were sent back by the reviewer.`;
} else if (proposed.length) {
  next = 'review'; focus = byPriority(proposed).map(h => h.key); why = `${proposed.length} hypothesis(es) await critique.`;
} else if (verification.length === 0) {
  next = 'fetch_evidence'; focus = byPriority(approvedUntested).map(h => h.key);
  why = approvedUntested.length ? `${approvedUntested.length} approved hypothesis(es) need raw evidence.` : 'Nothing is suspected; verify every record against raw bytes anyway.';
} else if (approvedUntested.length) {
  next = 'evaluate'; focus = byPriority(approvedUntested).map(h => h.key); why = 'Raw evidence is in; test each approved hypothesis against verified verdicts.';
} else if (findings.some(f => f.verdict !== 'PRESERVED' && !remedies.has(f.key))) {
  next = 'remedy'; focus = findings.filter(f => f.verdict !== 'PRESERVED' && !remedies.has(f.key)).map(f => f.key);
  why = `${focus.length} verified finding(s) need a permitted action.`;
} else if (decisions.length === 0) {
  next = 'decide'; why = 'Findings are settled; decide clearance per device.';
} else if (decisions.some(d => !explanations.has(d.key))) {
  next = 'explain'; focus = decisions.filter(d => !explanations.has(d.key)).map(d => d.key); why = 'Decisions need plain-language explanations.';
}

const counts = Object.fromEntries(['suspicion', 'hypothesis', 'finding', 'device_decision', 'explanation', 'observation']
  .map(t => [t, graph.query({type: t}).length]));
console.log(JSON.stringify({next_action: next, focus, why, counts,
  hypotheses: graph.query({type: 'hypothesis'}).map(e => ({id: e.id, attrs: e.attrs})).sort((a, b) =>
    String((a.attrs as Rec).key).localeCompare(String((b.attrs as Rec).key)) || Number((a.attrs as Rec).revision) - Number((b.attrs as Rec).revision)),
  latest_hypotheses: hypotheses, decisions,
  entities: graph.query({}).map(e => ({id: e.id, type: e.type})),
  event_count: world.events().length, state: world.stateShapeCanonical()}));
