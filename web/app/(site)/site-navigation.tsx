'use client';
import {usePathname} from 'next/navigation';
import {useEffect,useRef,useState} from 'react';
import {Icon,Mark} from './icons';
import OwnerSignout from './owner-signout';

export default function SiteNavigation({hosted=false}:{hosted?:boolean}){
  const path=usePathname(), workspace=path.startsWith('/app')||path.startsWith('/runs/')||path==='/integrations'||path==='/account';
  const [open,setOpen]=useState(false);const toggle=useRef<HTMLButtonElement>(null);
  useEffect(()=>setOpen(false),[path]);
  const links=workspace?[['/app','Record check'],['/app#saved-checks','Previous reports'],['/account','Your data']]:[['/#how-it-works','How it works'],['/demo','Try LastCopy'],['/signup','Create account']];
  return <header className="site-header" data-workspace={workspace}>
    <a href="/" className="brand" aria-label="LastCopy home"><Mark/><span>LastCopy<span className="brand-dot">.</span></span></a>
    <nav className="desktop-navigation" aria-label="Main navigation">{links.map(([href,name])=><a key={href} href={href} aria-current={path===href?'page':undefined}>{name}</a>)}</nav>
    <a className="header-action" onClick={()=>setOpen(false)} href={workspace?'/app/new':'/app'}><span className="nav-action-full">{workspace?'Start another check':'Check my records'}</span><span className="nav-action-short">Check records</span><Icon name="arrow" size={16}/></a>
    {hosted&&workspace&&<div className="desktop-signout"><OwnerSignout/></div>}
    <button ref={toggle} type="button" className="navigation-toggle quiet" aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} aria-controls="mobile-navigation" onClick={()=>setOpen(!open)}><span/><span/></button>
    {open&&<nav id="mobile-navigation" className="mobile-navigation" aria-label="Mobile navigation" onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);toggle.current?.focus();}}}>{links.map(([href,name])=><a key={href} href={href} onClick={()=>setOpen(false)}>{name}<Icon name="arrow" size={17}/></a>)}{hosted&&workspace&&<div className="mobile-signout"><OwnerSignout/></div>}</nav>}
  </header>;
}

export function SiteFooter(){const path=usePathname();const workspace=path.startsWith('/app')||path.startsWith('/runs/');return <footer className="site-footer" data-workspace={workspace}><div className="footer-signature"><Mark/><span>Every record matters.</span></div><p>Keep the originals. Keep the evidence.</p><nav aria-label="Footer"><a href="/#faq">Scope & limitations</a><a href="/technical">Technical notes</a><a href="/privacy">Privacy</a></nav></footer>;}
