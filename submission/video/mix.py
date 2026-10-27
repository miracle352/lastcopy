import json, numpy as np, soundfile as sf
SR=48000
T=json.load(open('timing.json'))
ORDER=[['cold',2.4],['problem',.6],['brand',1.0],['zetaris',1.0],['agents',.8],['bytes',.5],['decide',1.0],['adversary',.8],['proof',1.0],['blind',1.2],['different',1.0],['close',3.2]]
S={};acc=0
for k,h in ORDER: S[k]=acc; acc+=T[k]['dur']+h
D=acc+1.0; n=int(D*SR); t=np.arange(n)/SR
vo=np.zeros(n)
for k,_ in ORDER:
    a,sr=sf.read(f'{k}.wav'); 
    if a.ndim>1: a=a.mean(1)
    a=np.interp(np.arange(int(len(a)*SR/sr))/SR, np.arange(len(a))/sr, a)
    s=int(S[k]*SR); vo[s:s+len(a)]+=a[:n-s]
vo=vo/np.max(np.abs(vo))*0.89
# music bed: slow chords per scene, warm pad + soft pulse
chords={'cold':[110,130.81,164.81],'problem':[87.31,110,130.81],'brand':[130.81,164.81,196],'zetaris':[98,123.47,146.83],'agents':[110,130.81,164.81],'bytes':[87.31,110,130.81],'decide':[130.81,164.81,196],'adversary':[103.83,130.81,155.56],'proof':[98,123.47,146.83],'blind':[110,138.59,164.81],'different':[130.81,164.81,196],'close':[110,138.59,164.81]}
m=np.zeros(n)
keys=[k for k,_ in ORDER]
for i,k in enumerate(keys):
    a=int(max(0,S[k]-.4)*SR); b=int((S[keys[i+1]] if i+1<len(keys) else D)*SR); L=b-a
    env=np.ones(L); f=min(int(.8*SR),L//3); env[:f]=np.linspace(0,1,f); env[-f:]=np.linspace(1,0,f)
    x=np.arange(L)/SR+a/SR
    for fr in chords[k]:
        for det,amp in ((1,0.5),(2,0.28),(4,0.08)):
            m[a:b]+=env*amp*0.03*np.sin(2*np.pi*fr*det*x*(1+0.0007*np.sin(2*np.pi*.15*x)))
# soft pulse from brand onwards
beat=60/92
for c in np.arange(S['zetaris'],S['different'],beat):
    s=int(c*SR); L=int(.3*SR); x=np.arange(L)/SR; f=50+50*np.exp(-x*28)
    m[s:s+L]+=0.10*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*12)
# hits on scene cuts
rng=np.random.default_rng(3)
for k in keys[1:]:
    s=int(S[k]*SR)-int(.05*SR); L=int(1.6*SR); x=np.arange(L)/SR
    nz=np.convolve(rng.standard_normal(L),np.ones(30)/30,'same')
    m[s:s+L]+=0.10*nz*np.exp(-x*5)+0.16*np.sin(2*np.pi*(65*np.exp(-x*2))*x)*np.exp(-x*4)
m=m/np.max(np.abs(m))*0.30
# duck music under voice
envv=np.convolve(np.abs(vo),np.ones(int(.25*SR))/int(.25*SR),'same')
duck=1-0.45*np.clip(envv/0.05,0,1)
mix=vo+m*duck
mix*=np.minimum(1,t/0.5)*np.minimum(1,(D-t)/2.5)
mix=mix/np.max(np.abs(mix))*0.95
sf.write('mix.wav',np.stack([mix,mix],1),SR)
print('dur',D)
