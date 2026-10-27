'use client';
import {useEffect} from 'react';
import {usePathname} from 'next/navigation';
import {storyProgress} from '../../lib/story-progress';
/** Presentation only. Motion timing never determines run or recovery state. */
export default function Motion(){const path=usePathname();useEffect(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');let raf=0;const observed=new Set<Element>();
  const observer=new IntersectionObserver(entries=>{for(const e of entries){e.target.classList.toggle('in-viewport',e.isIntersecting);if(e.isIntersecting){e.target.classList.remove('reveal-pending');e.target.classList.add('revealed');}}scroll();},{threshold:0,rootMargin:'0px 0px -5% 0px'});
  function scan(){const added=[...document.querySelectorAll('[data-reveal], [data-ambient], [data-scroll-story]')].filter(e=>!observed.has(e));const pending=new Set(added.filter(e=>e.hasAttribute('data-reveal')&&!reduced.matches&&e.getBoundingClientRect().top>=innerHeight));for(const e of added){observed.add(e);if(pending.has(e))e.classList.add('reveal-pending');observer.observe(e);}}
  function frame(){raf=0;if(reduced.matches||document.hidden)return;const frames=[...observed].filter(e=>e.hasAttribute('data-scroll-story')&&e.classList.contains('in-viewport')).map(node=>{const e=node as HTMLElement,r=e.getBoundingClientRect();return {e,p:storyProgress(r.top,r.height,innerHeight,e.hasAttribute('data-story-hero'))};});for(const {e,p} of frames){e.style.setProperty('--story-progress',String(p));e.dataset.storyStep=String(Math.min(3,Math.floor(p*3)+1));}}
  function scroll(){if(!raf)raf=requestAnimationFrame(frame);}function visible(){document.documentElement.dataset.motionPaused=String(document.hidden);scroll();}function preference(){if(reduced.matches)for(const e of observed){e.classList.remove('reveal-pending');(e as HTMLElement).style.removeProperty('--story-progress');(e as HTMLElement).dataset.storyStep='3';}scroll();}
  scan();visible();const mutations=new MutationObserver(scan);mutations.observe(document.body,{childList:true,subtree:true});addEventListener('scroll',scroll,{passive:true});addEventListener('resize',scroll);document.addEventListener('visibilitychange',visible);reduced.addEventListener('change',preference);scroll();
  return()=>{observer.disconnect();mutations.disconnect();removeEventListener('scroll',scroll);removeEventListener('resize',scroll);document.removeEventListener('visibilitychange',visible);reduced.removeEventListener('change',preference);if(raf)cancelAnimationFrame(raf);for(const e of observed)e.classList.remove('reveal-pending');};
},[path]);return null;}
