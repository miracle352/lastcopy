"""Synthetic capture packs; Stage 3 action expectations authored independently."""
import json
from lastcopy.config import ROOT
from scripts.build_stage2_fixtures import example


def main():
    for name, case, seed, repeats, verdict, action in [
        ('export-review', 'export', 41, 2, 'EXPORT_VIEW_ONLY', 'export_guidance'),
        ('unresolved-conflict', 'conflict', 41, 2, 'CONTENT_CONFLICT', 'manual_review'),
        ('held-out', 'export', 9087, 5, 'EXPORT_VIEW_ONLY', 'export_guidance'),
    ]:
        data = example(case, seed, repeats)
        data['run']['run_id'] = f'stage3-{name}-{seed}'
        folder = ROOT / 'fixtures/stage3' / name
        folder.mkdir(parents=True, exist_ok=True)
        for key, filename in [('run', 'run-manifest.json'), ('snapshot', 'server-snapshot.json')]:
            (folder / filename).write_text(json.dumps(data[key], indent=2) + '\n', encoding='utf8')
        (folder / 'device.zip').write_bytes(data['device'])
        (folder / 'server-payload.zip').write_bytes(data['server'])
        expected = {'seed': seed, 'repeats': repeats, 'verdict': verdict, 'next_action': action,
            'recovery_eligible': False, 'initial_hypothesis': 'possible_missing_data',
            'final_hypothesis': 'rejected' if case == 'export' else 'unresolved_conflict',
            'provenance': 'Hand-specified expectations. No model or comparator used to author outcomes.'}
        (folder / 'expected.json').write_text(json.dumps(expected, indent=2) + '\n', encoding='utf8')
    print('Built three synthetic Stage 3 capture packs; no provider/model calls')


if __name__ == '__main__':
    main()
