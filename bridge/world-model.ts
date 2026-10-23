/** Real pinned reference; no endpoint or SDK invented. JSON in/out is the bridge. */
import { WorldModel, entityIdFromName } from "../third_party/world-model/reference/src/index.ts";

const world = new WorldModel({storage: "memory", namespace: "lastcopy-stage1", clock: () => new Date("2026-10-23T09:00:00Z")});
const source = {kind: "manual" as const, at: "2026-10-23T09:00:00Z"};
const observation = {externalId: "synthetic-import-001", title: "Synthetic archive inventory available", at: source.at, source, entities: [{type: "device_snapshot", name: "synthetic-device-a-001"}]};
const first = await world.ingest([observation]);
const before = world.stateShapeCanonical();
const second = await world.ingest([observation]);
if (first.processed !== 1 || second.processed !== 0 || before !== world.stateShapeCanonical()) throw new Error("Reference idempotency failed");
const entity = world.view("graph").entity(entityIdFromName("device_snapshot", "synthetic-device-a-001"));
if (!entity) throw new Error("Reference graph read returned no snapshot entity");
const entities = [entity];
console.log(JSON.stringify({provider: "meterless-world-model", status: "PASS", mode: "offline-reference", upstream_commit: "1742dec56a66e58eef9dda2d2b865823758ca8cd", observations_processed: first.processed, replay_processed: second.processed, graph_entities: entities.map(e => ({id: e.id, type: e.type})), preservation_checked: false}, null, 2));
