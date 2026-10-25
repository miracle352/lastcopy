"""Temporarily remove receipt validation, prove the test fails, restore exactly."""
import os,subprocess
from lastcopy.config import ROOT


def main():
    source=ROOT/'lastcopy/cloud_relay.py';original=source.read_bytes()
    before=b'if receipt!=expected:raise ValueError'
    if original.count(before)!=1:raise ValueError('Mutation target is ambiguous')
    try:
        source.write_bytes(original.replace(before,b'if False:raise ValueError'))
        r=subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),'-m','pytest','tests/test_cloud_relay.py::test_wrong_delivery_receipt_never_marks_source_sent','-q'],
            cwd=ROOT,env=dict(os.environ,SAMPLE_MODE='true',LASTCOPY_DEVICE_TRANSFER_ENABLED='false'),capture_output=True,text=True,timeout=90)
        if r.returncode==0 or 'DID NOT RAISE' not in r.stdout:raise ValueError('Broken delivery acknowledgement was not caught')
        (ROOT/'docs/verification/cloud/receipt-mutation-red.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
    finally:source.write_bytes(original)
    if source.read_bytes()!=original:raise ValueError('Original comparator module was not restored')
    print('PASS test rejected meaningful broken delivery-receipt validation; implementation restored byte-for-byte')


if __name__=='__main__':main()
