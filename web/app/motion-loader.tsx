'use client';
import {useEffect,useState,type ComponentType} from 'react';

/** Enhancement only: first content and controls never wait for choreography. */
export default function MotionLoader(){
  const [Motion,setMotion]=useState<ComponentType|null>(null);
  useEffect(()=>{
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    let active=true;
    const load=()=>{void import('./motion').then(m=>{if(active)setMotion(()=>m.default);});};
    const idle='requestIdleCallback' in window?requestIdleCallback(load,{timeout:1200}):null;
    const timer=idle===null?setTimeout(load,0):null;
    return()=>{active=false;if(idle!==null)cancelIdleCallback(idle);if(timer!==null)clearTimeout(timer);};
  },[]);
  return Motion?<Motion/>:null;
}
