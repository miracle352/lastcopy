import json, soundfile as sf, numpy as np
from kokoro import KPipeline
p = KPipeline(lang_code='a')
import sys
SR=24000; out=json.load(open('timing.json')) if len(sys.argv)>1 else {}
ONLY=sys.argv[1:]
for scene, lines in json.load(open('script.json')):
    if ONLY and scene not in ONLY: continue
    parts=[]; words=[]; caps=[]; t=0.45
    parts.append(np.zeros(int(SR*0.45),dtype=np.float32))
    for li,text in enumerate(lines):
        cap_start=t
        for r in p(text, voice='af_heart', speed=0.97):
            a=r.audio.numpy() if hasattr(r.audio,'numpy') else np.asarray(r.audio)
            for tk in (r.tokens or []):
                if tk.start_ts is not None and tk.text.strip() and any(ch.isalnum() for ch in tk.text):
                    words.append({'w':tk.text,'s':round(t+tk.start_ts,3),'e':round(t+(tk.end_ts or tk.start_ts+.2),3),'line':len(caps)})
            parts.append(a); t+=len(a)/SR
        caps.append({'text':text,'s':round(cap_start,3),'e':round(t,3)})
        gap=0.5 if li<len(lines)-1 else 0.7
        parts.append(np.zeros(int(SR*gap),dtype=np.float32)); t+=gap
    audio=np.concatenate(parts); sf.write(f'{scene}.wav',audio,SR)
    out[scene]={'dur':round(len(audio)/SR,3),'words':words,'caps':caps}
    print(scene, out[scene]['dur'], len(words))
json.dump(out,open('timing.json','w'))
