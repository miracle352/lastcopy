"""Sanitized tracked source archive; excludes private evidence and build outputs."""
import io,json,subprocess,tarfile
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    included=[];out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as archive:
        for name in sorted(set(names)):
            if not name:continue
            p=ROOT/name
            if not p.is_file() or p.is_symlink():continue
            if name.startswith(('private/','.git/','.env','.venv/','node_modules/','web/.next/','docs/verification/')):continue
            raw=p.read_bytes()
            if p.suffix in ('.py','.ts','.tsx','.mjs','.css'):
                try:raw.decode('utf-8')
                except UnicodeDecodeError:raise ValueError('Runtime source is not UTF-8: '+name) from None
            info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644
            archive.addfile(info,io.BytesIO(raw));included.append({'path':name,'sha256':digest(raw)})
    data=out.getvalue();target=ROOT/'private/cloud/source.tar.gz';target.write_bytes(data)
    receipt={'archive_sha256':digest(data),'archive_bytes':len(data),'files':included,'private_sources_included':False}
    (ROOT/'private/cloud/source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(included),'bytes':len(data),'sha256':digest(data),'private_sources_included':False}))


if __name__=='__main__':main()
