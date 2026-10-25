"""Operator-paired desktop link; cloud pause stops new capture/delivery.

PC/emulator must remain running. This cannot read a disconnected physical phone.
Sources and delivery acknowledgements persist privately across process restarts.
"""
import json,signal,threading
from dotenv import dotenv_values
from lastcopy.config import ROOT,Settings
from lastcopy.store import RunStore
from lastcopy.device_transfer import DeviceTransfer
from lastcopy.cloud_relay import Relay
from lastcopy.monitor import stamp


def cycle(transfer,relay):
    control=relay.poll(transfer.status()['state'])
    _,cfg,_,_=transfer.config()
    if cfg['device'] not in control['source_device_ids']:raise ValueError('Paired device is outside the cloud roster')
    if not control['enabled']:return {'state':'paused','message':'Cloud checking is paused; no device capture or delivery started.'}
    transfer.tick()
    count=relay.flush()
    return {'state':transfer.status()['state'],'exports_delivered_this_cycle':count,'preservation_proof':False}


def main():
    config=ROOT/'private/cloud/device-link.env'
    values=dict(dotenv_values(config))
    store=RunStore(ROOT/'private/cloud/device-link-ledger',Settings(values))
    transfer=DeviceTransfer(store);relay=Relay(store);stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
    try:
        while not stop.is_set():
            try:state=cycle(transfer,relay)
            except Exception as e:state={'state':'error','exception_type':type(e).__name__,'message':'Link could not complete; no preservation success inferred.'}
            (ROOT/'private/cloud/device-link-status.json').write_text(json.dumps({'checked_at':stamp(),**state},indent=2)+'\n',encoding='utf-8')
            stop.wait(30)
    finally:relay.close()


if __name__=='__main__':main()
