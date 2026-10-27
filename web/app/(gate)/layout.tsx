import type {Metadata} from 'next';
import './gate.css';
import {Mark,REPO} from './chrome';

export const metadata: Metadata = {
  title: 'LastCopy · Is it safe to wipe this tablet?',
  description: 'One answer per field tablet: safe to wipe, recover first, or hold. Proven byte-for-byte, explained in plain language.',
  robots: {index: true, follow: true},
};

export default function GateLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en">
    <head>
      <link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/>
      <link rel="preload" href="/fonts/figtree-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/>
    </head>
    <body>
      <a className="skip" href="#main">Skip to content</a>
      <div className="backdrop" aria-hidden="true"/>
      <header className="nav"><div className="wrap">
        <a className="brand" href="/" aria-label="LastCopy home"><Mark/>LastCopy</a>
        <nav aria-label="Main">
          <a href="/#problem">Problem</a><a href="/#gate">Try the gate</a><a href="/#agents">Agents</a><a href="/#sponsors">Under the hood</a><a href={REPO}>GitHub</a>
        </nav>
        <a className="cta" href="/demo">Watch an investigation →</a>
      </div></header>
      {children}
      <footer className="foot"><div className="wrap">
        <div><a className="brand" href="/"><Mark size={18}/>LastCopy</a><p style={{marginTop: 10, color: 'var(--muted)', fontSize: '.85rem'}}>Code proves. Agents investigate. Originals are never modified.</p></div>
        <nav aria-label="Footer"><a href="/demo">Investigation replay</a><a href={REPO}>Source &amp; README</a><a href="/technical">Technical notes</a><a href="/privacy">Privacy</a></nav>
      </div></footer>
    </body>
  </html>;
}
