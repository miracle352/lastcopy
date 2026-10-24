"""Build-only OFL font download/subsetting; no runtime font-service dependency."""
from pathlib import Path
from urllib.parse import quote
import io,json,hashlib
import httpx
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

PIN='e7db6ca603fd4862010383ff17ffd6cc4ffac1c0'
ROOT=Path(__file__).resolve().parents[1]
FONTS={'fraunces':('Fraunces[SOFT,WONK,opsz,wght].ttf',{'SOFT':50,'WONK':1,'opsz':64,'wght':(400,700)}),
       'figtree':('Figtree[wght].ttf',{'wght':(400,700)})}


def main():
    target=ROOT/'web/public/fonts';target.mkdir(parents=True,exist_ok=True);records=[]
    with httpx.Client(timeout=25,trust_env=False) as client:
        for name,(filename,axes) in FONTS.items():
            base=f'https://raw.githubusercontent.com/google/fonts/{PIN}/ofl/{name}/'
            response=client.get(base+quote(filename));response.raise_for_status()
            license=client.get(base+'OFL.txt');license.raise_for_status()
            if 'SIL OPEN FONT LICENSE' not in license.text: raise ValueError('Expected OFL license')
            font=TTFont(io.BytesIO(response.content),recalcTimestamp=False)
            options=subset.Options();options.flavor='woff2';options.recalc_timestamp=False
            # Latin/Latin extended and UI punctuation. Other scripts use system fallback.
            tool=subset.Subsetter(options=options)
            tool.populate(unicodes=set(range(0x20,0x250))|set(range(0x2000,0x2070))|set(range(0x2190,0x21a0))|{0x2212,0x2219,0x2713,0xfeff,0xfffd})
            tool.subset(font)
            instantiateVariableFont(font,axes,inplace=True)
            font.flavor='woff2';output=target/(name+'-latin.woff2');font.save(output)
            (target/(name+'-OFL.txt')).write_bytes(license.content)
            records.append({'family':name,'source':base+quote(filename),'license':base+'OFL.txt','source_sha256':hashlib.sha256(response.content).hexdigest(),
                'output':str(output.relative_to(ROOT)).replace('\\','/'),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'axes':axes})
    (target/'sources.json').write_text(json.dumps({'commit':PIN,'build_tool':'fonttools 4.61.1','subset':'Latin/Latin extended plus common UI punctuation; other scripts use system fallback','fonts':records},indent=2)+'\n',encoding='utf8')
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
