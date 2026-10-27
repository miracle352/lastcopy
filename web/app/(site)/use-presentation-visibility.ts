'use client';
import {useEffect,useState,type RefObject} from 'react';

/** Visibility controls presentation only, never completion of a real comparison. */
export function usePresentationVisibility(ref:RefObject<HTMLElement|null>){
  const [active,setActive]=useState(false),[reduced,setReduced]=useState(false);
  useEffect(()=>{
    const preference=matchMedia('(prefers-reduced-motion: reduce)');let visible=false;
    const update=()=>{setActive(visible&&!document.hidden);setReduced(preference.matches);};
    const observer=new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting??false;update();},{threshold:.12});
    if(ref.current)observer.observe(ref.current);update();
    document.addEventListener('visibilitychange',update);preference.addEventListener('change',update);
    return()=>{observer.disconnect();document.removeEventListener('visibilitychange',update);preference.removeEventListener('change',update);};
  },[ref]);
  return {active,reduced};
}
