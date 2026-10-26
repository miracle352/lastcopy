'use client';
import {useEffect,useState,type ComponentType} from 'react';

/** Enhancement only: first content and controls never wait for choreography. */
export default function MotionLoader(){
  const [Motion,setMotion]=useState<ComponentType|null>(null);
  useEffect(()=>{
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    let active=true;
    let started=false;const load=()=>{if(started)return;started=true;void import('./motion').then(m=>{if(active)setMotion(()=>m.default);});};
    addEventListener('scroll',load,{once:true,passive:true});addEventListener('keydown',load,{once:true});
    if(scrollY>0||location.hash)load();
    return()=>{active=false;removeEventListener('scroll',load);removeEventListener('keydown',load);};
  },[]);
  return Motion?<Motion/>:null;
}
