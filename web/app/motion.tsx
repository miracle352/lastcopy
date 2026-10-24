'use client';
import {useEffect} from 'react';
import {usePathname} from 'next/navigation';
/** Presentation only. Motion timing never determines run or recovery state. */
export default function Motion(){const path=usePathname();useEffect(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');let raf=0;const observed=new Set<Element>();
  const observer=new IntersectionObserver(entries=>{for(const e of entries){e.target.classList.toggle('in-viewport',e.isIntersecting);if(e.isIntersecting)e.target.classList.add('revealed');}scroll();},{threshold:.08});
  function scan(){for(const e of document.querySelectorAll('[data-reveal], [data-ambient], [data-scroll-story]'))if(!observed.has(e)){observed.add(e);observer.observe(e);}}
  function frame(){raf=0;if(reduced.matches)return;for(const e of document.querySelectorAll<HTMLElement>('[data-scroll-story].in-viewport')){const r=e.getBoundingClientRect();e.style.setProperty('--story-progress',String(Math.min(1,Math.max(0,(innerHeight-r.top)/(innerHeight+r.height)))));}}
  function scroll(){if(!raf)raf=requestAnimationFrame(frame);}function visible(){document.documentElement.dataset.motionPaused=String(document.hidden);}
  scan();visible();const mutations=new MutationObserver(scan);mutations.observe(document.body,{childList:true,subtree:true});addEventListener('scroll',scroll,{passive:true});document.addEventListener('visibilitychange',visible);reduced.addEventListener('change',scroll);scroll();
  return()=>{observer.disconnect();mutations.disconnect();removeEventListener('scroll',scroll);document.removeEventListener('visibilitychange',visible);reduced.removeEventListener('change',scroll);if(raf)cancelAnimationFrame(raf);};
},[path]);return null;}
