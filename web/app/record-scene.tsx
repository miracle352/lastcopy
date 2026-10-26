import {Icon,Mark} from './icons';

/** An illustration controlled by scroll, never a claim about a real run. */
export default function RecordScene(){return <figure className="record-scene journey-art">
  <div className="journey-caption"><span>ONE RECORD. EVERY PART.</span><span>Illustration</span></div>
  <div className="journey-stage">
    <svg className="journey-wires" viewBox="0 0 600 440" fill="none" aria-hidden="true"><path className="journey-wire" d="M130 270 C170 345 300 350 370 290 S470 200 485 110"/><path className="journey-wire-lit" pathLength="1" d="M130 270 C170 345 300 350 370 290 S470 200 485 110"/><circle cx="130" cy="270" r="5"/><circle cx="485" cy="110" r="5"/></svg>
    <article className="journey-original"><div className="journey-original-top"><Icon name="document" size={20}/><span>FIELD ORIGINAL</span><small>017</small></div><p className="journey-paper-title">North inlet.<br/><em>Nothing left behind.</em></p><div className="water-sketch" aria-hidden="true"><svg viewBox="0 0 240 80" fill="none"><path d="M0 57 Q30 40 60 57 T120 57 T180 57 T240 57 M0 68 Q30 51 60 68 T120 68 T180 68 T240 68"/><path d="M85 43V18h55v25M111 18V7h44v11h-15M93 43h39"/></svg></div><dl><div><dt>Condition</dt><dd>Working</dd></div><div><dt>Repeat answers</dt><dd>3 recorded</dd></div><div><dt>Photo</dt><dd>site-photo.jpg</dd></div></dl><div className="journey-original-seal"><Icon name="shield" size={14}/> Keep these original bytes</div></article>
    <div className="journey-copy"><div><Mark/><span>SERVER COPY</span></div><p className="journey-copy-title">Read the whole record.</p><ul><li><Icon name="check" size={15}/> Answers &amp; versions</li><li><Icon name="check" size={15}/> Every repeat</li><li className="journey-photo"><Icon name="file" size={15}/><span>Photo slot</span><span className="journey-waiting">Check bytes</span><Icon name="check" size={15}/></li></ul><span className="journey-copy-note">A count alone cannot prove a copy.</span></div>
    <div className="journey-parcel" aria-hidden="true"><Icon name="file" size={24}/><span>photo</span></div>
    <div className="journey-result"><span className="journey-phase phase-original"><b>01 / KEEP THE SOURCE</b>Answers, repeats and photo stay together.</span><span className="journey-phase phase-gap"><b>02 / INSPECT THE GAP</b>The record arrived. The photo did not.</span><span className="journey-phase phase-readback"><b>03 / READ IT AGAIN</b>Recovery needs fresh matching bytes.</span></div>
  </div>
  <figcaption>Illustrative record · scroll to follow its path. No upload or live recovery.</figcaption>
</figure>;}
