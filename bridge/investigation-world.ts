/** Pinned reference only. Rebuild private append-only observations; never use spec-only APIs. */
import fs from 'node:fs';
import {WorldModel} from '../third_party/world-model/reference/src/index.ts';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
if (!Array.isArray(input.records) || input.records.length > 512) throw Error('Bounded records required');
const world = new WorldModel({storage: 'memory', namespace: 'lastcopy-investigation'});
const previous = new Map<string, string>();
for (const record of input.records) {
  const source = {kind: 'manual' as const, at: record.at, runId: input.run_id, by: 'lastcopy-code'};
  const report = await world.ingest([{externalId: record.id, type: 'observation', title: record.id,
    text: JSON.stringify(record), at: record.at, source}]);
  if (report.processed === 0) continue;
  const entity = await world.upsertEntity({type: record.type,
    externalKey: {system: 'lastcopy', id: `${record.key}:${record.revision}`}, attrs: record, source});
  const revisionKey = `${record.type}:${record.key}`;
  if (previous.has(revisionKey)) {
    await world.relate({from: entity.id, type: 'revises', to: previous.get(revisionKey)!, source});
  }
  previous.set(revisionKey, entity.id);
  for (const evidence of record.evidence) {
    const observation = await world.upsertEntity({type: 'observation',
      externalKey: {system: 'lastcopy-evidence', id: evidence}, attrs: {evidence}, source});
    await world.relate({from: entity.id, type: 'supported-by', to: observation.id, source});
  }
}
const hypotheses = world.view('graph').query({type: 'hypothesis'}).sort((a,b) =>
  Number(a.attrs.revision) - Number(b.attrs.revision));
const latest = hypotheses.at(-1);
console.log(JSON.stringify({next_action: latest?.attrs.next_action ?? 'query_export', hypotheses,
  entities: world.view('graph').query({}).map(e => ({id:e.id,type:e.type})),
  event_count: world.events().length, state: world.stateShapeCanonical()}));
