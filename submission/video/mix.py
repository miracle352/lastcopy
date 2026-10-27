import json, numpy as np, soundfile as sf
SR=48000
T=json.load(open('timing.json'))
ORDER=[['cold',1.4],['problem',.6],['brand',.8],['zetaris',.8],['agents',.6],['bytes',.4],['adversary',.6],['decide',.8],['proof',.8],['blind',.8],['close',4.2]]
S={};acc=0
for k,h in ORDER: S[k]=acc; acc+=T[k]['dur']+h
D=acc+0.5; n=int(D*SR); t=np.arange(n)/SR
def W(sc,word):
    for w in T[sc]['words']:
        if w['w'].lower().strip(".,")==word: return S[sc]+w['s']
TZ=W('close','wipe'); T0=0.8
vo=np.zeros(n)
for k,_ in ORDER:
    a,sr=sf.read(f'{k}.wav')
    a=np.interp(np.arange(int(len(a)*SR/sr))/SR, np.arange(len(a))/sr, a)
    s=int(S[k]*SR); vo[s:s+len(a)]+=a[:n-s]
vo=vo/np.max(np.abs(vo))*0.9
m=np.zeros(n); rng=np.random.default_rng(5)
# low drone that slowly rises in pitch & intensity toward TZ
prog=np.clip(t/TZ,0,1)
base=55*(1+0.12*prog)
ph=2*np.pi*np.cumsum(base)/SR
drone=(np.sin(ph)+0.5*np.sin(2*ph)+0.25*np.sin(3.01*ph))*(0.35+0.65*prog)
drone*=(t<TZ)
m+=0.05*drone
# pad chords per scene (after TZ resolve major)
chords={'cold':[110,130.81,164.81],'problem':[87.31,110,130.81],'brand':[130.81,164.81,196],'zetaris':[98,123.47,146.83],'agents':[110,130.81,164.81],'bytes':[87.31,110,130.81],'adversary':[103.83,130.81,155.56],'decide':[130.81,164.81,196],'proof':[98,123.47,146.83],'blind':[110,138.59,164.81],'close':[130.81,164.81,196,261.63]}
keys=[k for k,_ in ORDER]
for i,k in enumerate(keys):
    a=int(max(0,S[k]-.3)*SR); b=int((S[keys[i+1]] if i+1<len(keys) else D)*SR); L=b-a
    env=np.ones(L); f=min(int(.7*SR),L//3); env[:f]=np.linspace(0,1,f); env[-f:]=np.linspace(1,0,f)
    x=np.arange(L)/SR
    for fr in chords[k]:
        m[a:b]+=env*0.016*(np.sin(2*np.pi*fr*x)+0.4*np.sin(2*np.pi*fr*2.003*x))
# clock ticks every countdown second
rate=150/(TZ-T0)
k=0
while True:
    tt=T0+k/rate
    if tt>=TZ-0.05: break
    s=int(tt*SR); L=int(.04*SR); x=np.arange(L)/SR
    loud=0.05+0.10*(tt>TZ-30)+0.05*(tt>TZ-10)
    hi=2400 if k%2==0 else 1900
    m[s:s+L]+=loud*np.sin(2*np.pi*hi*x)*np.exp(-x*160)+loud*0.5*rng.standard_normal(L)*np.exp(-x*300)
    k+=1
# whoosh + impact on scene cuts
for kk in keys[1:]:
    s=int((S[kk]-.35)*SR); L=int(.9*SR); x=np.arange(L)/SR
    nz=np.convolve(rng.standard_normal(L),np.ones(60)/60,'same')
    m[s:s+L]+=0.25*nz*np.sin(np.pi*x/0.9)**2
# stamps in decide
for w in ['safe','recover','three','four','five']:
    c=W('decide',w); s=int(c*SR); L=int(.5*SR); x=np.arange(L)/SR
    m[s:s+L]+=0.35*np.sin(2*np.pi*(90*np.exp(-x*6))*x)*np.exp(-x*9)
# reset at zero: sweep + big low hit, then silence of drone
s=int(TZ*SR); L=int(2.5*SR); x=np.arange(L)/SR
m[s:s+L]+=0.45*np.sin(2*np.pi*(60*np.exp(-x*1.5))*x)*np.exp(-x*2.2)
sw=np.convolve(rng.standard_normal(L),np.ones(25)/25,'same')*np.exp(-x*3)
m[s:s+L]+=0.25*sw
m=m/np.max(np.abs(m))*0.42
envv=np.convolve(np.abs(vo),np.ones(int(.25*SR))/int(.25*SR),'same')
duck=1-0.4*np.clip(envv/0.05,0,1)
mix=vo+m*duck
mix*=np.minimum(1,t/0.3)*np.minimum(1,(D-t)/2.0)
mix=mix/np.max(np.abs(mix))*0.95
sf.write('mix.wav',np.stack([mix,mix],1),SR); print('D',D,'TZ',TZ)
