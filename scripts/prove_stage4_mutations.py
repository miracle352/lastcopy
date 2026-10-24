"""Meaningful negative controls in disposable Python memory; never edits source."""
import argparse
import pytest
from lastcopy.config import ROOT


def main():
    p=argparse.ArgumentParser(); p.add_argument('mutation',choices=['ignore-xml-conflicts','ignore-version-change'])
    args=p.parse_args()
    if args.mutation=='ignore-xml-conflicts':
        import lastcopy.reconcile as comparator
        comparator.compare_xml=lambda *args,**kwargs:{'equal':True,'differences':[],'difference_count':0,'details_truncated':False}
        test='tests/test_stage4.py::test_change_between_review_and_apply_blocks[conflict]'
    else:
        import lastcopy.recovery as recovery
        source=(ROOT/'lastcopy/recovery.py').read_text(encoding='utf-8')
        old="if current['current_version_id'] != plan['expected_current_version'] and not ("
        if source.count(old)!=1: raise ValueError('Mutation anchor changed; revise negative control explicitly')
        source=source.replace(old,"if False and current['current_version_id'] != plan['expected_current_version'] and not (")
        source=source.replace("if current['current_version_id'] not in (plan['version_id'],plan['expected_current_version']):",
            "if False and current['current_version_id'] not in (plan['version_id'],plan['expected_current_version']):")
        exec(compile(source,str(ROOT/'lastcopy/recovery.py'),'exec'),recovery.__dict__)
        test='tests/test_stage4.py::test_change_between_review_and_apply_blocks[version]'
    return pytest.main([test,'-q'])


if __name__=='__main__': raise SystemExit(main())
