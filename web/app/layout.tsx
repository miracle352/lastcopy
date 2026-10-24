import type { Metadata } from "next";
import "./style.css";
import Link from 'next/link';

export const metadata: Metadata = {
  title: "LastCopy · Check your field records",
  description: "Compare field exports, review gaps and verify permitted recovery with evidence.",
  robots: {index: false, follow: false}
};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><a className="skip" href="#main">Skip to content</a><header className="site-header"><Link href="/" className="brand">LastCopy</Link><nav aria-label="Main navigation"><Link href="/app">Check copies</Link><Link href="/app#saved-checks">Saved checks</Link></nav><span>Private evidence · local application</span></header>{children}<footer className="site-footer">Only supplied sources and checked scope are assessed. Keep the original exports. <Link href="/app">Start a check</Link></footer></body></html>;
}
