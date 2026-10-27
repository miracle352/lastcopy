# Zetaris live footage: shot list (about 3 minutes)

The video competition scores "Meaningful use of Zetaris, shown live" at 25 points.
This is the only part that needs your screen. Claude edits everything else.

## Before you record

1. Open **Chrome** (not the Claude app), go to <http://localhost:3130> and sign in.
2. Maximise Chrome. Close other tabs. Zoom 110% (Ctrl + +) so text reads well on video.
3. In the left **Data Explorer**, expand **File Source & API**.

## Record

Press **Win + Shift + R** (Snipping Tool screen recording), drag over the **whole Chrome window**, and click **Start**.
Go slowly. Pause about 2 seconds after each step. Don't talk; narration is added later.

| # | Do this | Hold |
|---|---|---|
| 1 | In Data Explorer, click the arrow next to **`lc3_eed1459320a94152b1d2`** to show its tables (device_inventory, submission_versions, xml_facts, media_references, file_hashes…) | 4 s |
| 2 | Click **Workbench → SQL Workspace**, then **New Query** | 2 s |
| 3 | Paste **Query A** below, then press **Ctrl + Enter** | 5 s on the result (tablet-02, uuid:fleet-02-a, **b.bin**) |
| 4 | Select all, paste **Query B**, press **Ctrl + Enter** | 5 s on the result (**uuid:fleet-03-b**) |
| 5 | Select all, paste **Query C**, press **Ctrl + Enter** | 5 s on the result (**uuid:fleet-04-a**, two different hashes) |
| 6 | Select all, paste **Query D**, press **Ctrl + Enter** | 5 s on the result (device 4 sources / 84 rows, server 1 / 70, tabular 1 / 4) |

All four queries were run in this Zetaris instance on 27 Oct 2026 and returned exactly the results above (each in about 3–5 s).

Click **Stop** in the recording bar. Snipping Tool opens the video. Press **Ctrl + S** and save it as
`zetaris-live.mp4` in `Documents\ChatGPT\My experiments\lastcopy\outputs`. Then tell Claude "recorded".

## Queries (copy each block exactly)

**Query A: a photo that only exists on the tablet**
```sql
-- Photos referenced by a tablet record that the server never received
SELECT d.source_id AS tablet, d.version_id AS record, d.filename AS missing_file
FROM lc3_eed1459320a94152b1d2.media_references d
LEFT JOIN lc3_eed1459320a94152b1d2.media_references s
  ON s.version_id = d.version_id AND s.filename = d.filename AND s.side = 'server'
WHERE d.side = 'device' AND s.row_id IS NULL
  AND d.version_id IN (SELECT version_id FROM lc3_eed1459320a94152b1d2.submission_versions WHERE side = 'server')
```

**Query B: a whole record stuck on a tablet**
```sql
-- Completed records on a tablet with no server version at all
SELECT d.source_id AS tablet, d.version_id AS record_only_on_tablet
FROM lc3_eed1459320a94152b1d2.submission_versions d
LEFT JOIN lc3_eed1459320a94152b1d2.submission_versions s
  ON s.version_id = d.version_id AND s.side = 'server'
WHERE d.side = 'device' AND s.row_id IS NULL
```

**Query C: an answer that differs between tablet and server**
```sql
-- Same record, different bytes: someone edited it on the server
SELECT d.source_id AS tablet, d.version_id AS record, d.xml_object AS tablet_xml_sha256, s.xml_object AS server_xml_sha256
FROM lc3_eed1459320a94152b1d2.submission_versions d
JOIN lc3_eed1459320a94152b1d2.submission_versions s
  ON s.version_id = d.version_id AND s.side = 'server'
WHERE d.side = 'device' AND d.xml_object <> s.xml_object
```

**Query D: four sources, one query**
```sql
-- Every source LastCopy registered for this run, joined in place
SELECT side, COUNT(DISTINCT source_id) AS sources, COUNT(*) AS answer_rows
FROM lc3_eed1459320a94152b1d2.xml_facts
GROUP BY side ORDER BY side
```
