import type { Metadata } from "next";
import "./style.css";
import './landing.css';
import './responsive.css';
import Link from 'next/link';
import {Mark,Icon} from './icons';
import Motion from './motion-loader';

export const metadata: Metadata = {
  title: "LastCopy · Check your field records",
  description: "Compare field exports, review gaps and verify permitted recovery with evidence.",
  robots: {index: false, follow: false}
};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><head><link rel="preload" href="/fonts/figtree-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/><link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/></head><body><a className="skip" href="#main">Skip to content</a><header className="site-header"><Link prefetch={false} href="/" className="brand" aria-label="LastCopy home"><Mark/><span>LastCopy<span className="brand-dot">.</span></span></Link><nav aria-label="Main navigation"><Link prefetch={false} href="/#how-it-works">How it works</Link><Link prefetch={false} href="/app">Check copies</Link><Link prefetch={false} href="/app#saved-checks">Saved checks</Link></nav><Link prefetch={false} className="header-action" href="/app?sample=media">Try a sample<Icon name="arrow" size={16}/></Link></header>{children}<footer className="site-footer"><div className="footer-intro"><Link prefetch={false} href="/" className="brand"><Mark/><span>LastCopy<span className="brand-dot">.</span></span></Link><p>Bring every record home.<br/>Keep the evidence with it.</p><span className="footer-local"><Icon name="shield" size={14}/> Private evidence · local application</span></div><div className="footer-links"><div><h2>Workspace</h2><Link prefetch={false} href="/app?sample=media">Check a sample</Link><Link prefetch={false} href="/app?import=true">Add exports</Link><Link prefetch={false} href="/app#saved-checks">Saved checks</Link></div><div><h2>Understand</h2><Link prefetch={false} href="/#how-it-works">How it works</Link><Link prefetch={false} href="/#evidence">Evidence & recovery</Link><Link prefetch={false} href="/#faq">Scope & limitations</Link><Link prefetch={false} href="/technical">Technical notes</Link></div></div><div className="footer-bottom"><span>Only supplied sources and checked scope are assessed.</span><span>Keep the originals. Always.</span></div></footer><Motion/></body></html>;
}
