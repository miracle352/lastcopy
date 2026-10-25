import type { Metadata } from "next";
import "./style.css";
import './landing.css';
import './responsive.css';
import './redesign.css';
import './glass.css';
import SiteNavigation,{SiteFooter} from './site-navigation';
import Motion from './motion-loader';
import OwnerSignout from './owner-signout';

export const metadata: Metadata = {
  title: "LastCopy · Check your field records",
  description: "Compare field exports, review gaps and verify permitted recovery with evidence.",
  robots: {index: false, follow: false}
};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><head><link rel="preload" href="/fonts/figtree-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/><link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/></head><body><a className="skip" href="#main">Skip to content</a><SiteNavigation/>{children}{process.env.LASTCOPY_CLOUD_ACCESS==='true'&&<div style={{textAlign:'right',padding:'0 var(--gutter,24px)'}}><OwnerSignout/></div>}<SiteFooter/><Motion/></body></html>;
}
