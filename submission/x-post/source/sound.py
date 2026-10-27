# Code-synthesised soundtrack: warm pad + soft pulse, hits on scene cuts. No samples, no AI.
import numpy as np, wave
SR=48000; D=50.0; n=int(SR*D); t=np.arange(n)/SR
def env(a,r,start,length):
    e=np.zeros(n); s=int(start*SR); L=int(length*SR); L=min(L,n-s)
    x=np.arange(L)/SR; e[s:s+L]=np.minimum(1,x/a)*np.exp(-np.maximum(0,x-a)/r); return e
out=np.zeros(n)
# chord progression (A minor -> F -> C -> G -> resolve), changes per scene
chords=[(0,[220,261.63,329.63]),(11,[174.61,220,261.63]),(19.6,[261.63,329.63,392]),(25.6,[196,246.94,293.66]),(32,[174.61,220,261.63]),(38.6,[261.63,329.63,392]),(44,[220,277.18,329.63])]
for i,(st,fr) in enumerate(chords):
    en=chords[i+1][0] if i+1<len(chords) else D
    m=np.zeros(n); a,b=int(st*SR),int(en*SR); m[a:b]=1
    # crossfade edges
    fade=int(.6*SR); 
    if b-a>2*fade: m[a:a+fade]=np.linspace(0,1,fade); m[b-fade:b]=np.linspace(1,0,fade)
    for f in fr:
        for det in (-0.6,0.6):
            out+=m*0.05*np.sin(2*np.pi*(f*(1+det/1200))*t)*(0.75+0.25*np.sin(2*np.pi*0.2*t))
        out+=m*0.025*np.sin(2*np.pi*f/2*t)
# pulse (soft kick) every beat at 100 bpm from 4.6s, quieter in calm scenes
beat=60/100
for k in np.arange(4.6,D-2,beat):
    L=int(.25*SR); s=int(k*SR)
    if s+L>n: break
    x=np.arange(L)/SR; f=55+60*np.exp(-x*30)
    out[s:s+L]+=0.22*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*14)
# hits on cuts
for c in [4.6,7.3,11,12.45,15.6,19.9,26.9,27.28,27.66,28.04,28.42,32,38.6,39.8,44]:
    L=int(1.2*SR); s=int(c*SR); L=min(L,n-s); x=np.arange(L)/SR
    noise=np.random.default_rng(int(c*100)).standard_normal(L)
    out[s:s+L]+=0.06*noise*np.exp(-x*9) + 0.18*np.sin(2*np.pi*(80*np.exp(-x*3))*x)*np.exp(-x*6)
# tablet shatter whoosh
s=int(12.4*SR); L=int(1.6*SR); x=np.arange(L)/SR; nz=np.random.default_rng(7).standard_normal(L)
nz=np.convolve(nz,np.ones(40)/40,'same'); out[s:s+L]+=0.25*nz*np.sin(np.pi*x/1.6)
# master fade
out*=np.minimum(1,t/1.0)*np.minimum(1,(D-t)/2.0)
out/=np.max(np.abs(out))*1.15
st=np.stack([out,np.roll(out,int(.012*SR))],1)
w=wave.open('music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype('<i2').tobytes());w.close()
print('ok')
