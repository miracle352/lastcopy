"use client";
import { useState } from "react";
import type { components } from "../../lib/api.generated";
type Inventory = components["schemas"]["ImportInventory"];

export function InventoryCheck() {
  const [data, setData] = useState<Inventory | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function check() {
    setBusy(true); setError(""); setData(null);
    try {
      const response = await fetch("/api/inventory", {signal: AbortSignal.timeout(8000)});
      if (!response.ok) throw new Error(response.status === 409 ? "The local API is in Connected mode. Set SAMPLE_MODE=true to inspect this explicit sample." : "The private API is unavailable. Start the local API on port 8000. The Vercel skeleton has no connected evidence backend.");
      setData(await response.json() as Inventory);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Inventory request failed.");
    } finally { setBusy(false); }
  }
  return <div>
    <button type="button" onClick={check} disabled={busy} aria-describedby="sample-mode">{busy ? "Reading archive…" : "Validate sample archive"}</button>
    <p id="sample-mode" className="muted">Sample only · Synthetic files · No model or external service called</p>
    <div role="status" aria-live="polite" aria-busy={busy}>
      {error && <p className="error">{error}</p>}
      {data && <div className="result"><h3>Archive inventoried · Sample</h3>
        <p>{Object.keys(data.files).length} files, {data.versions.length} submission version. Preservation has not been checked.</p>
        <dl><dt>Device label</dt><dd>{data.manifest.device_id} / {data.manifest.device_provenance.origin.replaceAll("_", " ")}</dd>
        <dt>Completion</dt><dd>{data.versions[0]?.completion_status}</dd>
        <dt>Original filename</dt><dd>{data.versions[0]?.xml_path}</dd>
        <dt>Media references</dt><dd>{data.versions[0]?.media?.length} references (each retains its repeat occurrence)</dd>
        <dt>Archive SHA-256</dt><dd className="hash">{data.archive_sha256}</dd></dl>
        {data.limitations.length > 0 && <ul>{data.limitations.map(issue => <li key={issue}>{issue}</li>)}</ul>}
      </div>}
    </div>
  </div>;
}
