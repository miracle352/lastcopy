'use client';
import {useEffect,useRef,useState,type ComponentType} from 'react';

/** Load the real comparator interface before it enters view, after the first paint. */
export default function LandingExamples(){
  const ref=useRef<HTMLDivElement>(null),[Examples,setExamples]=useState<ComponentType|null>(null),[failed,setFailed]=useState(false);
  useEffect(()=>{let active=true;const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();void import('./landing-sample').then(m=>{if(active)setExamples(()=>m.default);}).catch(()=>{if(active)setFailed(true);});}},{rootMargin:'500px'});if(ref.current)observer.observe(ref.current);return()=>{active=false;observer.disconnect();};},[]);
  return <div ref={ref} className="deferred-examples">{Examples?<Examples/>:<div className="sample-workbench sample-preview"><p className="eyebrow">SYNTHETIC FILES · ACTUAL COMPARISON</p><h3>Follow a missing photo.</h3>{failed?<p role="alert">The example interface could not load. <a href="/demo">Open the full example check</a> or refresh when your connection returns.</p>:<p>The example opens automatically as you reach it.</p>}<noscript>JavaScript is needed for interactive checks. <a href="/technical">Read the recorded evidence walkthrough</a>.</noscript></div>}</div>;
}
