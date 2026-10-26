import json
import httpx
import pytest
from scripts import verify_zetaris_local as module


def test_stopped_driver_is_rejected_before_login_even_when_ui_is_healthy(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'BUNDLE',tmp_path)
    (tmp_path/'lastcopy-prepared.json').write_text(json.dumps({'project':module.PROJECT,'images':{'UI_IMAGE':'official/ui','DRIVER_IMAGE':'official/driver'}}))
    (tmp_path/'.env').write_text('GUI_URL=http://localhost:3130\nZETARIS_ADMIN_EMAIL=synthetic@example.test\nZETARIS_ADMIN_PASSWORD=test-only\n')
    calls=[];http=[]
    def container(command,**kwargs):
        service=command[-1];calls.append(service)
        assert kwargs['timeout']==15
        return json.dumps({'Project':module.PROJECT,'State':'running' if service=='ui' else 'exited','Image':'official/'+service,'Health':'healthy'})
    monkeypatch.setattr(module.subprocess,'check_output',container)
    with httpx.Client(transport=httpx.MockTransport(lambda r:http.append(r))) as client:
        with pytest.raises(RuntimeError,match='driver is not ready'):module.connect(client)
    assert calls==['ui','driver'] and not http
