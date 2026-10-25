"""Set only the verified LastCopy project's server-side production settings.

Credential values go through stdin, never command arguments or tool output.
This configures the existing project; deployment is a separate action.
"""
import json,subprocess,os
from lastcopy.config import ROOT


def main():
    project=json.loads((ROOT/'.vercel/project.json').read_text(encoding='utf-8'))
    if project['projectId']!='prj_r8QG2m01johhvamO9OXTbQuXxHka':raise ValueError('Unexpected linked project')
    secret=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    cli='C:/Users/IYANUOLUWA/AppData/Local/npm-cache/_npx/43d8461e34b9b106/node_modules/vercel/dist/index.js'
    settings={'LASTCOPY_CLOUD_ACCESS':'true','PUBLIC_APP_ORIGIN':'https://lastcopy-five.vercel.app',
        'API_ORIGIN':'https://api-18-141-113-136.sslip.io','LASTCOPY_TRANSPORT_KEY':secret['transport_key']}
    receipt=[]
    for key,value in settings.items():
        command=['node',cli,'env','add',key,'production','--force','--yes','--sensitive' if key=='LASTCOPY_TRANSPORT_KEY' else '--no-sensitive']
        result=subprocess.run(command,input=value,text=True,capture_output=True,cwd=ROOT,env=dict(os.environ,NO_UPDATE_NOTIFIER='1'),timeout=90)
        if result.returncode:raise ValueError('Vercel configuration failed for '+key+'; no secret output emitted')
        receipt.append({'name':key,'target':'production','secret':key=='LASTCOPY_TRANSPORT_KEY','exit_code':0})
    (ROOT/'docs/verification/cloud/vercel-settings.json').write_text(json.dumps({'project':'lastcopy','variables':receipt,'deployed':False},indent=2)+'\n',encoding='utf-8')
    print('Configured four production server settings on existing LastCopy project; secret values not printed. Deployment remains separate.')


if __name__=='__main__':main()
