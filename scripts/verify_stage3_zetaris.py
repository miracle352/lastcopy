"""Read-only actual queries against one LastCopy publication; no model/live-loop claim."""
import argparse
import json
import time
from pathlib import Path
from lastcopy.config import Settings
from lastcopy.investigation import Investigation, EvidencePack, encoded
from lastcopy.connected import ZetarisEvidence
from scripts.verify_zetaris_local import connect
from lastcopy.inventory import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('publication', type=Path)
    parser.add_argument('--fixture', type=Path, default=Path('fixtures/stage2/export'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture
    settings = Settings.load()
    pack = EvidencePack.build(json.loads((fixture / 'run-manifest.json').read_bytes()), [(fixture / 'device.zip').read_bytes()],
        (fixture / 'server-snapshot.json').read_bytes(), (fixture / 'server-payload.zip').read_bytes(), settings)
    publication = json.loads(args.publication.read_bytes())
    assert all(publication['tables'][name]['sha256'] == digest(data) for name, data in pack.csv_files().items())
    owner = Investigation(args.output, settings)
    owner.begin(pack, 'connected')
    adapter = ZetarisEvidence(args.output, owner)
    try:
        adapter.database = publication['database']
        adapter.headers = connect(adapter.client)
        results = {}
        for kind in ('export_gaps', 'versions', 'objects', 'media'):
            rows, query = adapter.query(kind, pack, owner)
            results[kind] = {'rows': rows, 'query': query}
            owner.event('query', **query)
        (args.output / 'query-results.json').write_bytes(encoded(results))
        owner.finish('completed', check='actual Zetaris queries only; no Nightshift inference or end-to-end investigation claim')
        print(json.dumps({kind: len(value['rows']) for kind, value in results.items()}))
    finally:
        adapter.close()


if __name__ == '__main__':
    main()
