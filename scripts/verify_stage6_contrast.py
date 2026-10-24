"""Deterministic WCAG contrast calculations for the authored semantic pairs."""
import json
from pathlib import Path


def luminance(hex):
    rgb=[int(hex[i:i+2],16)/255 for i in (1,3,5)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return sum(v*w for v,w in zip(linear,(.2126,.7152,.0722)))


def main():
    pairs=[('body','#eaf5f0','#060c0c'),('muted body','#a8bdb6','#060c0c'),('secondary labels','#849c94','#0d1818'),
        ('primary control','#06251d','#42dbb3'),('disabled control','#b3c9c0','#29413b'),
        ('evidence blue','#73bdf4','#10221c'),('missing amber','#f2b66d','#231e14'),
        ('verified badge','#a8ead2','#12281f'),('sample badge','#b0c9c2','#152525'),
        ('replay badge','#a7d8fc','#102331'),('error','#ffa797','#291c18'),
        ('footer secondary','#849c94','#060c0c'),('input placeholder','#849c94','#0b1514')]
    results=[]
    for name,fg,bg in pairs:
        a,b=sorted((luminance(fg),luminance(bg)))
        ratio=(b+.05)/(a+.05)
        results.append({'pair':name,'foreground':fg,'background':bg,'ratio':round(ratio,2),'normal_text_aa':ratio>=4.5})
    assert all(r['normal_text_aa'] for r in results)
    receipt={'method':'WCAG sRGB relative luminance, exact authored opaque semantic pairs','minimum':min(r['ratio'] for r in results),
        'pairs':results,'scope':'Token-pair checks, not a complete rendered-page accessibility audit; gradients/translucency require visual review'}
    out=Path(__file__).resolve().parents[1]/'docs/verification/stage6/contrast.json'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
