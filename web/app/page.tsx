import { InventoryCheck } from "./sample-check";

export default function Home() {
  return <main id="main">
    <header><a href="/" aria-label="LastCopy home">LastCopy</a><span>Stage 1 / Development skeleton</span></header>
    <h1>Establish the evidence.</h1>
    <p>LastCopy will check which field forms, answers and referenced files in supplied device backups have a verified ODK Central copy.</p>
    <aside><strong>Import inventory only.</strong> Preservation comparison, investigation and recovery are later stages. This skeleton does not declare records preserved or recovered.</aside>
    <section aria-labelledby="inventory-title"><h2 id="inventory-title">Inspect the synthetic archive</h2>
      <p>The representative archive retains its project directory, original XML filename, matching XForm and two references to one attachment. Completion and device labels have an explicit synthetic coordinator attestation.</p>
      <InventoryCheck />
    </section>
    <section aria-labelledby="scope-title"><h2 id="scope-title">Current scope</h2>
      <dl><dt>Platform</dt><dd>ODK Central. No Kobo compatibility claim.</dd>
      <dt>Local API</dt><dd>FastAPI on loopback port 8000. Credentials remain server-side.</dd>
      <dt>Connected integrations</dt><dd>Require explicit configuration and successful smoke receipts. No live model has been verified by this skeleton.</dd>
      <dt>Recovery</dt><dd>No writes are available. Future automated operations require a reviewed plan in a dedicated synthetic test project.</dd></dl>
    </section>
    <footer>Only supplied snapshots and checked scope can be assessed. Missing source bytes cannot be reconstructed.</footer>
  </main>;
}
