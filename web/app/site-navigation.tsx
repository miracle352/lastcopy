'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {useEffect,useRef,useState} from 'react';
import {Icon,Mark} from './icons';

export default function SiteNavigation(){
  const path=usePathname(), workspace=path.startsWith('/app')||path.startsWith('/runs/');
  const [open,setOpen]=useState(false);const toggle=useRef<HTMLButtonElement>(null);
  useEffect(()=>setOpen(false),[path]);
  const links=workspace?[['/app','Record check'],['/app#saved-checks','Previous reports'],['/#faq','Help']]:[['/#how-it-works','How it works'],['/demo','Try LastCopy'],['/signup','Create account']];
  return <header className="site-header" data-workspace={workspace}>
    <Link prefetch={false} href="/" className="brand" aria-label="LastCopy home"><Mark/><span>LastCopy<span className="brand-dot">.</span></span></Link>
    <nav className="desktop-navigation" aria-label="Main navigation">{links.map(([href,name])=><Link prefetch={false} key={href} href={href} aria-current={path===href?'page':undefined}>{name}</Link>)}</nav>
    <Link prefetch={false} className="header-action" aria-label={workspace?'Start another check':'Check my records'} onClick={()=>setOpen(false)} href={workspace?'/app/new':'/app'}><span className="nav-action-full">{workspace?'Start another check':'Check my records'}</span><span className="nav-action-short">Check records</span><Icon name="arrow" size={16}/></Link>
    <button ref={toggle} type="button" className="navigation-toggle quiet" aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} aria-controls="mobile-navigation" onClick={()=>setOpen(!open)}><span/><span/></button>
    {open&&<nav id="mobile-navigation" className="mobile-navigation" aria-label="Mobile navigation" onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);toggle.current?.focus();}}}>{links.map(([href,name])=><Link prefetch={false} key={href} href={href} onClick={()=>setOpen(false)}>{name}<Icon name="arrow" size={17}/></Link>)}</nav>}
  </header>;
}

export function SiteFooter(){const path=usePathname();const workspace=path.startsWith('/app')||path.startsWith('/runs/');return <footer className="site-footer" data-workspace={workspace}><div className="footer-signature"><Mark/><span>Every record matters.</span></div><p>Keep the originals. Keep the evidence.</p><nav aria-label="Footer"><Link prefetch={false} href="/#faq">Scope & limitations</Link><Link prefetch={false} href="/technical">Technical notes</Link></nav></footer>;}
