import json,os,subprocess,sys
import pytest
from scripts.backup_databases import ENKETO_KEYS,sha,snapshot_enketo
from scripts.verify_enketo_restore import validate


def test_link_backup_keeps_only_required_keys_and_valid_redis(tmp_path,monkeypatch):
    keys=tmp_path/'keys';keys.mkdir();stage=tmp_path/'stage'
    for name in ENKETO_KEYS:(keys/name).write_bytes(('synthetic-'+name).encode())
    (keys/'provider.env').write_bytes(b'do not copy')
    original={name:sha(keys/name) for name in ENKETO_KEYS}
    def run(command,**kwargs):
        assert command==['docker','exec','lastcopy-cloud-odk-enketo_redis_main-1','redis-cli','--rdb','-']
        assert kwargs['timeout']==60 and kwargs['check'] and callable(kwargs['preexec_fn'])
        kwargs['stdout'].write(b'REDIS0012'+b'synthetic bounded snapshot')
        return subprocess.CompletedProcess(command,0)
    monkeypatch.setattr(subprocess,'run',run)
    files=snapshot_enketo(stage,keys)
    assert set(files)=={'enketo/main.rdb',*('enketo/keys/'+name for name in ENKETO_KEYS)}
    assert not (stage/'enketo/keys/provider.env').exists()
    assert {name:sha(keys/name) for name in ENKETO_KEYS}==original
    assert {name:sha(stage/'enketo/keys'/name) for name in ENKETO_KEYS}==original
    manifest={'files':{name:sha(stage/name) for name in files}}
    assert validate(stage,manifest)==manifest['files']
    (stage/'enketo/main.rdb').write_bytes(b'REDIS0012changed')
    with pytest.raises(ValueError,match='integrity'):validate(stage,manifest)


@pytest.mark.parametrize('bad',['absent','oversized','invalid-rdb'])
def test_link_backup_refuses_incomplete_or_corrupt_state(tmp_path,monkeypatch,bad):
    keys=tmp_path/'keys';keys.mkdir()
    for name in ENKETO_KEYS:(keys/name).write_bytes(b'synthetic-key')
    if bad=='absent':(keys/ENKETO_KEYS[0]).unlink()
    if bad=='oversized':(keys/ENKETO_KEYS[0]).write_bytes(b'x'*4097)
    def run(command,**kwargs):kwargs['stdout'].write(b'not-a-redis-dump')
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(ValueError):snapshot_enketo(tmp_path/'stage',keys)


@pytest.mark.parametrize('changed',[False,True])
def test_restore_is_isolated_and_disagreement_never_passes(tmp_path,monkeypatch,capsys,changed):
    from scripts.verify_enketo_restore import main
    stage=tmp_path/'stage';(stage/'enketo/keys').mkdir(parents=True)
    for name in ENKETO_KEYS:(stage/'enketo/keys'/name).write_bytes(b'synthetic-key')
    (stage/'enketo/main.rdb').write_bytes(b'REDIS0012synthetic')
    files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()}
    (stage/'manifest.json').write_text(json.dumps({'files':files}))
    commands=[]
    def output(command,**kwargs):
        commands.append(command)
        if command[1]=='inspect':return 'sha256:'+'a'*64+'\n'
        return json.dumps([1,('b' if changed and 'lastcopy-cloud-odk-enketo_redis_main-1' in command else 'a')*40]).encode()
    def run(command,**kwargs):
        commands.append(command);return subprocess.CompletedProcess(command,0,stdout=b'PONG')
    monkeypatch.setattr(subprocess,'check_output',output);monkeypatch.setattr(subprocess,'run',run)
    monkeypatch.setattr(sys,'argv',['verify_enketo_restore','--stage',str(stage)])
    if changed:
        with pytest.raises(ValueError,match='differs'):main()
        assert not capsys.readouterr().out
    else:
        main();assert json.loads(capsys.readouterr().out)['production_writes']==0
    start=next(c for c in commands if c[1]=='run')
    assert start[start.index('--network')+1]=='none' and '--read-only' in start
    assert '-p' not in start and '--publish' not in start
    assert commands[-1][:3]==['docker','rm','-f'] and commands[-1][-1].startswith('lastcopy-restore-enketo-')
    assert {name:sha(stage/name) for name in files}==files


@pytest.mark.skipif(os.name!='posix',reason='Production file-size guard uses the Linux kernel')
@pytest.mark.parametrize('excessive',[False,True])
def test_linux_snapshot_output_limit_is_enforced_before_disk_growth(tmp_path,monkeypatch,excessive):
    keys=tmp_path/'keys';keys.mkdir()
    for name in ENKETO_KEYS:(keys/name).write_bytes(b'synthetic-key')
    real_run=subprocess.run
    def run(command,**kwargs):
        program="import os;os.write(1,b'REDIS0012');"+("[os.write(1,b'x'*4096) for _ in range(8193)]" if excessive else "os.write(1,b'synthetic')")
        return real_run([sys.executable,'-c',program],**kwargs)
    monkeypatch.setattr(subprocess,'run',run)
    if excessive:
        with pytest.raises(subprocess.CalledProcessError):snapshot_enketo(tmp_path/'stage',keys)
        assert (tmp_path/'stage/enketo/main.rdb').stat().st_size<=32*1024**2
    else:assert 'enketo/main.rdb' in snapshot_enketo(tmp_path/'stage',keys)
